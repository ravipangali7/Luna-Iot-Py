"""
NCHL ConnectIPS Payment Gateway Service
Handles token generation, payment form creation, and transaction validation
"""
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import pkcs12
import base64
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import os
from decimal import Decimal


class NCHLConnectIPS:
    """
    NCHL ConnectIPS Payment Gateway Integration
    """
    
    def __init__(self, merchant_id=None, app_id=None, app_name=None, app_password=None, 
                 pfx_path=None, pfx_password=None, base_url=None):
        """
        Initialize NCHL ConnectIPS service with credentials
        
        Args:
            merchant_id: Merchant ID from NCHL
            app_id: Application ID from NCHL
            app_name: Application Name
            app_password: App password for Basic Auth
            pfx_path: Path to PFX certificate file
            pfx_password: PFX certificate password
            base_url: ConnectIPS base URL (default: https://login.connectips.com)
        """
        self.merchant_id = merchant_id or os.getenv('NCHL_MERCHANT_ID', '3856')
        self.app_id = app_id or os.getenv('NCHL_APP_ID', 'MER-3856-APP-1')
        self.app_name = app_name or os.getenv('NCHL_APP_NAME', 'LUNA G.P.S. AND RESEARCH CENTER')
        self.app_password = app_password or os.getenv('NCHL_APP_PASSWORD', 'L@Na@Ba35')
        self.pfx_path = pfx_path or os.getenv('NCHL_PFX_PATH', 'LUNAG.pfx')
        self.pfx_password = pfx_password or os.getenv('NCHL_PFX_PASSWORD', 'LuCER3@55')
        self.base_url = base_url or os.getenv('NCHL_BASE_URL', 'https://login.connectips.com')
        self._private_key = None
    
    def _load_private_key(self):
        """Load and cache private key from PFX certificate."""
        if self._private_key is None:
            # Resolve PFX path relative to BASE_DIR if not absolute
            if not os.path.isabs(self.pfx_path):
                from django.conf import settings
                pfx_full_path = os.path.join(settings.BASE_DIR, self.pfx_path)
            else:
                pfx_full_path = self.pfx_path
            
            if not os.path.exists(pfx_full_path):
                raise FileNotFoundError(f"PFX certificate not found at: {pfx_full_path}")
            
            with open(pfx_full_path, 'rb') as f:
                pfx_data = f.read()
            
            # Load PKCS12 using cryptography library
            private_key_obj, certificate, additional_certificates = pkcs12.load_key_and_certificates(
                pfx_data,
                self.pfx_password.encode(),
                backend=default_backend()
            )
            
            if private_key_obj is None:
                raise ValueError("Failed to extract private key from PFX certificate. Check password.")
            
            self._private_key = private_key_obj
        return self._private_key
    
    def _sign_message(self, message):
        """
        Sign message with SHA256withRSA and return Base64 encoded token.
        
        Args:
            message: String message to sign
            
        Returns:
            Base64 encoded signature string
        """
        private_key = self._load_private_key()
        signature = private_key.sign(
            message.encode('utf-8'),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return base64.b64encode(signature).decode('utf-8')
    
    def generate_payment_token(self, txn_id, txn_date, txn_amt, 
                              reference_id, remarks='', particulars='', 
                              txn_crncy='NPR'):
        """
        Generate payment token for transaction.
        
        Args:
            txn_id: Unique transaction ID
            txn_date: Transaction date (DD-MM-YYYY)
            txn_amt: Amount in paisa (as string or int)
            reference_id: Reference ID
            remarks: Optional remarks
            particulars: Optional particulars
            txn_crncy: Currency (default: NPR)
            
        Returns:
            Base64 encoded token
        """
        # Convert amount to string if needed
        txn_amt_str = str(txn_amt)
        
        # Build message string (order is critical!)
        # IMPORTANT: Must include "TOKEN=TOKEN" at the end as per NCHL documentation
        message = (
            f"MERCHANTID={self.merchant_id},"
            f"APPID={self.app_id},"
            f"APPNAME={self.app_name},"
            f"TXNID={txn_id},"
            f"TXNDATE={txn_date},"
            f"TXNCRNCY={txn_crncy},"
            f"TXNAMT={txn_amt_str},"
            f"REFERENCEID={reference_id},"
            f"REMARKS={remarks},"
            f"PARTICULARS={particulars},"
            f"TOKEN=TOKEN"
        )
        
        return self._sign_message(message)
    
    def get_payment_form_data(self, txn_id, txn_amt, reference_id, 
                             remarks='', particulars='', txn_date=None):
        """
        Get payment form data for redirecting to gateway.
        
        Args:
            txn_id: Unique transaction ID
            txn_amt: Amount in paisa
            reference_id: Reference ID
            remarks: Optional remarks
            particulars: Optional particulars
            txn_date: Transaction date (default: today in DD-MM-YYYY)
            
        Returns:
            Dictionary with all form fields including token
        """
        if txn_date is None:
            txn_date = datetime.now().strftime('%d-%m-%Y')
        
        token = self.generate_payment_token(
            txn_id=txn_id,
            txn_date=txn_date,
            txn_amt=txn_amt,
            reference_id=reference_id,
            remarks=remarks,
            particulars=particulars
        )
        
        return {
            'MERCHANTID': self.merchant_id,
            'APPID': self.app_id,
            'APPNAME': self.app_name,
            'TXNID': txn_id,
            'TXNDATE': txn_date,
            'TXNCRNCY': 'NPR',
            'TXNAMT': str(txn_amt),
            'REFERENCEID': reference_id,
            'REMARKS': remarks,
            'PARTICULARS': particulars,
            'TOKEN': token,
            'gateway_url': f'{self.base_url}/connectipswebgw/loginpage'
        }
    
    def validate_transaction(self, reference_id, txn_amt):
        """
        Validate a completed transaction via ConnectIPS API.
        
        Args:
            reference_id: Reference ID (same as TXNID from payment)
            txn_amt: Transaction amount in paisa
            
        Returns:
            Validation response dictionary
        """
        # Build validation message string
        message = (
            f"MERCHANTID={self.merchant_id},"
            f"APPID={self.app_id},"
            f"REFERENCEID={reference_id},"
            f"TXNAMT={txn_amt}"
        )
        
        token = self._sign_message(message)
        
        request_body = {
            'merchantId': int(self.merchant_id),
            'appId': self.app_id,
            'referenceId': reference_id,
            'txnAmt': int(txn_amt),
            'token': token
        }
        
        url = f"{self.base_url}/connectipswebws/api/creditor/validatetxn"
        
        try:
            response = requests.post(
                url,
                json=request_body,
                auth=HTTPBasicAuth(self.app_id, self.app_password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error during validation: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" Response: {e.response.text}"
            raise Exception(error_msg)
    
    def get_transaction_details(self, reference_id, txn_amt):
        """
        Get detailed transaction information via ConnectIPS API.
        
        Args:
            reference_id: Reference ID (same as TXNID from payment)
            txn_amt: Transaction amount in paisa
            
        Returns:
            Transaction details response dictionary
        """
        # Build validation message string (same as validate_transaction)
        message = (
            f"MERCHANTID={self.merchant_id},"
            f"APPID={self.app_id},"
            f"REFERENCEID={reference_id},"
            f"TXNAMT={txn_amt}"
        )
        
        token = self._sign_message(message)
        
        request_body = {
            'merchantId': int(self.merchant_id),
            'appId': self.app_id,
            'referenceId': reference_id,
            'txnAmt': int(txn_amt),
            'token': token
        }
        
        url = f"{self.base_url}/connectipswebws/api/creditor/gettxndetail"
        
        try:
            response = requests.post(
                url,
                json=request_body,
                auth=HTTPBasicAuth(self.app_id, self.app_password),
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error getting transaction details: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" Response: {e.response.text}"
            raise Exception(error_msg)

