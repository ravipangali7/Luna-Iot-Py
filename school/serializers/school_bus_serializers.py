"""
School Bus Serializers
Handles serialization for school bus management endpoints
"""
from rest_framework import serializers
from school.models import SchoolBus
from core.serializers import InstituteSerializer
from fleet.serializers import VehicleSerializer


class SchoolBusSerializer(serializers.ModelSerializer):
    """Serializer for school bus model"""
    institute = InstituteSerializer(read_only=True)
    institute_id = serializers.IntegerField(write_only=True, required=False)
    bus = VehicleSerializer(read_only=True)
    bus_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = SchoolBus
        fields = ['id', 'institute', 'institute_id', 'bus', 'bus_id', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class SchoolBusCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating school buses"""
    
    class Meta:
        model = SchoolBus
        fields = ['institute', 'bus']
    
    def validate(self, data):
        """Validate that institute and bus combination is unique"""
        institute = data.get('institute')
        bus = data.get('bus')
        
        if institute and bus:
            if SchoolBus.objects.filter(institute=institute, bus=bus).exists():
                raise serializers.ValidationError(
                    "This bus is already assigned to this institute"
                )
        
        return data


class SchoolBusListSerializer(serializers.ModelSerializer):
    """Serializer for school bus list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    bus_name = serializers.CharField(source='bus.name', read_only=True)
    bus_vehicle_no = serializers.CharField(source='bus.vehicleNo', read_only=True)
    
    class Meta:
        model = SchoolBus
        fields = ['id', 'institute_name', 'bus_name', 'bus_vehicle_no', 'created_at']
        read_only_fields = ['id', 'created_at']

