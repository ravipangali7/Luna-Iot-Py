"""
Module Serializers
Handles serialization for module management endpoints
"""
from rest_framework import serializers
from django.utils.text import slugify
from core.models import Module


class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for module model"""
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'slug', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating modules"""
    
    class Meta:
        model = Module
        fields = ['name', 'slug']
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if Module.objects.filter(name__iexact=value).exists():
            raise serializers.ValidationError("Module with this name already exists")
        
        return value
    
    def validate_slug(self, value):
        """Validate slug and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Slug cannot be empty")
        
        value = value.strip()
        if Module.objects.filter(slug__iexact=value).exists():
            raise serializers.ValidationError("Module with this slug already exists")
        
        return value
    
    def create(self, validated_data):
        """Create module with auto-generated slug if not provided"""
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'])
        
        # Ensure slug is unique by appending number if necessary
        original_slug = validated_data['slug']
        counter = 1
        while Module.objects.filter(slug=validated_data['slug']).exists():
            validated_data['slug'] = f"{original_slug}-{counter}"
            counter += 1
        
        return Module.objects.create(**validated_data)


class ModuleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating modules"""
    
    class Meta:
        model = Module
        fields = ['name', 'slug']
    
    def validate_name(self, value):
        """Validate name and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        
        value = value.strip()
        if self.instance and Module.objects.filter(name__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Module with this name already exists")
        
        return value
    
    def validate_slug(self, value):
        """Validate slug and check uniqueness"""
        if not value or not value.strip():
            raise serializers.ValidationError("Slug cannot be empty")
        
        value = value.strip()
        if self.instance and Module.objects.filter(slug__iexact=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("Module with this slug already exists")
        
        return value
    
    def update(self, instance, validated_data):
        """Update module"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ModuleListSerializer(serializers.ModelSerializer):
    """Serializer for module list (minimal data)"""
    
    class Meta:
        model = Module
        fields = ['id', 'name', 'slug', 'created_at']
        read_only_fields = ['id', 'created_at']

