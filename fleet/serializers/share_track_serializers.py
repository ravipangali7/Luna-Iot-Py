from rest_framework import serializers
from fleet.models.share_track import ShareTrack


class ShareTrackSerializer(serializers.ModelSerializer):
    """
    Serializer for ShareTrack model
    """
    
    class Meta:
        model = ShareTrack
        fields = ['id', 'imei', 'token', 'created_at', 'scheduled_for']
        read_only_fields = ['id', 'token', 'created_at']
    
    def validate_imei(self, value):
        """
        Validate IMEI format (basic validation)
        """
        if not value or len(value) < 10:
            raise serializers.ValidationError("IMEI must be at least 10 characters long")
        return value
    
    def validate_scheduled_for(self, value):
        """
        Validate that scheduled_for is in the future
        """
        from django.utils import timezone
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled time must be in the future")
        return value


class ShareTrackCreateSerializer(serializers.Serializer):
    """
    Serializer for creating ShareTrack (only requires imei and duration_minutes)
    """
    imei = serializers.CharField(max_length=100, help_text="IMEI of the vehicle")
    duration_minutes = serializers.IntegerField(min_value=1, max_value=10080, help_text="Duration in minutes (max 1 week)")
    
    def validate_imei(self, value):
        """
        Validate IMEI format (basic validation)
        """
        if not value or len(value) < 10:
            raise serializers.ValidationError("IMEI must be at least 10 characters long")
        return value
    
    def validate_duration_minutes(self, value):
        """
        Validate duration is reasonable (max 1 week)
        """
        if value <= 0:
            raise serializers.ValidationError("Duration must be positive")
        if value > 10080:  # 1 week in minutes
            raise serializers.ValidationError("Duration cannot exceed 1 week (10080 minutes)")
        return value


class ShareTrackResponseSerializer(serializers.ModelSerializer):
    """
    Serializer for ShareTrack API responses
    """
    is_expired = serializers.SerializerMethodField()
    expires_in_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = ShareTrack
        fields = ['id', 'imei', 'token', 'created_at', 'scheduled_for', 'is_expired', 'expires_in_minutes']
    
    def get_is_expired(self, obj):
        """
        Check if the share track has expired
        """
        return obj.is_expired()
    
    def get_expires_in_minutes(self, obj):
        """
        Get remaining time in minutes
        """
        from django.utils import timezone
        now = timezone.now()
        if obj.scheduled_for > now:
            delta = obj.scheduled_for - now
            return int(delta.total_seconds() / 60)
        return 0
