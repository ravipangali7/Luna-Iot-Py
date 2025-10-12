from rest_framework import serializers
from finance.models import Transaction, Wallet
from core.models import User
from core.serializers.user_serializers import UserListSerializer


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model with full details"""
    
    wallet_info = serializers.SerializerMethodField()
    performed_by_info = serializers.SerializerMethodField()
    amount_display = serializers.SerializerMethodField()
    balance_change = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'wallet', 'wallet_info', 'amount', 'amount_display',
            'transaction_type', 'balance_before', 'balance_after', 'balance_change',
            'description', 'performed_by', 'performed_by_info', 'transaction_reference',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'transaction_reference']
    
    def get_wallet_info(self, obj):
        """Get wallet owner information"""
        return {
            'id': obj.wallet.id,
            'user_name': obj.wallet.user.name,
            'user_phone': obj.wallet.user.phone,
            'balance': float(obj.wallet.balance)
        }
    
    def get_performed_by_info(self, obj):
        """Get performed by user information"""
        if obj.performed_by:
            return {
                'id': obj.performed_by.id,
                'name': obj.performed_by.name,
                'phone': obj.performed_by.phone
            }
        return None
    
    def get_amount_display(self, obj):
        """Get formatted amount with sign"""
        return obj.get_amount_display()
    
    def get_balance_change(self, obj):
        """Get the balance change amount"""
        return float(obj.get_balance_change())


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Transaction instances"""
    
    wallet_id = serializers.PrimaryKeyRelatedField(
        queryset=Wallet.objects.all(),
        source='wallet',
        write_only=True,
        help_text="ID of the wallet for this transaction"
    )
    performed_by_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='performed_by',
        write_only=True,
        required=False,
        allow_null=True,
        help_text="ID of the user who performed this transaction"
    )
    
    class Meta:
        model = Transaction
        fields = [
            'wallet_id', 'amount', 'transaction_type', 'description',
            'performed_by_id', 'status'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        return value
    
    def validate(self, data):
        """Validate transaction data"""
        wallet = data.get('wallet')
        amount = data.get('amount')
        transaction_type = data.get('transaction_type')
        
        # Check if debit transaction has sufficient balance
        if transaction_type == 'DEBIT' and wallet:
            if wallet.balance < amount:
                raise serializers.ValidationError(
                    f"Insufficient balance. Available: {wallet.balance}, Required: {amount}"
                )
        
        return data


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer for listing Transaction instances (minimal data)"""
    
    user_name = serializers.CharField(source='wallet.user.name', read_only=True)
    user_phone = serializers.CharField(source='wallet.user.phone', read_only=True)
    performed_by_name = serializers.CharField(source='performed_by.name', read_only=True)
    amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'user_name', 'user_phone', 'amount', 'amount_display',
            'transaction_type', 'balance_after', 'description', 'performed_by_name',
            'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_amount_display(self, obj):
        """Get formatted amount with sign"""
        return obj.get_amount_display()


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for filtering transactions"""
    
    wallet_id = serializers.IntegerField(required=False, help_text="Filter by wallet ID")
    user_id = serializers.IntegerField(required=False, help_text="Filter by user ID")
    transaction_type = serializers.ChoiceField(
        choices=[('CREDIT', 'Credit'), ('DEBIT', 'Debit')],
        required=False,
        help_text="Filter by transaction type"
    )
    status = serializers.ChoiceField(
        choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed')],
        required=False,
        help_text="Filter by transaction status"
    )
    date_from = serializers.DateTimeField(required=False, help_text="Filter from date")
    date_to = serializers.DateTimeField(required=False, help_text="Filter to date")
    search = serializers.CharField(required=False, help_text="Search in description or user name")
    
    def validate(self, data):
        """Validate filter data"""
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise serializers.ValidationError("date_from cannot be after date_to")
        
        return data


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for transaction summary statistics"""
    
    total_transactions = serializers.IntegerField()
    total_credit = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_debit = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_change = serializers.DecimalField(max_digits=15, decimal_places=2)
    pending_transactions = serializers.IntegerField()
    completed_transactions = serializers.IntegerField()
    failed_transactions = serializers.IntegerField()
    
    def to_representation(self, instance):
        """Format the summary data"""
        data = super().to_representation(instance)
        data['total_credit'] = float(data['total_credit'])
        data['total_debit'] = float(data['total_debit'])
        data['net_change'] = float(data['net_change'])
        return data


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for wallet transactions (simplified)"""
    
    transaction_type_display = serializers.CharField(source='get_transaction_type_display', read_only=True)
    amount_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'amount_display', 'transaction_type', 'transaction_type_display',
            'balance_after', 'description', 'status', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_amount_display(self, obj):
        """Get formatted amount with sign"""
        return obj.get_amount_display()