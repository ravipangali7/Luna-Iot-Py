"""
Institute Service Serializers
Handles serialization for institute service management endpoints
"""
from rest_framework import serializers
from core.models import InstituteService


class InstituteServiceSerializer(serializers.ModelSerializer):
    """Serializer for institute service model"""
    
    class Meta:
        model = InstituteService
        fields = [
            'id', 'name', 'icon', 'description', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()


class InstituteServiceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating institute services"""
    
    class Meta:
        model = InstituteService
        fields = ['name', 'icon', 'description']
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if InstituteService.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Institute service with this name already exists")
        
        return value


class InstituteServiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating institute services"""
    
    class Meta:
        model = InstituteService
        fields = ['name', 'icon', 'description']
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if self.instance and InstituteService.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Institute service with this name already exists")
        
        return value


class InstituteServiceListSerializer(serializers.ModelSerializer):
    """Serializer for institute service list (minimal data)"""
    
    class Meta:
        model = InstituteService
        fields = ['id', 'name', 'icon']
        read_only_fields = ['id']
