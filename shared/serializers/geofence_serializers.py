"""
Geofence Serializers
Handles serialization for geofence management endpoints
"""
from rest_framework import serializers
from shared.models import Geofence, GeofenceUser
from core.models import User
from api_common.utils.validation_utils import validate_imei


class GeofenceSerializer(serializers.ModelSerializer):
    """Serializer for geofence model"""
    user_count = serializers.SerializerMethodField()
    vehicle_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Geofence
        fields = [
            'id', 'title', 'type', 'boundary', 
            'user_count', 'vehicle_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_user_count(self, obj):
        """Get count of users assigned to this geofence"""
        return obj.users.count()
    
    def get_vehicle_count(self, obj):
        """Get count of vehicles assigned to this geofence"""
        return obj.vehicles.count()


class GeofenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating geofences"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of user IDs to assign to geofence"
    )
    vehicle_imeis = serializers.ListField(
        child=serializers.CharField(max_length=15),
        required=False,
        help_text="List of vehicle IMEIs to assign to geofence"
    )
    
    class Meta:
        model = Geofence
        fields = ['title', 'type', 'boundary', 'user_ids', 'vehicle_imeis']
    
    def validate_title(self, value):
        """Validate geofence title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Geofence title cannot be empty")
        return value.strip()
    
    def validate_boundary(self, value):
        """Validate boundary data"""
        if not value:
            raise serializers.ValidationError("Boundary data is required")
        
        # Basic validation for boundary structure
        if not isinstance(value, dict):
            raise serializers.ValidationError("Boundary must be a valid JSON object")
        
        return value
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if value:
            existing_users = User.objects.filter(id__in=value)
            if len(existing_users) != len(value):
                raise serializers.ValidationError("One or more user IDs are invalid")
        return value
    
    def validate_vehicle_imeis(self, value):
        """Validate vehicle IMEIs exist"""
        if value:
            from fleet.models import Vehicle
            for imei in value:
                if not validate_imei(imei):
                    raise serializers.ValidationError(f"Invalid IMEI format: {imei}")
            
            existing_vehicles = Vehicle.objects.filter(imei__in=value)
            if len(existing_vehicles) != len(value):
                raise serializers.ValidationError("One or more vehicle IMEIs are invalid")
        return value
    
    def create(self, validated_data):
        """Create geofence with users and vehicles"""
        user_ids = validated_data.pop('user_ids', [])
        vehicle_imeis = validated_data.pop('vehicle_imeis', [])
        
        geofence = Geofence.objects.create(**validated_data)
        
        # Assign users
        if user_ids:
            users = User.objects.filter(id__in=user_ids)
            for user in users:
                GeofenceUser.objects.create(geofence=geofence, user=user)
        
        # Assign vehicles
        if vehicle_imeis:
            from fleet.models import Vehicle, GeofenceVehicle
            vehicles = Vehicle.objects.filter(imei__in=vehicle_imeis)
            for vehicle in vehicles:
                GeofenceVehicle.objects.create(geofence=geofence, vehicle=vehicle)
        
        return geofence


class GeofenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating geofences"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of user IDs to assign to geofence"
    )
    vehicle_imeis = serializers.ListField(
        child=serializers.CharField(max_length=15),
        required=False,
        help_text="List of vehicle IMEIs to assign to geofence"
    )
    
    class Meta:
        model = Geofence
        fields = ['title', 'type', 'boundary', 'user_ids', 'vehicle_imeis']
    
    def validate_title(self, value):
        """Validate geofence title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Geofence title cannot be empty")
        return value.strip()
    
    def validate_boundary(self, value):
        """Validate boundary data"""
        if not value:
            raise serializers.ValidationError("Boundary data is required")
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Boundary must be a valid JSON object")
        
        return value
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if value:
            existing_users = User.objects.filter(id__in=value)
            if len(existing_users) != len(value):
                raise serializers.ValidationError("One or more user IDs are invalid")
        return value
    
    def validate_vehicle_imeis(self, value):
        """Validate vehicle IMEIs exist"""
        if value:
            from fleet.models import Vehicle
            for imei in value:
                if not validate_imei(imei):
                    raise serializers.ValidationError(f"Invalid IMEI format: {imei}")
            
            existing_vehicles = Vehicle.objects.filter(imei__in=value)
            if len(existing_vehicles) != len(value):
                raise serializers.ValidationError("One or more vehicle IMEIs are invalid")
        return value
    
    def update(self, instance, validated_data):
        """Update geofence with users and vehicles"""
        user_ids = validated_data.pop('user_ids', None)
        vehicle_imeis = validated_data.pop('vehicle_imeis', None)
        
        # Update geofence fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update users if provided
        if user_ids is not None:
            # Clear existing user assignments
            GeofenceUser.objects.filter(geofence=instance).delete()
            
            # Add new user assignments
            if user_ids:
                users = User.objects.filter(id__in=user_ids)
                for user in users:
                    GeofenceUser.objects.create(geofence=instance, user=user)
        
        # Update vehicles if provided
        if vehicle_imeis is not None:
            from fleet.models import GeofenceVehicle
            # Clear existing vehicle assignments
            GeofenceVehicle.objects.filter(geofence=instance).delete()
            
            # Add new vehicle assignments
            if vehicle_imeis:
                from fleet.models import Vehicle
                vehicles = Vehicle.objects.filter(imei__in=vehicle_imeis)
                for vehicle in vehicles:
                    GeofenceVehicle.objects.create(geofence=instance, vehicle=vehicle)
        
        return instance


