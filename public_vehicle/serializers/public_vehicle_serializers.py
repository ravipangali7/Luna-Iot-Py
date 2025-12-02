"""
Public Vehicle Serializers
Handles serialization for public vehicle management endpoints
"""
from rest_framework import serializers
from public_vehicle.models import PublicVehicle, PublicVehicleImage
from core.serializers import InstituteSerializer
from fleet.serializers import VehicleSerializer


class PublicVehicleImageSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle images"""
    
    class Meta:
        model = PublicVehicleImage
        fields = ['id', 'image', 'title', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicVehicleSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle model with images"""
    institute = InstituteSerializer(read_only=True)
    institute_id = serializers.IntegerField(write_only=True, required=False)
    vehicle = VehicleSerializer(read_only=True)
    vehicle_id = serializers.IntegerField(write_only=True, required=False)
    images = PublicVehicleImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = PublicVehicle
        fields = ['id', 'institute', 'institute_id', 'vehicle', 'vehicle_id', 'description', 'is_active', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicVehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating public vehicles"""
    
    class Meta:
        model = PublicVehicle
        fields = ['institute', 'vehicle', 'description', 'is_active']
    
    def validate(self, data):
        """Validate that institute and vehicle combination is unique"""
        institute = data.get('institute')
        vehicle = data.get('vehicle')
        
        if institute and vehicle:
            # Check for existing public vehicle with same institute and vehicle
            existing = PublicVehicle.objects.filter(institute=institute, vehicle=vehicle)
            # Exclude current instance if updating
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    "This vehicle is already assigned to this institute"
                )
        
        return data


class PublicVehicleListSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    vehicle_vehicle_no = serializers.CharField(source='vehicle.vehicleNo', read_only=True)
    image_count = serializers.SerializerMethodField()
    first_image = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicVehicle
        fields = ['id', 'institute_name', 'vehicle_name', 'vehicle_vehicle_no', 'description', 'is_active', 'image_count', 'first_image', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_image_count(self, obj):
        """Get the number of images for this vehicle"""
        return obj.images.count()
    
    def get_first_image(self, obj):
        """Get the first image URL if available"""
        first_image = obj.images.order_by('order', 'created_at').first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None

