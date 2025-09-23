"""
Institute Module Views
Handles institute module management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import InstituteModule, Institute, User
from django.contrib.auth.models import Group
from core.serializers import (
    InstituteModuleSerializer, 
    InstituteModuleCreateSerializer, 
    InstituteModuleUpdateSerializer,
    InstituteModuleListSerializer,
    InstituteModuleUserSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_institute_modules(request):
    """
    Get all institute modules
    """
    try:
        modules = InstituteModule.objects.select_related('institute', 'group').prefetch_related('users').all().order_by('institute__name', 'group__name')
        serializer = InstituteModuleListSerializer(modules, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute modules retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            details=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_institute_modules_by_institute(request, institute_id):
    """
    Get institute modules by institute ID
    """
    try:
        try:
            institute = Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            raise NotFoundError("Institute not found")
        
        modules = InstituteModule.objects.select_related('institute', 'group').prefetch_related('users').filter(institute=institute).order_by('group__name')
        serializer = InstituteModuleListSerializer(modules, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute modules retrieved successfully')
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
def get_institute_module_by_id(request, module_id):
    """
    Get institute module by ID
    """
    try:
        try:
            module = InstituteModule.objects.select_related('institute', 'group').prefetch_related('users').get(id=module_id)
        except InstituteModule.DoesNotExist:
            raise NotFoundError("Institute module not found")
        
        serializer = InstituteModuleSerializer(module)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute module retrieved successfully')
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
def create_institute_module(request):
    """
    Create new institute module
    """
    try:
        serializer = InstituteModuleCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            module = serializer.save()
            response_serializer = InstituteModuleSerializer(module)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Institute module created successfully'),
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
def update_institute_module(request, module_id):
    """
    Update institute module
    """
    try:
        try:
            module = InstituteModule.objects.get(id=module_id)
        except InstituteModule.DoesNotExist:
            raise NotFoundError("Institute module not found")
        
        serializer = InstituteModuleUpdateSerializer(module, data=request.data)
        
        if serializer.is_valid():
            module = serializer.save()
            response_serializer = InstituteModuleSerializer(module)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Institute module updated successfully')
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
def delete_institute_module(request, module_id):
    """
    Delete institute module
    """
    try:
        try:
            module = InstituteModule.objects.get(id=module_id)
        except InstituteModule.DoesNotExist:
            raise NotFoundError("Institute module not found")
        
        module_name = f"{module.institute.name} - {module.group.name}"
        module.delete()
        
        return success_response(
            data={'id': module_id},
            message=f"Institute module '{module_name}' deleted successfully"
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


@api_view(['PUT'])
@require_super_admin
@api_response
def update_institute_module_users(request, module_id):
    """
    Update users in institute module
    """
    try:
        try:
            module = InstituteModule.objects.get(id=module_id)
        except InstituteModule.DoesNotExist:
            raise NotFoundError("Institute module not found")
        
        serializer = InstituteModuleUserSerializer(module, data=request.data)
        
        if serializer.is_valid():
            module = serializer.save()
            response_serializer = InstituteModuleSerializer(module)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Institute module users updated successfully')
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
