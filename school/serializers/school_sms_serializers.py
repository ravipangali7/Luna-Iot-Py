"""
School SMS Serializers
Handles serialization for school SMS management endpoints
"""
from rest_framework import serializers
from school.models import SchoolSMS
from core.serializers import InstituteSerializer


class SchoolSMSSerializer(serializers.ModelSerializer):
    """Serializer for school SMS model"""
    institute = InstituteSerializer(read_only=True)
    institute_id = serializers.IntegerField(write_only=True, required=False)
    phone_numbers = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=False
    )
    
    class Meta:
        model = SchoolSMS
        fields = [
            'id', 'message', 'institute', 'institute_id', 'phone_numbers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolSMSCreateSerializer(serializers.Serializer):
    """Serializer for validating school SMS creation data (no model creation)"""
    message = serializers.CharField(required=True, allow_blank=False)
    phone_numbers = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    # Note: institute is NOT in this serializer - handled in view
    
    def validate_phone_numbers(self, value):
        """Validate phone numbers list"""
        if not value or len(value) == 0:
            raise serializers.ValidationError("At least one phone number is required")
        
        # Validate each phone number format (basic validation)
        for phone in value:
            if not phone or not phone.strip():
                raise serializers.ValidationError("Phone numbers cannot be empty")
            if not phone.strip().isdigit() and not phone.strip().startswith('+'):
                raise serializers.ValidationError(f"Invalid phone number format: {phone}")
        
        return value
    
    def validate_message(self, value):
        """Validate message"""
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class SchoolSMSListSerializer(serializers.ModelSerializer):
    """Serializer for school SMS list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    phone_numbers_count = serializers.SerializerMethodField()
    message_preview = serializers.SerializerMethodField()
    
    class Meta:
        model = SchoolSMS
        fields = [
            'id', 'institute_name', 'message_preview', 'phone_numbers_count',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_phone_numbers_count(self, obj):
        return len(obj.phone_numbers) if obj.phone_numbers else 0
    
    def get_message_preview(self, obj):
        if obj.message and len(obj.message) > 50:
            return obj.message[:50] + "..."
        return obj.message or ""

