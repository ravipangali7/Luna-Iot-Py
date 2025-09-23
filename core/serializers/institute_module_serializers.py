"""
Institute Module Serializers
Handles serialization for institute module management endpoints
"""
from rest_framework import serializers
from core.models import InstituteModule, Institute, User
from django.contrib.auth.models import Group


class InstituteModuleSerializer(serializers.ModelSerializer):
    """Serializer for institute module model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    users = serializers.SerializerMethodField()
    user_count = serializers.ReadOnlyField()
    
    class Meta:
        model = InstituteModule
        fields = [
            'id', 'institute', 'institute_name', 'group', 'group_name',
            'users', 'user_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count']
    
    def get_users(self, obj):
        """Get users with basic info"""
        return [
            {
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'is_active': user.is_active
            }
            for user in obj.users.all()
        ]


class InstituteModuleCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating institute modules"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of User IDs"
    )
    
    class Meta:
        model = InstituteModule
        fields = ['institute', 'group', 'user_ids']
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_group(self, value):
        """Validate group exists"""
        if not value:
            raise serializers.ValidationError("Group is required")
        return value
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if value:
            existing_users = User.objects.filter(id__in=value)
            if len(existing_users) != len(value):
                raise serializers.ValidationError("One or more users do not exist")
        return value
    
    def validate(self, data):
        """Validate unique institute-group combination"""
        institute = data.get('institute')
        group = data.get('group')
        
        if institute and group:
            if InstituteModule.objects.filter(institute=institute, group=group).exists():
                raise serializers.ValidationError(
                    "A module for this institute and group combination already exists"
                )
        
        return data
    
    def create(self, validated_data):
        """Create institute module with users"""
        user_ids = validated_data.pop('user_ids', [])
        
        # Create module
        module = InstituteModule.objects.create(**validated_data)
        
        # Assign users
        if user_ids:
            module.users.set(user_ids)
        
        return module


class InstituteModuleUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating institute modules"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of User IDs"
    )
    
    class Meta:
        model = InstituteModule
        fields = ['institute', 'group', 'user_ids']
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_group(self, value):
        """Validate group exists"""
        if not value:
            raise serializers.ValidationError("Group is required")
        return value
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if value:
            existing_users = User.objects.filter(id__in=value)
            if len(existing_users) != len(value):
                raise serializers.ValidationError("One or more users do not exist")
        return value
    
    def validate(self, data):
        """Validate unique institute-group combination"""
        institute = data.get('institute')
        group = data.get('group')
        
        if institute and group and self.instance:
            if InstituteModule.objects.filter(
                institute=institute, 
                group=group
            ).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError(
                    "A module for this institute and group combination already exists"
                )
        
        return data
    
    def update(self, instance, validated_data):
        """Update institute module and users"""
        user_ids = validated_data.pop('user_ids', None)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        # Update users if provided
        if user_ids is not None:
            instance.users.set(user_ids)
        
        return instance


class InstituteModuleListSerializer(serializers.ModelSerializer):
    """Serializer for institute module list (minimal data)"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    user_count = serializers.ReadOnlyField()
    
    class Meta:
        model = InstituteModule
        fields = [
            'id', 'institute', 'institute_name', 'group', 'group_name',
            'user_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class InstituteModuleUserSerializer(serializers.ModelSerializer):
    """Serializer for managing users in institute modules"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of User IDs to assign to this module"
    )
    
    class Meta:
        model = InstituteModule
        fields = ['user_ids']
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if not value:
            raise serializers.ValidationError("At least one user ID is required")
        
        existing_users = User.objects.filter(id__in=value)
        if len(existing_users) != len(value):
            raise serializers.ValidationError("One or more users do not exist")
        
        return value
    
    def update(self, instance, validated_data):
        """Update users in the module"""
        user_ids = validated_data['user_ids']
        instance.users.set(user_ids)
        return instance
