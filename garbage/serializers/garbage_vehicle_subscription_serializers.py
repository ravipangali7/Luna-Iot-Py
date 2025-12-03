"""
Garbage Vehicle Subscription Serializers
Handles serialization for garbage vehicle subscription endpoints
"""
from rest_framework import serializers
from garbage.models import GarbageVehicleSubscription
from fleet.models import Vehicle
from core.models import User


class GarbageVehicleSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for garbage vehicle subscription"""
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    vehicle_id = serializers.IntegerField(source='vehicle.id', read_only=True)
    vehicle_imei = serializers.CharField(source='vehicle.imei', read_only=True)
    vehicle_name = serializers.CharField(source='vehicle.name', read_only=True)
    
    class Meta:
        model = GarbageVehicleSubscription
        fields = [
            'id', 'user_id', 'user_name', 'user_phone',
            'vehicle_id', 'vehicle_imei', 'vehicle_name',
            'latitude', 'longitude', 'notification',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GarbageVehicleSubscriptionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating garbage vehicle subscription"""
    imei = serializers.CharField(write_only=True, required=True)
    latitude = serializers.DecimalField(max_digits=18, decimal_places=15, required=True)
    longitude = serializers.DecimalField(max_digits=19, decimal_places=15, required=True)
    
    class Meta:
        model = GarbageVehicleSubscription
        fields = ['imei', 'latitude', 'longitude', 'notification']
    
    def validate_imei(self, value):
        """Validate that vehicle with IMEI exists and is a garbage vehicle"""
        try:
            vehicle = Vehicle.objects.get(imei=value, is_active=True)
        except Vehicle.DoesNotExist:
            raise serializers.ValidationError(f"Vehicle with IMEI {value} not found or inactive")
        
        # Check if vehicle is a garbage vehicle
        from garbage.models import GarbageVehicle
        if not GarbageVehicle.objects.filter(vehicle=vehicle).exists():
            raise serializers.ValidationError(f"Vehicle with IMEI {value} is not a garbage vehicle")
        
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
        subscription, created = GarbageVehicleSubscription.objects.update_or_create(
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

