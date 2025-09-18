"""
User Serializers
Handles serialization for user management endpoints
"""
from rest_framework import serializers
from core.models import User
from api_common.utils.validation_utils import validate_phone_number


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user model"""
    roles = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'phone', 'is_active', 'roles', 
            'permissions', 'fcm_token', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_roles(self, obj):
        """Get user's groups (roles) with their permissions"""
        groups_data = []
        for group in obj.groups.all():
            group_data = {
                'id': group.id,
                'name': group.name,
                'permissions': list(group.permissions.values_list('name', flat=True))
            }
            groups_data.append(group_data)
        return groups_data
    
    def get_permissions(self, obj):
        """Get user's combined permissions (group + direct)"""
        # Get group permissions
        group_permissions = []
        for group in obj.groups.all():
            group_permissions.extend(group.permissions.values_list('name', flat=True))
        
        # Get direct permissions
        direct_permissions = list(obj.user_permissions.values_list('name', flat=True))
        
        # Combine and deduplicate
        return list(set(group_permissions + direct_permissions))


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating users"""
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        help_text="User's password (minimum 6 characters)"
    )
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of Role IDs for the user"
    )
    
    class Meta:
        model = User
        fields = [
            'name', 'phone', 'password', 'role_ids', 
            'is_active', 'fcm_token'
        ]
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        
        # Check if phone already exists
        if User.objects.filter(phone=value.strip()).exists():
            raise serializers.ValidationError("User with this phone number already exists")
        
        return value.strip()
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_password(self, value):
        """Validate password strength"""
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
    
    def validate_role_ids(self, value):
        """Validate roles exist"""
        if value:
            from django.contrib.auth.models import Group
            existing_groups = Group.objects.filter(id__in=value)
            if len(existing_groups) != len(value):
                raise serializers.ValidationError("One or more roles do not exist")
        return value
    
    def create(self, validated_data):
        """Create user with hashed password and roles"""
        from django.contrib.auth.hashers import make_password
        from api_common.utils.auth_utils import generate_token
        from django.contrib.auth.models import Group
        
        # Extract role_ids and remove from validated_data
        role_ids = validated_data.pop('role_ids', [])
        
        # Hash password and generate token
        validated_data['password'] = make_password(validated_data['password'])
        validated_data['token'] = generate_token()
        
        # Create user
        user = User.objects.create(**validated_data)
        
        # Assign roles
        if role_ids:
            for role_id in role_ids:
                group = Group.objects.get(id=role_id)
                user.groups.add(group)
        
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating users"""
    role_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of Role IDs for the user"
    )
    
    class Meta:
        model = User
        fields = [
            'name', 'phone', 'is_active', 'role_ids', 'fcm_token'
        ]
    
    def validate_phone(self, value):
        """Validate phone number format"""
        if not validate_phone_number(value):
            raise serializers.ValidationError("Invalid phone number format")
        
        # Check if phone already exists (excluding current user)
        if self.instance and User.objects.filter(phone=value.strip()).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("User with this phone number already exists")
        
        return value.strip()
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_role_ids(self, value):
        """Validate roles exist"""
        if value:
            from django.contrib.auth.models import Group
            existing_groups = Group.objects.filter(id__in=value)
            if len(existing_groups) != len(value):
                raise serializers.ValidationError("One or more roles do not exist")
        return value
    
    def update(self, instance, validated_data):
        """Update user and roles"""
        from django.contrib.auth.models import Group
        
        # Handle role updates
        if 'role_ids' in validated_data:
            role_ids = validated_data.pop('role_ids')
            
            # Clear existing roles
            instance.userrole_set.all().delete()
            
            # Assign new roles
            if role_ids:
                for role_id in role_ids:
                    group = Group.objects.get(id=role_id)
                    instance.groups.add(group)
        
        # Update fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class UserListSerializer(serializers.ModelSerializer):
    """Serializer for user list (minimal data)"""
    roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'name', 'phone', 'is_active', 'roles', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_roles(self, obj):
        """Get user's groups (roles) with basic info"""
        return [{'id': group.id, 'name': group.name} for group in obj.groups.all()]


class UserFCMTokenSerializer(serializers.Serializer):
    """Serializer for updating FCM token"""
    fcm_token = serializers.CharField(
        max_length=500,
        help_text="Firebase Cloud Messaging token"
    )


class UserPasswordSerializer(serializers.Serializer):
    """Serializer for updating user password"""
    current_password = serializers.CharField(
        help_text="Current password"
    )
    new_password = serializers.CharField(
        min_length=6,
        help_text="New password (minimum 6 characters)"
    )
    
    def validate_new_password(self, value):
        """Validate new password strength"""
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long")
        return value
