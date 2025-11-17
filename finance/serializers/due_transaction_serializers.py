"""
Due Transaction Serializers
Handles serialization for due transaction management endpoints
"""
from rest_framework import serializers
from finance.models import DueTransaction, DueTransactionParticular
from core.models import User, Institute
from core.serializers.user_serializers import UserListSerializer


class DueTransactionParticularSerializer(serializers.ModelSerializer):
    """Serializer for due transaction particular"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = DueTransactionParticular
        fields = [
            'id', 'particular', 'type', 'institute', 'institute_name',
            'amount', 'quantity', 'total', 'created_at'
        ]
        read_only_fields = ['id', 'total', 'created_at']


class DueTransactionParticularCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating due transaction particular"""
    
    class Meta:
        model = DueTransactionParticular
        fields = [
            'particular', 'type', 'institute', 'amount', 'quantity'
        ]
    
    def validate_amount(self, value):
        """Validate amount is positive"""
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive")
        return value
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value
    
    def validate(self, data):
        """Validate type-specific requirements"""
        particular_type = data.get('type')
        institute = data.get('institute')
        
        if particular_type == 'parent' and not institute:
            raise serializers.ValidationError(
                "Institute is required for parent type particular"
            )
        
        return data


class DueTransactionSerializer(serializers.ModelSerializer):
    """Serializer for due transaction with particulars"""
    user_info = serializers.SerializerMethodField()
    particulars = DueTransactionParticularSerializer(many=True, read_only=True)
    
    class Meta:
        model = DueTransaction
        fields = [
            'id', 'user', 'user_info', 'subtotal', 'vat', 'total',
            'renew_date', 'expire_date', 'is_paid', 'pay_date',
            'particulars', 'created_at', 'updated_at'
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


class DueTransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating due transaction"""
    particulars = DueTransactionParticularCreateSerializer(many=True, required=False)
    
    class Meta:
        model = DueTransaction
        fields = [
            'user', 'subtotal', 'vat', 'total', 'renew_date', 'expire_date',
            'particulars'
        ]
    
    def validate_user(self, value):
        """Validate user exists"""
        if not value:
            raise serializers.ValidationError("User is required")
        return value
    
    def validate_subtotal(self, value):
        """Validate subtotal is positive"""
        if value <= 0:
            raise serializers.ValidationError("Subtotal must be positive")
        return value
    
    def validate(self, data):
        """Validate dates and calculate totals"""
        renew_date = data.get('renew_date')
        expire_date = data.get('expire_date')
        
        if renew_date and expire_date:
            if expire_date <= renew_date:
                raise serializers.ValidationError(
                    "Expire date must be after renew date"
                )
        
        # Calculate totals if not provided
        subtotal = data.get('subtotal', 0)
        if 'vat' not in data or 'total' not in data:
            from core.models import MySetting
            try:
                setting = MySetting.objects.first()
                vat_percent = float(setting.vat_percent) if setting and setting.vat_percent else 0.0
            except:
                vat_percent = 0.0
            
            from decimal import Decimal
            vat_amount = (Decimal(str(subtotal)) * Decimal(str(vat_percent))) / Decimal('100')
            total_amount = Decimal(str(subtotal)) + vat_amount
            
            data['vat'] = vat_amount
            data['total'] = total_amount
        
        return data
    
    def create(self, validated_data):
        """Create due transaction with particulars"""
        particulars_data = validated_data.pop('particulars', [])
        
        # Create due transaction
        due_transaction = DueTransaction.objects.create(**validated_data)
        
        # Create particulars
        for particular_data in particulars_data:
            DueTransactionParticular.objects.create(
                due_transaction=due_transaction,
                **particular_data
            )
        
        # Recalculate totals from particulars if needed
        if particulars_data:
            total_subtotal = sum(
                float(p['amount']) * p['quantity'] for p in particulars_data
            )
            due_transaction.subtotal = total_subtotal
            due_transaction.calculate_totals()
            due_transaction.save()
        
        return due_transaction


class DueTransactionUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating due transaction"""
    particulars = DueTransactionParticularCreateSerializer(many=True, required=False)
    
    class Meta:
        model = DueTransaction
        fields = [
            'subtotal', 'vat', 'total', 'renew_date', 'expire_date',
            'is_paid', 'pay_date', 'particulars'
        ]
    
    def validate_subtotal(self, value):
        """Validate subtotal is positive"""
        if value <= 0:
            raise serializers.ValidationError("Subtotal must be positive")
        return value
    
    def validate(self, data):
        """Validate dates and payment status"""
        renew_date = data.get('renew_date')
        expire_date = data.get('expire_date')
        
        if renew_date and expire_date:
            if expire_date <= renew_date:
                raise serializers.ValidationError(
                    "Expire date must be after renew date"
                )
        
        is_paid = data.get('is_paid')
        pay_date = data.get('pay_date')
        
        if is_paid and not pay_date:
            from django.utils import timezone
            data['pay_date'] = timezone.now()
        
        if not is_paid and pay_date:
            data['pay_date'] = None
        
        return data
    
    def update(self, instance, validated_data):
        """Update due transaction and particulars"""
        particulars_data = validated_data.pop('particulars', None)
        
        # Update main transaction fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update particulars if provided
        if particulars_data is not None:
            # Delete existing particulars
            instance.particulars.all().delete()
            
            # Create new particulars
            for particular_data in particulars_data:
                DueTransactionParticular.objects.create(
                    due_transaction=instance,
                    **particular_data
                )
            
            # Recalculate totals from particulars
            total_subtotal = sum(
                float(p.total) for p in instance.particulars.all()
            )
            instance.subtotal = total_subtotal
            instance.calculate_totals()
            instance.save()
        
        return instance


class DueTransactionListSerializer(serializers.ModelSerializer):
    """Serializer for due transaction list (minimal data)"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    particulars_count = serializers.SerializerMethodField()
    
    class Meta:
        model = DueTransaction
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'subtotal', 'vat', 'total',
            'renew_date', 'expire_date', 'is_paid', 'pay_date',
            'particulars_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_particulars_count(self, obj):
        """Get count of particulars"""
        return obj.particulars.count()


class DueTransactionPaySerializer(serializers.Serializer):
    """Serializer for paying due transaction with wallet"""
    pass  # No additional fields needed, just the action

