"""
Luna Tag Serializers
Handles serialization for Luna Tag management endpoints
"""
from rest_framework import serializers
from device.models import LunaTag


class LunaTagSerializer(serializers.ModelSerializer):
    """Serializer for LunaTag model"""
    
    class Meta:
        model = LunaTag
        fields = [
            'id', 'publicKey', 'is_lost_mode', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class LunaTagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating LunaTag"""
    
    class Meta:
        model = LunaTag
        fields = ['publicKey', 'is_lost_mode']
    
    def validate_publicKey(self, value):
        """Validate publicKey"""
        if not value or not value.strip():
            raise serializers.ValidationError("PublicKey cannot be empty")
        
        # Check if publicKey already exists
        if LunaTag.objects.filter(publicKey=value.strip()).exists():
            raise serializers.ValidationError("LunaTag with this publicKey already exists")
        
        return value.strip()


class LunaTagUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating LunaTag"""
    
    class Meta:
        model = LunaTag
        fields = ['is_lost_mode']
    
    def validate_publicKey(self, value):
        """PublicKey cannot be updated"""
        if 'publicKey' in self.initial_data:
            raise serializers.ValidationError("PublicKey cannot be updated")
        return value

