"""
Phone Book Views
Handles phone book management endpoints
"""
from rest_framework.decorators import api_view
from phone_call.models import PhoneBook
from phone_call.serializers import (
    PhoneBookSerializer,
    PhoneBookCreateSerializer,
    PhoneBookUpdateSerializer,
    PhoneBookListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.exceptions.api_exceptions import NotFoundError
from core.models import Module, InstituteModule
from django.db.models import Q


def require_phone_book_access(model_class=None, id_param_name='id'):
    """
    Decorator to require Super Admin role OR ownership access for phone book operations
    
    Args:
        model_class: Optional model class to fetch record for PUT/DELETE operations
        id_param_name: Name of the URL parameter containing the record ID (default: 'id')
    
    For create operations (POST): validates user/institute ownership
    For update/delete operations (PUT/DELETE): fetches record and validates ownership
    """
    def decorator(view_func):
        from functools import wraps
        from api_common.utils.response_utils import error_response
        
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return error_response(
                    message='Authentication required',
                    status_code=401
                )
            
            # Check if user is Super Admin - always allow
            user_groups = request.user.groups.all()
            user_role_names = [group.name for group in user_groups]
            is_super_admin = 'Super Admin' in user_role_names
            
            if is_super_admin:
                return view_func(request, *args, **kwargs)
            
            # For non-Super Admin users, check ownership
            if request.method == 'POST':
                # For create operations, validate ownership
                user_id = request.data.get('user')
                institute_id = request.data.get('institute')
                
                # User can only create phone books for themselves
                if user_id:
                    # Handle different formats
                    if isinstance(user_id, (int, float)):
                        user_id = int(user_id)
                    elif isinstance(user_id, dict):
                        user_id = user_id.get('id') or user_id.get('pk')
                    elif hasattr(user_id, 'id'):
                        user_id = user_id.id
                    elif isinstance(user_id, str) and user_id.isdigit():
                        user_id = int(user_id)
                    
                    if user_id != request.user.id:
                        return error_response(
                            message='You can only create phone books for yourself',
                            status_code=403
                        )
                
                # User can create phone books for institutes they belong to
                if institute_id:
                    # Handle different formats
                    if isinstance(institute_id, (int, float)):
                        institute_id = int(institute_id)
                    elif isinstance(institute_id, dict):
                        institute_id = institute_id.get('id') or institute_id.get('pk')
                    elif hasattr(institute_id, 'id'):
                        institute_id = institute_id.id
                    elif isinstance(institute_id, str) and institute_id.isdigit():
                        institute_id = int(institute_id)
                    
                    # Check if user belongs to this institute
                    has_access = InstituteModule.objects.filter(
                        institute_id=institute_id,
                        users=request.user
                    ).exists()
                    
                    if not has_access:
                        return error_response(
                            message='You do not have access to create phone books for this institute',
                            status_code=403
                        )
            
            elif request.method in ['PUT', 'DELETE'] and model_class:
                # For update/delete operations, get record and validate ownership
                record_id = kwargs.get(id_param_name) or kwargs.get('phone_book_id')
                if record_id:
                    try:
                        record = model_class.objects.get(id=record_id)
                        
                        # Check ownership
                        is_owner = False
                        if record.user and record.user.id == request.user.id:
                            is_owner = True
                        elif record.institute:
                            # Check if user belongs to this institute
                            has_access = InstituteModule.objects.filter(
                                institute=record.institute,
                                users=request.user
                            ).exists()
                            if has_access:
                                is_owner = True
                        
                        if not is_owner:
                            return error_response(
                                message='Access denied. You do not own this phone book',
                                status_code=403
                            )
                    except model_class.DoesNotExist:
                        # Record doesn't exist - let the view handle the 404
                        pass
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@api_view(['GET'])
@require_auth
@api_response
def get_all_phone_books(request):
    """Get all phone books (filtered by access)"""
    try:
        user_groups = request.user.groups.all()
        user_role_names = [group.name for group in user_groups]
        is_super_admin = 'Super Admin' in user_role_names
        
        if is_super_admin:
            # Super Admin sees all
            phone_books = PhoneBook.objects.select_related('user', 'institute').prefetch_related('numbers').all().order_by('-created_at')
        else:
            # Regular users see their own + institute phone books
            # Get institutes user belongs to
            user_institutes = InstituteModule.objects.filter(
                users=request.user
            ).values_list('institute_id', flat=True)
            
            phone_books = PhoneBook.objects.select_related('user', 'institute').prefetch_related('numbers').filter(
                Q(user=request.user) | Q(institute_id__in=user_institutes)
            ).order_by('-created_at')
        
        serializer = PhoneBookListSerializer(phone_books, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Phone books retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_phone_book_by_id(request, phone_book_id):
    """Get phone book by ID"""
    try:
        try:
            phone_book = PhoneBook.objects.select_related('user', 'institute').prefetch_related('numbers').get(id=phone_book_id)
        except PhoneBook.DoesNotExist:
            raise NotFoundError("Phone book not found")
        
        # Check access
        user_groups = request.user.groups.all()
        user_role_names = [group.name for group in user_groups]
        is_super_admin = 'Super Admin' in user_role_names
        
        if not is_super_admin:
            # Check ownership
            is_owner = False
            if phone_book.user and phone_book.user.id == request.user.id:
                is_owner = True
            elif phone_book.institute:
                has_access = InstituteModule.objects.filter(
                    institute=phone_book.institute,
                    users=request.user
                ).exists()
                if has_access:
                    is_owner = True
            
            if not is_owner:
                return error_response(
                    message='Access denied. You do not have permission to view this phone book',
                    status_code=403
                )
        
        serializer = PhoneBookSerializer(phone_book)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Phone book retrieved successfully')
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
def get_phone_books_by_user(request, user_id):
    """Get phone books by user"""
    try:
        user_groups = request.user.groups.all()
        user_role_names = [group.name for group in user_groups]
        is_super_admin = 'Super Admin' in user_role_names
        
        # Non-super admins can only see their own phone books
        if not is_super_admin and int(user_id) != request.user.id:
            return error_response(
                message='Access denied. You can only view your own phone books',
                status_code=403
            )
        
        phone_books = PhoneBook.objects.select_related('user', 'institute').prefetch_related('numbers').filter(user_id=user_id).order_by('-created_at')
        serializer = PhoneBookListSerializer(phone_books, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Phone books retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_phone_books_by_institute(request, institute_id):
    """Get phone books by institute"""
    try:
        user_groups = request.user.groups.all()
        user_role_names = [group.name for group in user_groups]
        is_super_admin = 'Super Admin' in user_role_names
        
        # Non-super admins can only see institute phone books they belong to
        if not is_super_admin:
            has_access = InstituteModule.objects.filter(
                institute_id=institute_id,
                users=request.user
            ).exists()
            
            if not has_access:
                return error_response(
                    message='Access denied. You do not have access to this institute',
                    status_code=403
                )
        
        phone_books = PhoneBook.objects.select_related('user', 'institute').prefetch_related('numbers').filter(institute_id=institute_id).order_by('-created_at')
        serializer = PhoneBookListSerializer(phone_books, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Phone books retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_phone_book_access(PhoneBook, 'phone_book_id')
@api_response
def create_phone_book(request):
    """Create new phone book"""
    try:
        serializer = PhoneBookCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            phone_book = serializer.save()
            response_serializer = PhoneBookSerializer(phone_book)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_CREATED', 'Phone book created successfully'),
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
@require_phone_book_access(PhoneBook, 'phone_book_id')
@api_response
def update_phone_book(request, phone_book_id):
    """Update phone book"""
    try:
        try:
            phone_book = PhoneBook.objects.get(id=phone_book_id)
        except PhoneBook.DoesNotExist:
            raise NotFoundError("Phone book not found")
        
        serializer = PhoneBookUpdateSerializer(phone_book, data=request.data)
        
        if serializer.is_valid():
            phone_book = serializer.save()
            response_serializer = PhoneBookSerializer(phone_book)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'Phone book updated successfully')
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
@require_phone_book_access(PhoneBook, 'phone_book_id')
@api_response
def delete_phone_book(request, phone_book_id):
    """Delete phone book"""
    try:
        try:
            phone_book = PhoneBook.objects.get(id=phone_book_id)
        except PhoneBook.DoesNotExist:
            raise NotFoundError("Phone book not found")
        
        phone_book_name = phone_book.name
        phone_book.delete()
        
        return success_response(
            data={'id': phone_book_id},
            message=f"Phone book '{phone_book_name}' deleted successfully"
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
