"""
Alert Geofence Serializers
Handles serialization for alert geofence management endpoints
"""
from rest_framework import serializers
from alert_system.models import AlertGeofence
from core.models import Institute


class AlertGeofenceSerializer(serializers.ModelSerializer):
    """Serializer for alert geofence model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    institute_latitude = serializers.FloatField(source='institute.latitude', read_only=True)
    institute_longitude = serializers.FloatField(source='institute.longitude', read_only=True)
    alert_types = serializers.SerializerMethodField()
    alert_types_names = serializers.SerializerMethodField()
    alert_types_count = serializers.SerializerMethodField()
    # Let boundary use default JSONField serialization for web management
    
    class Meta:
        model = AlertGeofence
        fields = [
            'id', 'title', 'institute', 'institute_name', 'institute_latitude', 
            'institute_longitude', 'boundary', 'alert_types', 'alert_types_names', 
            'alert_types_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'alert_types_count']
    
    def get_alert_types(self, obj):
        """Get alert types with basic info"""
        return [
            {
                'id': alert_type.id,
                'name': alert_type.name,
                'icon': alert_type.icon
            }
            for alert_type in obj.alert_types.all()
        ]
    
    def get_alert_types_names(self, obj):
        """Get alert type names as list of strings"""
        return [alert_type.name for alert_type in obj.alert_types.all()]
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()


class AlertGeofenceSosSerializer(serializers.ModelSerializer):
    """Serializer for SOS feature - converts GeoJSON to simple coordinate array"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    institute_latitude = serializers.FloatField(source='institute.latitude', read_only=True)
    institute_longitude = serializers.FloatField(source='institute.longitude', read_only=True)
    alert_types = serializers.SerializerMethodField()
    boundary = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertGeofence
        fields = [
            'id', 'title', 'institute', 'institute_name', 'institute_latitude', 
            'institute_longitude', 'boundary', 'alert_types'
        ]
        read_only_fields = ['id']
    
    def get_boundary(self, obj):
        """Convert GeoJSON boundary to simple coordinate array string for Flutter"""
        import json
        
        if not obj.boundary:
            return ""
        
        try:
            geojson = obj.boundary
            
            # Handle Polygon type
            if geojson.get('type') == 'Polygon':
                coordinates = geojson.get('coordinates', [[]])[0]
                # Convert from [lng, lat] to [lat, lng]
                simple_coords = [[coord[1], coord[0]] for coord in coordinates]
                return json.dumps(simple_coords)
            
            # Handle MultiPolygon type
            elif geojson.get('type') == 'MultiPolygon':
                coordinates = geojson.get('coordinates', [[[]]])[0][0]
                # Convert from [lng, lat] to [lat, lng]
                simple_coords = [[coord[1], coord[0]] for coord in coordinates]
                return json.dumps(simple_coords)
            
            return ""
        except (KeyError, IndexError, TypeError) as e:
            print(f"Error converting boundary: {e}")
            return ""
    
    def get_alert_types(self, obj):
        """Get alert types with basic info"""
        return [
            {
                'id': alert_type.id,
                'name': alert_type.name,
                'icon': alert_type.icon
            }
            for alert_type in obj.alert_types.all()
        ]


class AlertGeofenceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating alert geofences"""
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertGeofence
        fields = ['title', 'institute', 'boundary', 'alert_type_ids']
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_boundary(self, value):
        """Validate GeoJSON boundary format"""
        if not value:
            raise serializers.ValidationError("Boundary is required")
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Boundary must be a valid GeoJSON object")
        
        # Check for required GeoJSON fields
        if 'type' not in value:
            raise serializers.ValidationError("Boundary must have a 'type' field")
        
        if 'coordinates' not in value:
            raise serializers.ValidationError("Boundary must have a 'coordinates' field")
        
        # Support Polygon and MultiPolygon
        if value['type'] not in ['Polygon', 'MultiPolygon']:
            raise serializers.ValidationError("Boundary type must be 'Polygon' or 'MultiPolygon'")
        
        # Validate coordinates structure
        coordinates = value['coordinates']
        if not isinstance(coordinates, list):
            raise serializers.ValidationError("Coordinates must be a list")
        
        if value['type'] == 'Polygon':
            if len(coordinates) == 0:
                raise serializers.ValidationError("Polygon must have at least one ring")
            # Validate first ring (exterior ring)
            if not isinstance(coordinates[0], list) or len(coordinates[0]) < 4:
                raise serializers.ValidationError("Polygon exterior ring must have at least 4 coordinates")
            # Check if first and last coordinates are the same (closed polygon)
            if coordinates[0][0] != coordinates[0][-1]:
                raise serializers.ValidationError("Polygon must be closed (first and last coordinates must be the same)")
        
        elif value['type'] == 'MultiPolygon':
            if len(coordinates) == 0:
                raise serializers.ValidationError("MultiPolygon must have at least one polygon")
            for i, polygon in enumerate(coordinates):
                if not isinstance(polygon, list) or len(polygon) == 0:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} must have at least one ring")
                if not isinstance(polygon[0], list) or len(polygon[0]) < 4:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} exterior ring must have at least 4 coordinates")
                if polygon[0][0] != polygon[0][-1]:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} must be closed")
        
        return value
    
    def create(self, validated_data):
        """Create alert geofence with alert types"""
        alert_type_ids = validated_data.pop('alert_type_ids', [])
        
        # Create geofence
        geofence = AlertGeofence.objects.create(**validated_data)
        
        # Assign alert types
        if alert_type_ids:
            geofence.alert_types.set(alert_type_ids)
        
        return geofence


class AlertGeofenceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating alert geofences"""
    alert_type_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Alert Type IDs"
    )
    
    class Meta:
        model = AlertGeofence
        fields = ['title', 'institute', 'boundary', 'alert_type_ids']
        extra_kwargs = {
            'institute': {'required': False},
            'boundary': {'required': False}
        }
    
    def validate_title(self, value):
        """Validate title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists (optional for updates)"""
        if value and not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_boundary(self, value):
        """Validate GeoJSON boundary format (optional for updates)"""
        if not value:
            return value  # Allow None/empty for updates
        
        if not isinstance(value, dict):
            raise serializers.ValidationError("Boundary must be a valid GeoJSON object")
        
        # Check for required GeoJSON fields
        if 'type' not in value:
            raise serializers.ValidationError("Boundary must have a 'type' field")
        
        if 'coordinates' not in value:
            raise serializers.ValidationError("Boundary must have a 'coordinates' field")
        
        # Support Polygon and MultiPolygon
        if value['type'] not in ['Polygon', 'MultiPolygon']:
            raise serializers.ValidationError("Boundary type must be 'Polygon' or 'MultiPolygon'")
        
        # Validate coordinates structure
        coordinates = value['coordinates']
        if not isinstance(coordinates, list):
            raise serializers.ValidationError("Coordinates must be a list")
        
        if value['type'] == 'Polygon':
            if len(coordinates) == 0:
                raise serializers.ValidationError("Polygon must have at least one ring")
            # Validate first ring (exterior ring)
            if not isinstance(coordinates[0], list) or len(coordinates[0]) < 4:
                raise serializers.ValidationError("Polygon exterior ring must have at least 4 coordinates")
            # Check if first and last coordinates are the same (closed polygon)
            if coordinates[0][0] != coordinates[0][-1]:
                raise serializers.ValidationError("Polygon must be closed (first and last coordinates must be the same)")
        
        elif value['type'] == 'MultiPolygon':
            if len(coordinates) == 0:
                raise serializers.ValidationError("MultiPolygon must have at least one polygon")
            for i, polygon in enumerate(coordinates):
                if not isinstance(polygon, list) or len(polygon) == 0:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} must have at least one ring")
                if not isinstance(polygon[0], list) or len(polygon[0]) < 4:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} exterior ring must have at least 4 coordinates")
                if polygon[0][0] != polygon[0][-1]:
                    raise serializers.ValidationError(f"MultiPolygon polygon {i} must be closed")
        
        return value
    
    def update(self, instance, validated_data):
        """Update alert geofence and alert types"""
        alert_type_ids = validated_data.pop('alert_type_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update alert types if provided
        if alert_type_ids is not None:
            instance.alert_types.set(alert_type_ids)
        
        return instance


class AlertGeofenceListSerializer(serializers.ModelSerializer):
    """Serializer for alert geofence list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    alert_types_names = serializers.SerializerMethodField()
    alert_types_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertGeofence
        fields = [
            'id', 'title', 'institute', 'institute_name',
            'alert_types_names', 'alert_types_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_alert_types_names(self, obj):
        """Get alert type names as list of strings"""
        return [alert_type.name for alert_type in obj.alert_types.all()]
    
    def get_alert_types_count(self, obj):
        """Get number of alert types"""
        return obj.alert_types.count()
