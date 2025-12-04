"""
Vehicle Tag Serializers
Handles serialization for vehicle tag management endpoints
"""
from rest_framework import serializers
from vehicle_tag.models import VehicleTag
from core.serializers import UserSerializer


class VehicleTagSerializer(serializers.ModelSerializer):
    """Serializer for vehicle tag model"""
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleTag
        fields = [
            'id', 'user', 'user_id', 'user_info', 'vtid', 'vehicle_model',
            'registration_no', 'register_type', 'vehicle_category', 'sos_number',
            'sms_number', 'is_active', 'is_downloaded', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vtid', 'created_at', 'updated_at']
    
    def get_user_info(self, obj):
        """Get user info or 'unassigned'"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.name,
                'phone': obj.user.phone
            }
        return None


class VehicleTagCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating vehicle tags"""
    user_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = VehicleTag
        fields = [
            'user', 'user_id', 'vehicle_model', 'registration_no', 'register_type',
            'vehicle_category', 'sos_number', 'sms_number', 'is_active', 'is_downloaded'
        ]
    
    def validate_user_id(self, value):
        """Validate user_id if provided"""
        if value is not None:
            from core.models import User
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError(f"User with ID {value} does not exist")
        return value
    
    def create(self, validated_data):
        """Handle user assignment via user_id"""
        user_id = validated_data.pop('user_id', None)
        if user_id is not None:
            from core.models import User
            validated_data['user'] = User.objects.get(id=user_id) if user_id else None
        elif 'user' not in validated_data:
            validated_data['user'] = None
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        """Handle user assignment via user_id"""
        user_id = validated_data.pop('user_id', None)
        if user_id is not None:
            from core.models import User
            instance.user = User.objects.get(id=user_id) if user_id else None
        return super().update(instance, validated_data)


class VehicleTagListSerializer(serializers.ModelSerializer):
    """Serializer for vehicle tag list (with user info)"""
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = VehicleTag
        fields = [
            'id', 'vtid', 'user_info', 'vehicle_model', 'registration_no',
            'register_type', 'vehicle_category', 'sos_number', 'sms_number',
            'is_active', 'is_downloaded', 'created_at'
        ]
        read_only_fields = ['id', 'vtid', 'created_at']
    
    def get_user_info(self, obj):
        """Get user info or 'unassigned'"""
        if obj.user:
            return {
                'id': obj.user.id,
                'name': obj.user.name,
                'phone': obj.user.phone
            }
        return 'unassigned'

