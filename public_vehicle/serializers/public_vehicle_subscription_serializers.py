"""
Public Vehicle Subscription Serializers
Handles serialization for public vehicle subscription endpoints
"""
from rest_framework import serializers
from public_vehicle.models import PublicVehicleSubscription
from fleet.models import Vehicle
from core.models import User


class PublicVehicleSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for public vehicle subscription"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    vehicle_id = serializers.IntegerField(source='vehicle.id', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = PublicVehicleSubscription
        fields = [
            'id', 'user_id', 'user_name', 'user_phone',
            'vehicle_id', 'vehicle_imei', 'vehicle_name',
            'latitude', 'longitude', 'notification',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PublicVehicleSubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating public vehicle subscription"""
    imei = serializers.CharField(write_only=True, required=True)
    latitude = serializers.DecimalField(max_digits=18, decimal_places=15, required=True)
    longitude = serializers.DecimalField(max_digits=19, decimal_places=15, required=True)
    
    class Meta:
        model = PublicVehicleSubscription
        fields = ['imei', 'latitude', 'longitude', 'notification']
    
    def validate_imei(self, value):
        """Validate that vehicle with IMEI exists and is a public vehicle"""
        try:
            vehicle = Vehicle.objects.get(imei=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle with IMEI {value} not found or inactive")
        
        # Check if vehicle is a public vehicle
        from public_vehicle.models import PublicVehicle
        if not PublicVehicle.objects.filter(vehicle=vehicle, is_active=True).exists():
            raise serializers.ValidationError(f"Vehicle with IMEI {value} is not a public vehicle")
        
        return value
    
    def validate_latitude(self, value):
        """Validate latitude range"""
        if value < -90 or value > 90:
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude range"""
        if value < -180 or value > 180:
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value
    
    def create(self, validated_data):
        """Create or update subscription"""
        imei = validated_data.pop('imei')
        user = self.context['request'].user
        
        # Get vehicle
        vehicle = Vehicle.objects.get(imei=imei)
        
        # Get or create subscription
        subscription, created = PublicVehicleSubscription.objects.update_or_create(
            user=user,
            vehicle=vehicle,
            defaults={
                'latitude': validated_data['latitude'],
                'longitude': validated_data['longitude'],
                'notification': validated_data.get('notification', True)
            }
        )
        
        return subscription
    
    def update(self, instance, validated_data):
        """Update subscription location"""
        if 'latitude' in validated_data:
            instance.latitude = validated_data['latitude']
        if 'longitude' in validated_data:
            instance.longitude = validated_data['longitude']
        if 'notification' in validated_data:
            instance.notification = validated_data['notification']
        instance.save()
        return instance

