"""
Wallet Serializers
Handles serialization for wallet management endpoints with transaction tracking
"""
from rest_framework import serializers
from finance.models import Wallet, Transaction
from core.models import User
from core.serializers.user_serializers import UserListSerializer


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet model with user info and recent transactions"""
    user_info = serializers.SerializerMethodField()
    recent_transactions = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'user', 'user_info', 'call_price', 'sms_price',
            'recent_transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Get user information"""
        return {
            'id': obj.user.id,
            'name': obj.user.name,
            'phone': obj.user.phone,
            'is_active': obj.user.is_active
        }
    
    def get_recent_transactions(self, obj):
        """Get recent 5 transactions for this wallet"""
        recent_transactions = obj.get_recent_transactions(5)
        return [
            {
                'id': t.id,
                'amount': float(t.amount),
                'transaction_type': t.transaction_type,
                'description': t.description,
                'created_at': t.created_at.isoformat()
            }
            for t in recent_transactions
        ]


class WalletCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wallets"""
    user_id = serializers.IntegerField(
        write_only=True,
        help_text="User ID for the wallet"
    )
    
    class Meta:
        model = Wallet
        fields = ['user_id', 'balance', 'call_price', 'sms_price']
    
    def validate_user_id(self, value):
        """Validate user exists and doesn't already have a wallet"""
        try:
            user = User.objects.get(id=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this ID does not exist")
        
        if Wallet.objects.filter(user=user).exists():
            raise serializers.ValidationError("User already has a wallet")
        
        return value
    
    def validate_balance(self, value):
        """Validate balance is not negative"""
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value
    
    def create(self, validated_data):
        """Create wallet for the specified user"""
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        validated_data['user'] = user
        return Wallet.objects.create(**validated_data)


class WalletUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating wallet balance"""
    
    class Meta:
        model = Wallet
        fields = ['balance', 'call_price', 'sms_price']
    
    def validate_balance(self, value):
        """Validate balance is not negative"""
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value


class WalletListSerializer(serializers.ModelSerializer):
    """Serializer for wallet list (minimal data)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'user_name', 'user_phone', 'call_price', 'sms_price',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class WalletBalanceUpdateSerializer(serializers.Serializer):
    """Serializer for updating wallet balance with operations"""
    operation = serializers.ChoiceField(
        choices=['add', 'subtract', 'set'],
        help_text="Operation to perform: add, subtract, or set"
    )
    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Amount for the operation"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Description for this transaction"
    )
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value


class WalletTopUpSerializer(serializers.Serializer):
    """Serializer for wallet top-up operations (Super Admin only)"""
    operation = serializers.ChoiceField(
        choices=['add', 'subtract'],
        help_text="Operation to perform: add or subtract"
    )
    amount = serializers.DecimalField(
        max_digits=15, 
        decimal_places=2,
        help_text="Amount for the operation"
    )
    description = serializers.CharField(
        required=True,
        help_text="Description for this top-up transaction"
    )
    performed_by_id = serializers.IntegerField(
        required=False,
        help_text="ID of the admin performing this operation"
    )
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
    
    def validate_performed_by_id(self, value):
        """Validate performed_by user exists"""
        if value:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value


class WalletDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed wallet view with full transaction history"""
    user = UserListSerializer(read_only=True)
    transactions = serializers.SerializerMethodField()
    balance_change_today = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'user', 'call_price', 'sms_price', 'transactions',
            'balance_change_today', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_transactions(self, obj):
        """Get all transactions for this wallet"""
        transactions = obj.transactions.all()[:20]  # Limit to recent 20
        return [
            {
                'id': t.id,
                'amount': float(t.amount),
                'transaction_type': t.transaction_type,
                'balance_before': float(t.balance_before),
                'balance_after': float(t.balance_after),
                'description': t.description,
                'performed_by': {
                    'id': t.performed_by.id,
                    'name': t.performed_by.name
                } if t.performed_by else None,
                'status': t.status,
                'created_at': t.created_at.isoformat()
            }
            for t in transactions
        ]
    
    def get_balance_change_today(self, obj):
        """Get today's balance change summary"""
        return obj.get_balance_change_today()


class WalletSummarySerializer(serializers.Serializer):
    """Serializer for wallet summary statistics"""
    total_wallets = serializers.IntegerField()
    total_balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    active_wallets = serializers.IntegerField()
    inactive_wallets = serializers.IntegerField()
    wallets_with_balance = serializers.IntegerField()
    wallets_with_zero_balance = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Format the summary data"""
        data = super().to_representation(instance)
        data['total_balance'] = float(data['total_balance'])
        return data


class WalletTransferSerializer(serializers.Serializer):
    """Serializer for wallet transfer between users"""
    recipient_phone = serializers.CharField(
        max_length=100,
        help_text="Phone number of the recipient user"
    )
    amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Amount to transfer"
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500,
        help_text="Optional description for the transfer"
    )
    
    def validate_recipient_phone(self, value):
        """Validate recipient phone number exists"""
        from api_common.utils.validation_utils import validate_phone_number
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        
        if not User.objects.filter(phone=value.strip()).exists():
            raise serializers.ValidationError("Recipient user with this phone number does not exist")
        
        return value.strip()
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value