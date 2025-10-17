"""
Module Views
Handles module management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import Module
from core.serializers import (
    ModuleSerializer, 
    ModuleCreateSerializer, 
    ModuleUpdateSerializer,
    ModuleListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from api_common.exceptions.api_exceptions import NotFoundError, ValidationError


@api_view(['GET'])
@require_auth
@api_response
def get_all_modules(request):
    """
    Get all modules
    """
    try:
        modules = Module.objects.all().order_by('name')
        serializer = ModuleListSerializer(modules, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Modules retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_module_by_id(request, module_id):
    """
    Get module by ID
    """
    try:
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            raise NotFoundError("Module not found")
        
        serializer = ModuleSerializer(module)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Module retrieved successfully')
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


@api_view(['POST'])
@require_super_admin
@api_response
def create_module(request):
    """
    Create new module
    """
    try:
        serializer = ModuleCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            module = serializer.save()
            response_serializer = ModuleSerializer(module)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Module created successfully'),
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
def update_module(request, module_id):
    """
    Update module
    """
    try:
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            raise NotFoundError("Module not found")
        
        serializer = ModuleUpdateSerializer(module, data=request.data)
        
        if serializer.is_valid():
            module = serializer.save()
            response_serializer = ModuleSerializer(module)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Module updated successfully')
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
def delete_module(request, module_id):
    """
    Delete module
    """
    try:
        try:
            module = Module.objects.get(id=module_id)
        except Module.DoesNotExist:
            raise NotFoundError("Module not found")
        
        module_name = module.name
        module.delete()
        
        return success_response(
            data={'id': module_id},
            message=f"Module '{module_name}' deleted successfully"
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