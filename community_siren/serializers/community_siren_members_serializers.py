"""
Community Siren Members Serializers
Handles serialization for community siren members management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenMembers
from core.models import User


class CommunitySirenMembersSerializer(serializers.ModelSerializer):
    """Serializer for community siren members model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenMembers
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenMembersCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren members"""
    
    class Meta:
        model = CommunitySirenMembers
        fields = ['user']
    
    def validate_user(self, value):
        """Validate user exists"""
        if not value:
            raise serializers.ValidationError("User is required")
        return value


class CommunitySirenMembersUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren members"""
    
    class Meta:
        model = CommunitySirenMembers
        fields = ['user']
    
    def validate_user(self, value):
        """Validate user exists"""
        if not value:
            raise serializers.ValidationError("User is required")
        return value


class CommunitySirenMembersListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren members"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = CommunitySirenMembers
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'created_at', 'updated_at'
        ]
