"""
Notification Serializers
Handles serialization for notification management endpoints
"""
from rest_framework import serializers
from shared.models import Notification, UserNotification
from core.models import User


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notification model"""
    sent_by_name = serializers.CharField(source='sentBy.name', read_only=True)
    sent_by_phone = serializers.CharField(source='sentBy.phone', read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'type', 'sentBy', 
            'sent_by_name', 'sent_by_phone', 'user_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_count(self, obj):
        """Get count of users this notification was sent to"""
        return obj.userNotifications.count()


class NotificationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating notifications"""
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of user IDs to send notification to"
    )
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'type', 'user_ids']
    
    def validate_title(self, value):
        """Validate notification title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Notification title cannot be empty")
        return value.strip()
    
    def validate_message(self, value):
        """Validate notification message"""
        if not value or not value.strip():
            raise serializers.ValidationError("Notification message cannot be empty")
        return value.strip()
    
    def validate_user_ids(self, value):
        """Validate user IDs exist"""
        if value:
            existing_users = User.objects.filter(id__in=value)
            if len(existing_users) != len(value):
                raise serializers.ValidationError("One or more user IDs are invalid")
        return value
    
    def create(self, validated_data):
        """Create notification and send to users"""
        user_ids = validated_data.pop('user_ids', [])
        sent_by = self.context['request'].user
        
        notification = Notification.objects.create(
            sentBy=sent_by,
            **validated_data
        )
        
        # Send to specified users
        if user_ids:
            users = User.objects.filter(id__in=user_ids)
            for user in users:
                UserNotification.objects.create(
                    user=user,
                    notification=notification
                )
        
        return notification


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating notifications"""
    
    class Meta:
        model = Notification
        fields = ['title', 'message', 'type']
    
    def validate_title(self, value):
        """Validate notification title"""
        if not value or not value.strip():
            raise serializers.ValidationError("Notification title cannot be empty")
        return value.strip()
    
    def validate_message(self, value):
        """Validate notification message"""
        if not value or not value.strip():
            raise serializers.ValidationError("Notification message cannot be empty")
        return value.strip()


class NotificationListSerializer(serializers.ModelSerializer):
    """Serializer for notification list (minimal data)"""
    sent_by_name = serializers.CharField(source='sentBy.name', read_only=True)
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'type', 'sent_by_name', 
            'user_count', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_count(self, obj):
        """Get count of users this notification was sent to"""
        return obj.userNotifications.count()


class UserNotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notification model"""
    notification_title = serializers.CharField(source='notification.title', read_only=True)
    notification_message = serializers.CharField(source='notification.message', read_only=True)
    notification_type = serializers.CharField(source='notification.type', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_phone = serializers.CharField(source='user.phone', read_only=True)
    
    class Meta:
        model = UserNotification
        fields = [
            'id', 'user', 'user_name', 'user_phone', 'notification', 
            'notification_title', 'notification_message', 'notification_type', 
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class UserNotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user notifications"""
    
    class Meta:
        model = UserNotification
        fields = ['is_read']


class NotificationFilterSerializer(serializers.Serializer):
    """Serializer for notification search filters"""
    title = serializers.CharField(
        required=False,
        help_text="Filter by notification title"
    )
    type = serializers.CharField(
        required=False,
        help_text="Filter by notification type"
    )
    sent_by_id = serializers.IntegerField(
        required=False,
        help_text="Filter by sender ID"
    )
    start_date = serializers.DateTimeField(
        required=False,
        help_text="Start date for filtering"
    )
    end_date = serializers.DateTimeField(
        required=False,
        help_text="End date for filtering"
    )
    
    def validate_sent_by_id(self, value):
        """Validate sender exists if provided"""
        if value:
            try:
                User.objects.get(id=value)
            except User.DoesNotExist:
                raise serializers.ValidationError("User with this ID does not exist")
        return value
    
    def validate(self, data):
        """Validate date range"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError("Start date must be before end date")
        
        return data


class NotificationStatsSerializer(serializers.Serializer):
    """Serializer for notification statistics"""
    total_notifications = serializers.IntegerField()
    notifications_by_type = serializers.DictField()
    total_users_notified = serializers.IntegerField()
    unread_notifications = serializers.IntegerField()
    recent_notifications = serializers.IntegerField()


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notifications as read"""
    notification_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="List of notification IDs to mark as read"
    )
    
    def validate_notification_ids(self, value):
        """Validate notification IDs exist and belong to user"""
        if not value:
            raise serializers.ValidationError("At least one notification ID is required")
        
        user = self.context['request'].user
        existing_notifications = UserNotification.objects.filter(
            user=user,
            notification_id__in=value
        )
        
        if len(existing_notifications) != len(value):
            raise serializers.ValidationError("One or more notification IDs are invalid")
        
        return value
