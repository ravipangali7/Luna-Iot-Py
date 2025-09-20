from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import json
import os

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_api_exception

from shared.models import Popup


@csrf_exempt
@require_http_methods(["GET"])
def get_active_popups(request):
    """
    Get all active popups (public endpoint)
    """
    try:
        popups = Popup.objects.filter(isActive=True).order_by('-createdAt')
        
        popups_data = []
        for popup in popups:
            popup_data = {
                'id': popup.id,
                'title': popup.title,
                'message': popup.message,
                'isActive': popup.isActive,
                'image': popup.image.name if popup.image else None,
                'imageUrl': f'/media/{popup.image.name}' if popup.image else None,
                'createdAt': popup.createdAt.isoformat() if popup.createdAt else None,
                'updatedAt': popup.updatedAt.isoformat() if popup.updatedAt else None
            }
            popups_data.append(popup_data)
        
        return success_response(popups_data, 'Active popups retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
@require_role(['Super Admin'])
def get_all_popups(request):
    """
    Get all popups (only Super Admin)
    """
    try:
        popups = Popup.objects.all().order_by('-createdAt')
        
        popups_data = []
        for popup in popups:
            popup_data = {
                'id': popup.id,
                'title': popup.title,
                'message': popup.message,
                'isActive': popup.isActive,
                'image': popup.image.name if popup.image else None,
                'imageUrl': f'/media/{popup.image.name}' if popup.image else None,
                'createdAt': popup.createdAt.isoformat() if popup.createdAt else None,
                'updatedAt': popup.updatedAt.isoformat() if popup.updatedAt else None
            }
            popups_data.append(popup_data)
        
        return success_response(popups_data, 'All popups retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
@require_role(['Super Admin'])
def get_popup_by_id(request, id):
    """
    Get popup by ID (only Super Admin)
    """
    try:
        try:
            popup = Popup.objects.get(id=id)
        except Popup.DoesNotExist:
            return error_response('Popup not found', HTTP_STATUS['NOT_FOUND'])
        
        popup_data = {
            'id': popup.id,
            'title': popup.title,
            'message': popup.message,
            'isActive': popup.isActive,
            'image': popup.image.name if popup.image else None,
                'imageUrl': f'/media/{popup.image.name}' if popup.image else None,
            'createdAt': popup.createdAt.isoformat() if popup.createdAt else None,
            'updatedAt': popup.updatedAt.isoformat() if popup.updatedAt else None
        }
        
        return success_response(popup_data, 'Popup retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
@require_role(['Super Admin'])
def create_popup(request):
    """
    Create new popup (only Super Admin)
    """
    try:
        # Get form data
        title = request.POST.get('title')
        message = request.POST.get('message')
        isActive = request.POST.get('isActive', 'true').lower() == 'true'
        
        # Validate required fields
        if not title or not message:
            return error_response('Title and message are required', HTTP_STATUS['BAD_REQUEST'])
        
        # Handle image upload
        image_file = None
        if 'image' in request.FILES:
            image_file = request.FILES['image']
        
        # Create popup
        popup = Popup.objects.create(
            title=title,
            message=message,
            isActive=isActive,
            image=image_file
        )
        
        popup_data = {
            'id': popup.id,
            'title': popup.title,
            'message': popup.message,
            'isActive': popup.isActive,
            'image': popup.image.name if popup.image else None,
                'imageUrl': f'/media/{popup.image.name}' if popup.image else None,
            'createdAt': popup.createdAt.isoformat() if popup.createdAt else None,
            'updatedAt': popup.updatedAt.isoformat() if popup.updatedAt else None
        }
        
        return success_response(popup_data, 'Popup created successfully', HTTP_STATUS['CREATED'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
@require_role(['Super Admin'])
def update_popup(request, id):
    """
    Update popup (only Super Admin)
    """
    try:
        # Get popup
        try:
            popup = Popup.objects.get(id=id)
        except Popup.DoesNotExist:
            return error_response('Popup not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get form data
        title = request.POST.get('title')
        message = request.POST.get('message')
        isActive = request.POST.get('isActive')
        
        # Update popup fields
        if title is not None:
            popup.title = title
        if message is not None:
            popup.message = message
        if isActive is not None:
            popup.isActive = isActive.lower() == 'true'
        
        # Handle image update
        if 'image' in request.FILES:
            # Delete old image if exists
            if popup.image:
                try:
                    if default_storage.exists(popup.image.name):
                        default_storage.delete(popup.image.name)
                except Exception as image_error:
                    print(f'Error deleting old image: {image_error}')
            
            # Set new image
            popup.image = request.FILES['image']
        
        popup.save()
        
        popup_data = {
            'id': popup.id,
            'title': popup.title,
            'message': popup.message,
            'isActive': popup.isActive,
            'image': popup.image.name if popup.image else None,
                'imageUrl': f'/media/{popup.image.name}' if popup.image else None,
            'createdAt': popup.createdAt.isoformat() if popup.createdAt else None,
            'updatedAt': popup.updatedAt.isoformat() if popup.updatedAt else None
        }
        
        return success_response(popup_data, 'Popup updated successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_popup(request, id):
    """
    Delete popup (only Super Admin)
    """
    try:
        # Get popup
        try:
            popup = Popup.objects.get(id=id)
        except Popup.DoesNotExist:
            return error_response('Popup not found', HTTP_STATUS['NOT_FOUND'])
        
        # Delete associated image if exists
        if popup.image:
            try:
                if default_storage.exists(popup.image.name):
                    default_storage.delete(popup.image.name)
            except Exception as image_error:
                print(f'Error deleting image file: {image_error}')
                # Continue with popup deletion even if image deletion fails
        
        # Delete popup
        popup.delete()
        
        return success_response({'success': True}, 'Popup deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)