class GeofenceListSerializer(serializers.ModelSerializer):
    """Serializer for geofence list (minimal data)"""
    user_count = serializers.SerializerMethodField()
    vehicle_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Geofence
        fields = [
            'id', 'title', 'type', 'user_count', 
            'vehicle_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_count(self, obj):
        """Get count of users assigned to this geofence"""
        return obj.users.count()
    
    def get_vehicle_count(self, obj):
        """Get count of vehicles assigned to this geofence"""
        return obj.vehicles.count()


class GeofenceFilterSerializer(serializers.Serializer):
    """Serializer for geofence search filters"""
    title = serializers.CharField(
        required=False,
        help_text="Filter by geofence title"
    )
    type = serializers.CharField(
        required=False,
        help_text="Filter by geofence type"
    )
    user_id = serializers.IntegerField(
        required=False,
        help_text="Filter by user ID"
    )
    vehicle_imei = serializers.CharField(
        required=False,
        help_text="Filter by vehicle IMEI"
    )
    
    def validate_user_id(self, value):
        """Validate user exists if provided"""
        if value:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate_vehicle_imei(self, value):
        """Validate IMEI format if provided"""
        if value and not validate_imei(value):
            raise serializers.ValidationError("Invalid IMEI format")
        return value


class GeofenceUserSerializer(serializers.ModelSerializer):
    """Serializer for geofence-user relationships"""
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    geofence_title = serializers.CharField(source='geofence.title', read_only=True)
    
    class Meta:
        model = GeofenceUser
        fields = [
            'id', 'geofence', 'geofence_title', 'user', 
            'user_name', 'user_phone', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class GeofenceStatsSerializer(serializers.Serializer):
    """Serializer for geofence statistics"""
    total_geofences = serializers.IntegerField()
    geofences_by_type = serializers.DictField()
    total_users = serializers.IntegerField()
    total_vehicles = serializers.IntegerField()
    recent_geofences = serializers.IntegerField()


class GeofenceEventSerializer(serializers.Serializer):
    """Serializer for geofence event model with full details"""
    id = serializers.IntegerField(read_only=True)
    vehicle_id = serializers.IntegerField()
    geofence_id = serializers.IntegerField()
    is_inside = serializers.BooleanField()
    last_event_type = serializers.ChoiceField(choices=['Entry', 'Exit'])
    last_event_at = serializers.DateTimeField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Additional fields for display
    vehicle_name = serializers.CharField(read_only=True, required=False)
    vehicle_no = serializers.CharField(read_only=True, required=False)
    vehicle_imei = serializers.CharField(read_only=True, required=False)
    geofence_title = serializers.CharField(read_only=True, required=False)
    geofence_type = serializers.CharField(read_only=True, required=False)


class GeofenceEventListSerializer(serializers.Serializer):
    """Serializer for geofence event list (minimal data)"""
    id = serializers.IntegerField(read_only=True)
    vehicle_id = serializers.IntegerField()
    geofence_id = serializers.IntegerField()
    is_inside = serializers.BooleanField()
    last_event_type = serializers.ChoiceField(choices=['Entry', 'Exit'])
    last_event_at = serializers.DateTimeField()
    vehicle_no = serializers.CharField(read_only=True, required=False)
    geofence_title = serializers.CharField(read_only=True, required=False)


class GeofenceEventFilterSerializer(serializers.Serializer):
    """Serializer for geofence event search filters"""
    vehicle_id = serializers.IntegerField(
        required=False,
        help_text="Filter by vehicle ID"
    )
    geofence_id = serializers.IntegerField(
        required=False,
        help_text="Filter by geofence ID"
    )
    imei = serializers.CharField(
        required=False,
        help_text="Filter by vehicle IMEI"
    )
    is_inside = serializers.BooleanField(
        required=False,
        help_text="Filter by current state (inside/outside)"
    )
    event_type = serializers.ChoiceField(
        choices=['Entry', 'Exit'],
        required=False,
        help_text="Filter by event type"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data