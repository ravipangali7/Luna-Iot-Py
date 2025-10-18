"""
Alert Switch Views
Handles alert switch management endpoints
"""
from rest_framework.decorators import api_view
from alert_system.models import AlertSwitch
from alert_system.serializers import (
    AlertSwitchSerializer,
    AlertSwitchCreateSerializer,
    AlertSwitchUpdateSerializer,
    AlertSwitchListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_switches(request):
    """Get all alert switches"""
    try:
        switches = AlertSwitch.objects.select_related('institute', 'device').all().order_by('-created_at')
        serializer = AlertSwitchListSerializer(switches, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert switches retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_switch_by_id(request, switch_id):
    """Get alert switch by ID"""
    try:
        try:
            switch = AlertSwitch.objects.select_related('institute', 'device').get(id=switch_id)
        except AlertSwitch.DoesNotExist:
            raise NotFoundError("Alert switch not found")
        
        serializer = AlertSwitchSerializer(switch)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert switch retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_switches_by_institute(request, institute_id):
    """Get alert switches by institute"""
    try:
        switches = AlertSwitch.objects.select_related('device').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertSwitchListSerializer(switches, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert switches retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_switch(request):
    """Create new alert switch"""
    try:
        serializer = AlertSwitchCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            switch = serializer.save()
            response_serializer = AlertSwitchSerializer(switch)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert switch created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_alert_switch(request, switch_id):
    """Update alert switch"""
    try:
        try:
            switch = AlertSwitch.objects.get(id=switch_id)
        except AlertSwitch.DoesNotExist:
            raise NotFoundError("Alert switch not found")
        
        serializer = AlertSwitchUpdateSerializer(switch, data=request.data)
        
        if serializer.is_valid():
            switch = serializer.save()
            response_serializer = AlertSwitchSerializer(switch)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert switch updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_alert_switch(request, switch_id):
    """Delete alert switch"""
    try:
        try:
            switch = AlertSwitch.objects.get(id=switch_id)
        except AlertSwitch.DoesNotExist:
            raise NotFoundError("Alert switch not found")
        
        switch_title = switch.title
        switch.delete()
        
        return success_response(
            data={'id': switch_id},
            message=f"Alert switch '{switch_title}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )
