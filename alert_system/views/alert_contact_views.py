"""
Alert Contact Views
Handles alert contact management endpoints
"""
from rest_framework.decorators import api_view
from alert_system.models import AlertContact
from alert_system.serializers import (
    AlertContactSerializer,
    AlertContactCreateSerializer,
    AlertContactUpdateSerializer,
    AlertContactListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError


@api_view(['GET'])
@require_auth
@api_response
def get_all_alert_contacts(request):
    """Get all alert contacts"""
    try:
        contacts = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').select_related('institute').all().order_by('-created_at')
        serializer = AlertContactListSerializer(contacts, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_contact_by_id(request, contact_id):
    """Get alert contact by ID"""
    try:
        try:
            contact = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').select_related('institute').get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        serializer = AlertContactSerializer(contact)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contact retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_alert_contacts_by_institute(request, institute_id):
    """Get alert contacts by institute"""
    try:
        contacts = AlertContact.objects.prefetch_related('alert_geofences', 'alert_types').filter(institute_id=institute_id).order_by('-created_at')
        serializer = AlertContactListSerializer(contacts, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert contacts retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['POST'])
@require_super_admin
@api_response
def create_alert_contact(request):
    """Create new alert contact"""
    try:
        serializer = AlertContactCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = AlertContactSerializer(contact)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Alert contact created successfully'),
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                details=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['PUT'])
@require_super_admin
@api_response
def update_alert_contact(request, contact_id):
    """Update alert contact"""
    try:
        try:
            contact = AlertContact.objects.get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        serializer = AlertContactUpdateSerializer(contact, data=request.data)
        
        if serializer.is_valid():
            contact = serializer.save()
            response_serializer = AlertContactSerializer(contact)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Alert contact updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                details=serializer.errors,
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
            details=str(e)
        )


@api_view(['DELETE'])
@require_super_admin
@api_response
def delete_alert_contact(request, contact_id):
    """Delete alert contact"""
    try:
        try:
            contact = AlertContact.objects.get(id=contact_id)
        except AlertContact.DoesNotExist:
            raise NotFoundError("Alert contact not found")
        
        contact_name = contact.name
        contact.delete()
        
        return success_response(
            data={'id': contact_id},
            message=f"Alert contact '{contact_name}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )
