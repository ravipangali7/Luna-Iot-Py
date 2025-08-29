from rest_framework import serializers
from .models import *

class UserSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='role.name', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'name', 'phone', 'status', 'role_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = '__all__'
    
    def get_permissions(self, obj):
        return [
            {
                'permission': {
                    'id': rp.permission.id,
                    'name': rp.permission.name,
                }
            }
            for rp in obj.permissions.all()
        ]
    
    def get_users(self, obj):
        return [{'id': user.id, 'name': user.name, 'phone': user.phone} 
                for user in obj.users.all()]

class PermissionSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = Permission
        fields = '__all__'
    
    def get_roles(self, obj):
        return [
            {
                'role': {
                    'id': rp.role.id,
                    'name': rp.role.name,
                }
            }
            for rp in obj.roles.all()
        ]

class DeviceSerializer(serializers.ModelSerializer):
    user_devices = serializers.SerializerMethodField()
    vehicles = serializers.SerializerMethodField()
    
    class Meta:
        model = Device
        fields = '__all__'
    
    def get_user_devices(self, obj):
        user_devices = obj.userDevices.all()
        return [{
            'user': {
                'id': ud.user.id,
                'name': ud.user.name,
                'phone': ud.user.phone,
                'role': {'name': ud.user.role.name} if ud.user.role else None
            }
        } for ud in user_devices]
    
    def get_vehicles(self, obj):
        vehicles = obj.vehicles.all()
        return [{
            'id': v.id,
            'name': v.name,
            'vehicleNo': v.vehicle_no,
            'vehicleType': v.vehicle_type,
            'userVehicle': {
                'isMain': v.is_main,
                'user': {
                    'id': v.user.id,
                    'name': v.user.name,
                    'phone': v.user.phone
                }
            } if hasattr(v, 'uservehicle') else None
        } for v in vehicles]

class VehicleSerializer(serializers.ModelSerializer):
    latest_status = serializers.SerializerMethodField()
    latest_location = serializers.SerializerMethodField()
    today_km = serializers.SerializerMethodField()
    ownership_type = serializers.SerializerMethodField()
    user_vehicle = serializers.SerializerMethodField()
    
    class Meta:
        model = Vehicle
        fields = '__all__'
    
    def get_latest_status(self, obj):
        latest = obj.status_set.order_by('-created_at').first()
        return {
            'battery': latest.battery,
            'signal': latest.signal,
            'ignition': latest.ignition,
            'charging': latest.charging,
            'relay': latest.relay,
            'created_at': latest.created_at
        } if latest else None
    
    def get_latest_location(self, obj):
        latest = obj.location_set.order_by('-created_at').first()
        return {
            'latitude': latest.latitude,
            'longitude': latest.longitude,
            'speed': latest.speed,
            'created_at': latest.created_at
        } if latest else None
    
    def get_today_km(self, obj):
        # Calculate today's kilometers logic here
        return 0.0
    
    def get_ownership_type(self, obj):
        user_id = self.context.get('user_id')
        if user_id:
            user_vehicle = obj.uservehicle_set.filter(user_id=user_id).first()
            if user_vehicle:
                return 'Own' if user_vehicle.is_main else 'Shared'
        return 'Customer'
    
    def get_user_vehicle(self, obj):
        user_id = self.context.get('user_id')
        if user_id:
            return obj.uservehicle_set.filter(user_id=user_id).first()
        return None

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Status
        fields = '__all__'

class GeofenceSerializer(serializers.ModelSerializer):
    vehicles = serializers.SerializerMethodField()
    users = serializers.SerializerMethodField()
    
    class Meta:
        model = Geofence
        fields = '__all__'
    
    def get_vehicles(self, obj):
        return [{'vehicle': {'id': gv.vehicle.id, 'name': gv.vehicle.name}} 
                for gv in obj.geofencevehicle_set.all()]
    
    def get_users(self, obj):
        return [{'userId': gu.user.id, 'user': {'id': gu.user.id, 'name': gu.user.name, 'role': {'name': gu.user.role.name}}} 
                for gu in obj.geofenceuser_set.all()]

class NotificationSerializer(serializers.ModelSerializer):
    sent_by_role = serializers.CharField(source='sent_by.role.name', read_only=True)
    
    class Meta:
        model = Notification
        fields = '__all__'

class PopupSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Popup
        fields = '__all__'
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
        return None