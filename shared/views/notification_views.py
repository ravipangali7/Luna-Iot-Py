from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
import json

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS_CODES
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_exception

from shared.models import Notification, NotificationUser
from core.models import User, Role


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_notifications(request):
    """
    Get notifications based on user role
    """
    try:
        user = request.user
        
        # Get notifications based on user role
        if user.role.name == 'Super Admin':
            notifications = Notification.objects.prefetch_related('notificationuser_set__user').all().order_by('-created_at')
        else:
            # Get notifications assigned to this user
            notifications = Notification.objects.filter(
                notificationuser__user=user
            ).prefetch_related('notificationuser_set__user').distinct().order_by('-created_at')
        
        notifications_data = []
        for notification in notifications:
            # Check if this user has read this notification
            is_read = False
            if hasattr(notification, 'notificationuser_set'):
                user_notification = notification.notificationuser_set.filter(user=user).first()
                if user_notification:
                    is_read = user_notification.is_read
            
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'sentBy': {
                    'id': notification.sent_by.id,
                    'name': notification.sent_by.name,
                    'phone': notification.sent_by.phone
                } if notification.sent_by else None,
                'isRead': is_read,
                'createdAt': notification.created_at.isoformat() if notification.created_at else None,
                'updatedAt': notification.updated_at.isoformat() if notification.updated_at else None
            }
            notifications_data.append(notification_data)
        
        return success_response(notifications_data, 'Notifications retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to fetch notifications')


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
@require_role(['Super Admin'])
def create_notification(request):
    """
    Create notification (Super Admin only)
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'message', 'type']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        title = data['title']
        message = data['message']
        notification_type = data['type']
        target_user_ids = data.get('targetUserIds', [])
        target_role_ids = data.get('targetRoleIds', [])
        
        # Validate type
        if notification_type not in ['all', 'specific', 'role']:
            return error_response('Type must be all, specific, or role', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Validate targetUserIds for specific type
        if notification_type == 'specific' and (not target_user_ids or not isinstance(target_user_ids, list)):
            return error_response('targetUserIds array is required for specific type', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Validate targetRoleIds for role type
        if notification_type == 'role' and (not target_role_ids or not isinstance(target_role_ids, list)):
            return error_response('targetRoleIds array is required for role type', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Create notification
        with transaction.atomic():
            notification = Notification.objects.create(
                title=title,
                message=message,
                type=notification_type,
                sent_by=user
            )
            
            # Determine target users based on type
            target_users = []
            
            if notification_type == 'all':
                # Get all active users
                target_users = User.objects.filter(status='ACTIVE')
            elif notification_type == 'specific' and target_user_ids:
                # Get specific users
                target_users = User.objects.filter(id__in=target_user_ids, status='ACTIVE')
            elif notification_type == 'role' and target_role_ids:
                # Get users with specific roles
                target_users = User.objects.filter(role_id__in=target_role_ids, status='ACTIVE')
            
            # Create notification-user relationships
            for target_user in target_users:
                NotificationUser.objects.create(
                    notification=notification,
                    user=target_user,
                    is_read=False
                )
        
        # Send push notifications (you'll need to implement Firebase service)
        try:
            fcm_tokens = []
            for target_user in target_users:
                if target_user.fcm_token:
                    fcm_tokens.append(target_user.fcm_token)
            
            if fcm_tokens:
                # TODO: Implement Firebase notification sending
                # await FirebaseService.sendNotificationToMultipleUsers(
                #     fcm_tokens,
                #     title,
                #     message,
                #     {'notificationId': str(notification.id)}
                # )
                pass
        except Exception as firebase_error:
            print(f'Firebase notification error: {firebase_error}')
            # Don't fail the request if Firebase fails
        
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'sentBy': {
                'id': notification.sent_by.id,
                'name': notification.sent_by.name,
                'phone': notification.sent_by.phone
            } if notification.sent_by else None,
            'createdAt': notification.created_at.isoformat() if notification.created_at else None,
            'updatedAt': notification.updated_at.isoformat() if notification.updated_at else None
        }
        
        return success_response(notification_data, 'Notification created successfully', HTTP_STATUS_CODES['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to create notification')


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_notification(request, id):
    """
    Delete notification (Super Admin only)
    """
    try:
        # Get notification
        try:
            notification = Notification.objects.get(id=id)
        except Notification.DoesNotExist:
            return error_response('Notification not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Delete notification
        notification.delete()
        
        return success_response(None, 'Notification deleted successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to delete notification')


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def mark_notification_as_read(request, notification_id):
    """
    Mark notification as read
    """
    try:
        user = request.user
        
        # Get notification-user relationship
        try:
            notification_user = NotificationUser.objects.get(
                notification_id=notification_id,
                user=user
            )
        except NotificationUser.DoesNotExist:
            return error_response('Notification not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Mark as read
        notification_user.is_read = True
        notification_user.save()
        
        return success_response(None, 'Notification marked as read')
    
    except Exception as e:
        return handle_exception(e, 'Failed to mark notification as read')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_unread_notification_count(request):
    """
    Get unread notification count
    """
    try:
        user = request.user
        
        # Count unread notifications for this user
        count = NotificationUser.objects.filter(
            user=user,
            is_read=False
        ).count()
        
        return success_response({'count': count}, 'Unread count retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to get unread count')
