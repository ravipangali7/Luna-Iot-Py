from rest_framework import serializers
from ..models.subscription_plan import SubscriptionPlan, SubscriptionPlanPermission
from django.contrib.auth.models import Permission


class SubscriptionPlanPermissionSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlanPermission model"""
    permission_name = serializers.CharField(source='permission.name', read_only=True)
    permission_codename = serializers.CharField(source='permission.codename', read_only=True)
    
    class Meta:
        model = SubscriptionPlanPermission
        fields = ['id', 'permission', 'permission_name', 'permission_codename', 'created_at']
        read_only_fields = ['id', 'created_at']


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """Serializer for SubscriptionPlan model"""
    permissions = SubscriptionPlanPermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        help_text="List of permission IDs to associate with this subscription plan"
    )
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'title', 'price', 'permissions', 'permission_ids', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        """Create subscription plan with permissions"""
        permission_ids = validated_data.pop('permission_ids', [])
        subscription_plan = SubscriptionPlan.objects.create(**validated_data)
        
        # Add permissions if provided
        if permission_ids:
            permissions = Permission.objects.filter(id__in=permission_ids)
            for permission in permissions:
                SubscriptionPlanPermission.objects.create(
                    subscription_plan=subscription_plan,
                    permission=permission
                )
        
        return subscription_plan
    
    def update(self, instance, validated_data):
        """Update subscription plan with permissions"""
        permission_ids = validated_data.pop('permission_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update permissions if provided
        if permission_ids is not None:
            # Clear existing permissions
            instance.permissions.all().delete()
            
            # Add new permissions
            if permission_ids:
                permissions = Permission.objects.filter(id__in=permission_ids)
                for permission in permissions:
                    SubscriptionPlanPermission.objects.create(
                        subscription_plan=instance,
                        permission=permission
                    )
        
        return instance


class SubscriptionPlanListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing subscription plans"""
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SubscriptionPlan
        fields = ['id', 'title', 'price', 'permissions_count', 'created_at', 'updated_at']
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()
