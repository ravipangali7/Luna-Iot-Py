"""
Popup Serializers
Handles serialization for popup management endpoints
"""
from rest_framework import serializers
from shared.models import Popup


class PopupSerializer(serializers.ModelSerializer):
    """Serializer for popup model"""
    
    class Meta:
        model = Popup
        fields = [
            'id', 'title', 'message', 'image', 
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PopupCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating popups"""
    
    class Meta:
        model = Popup
        fields = ['title', 'message', 'image', 'is_active']
    
    def validate_title(self, value):
        """Validate popup title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Popup title cannot be empty")
        return value.strip()
    
    def validate_message(self, value):
        """Validate popup message"""
        if not value or not value.strip():
            raise serializers.ValidationError("Popup message cannot be empty")
        return value.strip()
    
    def validate_image(self, value):
        """Validate image URL"""
        if value and not value.strip():
            raise serializers.ValidationError("Image URL cannot be empty")
        return value.strip() if value else value


class PopupUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating popups"""
    
    class Meta:
        model = Popup
        fields = ['title', 'message', 'image', 'is_active']
    
    def validate_title(self, value):
        """Validate popup title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Popup title cannot be empty")
        return value.strip()
    
    def validate_message(self, value):
        """Validate popup message"""
        if not value or not value.strip():
            raise serializers.ValidationError("Popup message cannot be empty")
        return value.strip()
    
    def validate_image(self, value):
        """Validate image URL"""
        if value and not value.strip():
            raise serializers.ValidationError("Image URL cannot be empty")
        return value.strip() if value else value


class PopupListSerializer(serializers.ModelSerializer):
    """Serializer for popup list (minimal data)"""
    
    class Meta:
        model = Popup
        fields = [
            'id', 'title', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PopupFilterSerializer(serializers.Serializer):
    """Serializer for popup search filters"""
    title = serializers.CharField(
        required=False,
        help_text="Filter by popup title"
    )
    is_active = serializers.BooleanField(
        required=False,
        help_text="Filter by active status"
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


class ActivePopupSerializer(serializers.ModelSerializer):
    """Serializer for active popups"""
    
    class Meta:
        model = Popup
        fields = [
            'id', 'title', 'message', 'image', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class PopupStatsSerializer(serializers.Serializer):
    """Serializer for popup statistics"""
    total_popups = serializers.IntegerField()
    active_popups = serializers.IntegerField()
    inactive_popups = serializers.IntegerField()
    recent_popups = serializers.IntegerField()
    popups_with_images = serializers.IntegerField()
    popups_without_images = serializers.IntegerField()
