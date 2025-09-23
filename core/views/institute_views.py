"""
Institute Views
Handles institute management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import Institute, InstituteService
from core.serializers import (
    InstituteSerializer, 
    InstituteCreateSerializer, 
    InstituteUpdateSerializer,
    InstituteListSerializer,
    InstituteLocationSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_institutes(request):
    """
    Get all institutes
    """
    try:
        institutes = Institute.objects.prefetch_related('institute_services').all().order_by('name')
        serializer = InstituteListSerializer(institutes, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institutes retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_institute_by_id(request, institute_id):
    """
    Get institute by ID
    """
    try:
        try:
            institute = Institute.objects.prefetch_related('institute_services').get(id=institute_id)
        except Institute.DoesNotExist:
            raise NotFoundError("Institute not found")
        
        serializer = InstituteSerializer(institute)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute retrieved successfully')
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
def create_institute(request):
    """
    Create new institute
    """
    try:
        serializer = InstituteCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            institute = serializer.save()
            response_serializer = InstituteSerializer(institute)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Institute created successfully'),
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
def update_institute(request, institute_id):
    """
    Update institute
    """
    try:
        try:
            institute = Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            raise NotFoundError("Institute not found")
        
        serializer = InstituteUpdateSerializer(institute, data=request.data)
        
        if serializer.is_valid():
            institute = serializer.save()
            response_serializer = InstituteSerializer(institute)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Institute updated successfully')
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
def delete_institute(request, institute_id):
    """
    Delete institute
    """
    try:
        try:
            institute = Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            raise NotFoundError("Institute not found")
        
        institute_name = institute.name
        institute.delete()
        
        return success_response(
            data={'id': institute_id},
            message=f"Institute '{institute_name}' deleted successfully"
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
def get_institute_locations(request):
    """
    Get all institute locations for mapping
    """
    try:
        institutes = Institute.objects.filter(
            latitude__isnull=False, 
            longitude__isnull=False
        ).exclude(latitude=0, longitude=0)
        
        serializer = InstituteLocationSerializer(institutes, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute locations retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )
