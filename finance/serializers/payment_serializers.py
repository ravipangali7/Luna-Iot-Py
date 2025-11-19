"""
Payment Serializers
Handles serialization for payment transaction requests and responses
"""
from rest_framework import serializers
from finance.models import PaymentTransaction
from decimal import Decimal


class PaymentInitiateSerializer(serializers.Serializer):
    """Serializer for initiating a payment"""
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text="Amount in NPR (not paisa)"
    )
    remarks = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        default='',
        help_text="Optional remarks"
    )
    particulars = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        default='',
        help_text="Optional particulars"
    )
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value


class PaymentFormDataSerializer(serializers.Serializer):
    """Serializer for payment form data response"""
    MERCHANTID = serializers.CharField()
    APPID = serializers.CharField()
    APPNAME = serializers.CharField()
    TXNID = serializers.CharField()
    TXNDATE = serializers.CharField()
    TXNCRNCY = serializers.CharField()
    TXNAMT = serializers.CharField()
    REFERENCEID = serializers.CharField()
    REMARKS = serializers.CharField()
    PARTICULARS = serializers.CharField()
    TOKEN = serializers.CharField()
    gateway_url = serializers.URLField()
    success_url = serializers.URLField()
    failure_url = serializers.URLField()


class PaymentTransactionSerializer(serializers.ModelSerializer):
    """Serializer for PaymentTransaction model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'user',
            'user_name',
            'user_phone',
            'wallet',
            'txn_id',
            'reference_id',
            'amount',
            'amount_paisa',
            'status',
            'status_display',
            'connectips_txn_id',
            'connectips_batch_id',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'wallet',
            'txn_id',
            'reference_id',
            'status',
            'connectips_txn_id',
            'connectips_batch_id',
            'error_message',
            'created_at',
            'updated_at',
            'completed_at',
        ]


class PaymentCallbackSerializer(serializers.Serializer):
    """Serializer for payment callback from ConnectIPS"""
    txn_id = serializers.CharField(
        required=False,
        help_text="Transaction ID from ConnectIPS (in query params)"
    )
    status = serializers.CharField(
        required=False,
        help_text="Status from callback (success/failure)"
    )


class PaymentValidateSerializer(serializers.Serializer):
    """Serializer for manual payment validation"""
    txn_id = serializers.CharField(
        required=True,
        help_text="Transaction ID to validate"
    )

