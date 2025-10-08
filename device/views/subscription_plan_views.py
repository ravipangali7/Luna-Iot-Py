"""
Subscription Plan Views
Handles subscription plan CRUD operations
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator

from ..models.subscription_plan import SubscriptionPlan, SubscriptionPlanPermission
from ..serializers.subscription_plan_serializers import (
    SubscriptionPlanSerializer, 
    SubscriptionPlanListSerializer,
    SubscriptionPlanPermissionSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


@api_view(['GET'])
@require_auth
@api_response
def list_subscription_plans(request):
    """
    List all subscription plans with pagination and search
    """
    try:
        # Get query parameters
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        search = request.GET.get('search', '')
        
        # Build queryset
        queryset = SubscriptionPlan.objects.all().order_by('-created_at')
        
        # Apply search filter
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(price__icontains=search)
            )
        
        # Pagination
        paginator = Paginator(queryset, limit)
        page_obj = paginator.get_page(page)
        
        # Serialize data
        serializer = SubscriptionPlanListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            data={
                'subscription_plans': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                }
            },
            message='Subscription plans retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving subscription plans: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_subscription_plan(request, plan_id):
    """
    Get a specific subscription plan by ID
    """
    try:
        subscription_plan = SubscriptionPlan.objects.get(id=plan_id)
        serializer = SubscriptionPlanSerializer(subscription_plan)
        
        return success_response(
            data=serializer.data,
            message='Subscription plan retrieved successfully'
        )
        
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            message='Subscription plan not found',
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f'Error retrieving subscription plan: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@require_auth
@api_response
def create_subscription_plan(request):
    """
    Create a new subscription plan
    """
    try:
        serializer = SubscriptionPlanSerializer(data=request.data)
        
        if serializer.is_valid():
            subscription_plan = serializer.save()
            response_serializer = SubscriptionPlanSerializer(subscription_plan)
            
            return success_response(
                data=response_serializer.data,
                message='Subscription plan created successfully',
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message='Validation error',
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except Exception as e:
        return error_response(
            message=f'Error creating subscription plan: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['PUT'])
@require_auth
@api_response
def update_subscription_plan(request, plan_id):
    """
    Update an existing subscription plan
    """
    try:
        subscription_plan = SubscriptionPlan.objects.get(id=plan_id)
        serializer = SubscriptionPlanSerializer(subscription_plan, data=request.data, partial=True)
        
        if serializer.is_valid():
            subscription_plan = serializer.save()
            response_serializer = SubscriptionPlanSerializer(subscription_plan)
            
            return success_response(
                data=response_serializer.data,
                message='Subscription plan updated successfully'
            )
        else:
            return error_response(
                message='Validation error',
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
            
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            message='Subscription plan not found',
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f'Error updating subscription plan: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_subscription_plan(request, plan_id):
    """
    Delete a subscription plan
    """
    try:
        subscription_plan = SubscriptionPlan.objects.get(id=plan_id)
        subscription_plan.delete()
        
        return success_response(
            message='Subscription plan deleted successfully'
        )
        
    except SubscriptionPlan.DoesNotExist:
        return error_response(
            message='Subscription plan not found',
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=f'Error deleting subscription plan: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_auth
@api_response
def get_available_permissions(request):
    """
    Get all available permissions for subscription plans
    """
    try:
        from django.contrib.auth.models import Permission
        permissions = Permission.objects.all().order_by('content_type__app_label', 'name')
        
        permission_data = []
        for permission in permissions:
            permission_data.append({
                'id': permission.id,
                'name': permission.name,
                'codename': permission.codename,
                'content_type': permission.content_type.app_label
            })
        
        return success_response(
            data=permission_data,
            message='Available permissions retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=f'Error retrieving permissions: {str(e)}',
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )
