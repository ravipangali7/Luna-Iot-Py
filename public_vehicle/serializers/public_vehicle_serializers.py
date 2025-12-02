"""
Public Vehicle Serializers
Handles serialization for public vehicle management endpoints
"""
from rest_framework import serializers
from public_vehicle.models import PublicVehicle, PublicVehicleImage
from core.serializers import InstituteSerializer


class PublicVehicleImageSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle images"""
    
    class Meta:
        model = PublicVehicleImage
        fields = ['id', 'image', 'order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicVehicleSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle model with images"""
    institute = InstituteSerializer(read_only=True)
    institute_id = serializers.IntegerField(write_only=True, required=False)
    images = PublicVehicleImageSerializer(many=True, read_only=True)
    
    class Meta:
        model = PublicVehicle
        fields = ['id', 'institute', 'institute_id', 'description', 'is_active', 'images', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicVehicleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating public vehicles"""
    
    class Meta:
        model = PublicVehicle
        fields = ['institute', 'description', 'is_active']
    
    def validate(self, data):
        """Validate the data"""
        return data


class PublicVehicleListSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    image_count = serializers.SerializerMethodField()
    first_image = serializers.SerializerMethodField()
    
    class Meta:
        model = PublicVehicle
        fields = ['id', 'institute_name', 'description', 'is_active', 'image_count', 'first_image', 'created_at']
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

