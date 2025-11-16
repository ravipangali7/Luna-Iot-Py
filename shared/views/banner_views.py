from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import QueryDict
from django.utils.datastructures import MultiValueDict
import json
import os
import cgi
import io

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_api_exception

from shared.models import Banner


@csrf_exempt
@require_http_methods(["GET"])
def get_active_banners(request):
    """
    Get all active banners (public endpoint)
    """
    try:
        banners = Banner.objects.filter(isActive=True).order_by('orderPosition', '-createdAt')
        
        banners_data = []
        for banner in banners:
            banner_data = {
                'id': banner.id,
                'title': banner.title,
                'url': banner.url,
                'isActive': banner.isActive,
                'click': banner.click,
                'orderPosition': banner.orderPosition,
                'image': banner.image.name if banner.image else None,
                'imageUrl': f'https://py.mylunago.com/media/{banner.image.name}' if banner.image else None,
                'createdAt': banner.createdAt.isoformat() if banner.createdAt else None,
                'updatedAt': banner.updatedAt.isoformat() if banner.updatedAt else None
            }
            banners_data.append(banner_data)
        
        return success_response(banners_data, 'Active banners retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
@require_role(['Super Admin'])
def get_all_banners(request):
    """
    Get all banners (only Super Admin)
    """
    try:
        banners = Banner.objects.all().order_by('orderPosition', '-createdAt')
        
        banners_data = []
        for banner in banners:
            banner_data = {
                'id': banner.id,
                'title': banner.title,
                'url': banner.url,
                'isActive': banner.isActive,
                'click': banner.click,
                'orderPosition': banner.orderPosition,
                'image': banner.image.name if banner.image else None,
                'imageUrl': f'https://py.mylunago.com/media/{banner.image.name}' if banner.image else None,
                'createdAt': banner.createdAt.isoformat() if banner.createdAt else None,
                'updatedAt': banner.updatedAt.isoformat() if banner.updatedAt else None
            }
            banners_data.append(banner_data)
        
        return success_response(banners_data, 'All banners retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
@require_role(['Super Admin'])
def get_banner_by_id(request, id):
    """
    Get banner by ID (only Super Admin)
    """
    try:
        try:
            banner = Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return error_response('Banner not found', HTTP_STATUS['NOT_FOUND'])
        
        banner_data = {
            'id': banner.id,
            'title': banner.title,
            'url': banner.url,
            'isActive': banner.isActive,
            'click': banner.click,
            'orderPosition': banner.orderPosition,
            'image': banner.image.name if banner.image else None,
            'imageUrl': f'https://py.mylunago.com/media/{banner.image.name}' if banner.image else None,
            'createdAt': banner.createdAt.isoformat() if banner.createdAt else None,
            'updatedAt': banner.updatedAt.isoformat() if banner.updatedAt else None
        }
        
        return success_response(banner_data, 'Banner retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
@require_role(['Super Admin'])
def create_banner(request):
    """
    Create new banner (only Super Admin)
    """
    try:
        # Get form data
        title = request.POST.get('title')
        url = request.POST.get('url') or None
        isActive = request.POST.get('isActive', 'true').lower() == 'true'
        orderPosition = request.POST.get('orderPosition', '0')
        
        # Validate required fields
        if not title:
            return error_response('Title is required', HTTP_STATUS['BAD_REQUEST'])
        
        # Validate order position
        try:
            orderPosition = int(orderPosition) if orderPosition else 0
            if orderPosition < 0:
                return error_response('Order position must be >= 0', HTTP_STATUS['BAD_REQUEST'])
        except ValueError:
            return error_response('Order position must be a valid number', HTTP_STATUS['BAD_REQUEST'])
        
        # Handle image upload
        image_file = None
        if 'image' in request.FILES:
            image_file = request.FILES['image']
        
        # Create banner
        banner = Banner.objects.create(
            title=title,
            url=url if url and url.strip() else None,
            isActive=isActive,
            orderPosition=orderPosition,
            image=image_file
        )
        
        banner_data = {
            'id': banner.id,
            'title': banner.title,
            'url': banner.url,
            'isActive': banner.isActive,
            'click': banner.click,
            'orderPosition': banner.orderPosition,
            'image': banner.image.name if banner.image else None,
            'imageUrl': f'https://py.mylunago.com/media/{banner.image.name}' if banner.image else None,
            'createdAt': banner.createdAt.isoformat() if banner.createdAt else None,
            'updatedAt': banner.updatedAt.isoformat() if banner.updatedAt else None
        }
        
        return success_response(banner_data, 'Banner created successfully', HTTP_STATUS['CREATED'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
@require_role(['Super Admin'])
def update_banner(request, id):
    """
    Update banner (only Super Admin)
    """
    try:
        # Get banner
        try:
            banner = Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return error_response('Banner not found', HTTP_STATUS['NOT_FOUND'])
        
        # For PUT requests, Django doesn't populate request.POST automatically
        # We need to manually parse multipart/form-data
        # Check if request.POST is empty (which happens for PUT requests)
        if request.method == 'PUT' and len(request.POST) == 0:
            # Debug logging
            print(f'PUT request detected, POST is empty. Content-Type: {request.META.get("CONTENT_TYPE", "")}')
            print(f'Request body length: {len(request.body)}')
            
            # Manually parse multipart/form-data for PUT requests
            try:
                # Get content type
                content_type = request.META.get('CONTENT_TYPE', '')
                if 'multipart/form-data' in content_type:
                    # Create a FieldStorage object to parse multipart data
                    environ = request.META.copy()
                    environ['CONTENT_TYPE'] = content_type
                    environ['CONTENT_LENGTH'] = str(len(request.body))
                    
                    # Create a file-like object from request.body
                    body_file = io.BytesIO(request.body)
                    
                    # Parse multipart data
                    form = cgi.FieldStorage(
                        fp=body_file,
                        environ=environ,
                        keep_blank_values=True
                    )
                    
                    # Populate request._post and request._files
                    request._post = QueryDict('', mutable=True)
                    request._files = MultiValueDict()
                    
                    for field in form.list:
                        if field.filename:
                            # It's a file
                            file_obj = ContentFile(field.file.read())
                            file_obj.name = field.filename
                            request._files.appendlist(field.name, file_obj)
                            print(f'Parsed file field: {field.name} = {field.filename}')
                        else:
                            # It's a regular field
                            request._post[field.name] = field.value
                            print(f'Parsed form field: {field.name} = {field.value}')
                    
                    print(f'Parsed POST data: {dict(request._post)}')
                    print(f'Parsed FILES keys: {list(request._files.keys())}')
                else:
                    print(f'Content-Type is not multipart/form-data: {content_type}')
            except Exception as parse_error:
                print(f'Error parsing multipart data: {parse_error}')
                import traceback
                traceback.print_exc()
        
        # Get form data (now should work for both POST and PUT)
        title = request.POST.get('title')
        url = request.POST.get('url')
        isActive = request.POST.get('isActive')
        orderPosition = request.POST.get('orderPosition')
        
        # Update banner fields
        if title is not None:
            banner.title = title
        if url is not None:
            # Handle "undefined" string explicitly and convert to None
            # Allow empty string to set URL to None
            if url == 'undefined' or (isinstance(url, str) and url.strip() == 'undefined'):
                banner.url = None
            else:
                banner.url = url.strip() if url and url.strip() else None
        elif url == '':
            # Explicitly handle empty string to clear URL
            banner.url = None
        if isActive is not None:
            banner.isActive = isActive.lower() == 'true'
        if orderPosition is not None and orderPosition != '':
            try:
                orderPositionInt = int(orderPosition)
                if orderPositionInt < 0:
                    return error_response('Order position must be >= 0', HTTP_STATUS['BAD_REQUEST'])
                banner.orderPosition = orderPositionInt
            except (ValueError, TypeError):
                return error_response('Order position must be a valid number', HTTP_STATUS['BAD_REQUEST'])
        
        # Handle image update
        if 'image' in request.FILES:
            # Delete old image if exists
            if banner.image:
                try:
                    if default_storage.exists(banner.image.name):
                        default_storage.delete(banner.image.name)
                except Exception as image_error:
                    print(f'Error deleting old image: {image_error}')
            
            # Set new image
            banner.image = request.FILES['image']
        
        banner.save()
        
        banner_data = {
            'id': banner.id,
            'title': banner.title,
            'url': banner.url,
            'isActive': banner.isActive,
            'click': banner.click,
            'orderPosition': banner.orderPosition,
            'image': banner.image.name if banner.image else None,
            'imageUrl': f'https://py.mylunago.com/media/{banner.image.name}' if banner.image else None,
            'createdAt': banner.createdAt.isoformat() if banner.createdAt else None,
            'updatedAt': banner.updatedAt.isoformat() if banner.updatedAt else None
        }
        
        return success_response(banner_data, 'Banner updated successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_banner(request, id):
    """
    Delete banner (only Super Admin)
    """
    try:
        # Get banner
        try:
            banner = Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return error_response('Banner not found', HTTP_STATUS['NOT_FOUND'])
        
        # Delete associated image if exists
        if banner.image:
            try:
                if default_storage.exists(banner.image.name):
                    default_storage.delete(banner.image.name)
            except Exception as image_error:
                print(f'Error deleting image file: {image_error}')
                # Continue with banner deletion even if image deletion fails
        
        # Delete banner
        banner.delete()
        
        return success_response({'success': True}, 'Banner deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
def increment_banner_click(request, id):
    """
    Increment banner click count (public endpoint)
    """
    try:
        try:
            banner = Banner.objects.get(id=id)
        except Banner.DoesNotExist:
            return error_response('Banner not found', HTTP_STATUS['NOT_FOUND'])
        
        # Increment click count
        banner.click += 1
        banner.save()
        
        return success_response({'click': banner.click}, 'Banner click count incremented successfully')
    
    except Exception as e:
        return handle_api_exception(e)

