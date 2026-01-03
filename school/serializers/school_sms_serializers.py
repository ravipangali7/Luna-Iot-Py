"""
School SMS Serializers
Handles serialization for school SMS management endpoints
"""
import json
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


class SchoolSMSCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating school SMS"""
    institute = serializers.IntegerField(required=True, min_value=1, write_only=True)
    phone_numbers = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    
    class Meta:
        model = SchoolSMS
        fields = ['message', 'phone_numbers']
        # Note: 'institute' is handled manually, not included in fields to prevent DRF from trying to set it as ForeignKey
    
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
    
    def validate_institute(self, value):
        """Validate institute is a valid positive integer"""
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"school_sms_serializers.py:61","message":"validate_institute called","data":{"value":value,"type":str(type(value))},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        if value is None:
            raise serializers.ValidationError("Institute is required")
        if value == 0:
            raise serializers.ValidationError("Institute ID cannot be 0")
        # Check if institute exists
        from core.models import Institute
        if not Institute.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"Institute with ID {value} does not exist")
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"school_sms_serializers.py:71","message":"validate_institute returning","data":{"value":value},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        return value
    
    def create(self, validated_data):
        """Create SchoolSMS instance, converting institute ID to Institute instance"""
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"school_sms_serializers.py:73","message":"create method called","data":{"validated_data_keys":list(validated_data.keys()),"institute_in_data":"institute" in validated_data},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        from core.models import Institute
        
        # Extract institute ID from validated_data
        institute_id = validated_data.pop('institute')
        
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"school_sms_serializers.py:80","message":"Institute ID extracted","data":{"institute_id":institute_id,"type":str(type(institute_id))},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        # Safety check: prevent 0 or None from reaching database
        if institute_id is None or institute_id == 0:
            raise serializers.ValidationError("Institute ID cannot be 0 or None")
        
        # Get the Institute instance
        institute = Institute.objects.get(id=institute_id)
        
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"school_sms_serializers.py:85","message":"About to create SchoolSMS","data":{"institute_id":institute.id,"institute_type":str(type(institute))},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        # Create SchoolSMS with Institute instance
        school_sms = SchoolSMS.objects.create(
            institute=institute,
            **validated_data
        )
        
        return school_sms


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

