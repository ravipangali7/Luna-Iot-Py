"""
Community Siren Members Serializers
Handles serialization for community siren members management endpoints
"""
from rest_framework import serializers
from community_siren.models import CommunitySirenMembers
from core.models import User, Institute


class CommunitySirenMembersSerializer(serializers.ModelSerializer):
    """Serializer for community siren members model"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = CommunitySirenMembers
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'institute', 'institute_name', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenMembersCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren members"""
    
    class Meta:
        model = CommunitySirenMembers
        fields = ['user', 'institute']
    
    def validate_user(self, value):
        """Validate user exists"""
        if not value:
            raise serializers.ValidationError("User is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate(self, data):
        """Validate that user-institute combination is unique"""
        user = data.get('user')
        institute = data.get('institute')
        
        if user and institute:
            if CommunitySirenMembers.objects.filter(user=user, institute=institute).exists():
                raise serializers.ValidationError(
                    "This user is already a member of this institute."
                )
        return data


class CommunitySirenMembersUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren members"""
    
    class Meta:
        model = CommunitySirenMembers
        fields = ['user', 'institute']
    
    def validate_user(self, value):
        """Validate user exists"""
        if not value:
            raise serializers.ValidationError("User is required")
        return value
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate(self, data):
        """Validate that user-institute combination is unique (excluding current instance)"""
        user = data.get('user', self.instance.user if self.instance else None)
        institute = data.get('institute', self.instance.institute if self.instance else None)
        
        if user and institute:
            existing = CommunitySirenMembers.objects.filter(user=user, institute=institute)
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    "This user is already a member of this institute."
                )
        return data


class CommunitySirenMembersListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren members"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    
    class Meta:
        model = CommunitySirenMembers
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'institute', 'institute_name', 'created_at', 'updated_at'
        ]
