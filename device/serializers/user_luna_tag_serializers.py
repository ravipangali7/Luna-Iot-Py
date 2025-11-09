"""
User Luna Tag Serializers
Handles serialization for UserLunaTag management endpoints
"""
from rest_framework import serializers
from device.models import UserLunaTag, LunaTag


class UserLunaTagSerializer(serializers.ModelSerializer):
    """Serializer for UserLunaTag model"""
    publicKey_value = serializers.CharField(source='publicKey.publicKey', read_only=True)
    
    class Meta:
        model = UserLunaTag
        fields = [
            'id', 'publicKey', 'publicKey_value', 'name', 'image', 
            'expire_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserLunaTagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating UserLunaTag"""
    
    class Meta:
        model = UserLunaTag
        fields = ['publicKey', 'name', 'image', 'expire_date', 'is_active']
    
    def validate_publicKey(self, value):
        """Validate that LunaTag exists"""
        if not value:
            raise serializers.ValidationError("PublicKey is required")
        
        try:
            luna_tag = LunaTag.objects.get(publicKey=value)
            return luna_tag
        except LunaTag.DoesNotExist:
            raise serializers.ValidationError("LunaTag with this publicKey does not exist")
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()


class UserLunaTagUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating UserLunaTag"""
    
    class Meta:
        model = UserLunaTag
        fields = ['name', 'image', 'expire_date', 'is_active']
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value

