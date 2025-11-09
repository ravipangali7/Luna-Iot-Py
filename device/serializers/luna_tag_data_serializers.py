"""
Luna Tag Data Serializers
Handles serialization for LunaTagData endpoints
"""
from rest_framework import serializers
from device.models import LunaTagData


class LunaTagDataSerializer(serializers.ModelSerializer):
    """Serializer for LunaTagData model (read-only)"""
    publicKey_value = serializers.CharField(source='publicKey.publicKey', read_only=True)
    
    class Meta:
        model = LunaTagData
        fields = [
            'id', 'publicKey', 'publicKey_value', 'battery', 
            'latitude', 'longitude', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'publicKey', 'battery', 'latitude', 'longitude', 'created_at', 'updated_at']

