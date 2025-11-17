"""
MySetting Serializers
Handles serialization for MySetting management endpoints
"""
from rest_framework import serializers
from core.models import MySetting


class MySettingSerializer(serializers.ModelSerializer):
    """Serializer for MySetting model"""
    
    class Meta:
        model = MySetting
        fields = [
            'id', 'mypay_balance', 'vat_percent', 'call_price', 'sms_price',
            'parent_price', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class MySettingUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating MySetting"""
    
    class Meta:
        model = MySetting
        fields = [
            'mypay_balance', 'vat_percent', 'call_price', 'sms_price', 'parent_price'
        ]
    
    def validate_vat_percent(self, value):
        """Validate VAT percent is not negative"""
        if value < 0:
            raise serializers.ValidationError("VAT percent cannot be negative")
        if value > 100:
            raise serializers.ValidationError("VAT percent cannot exceed 100")
        return value
    
    def validate_mypay_balance(self, value):
        """Validate balance is not negative"""
        if value < 0:
            raise serializers.ValidationError("Balance cannot be negative")
        return value
    
    def validate_call_price(self, value):
        """Validate call price is not negative"""
        if value < 0:
            raise serializers.ValidationError("Call price cannot be negative")
        return value
    
    def validate_sms_price(self, value):
        """Validate SMS price is not negative"""
        if value < 0:
            raise serializers.ValidationError("SMS price cannot be negative")
        return value
    
    def validate_parent_price(self, value):
        """Validate parent price is not negative"""
        if value < 0:
            raise serializers.ValidationError("Parent price cannot be negative")
        return value

