"""
Wallet Serializers
Handles serialization for wallet management endpoints
"""
from rest_framework import serializers
from core.models import Wallet, User


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet model with user info"""
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'id', 'balance', 'user', 'user_info', 
            'created_at', 'updated_at'
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


class WalletCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating wallets"""
    user_id = serializers.IntegerField(
        write_only=True,
        help_text="User ID for the wallet"
    )
    
    class Meta:
        model = Wallet
        fields = ['user_id', 'balance']
    
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
        fields = ['balance']
    
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
            'id', 'balance', 'user_name', 'user_phone', 'created_at'
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
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
