"""
Institute Module Views
Handles institute module management endpoints
"""
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status

from core.models import InstituteModule, Institute, User, Module
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
        modules = InstituteModule.objects.select_related('institute', 'module').prefetch_related('users').all().order_by('institute__name', 'module__name')
        serializer = InstituteModuleListSerializer(modules, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Institute modules retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
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
        
        modules = InstituteModule.objects.select_related('institute', 'module').prefetch_related('users').filter(institute=institute).order_by('module__name')
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
            data=str(e)
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
            module = InstituteModule.objects.select_related('institute', 'module').prefetch_related('users').get(id=module_id)
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
            data=str(e)
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
def delete_institute_module(request, module_id):
    """
    Delete institute module
    """
    try:
        try:
            module = InstituteModule.objects.get(id=module_id)
        except InstituteModule.DoesNotExist:
            raise NotFoundError("Institute module not found")
        
        module_name = f"{module.institute.name} - {module.module.name}"
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
            data=str(e)
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


@api_view(['GET'])
@require_auth
@api_response
def get_alert_system_institutes(request):
    """
    Get institutes where the current user has access to the alert-system module
    For Super Admin: returns all institutes with alert-system module enabled
    For other users: returns only institutes where user has access
    """
    try:
        # Get the alert-system module
        try:
            alert_system_module = Module.objects.get(slug='alert-system')
        except Module.DoesNotExist:
            return success_response(
                data=[],
                message="Alert system module not found"
            )
        
        # Check if user is Super Admin
        user_groups = request.user.groups.all()
        is_admin = user_groups.filter(name='Super Admin').exists()
        
        if is_admin:
            # Super Admin: Get all institutes with alert-system module enabled
            all_institute_modules = InstituteModule.objects.filter(
                module=alert_system_module
            ).select_related('institute')
            
            institutes_data = []
            for institute_module in all_institute_modules:
                institutes_data.append({
                    'institute_id': institute_module.institute.id,
                    'institute_name': institute_module.institute.name,
                    'has_alert_system_access': True
                })
        else:
            # Regular users: Get only institutes where user has access to alert-system module
            user_institute_modules = InstituteModule.objects.filter(
                module=alert_system_module,
                users=request.user
            ).select_related('institute')
            
            institutes_data = []
            for institute_module in user_institute_modules:
                institutes_data.append({
                    'institute_id': institute_module.institute.id,
                    'institute_name': institute_module.institute.name,
                    'has_alert_system_access': True
                })
        
        return success_response(
            data=institutes_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Alert system institutes retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_institutes(request):
    """
    Get institutes where the current user has access to the school module
    For Super Admin: returns all institutes with school module enabled
    For other users: returns only institutes where user has access
    """
    try:
        # Get the school module
        try:
            school_module = Module.objects.get(slug='school')
        except Module.DoesNotExist:
            return success_response(
                data=[],
                message="School module not found"
            )
        
        # Check if user is Super Admin
        user_groups = request.user.groups.all()
        is_admin = user_groups.filter(name='Super Admin').exists()
        
        if is_admin:
            # Super Admin: Get all institutes with school module enabled
            all_institute_modules = InstituteModule.objects.filter(
                module=school_module
            ).select_related('institute')
            
            institutes_data = []
            for institute_module in all_institute_modules:
                institutes_data.append({
                    'institute_id': institute_module.institute.id,
                    'institute_name': institute_module.institute.name,
                    'has_school_access': True
                })
        else:
            # Regular users: Get only institutes where user has access to school module
            user_institute_modules = InstituteModule.objects.filter(
                module=school_module,
                users=request.user
            ).select_related('institute')
            
            institutes_data = []
            for institute_module in user_institute_modules:
                institutes_data.append({
                    'institute_id': institute_module.institute.id,
                    'institute_name': institute_module.institute.name,
                    'has_school_access': True
                })
        
        return success_response(
            data=institutes_data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School institutes retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )