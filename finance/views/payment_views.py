"""
Payment Views
Handles payment gateway integration endpoints for wallet top-up
"""
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response
from decimal import Decimal
import uuid
import os

from finance.models import Wallet, PaymentTransaction, Transaction
from finance.serializers import (
    PaymentInitiateSerializer,
    PaymentFormDataSerializer,
    PaymentTransactionSerializer,
    PaymentCallbackSerializer,
    PaymentValidateSerializer
)
from finance.services.nchl_connectips import NCHLConnectIPS
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


@api_view(['POST'])
@require_auth
@api_response
def initiate_payment(request):
    """
    Initiate payment by generating payment form data for ConnectIPS gateway.
    
    Request body:
    {
        "amount": 100.00,  // Amount in NPR
        "remarks": "Wallet top-up",
        "particulars": "User deposit"
    }
    
    Returns payment form data including token and gateway URL.
    """
    try:
        # Validate request data
        serializer = PaymentInitiateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid payment data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        amount = Decimal(str(serializer.validated_data['amount']))
        remarks = serializer.validated_data.get('remarks', '')
        particulars = serializer.validated_data.get('particulars', '')
        
        # Get or create user's wallet
        try:
            wallet = Wallet.objects.get(user=request.user)
        except Wallet.DoesNotExist:
            wallet = Wallet.objects.create(
                user=request.user,
                balance=Decimal('0.00')
            )
        
        # Generate unique transaction IDs
        txn_id = f"TXN-{uuid.uuid4().hex[:12].upper()}"
        reference_id = f"REF-{uuid.uuid4().hex[:8].upper()}"
        
        # Convert amount to paisa (ConnectIPS uses paisa)
        amount_paisa = int(amount * 100)
        
        # Create payment transaction record
        payment_txn = PaymentTransaction.objects.create(
            user=request.user,
            wallet=wallet,
            txn_id=txn_id,
            reference_id=reference_id,
            amount=amount,
            amount_paisa=amount_paisa,
            status='PENDING'
        )
        
        # Initialize NCHL ConnectIPS service
        nchl_service = NCHLConnectIPS()
        
        # Generate payment form data
        form_data = nchl_service.get_payment_form_data(
            txn_id=txn_id,
            txn_amt=amount_paisa,
            reference_id=reference_id,
            remarks=remarks,
            particulars=particulars
        )
        
        # Get base URL for callback URLs (frontend URL)
        from django.conf import settings
        # Try to get frontend URL from request origin or settings
        # For production, set FRONTEND_URL in environment variables
        frontend_url = os.getenv('FRONTEND_URL', '')
        if not frontend_url:
            # Try to infer from request
            origin = request.META.get('HTTP_ORIGIN', '')
            if origin:
                frontend_url = origin
            else:
                # Fallback: construct from request
                scheme = request.scheme
                host = request.get_host()
                frontend_url = f"{scheme}://{host}"
        
        # Generate frontend callback URLs (ConnectIPS will redirect here)
        success_url = f"{frontend_url}/payment/callback?txn_id={txn_id}&status=success"
        failure_url = f"{frontend_url}/payment/callback?txn_id={txn_id}&status=failure"
        
        # Add callback URLs to form data
        form_data['success_url'] = success_url
        form_data['failure_url'] = failure_url
        
        # Serialize response
        response_serializer = PaymentFormDataSerializer(form_data)
        
        return success_response(
            data=response_serializer.data,
            message="Payment initiated successfully. Redirect to gateway."
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(
            message=f"Error initiating payment: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def payment_callback(request):
    """
    Handle payment callback from ConnectIPS gateway.
    
    Query params:
    - txn_id: Transaction ID from ConnectIPS
    - status: success or failure
    
    This endpoint validates the transaction and updates wallet balance.
    """
    try:
        txn_id = request.GET.get('txn_id')
        callback_status = request.GET.get('status', '').lower()
        
        if not txn_id:
            return error_response(
                message="Transaction ID is required",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get payment transaction
        try:
            payment_txn = PaymentTransaction.objects.get(txn_id=txn_id)
        except PaymentTransaction.DoesNotExist:
            return error_response(
                message="Payment transaction not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # If already processed, return current status
        if payment_txn.status in ['SUCCESS', 'FAILED', 'ERROR']:
            serializer = PaymentTransactionSerializer(payment_txn)
            return success_response(
                data=serializer.data,
                message=f"Payment already processed. Status: {payment_txn.status}"
            )
        
        # Initialize NCHL ConnectIPS service
        nchl_service = NCHLConnectIPS()
        
        # Validate transaction with ConnectIPS
        try:
            validation_response = nchl_service.validate_transaction(
                reference_id=txn_id,
                txn_amt=payment_txn.amount_paisa
            )
        except Exception as e:
            payment_txn.mark_error(f"Validation error: {str(e)}")
            return error_response(
                message=f"Failed to validate transaction: {str(e)}",
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
        
        # Check validation response
        status_from_api = validation_response.get('status', '').upper()
        status_desc = validation_response.get('statusDesc', '')
        
        # Process based on validation result
        if status_from_api == 'SUCCESS':
            # Transaction successful - credit wallet
            with db_transaction.atomic():
                # Update payment transaction
                payment_txn.mark_success(connectips_response=validation_response)
                
                # Credit wallet balance
                description = f"Wallet top-up via ConnectIPS - Transaction {txn_id}"
                success = payment_txn.wallet.add_balance(
                    amount=payment_txn.amount,
                    description=description,
                    performed_by=payment_txn.user
                )
                
                if not success:
                    payment_txn.mark_error("Failed to credit wallet balance")
                    return error_response(
                        message="Payment validated but failed to credit wallet",
                        status_code=HTTP_STATUS['INTERNAL_ERROR']
                    )
            
            serializer = PaymentTransactionSerializer(payment_txn)
            return success_response(
                data=serializer.data,
                message="Payment successful. Wallet balance updated."
            )
        
        elif status_from_api == 'FAILED':
            # Transaction failed
            payment_txn.mark_failed(status_desc or "Transaction failed")
            serializer = PaymentTransactionSerializer(payment_txn)
            return error_response(
                message=f"Payment failed: {status_desc}",
                data=serializer.data,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        elif status_from_api == 'ERROR':
            # Transaction error (not found, incomplete, etc.)
            payment_txn.mark_error(status_desc or "Transaction error")
            serializer = PaymentTransactionSerializer(payment_txn)
            return error_response(
                message=f"Payment error: {status_desc}",
                data=serializer.data,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        else:
            # Unknown status
            payment_txn.mark_error(f"Unknown status: {status_from_api}")
            serializer = PaymentTransactionSerializer(payment_txn)
            return error_response(
                message=f"Unknown payment status: {status_from_api}",
                data=serializer.data,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(
            message=f"Error processing payment callback: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def validate_payment(request):
    """
    Manually validate a payment transaction.
    
    Request body:
    {
        "txn_id": "TXN-ABC123"
    }
    """
    try:
        serializer = PaymentValidateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response(
                message="Invalid validation data",
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        txn_id = serializer.validated_data['txn_id']
        
        # Get payment transaction
        try:
            payment_txn = PaymentTransaction.objects.get(txn_id=txn_id)
        except PaymentTransaction.DoesNotExist:
            return error_response(
                message="Payment transaction not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check if user owns this transaction
        if payment_txn.user != request.user and not request.user.groups.filter(name='Super Admin').exists():
            return error_response(
                message="Access denied. You can only validate your own payments.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        # If already successful, return current status
        if payment_txn.status == 'SUCCESS':
            serializer = PaymentTransactionSerializer(payment_txn)
            return success_response(
                data=serializer.data,
                message="Payment already validated and successful"
            )
        
        # Initialize NCHL ConnectIPS service
        nchl_service = NCHLConnectIPS()
        
        # Validate transaction with ConnectIPS
        try:
            validation_response = nchl_service.validate_transaction(
                reference_id=txn_id,
                txn_amt=payment_txn.amount_paisa
            )
        except Exception as e:
            payment_txn.mark_error(f"Validation error: {str(e)}")
            return error_response(
                message=f"Failed to validate transaction: {str(e)}",
                status_code=HTTP_STATUS['INTERNAL_ERROR']
            )
        
        # Check validation response
        status_from_api = validation_response.get('status', '').upper()
        status_desc = validation_response.get('statusDesc', '')
        
        # Process based on validation result
        if status_from_api == 'SUCCESS':
            # Transaction successful - credit wallet if not already credited
            if payment_txn.status != 'SUCCESS':
                with db_transaction.atomic():
                    payment_txn.mark_success(connectips_response=validation_response)
                    
                    description = f"Wallet top-up via ConnectIPS - Transaction {txn_id}"
                    success = payment_txn.wallet.add_balance(
                        amount=payment_txn.amount,
                        description=description,
                        performed_by=payment_txn.user
                    )
                    
                    if not success:
                        payment_txn.mark_error("Failed to credit wallet balance")
                        return error_response(
                            message="Payment validated but failed to credit wallet",
                            status_code=HTTP_STATUS['INTERNAL_ERROR']
                        )
            
            serializer = PaymentTransactionSerializer(payment_txn)
            return success_response(
                data=serializer.data,
                message="Payment validated successfully. Wallet balance updated."
            )
        
        elif status_from_api == 'FAILED':
            payment_txn.mark_failed(status_desc or "Transaction failed")
            serializer = PaymentTransactionSerializer(payment_txn)
            return error_response(
                message=f"Payment validation failed: {status_desc}",
                data=serializer.data,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        else:
            payment_txn.mark_error(status_desc or f"Transaction error: {status_from_api}")
            serializer = PaymentTransactionSerializer(payment_txn)
            return error_response(
                message=f"Payment validation error: {status_desc}",
                data=serializer.data,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return error_response(
            message=f"Error validating payment: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_payment_transactions(request):
    """
    Get payment transactions for the current user.
    """
    try:
        # Check if user is Super Admin
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        
        if is_super_admin:
            # Super Admin can see all transactions
            transactions = PaymentTransaction.objects.select_related('user', 'wallet').all()
        else:
            # Regular users see only their transactions
            transactions = PaymentTransaction.objects.filter(
                user=request.user
            ).select_related('user', 'wallet')
        
        # Order by created_at descending
        transactions = transactions.order_by('-created_at')
        
        # Serialize
        serializer = PaymentTransactionSerializer(transactions, many=True)
        
        return success_response(
            data=serializer.data,
            message="Payment transactions retrieved successfully"
        )
        
    except Exception as e:
        return error_response(
            message=f"Error retrieving payment transactions: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_payment_transaction_by_id(request, payment_id):
    """
    Get a specific payment transaction by ID.
    """
    try:
        try:
            payment_txn = PaymentTransaction.objects.select_related('user', 'wallet').get(id=payment_id)
        except PaymentTransaction.DoesNotExist:
            return error_response(
                message="Payment transaction not found",
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Check permissions
        is_super_admin = request.user.groups.filter(name='Super Admin').exists()
        if not is_super_admin and payment_txn.user != request.user:
            return error_response(
                message="Access denied. You can only view your own payment transactions.",
                status_code=HTTP_STATUS['FORBIDDEN']
            )
        
        serializer = PaymentTransactionSerializer(payment_txn)
        
        return success_response(
            data=serializer.data,
            message="Payment transaction retrieved successfully"
        )
        
    except Exception as e:
        return error_response(
            message=f"Error retrieving payment transaction: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

