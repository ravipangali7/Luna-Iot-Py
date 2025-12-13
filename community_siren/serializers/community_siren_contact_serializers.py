"""
Community Siren Contact Serializers
Handles serialization for community siren contact management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenContact
from core.models import Institute


class CommunitySirenContactSerializer(serializers.ModelSerializer):
    """Serializer for community siren contact model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = CommunitySirenContact
        fields = [
            'id', 'name', 'phone', 'institute', 'institute_name',
            'is_sms', 'is_call', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenContactCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren contacts"""
    
    class Meta:
        model = CommunitySirenContact
        fields = ['name', 'phone', 'institute', 'is_sms', 'is_call']
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value


class CommunitySirenContactUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren contacts"""
    
    class Meta:
        model = CommunitySirenContact
        fields = ['name', 'phone', 'is_sms', 'is_call']
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value
    
    def validate_phone(self, value):
        """Validate phone"""
        if value and not value.strip():
            raise serializers.ValidationError("Phone cannot be empty")
        return value.strip() if value else value


class CommunitySirenContactListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren contacts"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = CommunitySirenContact
        fields = [
            'id', 'name', 'phone', 'institute', 'institute_name',
            'is_sms', 'is_call', 'created_at', 'updated_at'
        ]
