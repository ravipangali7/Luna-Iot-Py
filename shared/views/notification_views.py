from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
import json

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_api_exception

from shared.models import Notification, UserNotification
from core.models import User


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
            notifications = Notification.objects.prefetch_related('userNotifications__user').all().order_by('-createdAt')
        else:
            # Get notifications assigned to this user
            notifications = Notification.objects.filter(
                userNotifications__user=user
            ).prefetch_related('userNotifications__user').distinct().order_by('-createdAt')
        
        notifications_data = []
        for notification in notifications:
            # Check if this user has read this notification
            is_read = False
            if hasattr(notification, 'userNotifications'):
                user_notification = notification.userNotifications.filter(user=user).first()
                if user_notification:
                    is_read = user_notification.isRead
            
            notification_data = {
                'id': notification.id,
                'title': notification.title,
                'message': notification.message,
                'type': notification.type,
                'sentBy': {
                    'id': notification.sentBy.id,
                    'name': notification.sentBy.name,
                    'phone': notification.sentBy.phone
                } if notification.sentBy else None,
                'isRead': is_read,
                'createdAt': notification.createdAt.isoformat() if notification.createdAt else None,
                'updatedAt': notification.updatedAt.isoformat() if notification.updatedAt else None
            }
            notifications_data.append(notification_data)
        
        return success_response(notifications_data, 'Notifications retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


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
        
        # Remove any id field from data to prevent AutoField errors
        if 'id' in data:
            del data['id']
        
        # Validate required fields
        required_fields = ['title', 'message', 'type']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
        title = data['title']
        message = data['message']
        notification_type = data['type']
        target_user_ids = data.get('targetUserIds', [])
        target_role_ids = data.get('targetRoleIds', [])
        
        # Validate type
        if notification_type not in ['all', 'specific', 'role']:
            return error_response('Type must be all, specific, or role', HTTP_STATUS['BAD_REQUEST'])
        
        # Filter out invalid IDs (0, negative, or non-integer values)
        if target_user_ids and isinstance(target_user_ids, list):
            target_user_ids = [uid for uid in target_user_ids if isinstance(uid, int) and uid > 0]
        
        if target_role_ids and isinstance(target_role_ids, list):
            target_role_ids = [rid for rid in target_role_ids if isinstance(rid, int) and rid > 0]
        
        # Validate targetUserIds for specific type
        if notification_type == 'specific' and (not target_user_ids or not isinstance(target_user_ids, list) or len(target_user_ids) == 0):
            return error_response('targetUserIds array with valid user IDs is required for specific type', HTTP_STATUS['BAD_REQUEST'])
        
        # Validate targetRoleIds for role type
        if notification_type == 'role' and (not target_role_ids or not isinstance(target_role_ids, list) or len(target_role_ids) == 0):
            return error_response('targetRoleIds array with valid role IDs is required for role type', HTTP_STATUS['BAD_REQUEST'])
        
        # Create notification
        with transaction.atomic():
            # Explicitly exclude id and other AutoField fields to prevent setting them to 0
            notification = Notification.objects.create(
                title=title,
                message=message,
                type=notification_type,
                sentBy=user
            )
            
            # Determine target users based on type
            target_users = []
            
            if notification_type == 'all':
                # Get all active users (exclude id=0 to be safe)
                target_users = User.objects.filter(is_active=True).exclude(id=0)
            elif notification_type == 'specific' and target_user_ids:
                # Get specific users (exclude id=0 to be safe)
                target_users = User.objects.filter(id__in=target_user_ids, is_active=True).exclude(id=0)
            elif notification_type == 'role' and target_role_ids:
                # Get users with specific roles (exclude id=0 to be safe)
                target_users = User.objects.filter(groups__id__in=target_role_ids, is_active=True).exclude(id=0)
            
            # Create notification-user relationships
            for target_user in target_users:
                # Double-check user id is valid before creating
                if target_user and target_user.id and target_user.id > 0:
                    UserNotification.objects.create(
                        notification=notification,
                        user=target_user,
                        isRead=False
                    )
        
        # Send push notifications using Firebase service
        try:
            from api_common.services.firebase_service import send_push_notification
            
            # Send push notification based on type
            # Only pass target_user_ids/target_role_ids if they are valid and match the notification type
            firebase_target_user_ids = None
            firebase_target_role_ids = None
            
            if notification_type == 'specific' and target_user_ids and len(target_user_ids) > 0:
                firebase_target_user_ids = target_user_ids
            elif notification_type == 'role' and target_role_ids and len(target_role_ids) > 0:
                firebase_target_role_ids = target_role_ids
            
            send_push_notification(
                notification_id=notification.id,
                title=title,
                body=message,  # Fixed: changed 'message' to 'body'
                notification_type=notification_type,
                target_user_ids=firebase_target_user_ids,
                target_role_ids=firebase_target_role_ids
            )
        except Exception as firebase_error:
            print(f'Firebase notification error: {firebase_error}')
            # Don't fail the request if Firebase fails
        
        notification_data = {
            'id': notification.id,
            'title': notification.title,
            'message': notification.message,
            'type': notification.type,
            'sentBy': {
                'id': notification.sentBy.id,
                'name': notification.sentBy.name,
                'phone': notification.sentBy.phone
            } if notification.sentBy else None,
            'createdAt': notification.createdAt.isoformat() if notification.createdAt else None,
            'updatedAt': notification.updatedAt.isoformat() if notification.updatedAt else None
        }
        
        return success_response(notification_data, 'Notification created successfully', HTTP_STATUS['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except ValueError as ve:
        # Catch AutoField errors specifically
        error_msg = str(ve)
        if 'AutoField' in error_msg or '0 as a value' in error_msg:
            return error_response('Invalid ID value in request. Please ensure all ID fields are valid positive integers.', HTTP_STATUS['BAD_REQUEST'])
        return error_response(f'Validation error: {error_msg}', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        # Log the full error for debugging
        import traceback
        print(f'Notification creation error: {str(e)}')
        print(traceback.format_exc())
        return handle_api_exception(e)


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
            return error_response('Notification not found', HTTP_STATUS['NOT_FOUND'])
        
        # Delete notification
        notification.delete()
        
        return success_response(None, 'Notification deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


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
            notification_user = UserNotification.objects.get(
                notification_id=notification_id,
                user=user
            )
        except UserNotification.DoesNotExist:
            return error_response('Notification not found or access denied', HTTP_STATUS['NOT_FOUND'])
        
        # Mark as read
        notification_user.isRead = True
        notification_user.save()
        
        return success_response(None, 'Notification marked as read')
    
    except Exception as e:
        return handle_api_exception(e)


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
        count = UserNotification.objects.filter(
            user=user,
            isRead=False
        ).count()
        
        return success_response({'count': count}, 'Unread count retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)
