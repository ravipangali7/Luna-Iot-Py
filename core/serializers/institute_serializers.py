"""
Institute Serializers
Handles serialization for institute management endpoints
"""
from rest_framework import serializers
from core.models import Institute, InstituteService


class InstituteSerializer(serializers.ModelSerializer):
    """Serializer for institute model"""
    institute_services = serializers.SerializerMethodField()
    location = serializers.ReadOnlyField()
    
    class Meta:
        model = Institute
        fields = [
            'id', 'name', 'description', 'phone', 'address', 
            'latitude', 'longitude', 'logo', 'institute_services',
            'location', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'location']
    
    def get_institute_services(self, obj):
        """Get institute services with basic info"""
        return [
            {
                'id': service.id, 
                'name': service.name, 
                'icon': service.icon
            } 
            for service in obj.institute_services.all()
        ]
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_phone(self, value):
        """Validate phone number"""
        if value and not value.strip():
            return None
        return value.strip() if value else None


class InstituteCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating institutes"""
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Institute Service IDs"
    )
    
    class Meta:
        model = Institute
        fields = [
            'name', 'description', 'phone', 'address', 
            'latitude', 'longitude', 'logo', 'service_ids'
        ]
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if Institute.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Institute with this name already exists")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number"""
        if value and not value.strip():
            return None
        return value.strip() if value else None
    
    def validate_service_ids(self, value):
        """Validate service IDs exist"""
        if value:
            existing_services = InstituteService.objects.filter(id__in=value)
            if len(existing_services) != len(value):
                raise serializers.ValidationError("One or more institute services do not exist")
        return value
    
    def create(self, validated_data):
        """Create institute with services"""
        service_ids = validated_data.pop('service_ids', [])
        
        # Create institute
        institute = Institute.objects.create(**validated_data)
        
        # Assign services
        if service_ids:
            institute.institute_services.set(service_ids)
        
        return institute


class InstituteUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating institutes"""
    service_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Institute Service IDs"
    )
    
    class Meta:
        model = Institute
        fields = [
            'name', 'description', 'phone', 'address', 
            'latitude', 'longitude', 'logo', 'service_ids'
        ]
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if self.instance and Institute.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Institute with this name already exists")
        
        return value
    
    def validate_phone(self, value):
        """Validate phone number"""
        if value and not value.strip():
            return None
        return value.strip() if value else None
    
    def validate_service_ids(self, value):
        """Validate service IDs exist"""
        if value:
            existing_services = InstituteService.objects.filter(id__in=value)
            if len(existing_services) != len(value):
                raise serializers.ValidationError("One or more institute services do not exist")
        return value
    
    def update(self, instance, validated_data):
        """Update institute and services"""
        service_ids = validated_data.pop('service_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update services if provided
        if service_ids is not None:
            instance.institute_services.set(service_ids)
        
        return instance


class InstituteListSerializer(serializers.ModelSerializer):
    """Serializer for institute list (minimal data)"""
    institute_services = InstituteServiceSerializer(many=True, read_only=True)
    service_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Institute
        fields = [
            'id', 'name', 'phone', 'address', 
            'institute_services', 'service_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_service_count(self, obj):
        """Get number of services"""
        return obj.institute_services.count()


class InstituteLocationSerializer(serializers.ModelSerializer):
    """Serializer for institute location data"""
    
    class Meta:
        model = Institute
        fields = ['id', 'name', 'latitude', 'longitude', 'address']
        read_only_fields = ['id']
