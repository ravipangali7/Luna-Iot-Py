"""
Institute Service Views
Handles institute service management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import InstituteService
from core.serializers import (
    InstituteServiceSerializer, 
    InstituteServiceCreateSerializer, 
    InstituteServiceUpdateSerializer,
    InstituteServiceListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_institute_services(request):
    """
    Get all institute services
    """
    try:
        services = InstituteService.objects.all().order_by('name')
        serializer = InstituteServiceListSerializer(services, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute services retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_institute_service_by_id(request, service_id):
    """
    Get institute service by ID
    """
    try:
        try:
            service = InstituteService.objects.get(id=service_id)
        except InstituteService.DoesNotExist:
            raise NotFoundError("Institute service not found")
        
        serializer = InstituteServiceSerializer(service)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute service retrieved successfully')
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


@api_view(['POST'])
@require_super_admin
@api_response
def create_institute_service(request):
    """
    Create new institute service
    """
    try:
        serializer = InstituteServiceCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            service = serializer.save()
            response_serializer = InstituteServiceSerializer(service)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Institute service created successfully'),
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
def update_institute_service(request, service_id):
    """
    Update institute service
    """
    try:
        try:
            service = InstituteService.objects.get(id=service_id)
        except InstituteService.DoesNotExist:
            raise NotFoundError("Institute service not found")
        
        serializer = InstituteServiceUpdateSerializer(service, data=request.data)
        
        if serializer.is_valid():
            service = serializer.save()
            response_serializer = InstituteServiceSerializer(service)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Institute service updated successfully')
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
def delete_institute_service(request, service_id):
    """
    Delete institute service
    """
    try:
        try:
            service = InstituteService.objects.get(id=service_id)
        except InstituteService.DoesNotExist:
            raise NotFoundError("Institute service not found")
        
        service_name = service.name
        service.delete()
        
        return success_response(
            data={'id': service_id},
            message=f"Institute service '{service_name}' deleted successfully"
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
