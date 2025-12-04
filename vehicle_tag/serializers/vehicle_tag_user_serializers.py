"""
Vehicle Tag User Serializers
Handles serialization for vehicle tag user assignment endpoints
"""
from rest_framework import serializers
from vehicle_tag.models import VehicleTagUser
from core.serializers import UserSerializer


class VehicleTagUserSerializer(serializers.ModelSerializer):
    """Serializer for vehicle tag user model"""
    user = UserSerializer(read_only=True)
    vehicle_tag_vtid = serializers.CharField(source='vehicle_tag.vtid', read_only=True)
    
    class Meta:
        model = VehicleTagUser
        fields = [
            'id', 'vehicle_tag', 'vehicle_tag_vtid', 'vtid', 'user', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vtid', 'created_at', 'updated_at']

