"""
Community Siren History Serializers
Handles serialization for community siren history management endpoints
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers
from community_siren.models import CommunitySirenHistory
from core.models import Institute
from shared_utils.constants import AlertSource, AlertStatus


class CommunitySirenHistorySerializer(serializers.ModelSerializer):
    """Serializer for community siren history model"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True, allow_null=True)
    member_phone = serializers.CharField(source='member.phone', read_only=True, allow_null=True)
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'status_display',
            'institute', 'institute_name', 'member', 'member_name', 'member_phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CommunitySirenHistoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating community siren histories"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'institute', 'member'
        ]
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        valid_sources = ['app', 'switch']
        if value not in valid_sources:
            raise serializers.ValidationError(f"Source must be one of: {', '.join(valid_sources)}")
        return value
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if not value or not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip()
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if not value or not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip()
    
    def validate_institute(self, value):
        """Validate institute exists"""
        if not value:
            raise serializers.ValidationError("Institute is required")
        return value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range (optional)"""
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range (optional)"""
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value
    
    def validate(self, attrs):
        """
        Cross-field validation for rate limiting.
        For app source alerts, check if the same user (by phone) has sent
        an alert within the last 5 minutes.
        """
        source = attrs.get('source')
        primary_phone = attrs.get('primary_phone')
        
        # Only apply rate limiting for app source alerts
        if source == 'app' and primary_phone:
            five_mins_ago = timezone.now() - timedelta(minutes=5)
            
            # Check for recent alert from the same phone number
            recent_alert = CommunitySirenHistory.objects.filter(
                source='app',
                primary_phone=primary_phone,
                datetime__gte=five_mins_ago
            ).order_by('-datetime').first()
            
            if recent_alert:
                # Calculate remaining time
                time_since_alert = timezone.now() - recent_alert.datetime
                remaining_seconds = 300 - int(time_since_alert.total_seconds())  # 5 minutes = 300 seconds
                
                if remaining_seconds > 0:
                    remaining_minutes = remaining_seconds // 60
                    remaining_secs = remaining_seconds % 60
                    
                    if remaining_minutes > 0:
                        time_str = f"{remaining_minutes} minute{'s' if remaining_minutes > 1 else ''}"
                        if remaining_secs > 0:
                            time_str += f" {remaining_secs} second{'s' if remaining_secs > 1 else ''}"
                    else:
                        time_str = f"{remaining_secs} second{'s' if remaining_secs > 1 else ''}"
                    
                    raise serializers.ValidationError({
                        'rate_limit': f'Please wait {time_str} before sending another community siren alert.'
                    })
        
        return attrs


class CommunitySirenHistoryUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren histories"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'source', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status'
        ]
    
    def validate_source(self, value):
        """Validate source is valid choice"""
        if value:
            valid_sources = ['app', 'switch']
            if value not in valid_sources:
                raise serializers.ValidationError(f"Source must be one of: {', '.join(valid_sources)}")
        return value
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value and value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
    
    def validate_name(self, value):
        """Validate name"""
        if value and not value.strip():
            raise serializers.ValidationError("Name cannot be empty")
        return value.strip() if value else value
    
    def validate_primary_phone(self, value):
        """Validate primary phone"""
        if value and not value.strip():
            raise serializers.ValidationError("Primary phone cannot be empty")
        return value.strip() if value else value
    
    def validate_latitude(self, value):
        """Validate latitude is within valid range"""
        if value is not None and (value < -90 or value > 90):
            raise serializers.ValidationError("Latitude must be between -90 and 90")
        return value
    
    def validate_longitude(self, value):
        """Validate longitude is within valid range"""
        if value is not None and (value < -180 or value > 180):
            raise serializers.ValidationError("Longitude must be between -180 and 180")
        return value


class CommunitySirenHistoryListSerializer(serializers.ModelSerializer):
    """Serializer for listing community siren histories"""
    institute_name = serializers.CharField(source='institute.name', read_only=True)
    source_display = serializers.CharField(source='get_source_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    member_name = serializers.CharField(source='member.name', read_only=True, allow_null=True)
    member_phone = serializers.CharField(source='member.phone', read_only=True, allow_null=True)
    
    class Meta:
        model = CommunitySirenHistory
        fields = [
            'id', 'source', 'source_display', 'name', 'primary_phone', 'secondary_phone',
            'latitude', 'longitude', 'datetime', 'images', 'remarks', 'status', 'status_display',
            'institute', 'institute_name', 'member', 'member_name', 'member_phone',
            'created_at', 'updated_at'
        ]


class CommunitySirenHistoryStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating community siren history status only"""
    
    class Meta:
        model = CommunitySirenHistory
        fields = ['status']
    
    def validate_status(self, value):
        """Validate status is valid choice"""
        if value not in [choice[0] for choice in AlertStatus.choices]:
            raise serializers.ValidationError("Invalid status choice")
        return value
