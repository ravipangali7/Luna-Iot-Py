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
    vehicle_id = serializers.IntegerField(source='vehicle.id', read_only=True, allow_null=True)
    vehicle_info = serializers.SerializerMethodField()
    display_amount = serializers.SerializerMethodField()
    is_dealer_view = serializers.SerializerMethodField()
    
    class Meta:
        model = DueTransactionParticular
        fields = [
            'id', 'particular', 'type', 'institute', 'institute_name',
            'vehicle', 'vehicle_id', 'vehicle_info',
            'amount', 'dealer_amount', 'display_amount', 'quantity', 'total', 'is_dealer_view', 'created_at'
        ]
        read_only_fields = ['id', 'total', 'created_at']
    
    def get_vehicle_info(self, obj):
        """Get vehicle information if vehicle exists"""
        if obj.vehicle:
            return {
                'id': obj.vehicle.id,
                'imei': obj.vehicle.imei,
                'name': obj.vehicle.name,
                'vehicleNo': obj.vehicle.vehicleNo,
            }
        return None
    
    def get_display_amount(self, obj):
        """Get display amount based on viewer's role"""
        request = self.context.get('request')
        if request and request.user:
            is_dealer = request.user.groups.filter(name='Dealer').exists()
            if is_dealer and obj.dealer_amount is not None:
                return float(obj.dealer_amount)
        return float(obj.amount)
    
    def get_is_dealer_view(self, obj):
        """Check if dealer price is being shown"""
        request = self.context.get('request')
        if request and request.user:
            is_dealer = request.user.groups.filter(name='Dealer').exists()
            return is_dealer and obj.dealer_amount is not None
        return False


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
    paid_by_info = serializers.SerializerMethodField()
    particulars = DueTransactionParticularSerializer(many=True, read_only=True)
    display_subtotal = serializers.SerializerMethodField()
    display_vat = serializers.SerializerMethodField()
    display_total = serializers.SerializerMethodField()
    show_vat = serializers.SerializerMethodField()
    show_dealer_price = serializers.SerializerMethodField()
    
    class Meta:
        model = DueTransaction
        fields = [
            'id', 'user', 'user_info', 'paid_by', 'paid_by_info', 
            'subtotal', 'vat', 'total',
            'display_subtotal', 'display_vat', 'display_total',
            'show_vat', 'show_dealer_price',
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
    
    def get_paid_by_info(self, obj):
        """Get paid_by user information"""
        if obj.paid_by:
            return {
                'id': obj.paid_by.id,
                'name': obj.paid_by.name,
                'phone': obj.paid_by.phone,
                'is_active': obj.paid_by.is_active
            }
        return None
    
    def _is_dealer_or_admin(self):
        """Check if current user is Dealer or Admin"""
        request = self.context.get('request')
        if request and request.user:
            is_dealer = request.user.groups.filter(name='Dealer').exists()
            is_admin = request.user.groups.filter(name='Super Admin').exists()
            return is_dealer or is_admin
        return False
    
    def _is_customer(self):
        """Check if current user is Customer"""
        request = self.context.get('request')
        if request and request.user:
            is_customer = request.user.groups.filter(name='Customer').exists()
            # If user has no groups or only Customer group, treat as customer
            user_groups = request.user.groups.all()
            if not user_groups.exists() or (user_groups.count() == 1 and is_customer):
                return True
        return False
    
    def get_display_subtotal(self, obj):
        """Calculate display subtotal based on viewer's role"""
        from decimal import Decimal
        
        is_dealer_or_admin = self._is_dealer_or_admin()
        
        if is_dealer_or_admin:
            # For Dealer/Admin: Sum dealer_amount * quantity (or amount if dealer_amount is null)
            subtotal = Decimal('0.00')
            for particular in obj.particulars.all():
                if particular.dealer_amount is not None:
                    subtotal += Decimal(str(particular.dealer_amount)) * Decimal(str(particular.quantity))
                else:
                    subtotal += Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
        else:
            # For Customer: Sum amount * quantity
            subtotal = Decimal('0.00')
            for particular in obj.particulars.all():
                subtotal += Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
        
        return float(subtotal)
    
    def get_display_vat(self, obj):
        """Calculate display VAT based on viewer's role"""
        from decimal import Decimal
        from core.models import MySetting
        
        is_dealer_or_admin = self._is_dealer_or_admin()
        
        if not is_dealer_or_admin:
            # Customer: Don't show VAT
            return None
        
        # For Dealer/Admin: Calculate VAT from display_subtotal
        display_subtotal = Decimal(str(self.get_display_subtotal(obj)))
        
        try:
            setting = MySetting.objects.first()
            vat_percent = Decimal(str(setting.vat_percent)) if setting and setting.vat_percent else Decimal('0.00')
        except:
            vat_percent = Decimal('0.00')
        
        vat_amount = (display_subtotal * vat_percent) / Decimal('100')
        return float(vat_amount)
    
    def get_display_total(self, obj):
        """Calculate display total based on viewer's role"""
        from decimal import Decimal
        
        display_subtotal = Decimal(str(self.get_display_subtotal(obj)))
        display_vat = self.get_display_vat(obj)
        
        if display_vat is not None:
            total = display_subtotal + Decimal(str(display_vat))
        else:
            # Customer: Total = subtotal (no VAT shown)
            total = display_subtotal
        
        return float(total)
    
    def get_show_vat(self, obj):
        """Determine if VAT should be shown"""
        return self._is_dealer_or_admin()
    
    def get_show_dealer_price(self, obj):
        """Determine if dealer price should be shown"""
        return self._is_dealer_or_admin()


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
    user_name = serializers.SerializerMethodField()
    user_phone = serializers.SerializerMethodField()
    particulars_count = serializers.SerializerMethodField()
    display_total = serializers.SerializerMethodField()
    show_vat = serializers.SerializerMethodField()
    
    class Meta:
        model = DueTransaction
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'subtotal', 'vat', 'total',
            'display_total', 'show_vat',
            'renew_date', 'expire_date', 'is_paid', 'pay_date',
            'particulars_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_name(self, obj):
        """Get user name safely"""
        return obj.user.name if obj.user else None
    
    def get_user_phone(self, obj):
        """Get user phone safely"""
        return obj.user.phone if obj.user else None
    
    def get_particulars_count(self, obj):
        """Get count of particulars"""
        return obj.particulars.count()
    
    def _is_dealer_or_admin(self):
        """Check if current user is Dealer or Admin"""
        request = self.context.get('request')
        if request and request.user:
            is_dealer = request.user.groups.filter(name='Dealer').exists()
            is_admin = request.user.groups.filter(name='Super Admin').exists()
            return is_dealer or is_admin
        return False
    
    def get_display_total(self, obj):
        """Calculate display total based on viewer's role"""
        from decimal import Decimal
        
        is_dealer_or_admin = self._is_dealer_or_admin()
        
        if is_dealer_or_admin:
            # For Dealer/Admin: Sum dealer_amount * quantity (or amount if dealer_amount is null)
            subtotal = Decimal('0.00')
            for particular in obj.particulars.all():
                if particular.dealer_amount is not None:
                    subtotal += Decimal(str(particular.dealer_amount)) * Decimal(str(particular.quantity))
                else:
                    subtotal += Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
            
            # Add VAT
            try:
                from core.models import MySetting
                setting = MySetting.objects.first()
                vat_percent = Decimal(str(setting.vat_percent)) if setting and setting.vat_percent else Decimal('0.00')
            except:
                vat_percent = Decimal('0.00')
            vat_amount = (subtotal * vat_percent) / Decimal('100')
            total = subtotal + vat_amount
        else:
            # For Customer: Sum amount * quantity (no VAT)
            total = Decimal('0.00')
            for particular in obj.particulars.all():
                total += Decimal(str(particular.amount)) * Decimal(str(particular.quantity))
        
        return float(total)
    
    def get_show_vat(self, obj):
        """Determine if VAT should be shown"""
        return self._is_dealer_or_admin()


class DueTransactionPaySerializer(serializers.Serializer):
    """Serializer for paying due transaction with wallet"""
    pass  # No additional fields needed, just the action


class PayParticularSerializer(serializers.Serializer):
    """Serializer for paying a particular with wallet"""
    pass  # No additional fields needed, just the action

