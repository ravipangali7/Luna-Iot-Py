"""
Vehicle Tag Views
Handles vehicle tag management endpoints
"""
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.http import HttpResponse
from vehicle_tag.models import VehicleTag, VehicleTagAlert
from vehicle_tag.serializers import (
    VehicleTagSerializer,
    VehicleTagListSerializer,
    VehicleTagAlertCreateSerializer,
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin
from vehicle_tag.services.qr_service import generate_tag_image
from vehicle_tag.services.notification_service import send_vehicle_tag_alert_notification


@api_view(['POST'])
@require_super_admin
@api_response
def generate_vehicle_tags(request):
    """
    Generate N vehicle tags
    Accepts count parameter (1, 5, 10, 20, 30, 50, 75, 100)
    Creates tags with only id, vtid (auto-generated), is_active=true, is_downloaded=false
    """
    try:
        data = request.data
        count = data.get('count', 1)
        
        # Validate count
        allowed_counts = [1, 5, 10, 20, 30, 50, 75, 100]
        if count not in allowed_counts:
            return error_response(
                message=f'Invalid count. Allowed values: {allowed_counts}',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Generate tags - let database auto-assign IDs
        created_tags = []
        for _ in range(count):
            # Create tag without specifying id - let database handle it
            tag = VehicleTag(
                is_active=True,
                is_downloaded=False
            )
            # Save will auto-generate vtid based on auto-assigned id
            tag.save()
            created_tags.append(tag)
        
        # Serialize response
        serializer = VehicleTagSerializer(created_tags, many=True)
        
        return success_response(
            data=serializer.data,
            message=f'Successfully generated {count} vehicle tag(s)'
        )
        
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_super_admin
@api_response
def get_all_vehicle_tags(request):
    """
    Get all vehicle tags (paginated)
    Include user info (name, phone) if assigned, else "unassigned"
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 25))
        
        # Get all tags
        tags = VehicleTag.objects.all().select_related('user').order_by('-created_at')
        
        # Paginate
        paginator = Paginator(tags, page_size)
        page_obj = paginator.get_page(page)
        
        # Serialize
        serializer = VehicleTagListSerializer(page_obj.object_list, many=True, context={'request': request})
        
        # Build pagination response
        pagination_data = {
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'total_items': paginator.count,
            'page_size': page_size,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
        
        return success_response(
            data={
                'tags': serializer.data,
                'pagination': pagination_data
            },
            message='Vehicle tags retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@api_response
def get_vehicle_tag_by_vtid(request, vtid):
    """
    Get vehicle tag details by vtid
    Used for alert page
    Public access - no authentication required
    """
    try:
        try:
            tag = VehicleTag.objects.select_related('user').get(vtid=vtid)
        except VehicleTag.DoesNotExist:
            return error_response(
                message=f'Vehicle tag with VTID {vtid} not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        serializer = VehicleTagSerializer(tag, context={'request': request})
        
        return success_response(
            data=serializer.data,
            message='Vehicle tag retrieved successfully'
        )
        
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['POST'])
@api_response
def create_vehicle_tag_alert(request):
    """
    Create vehicle tag alert
    Accepts vtid, latitude, longitude, person_image (optional), alert type
    Sends FCM notification if vehicle tag has user
    Public access - no authentication required
    """
    try:
        serializer = VehicleTagAlertCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return error_response(
                message='Validation error',
                status_code=HTTP_STATUS['BAD_REQUEST'],
                data=serializer.errors
            )
        
        # Create alert
        alert = serializer.save()
        
        # Send notification if vehicle tag has user
        send_vehicle_tag_alert_notification(alert)
        
        # Return success response
        from vehicle_tag.serializers import VehicleTagAlertSerializer
        alert_serializer = VehicleTagAlertSerializer(alert, context={'request': request})
        
        return success_response(
            data=alert_serializer.data,
            message='Alert created successfully'
        )
        
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
@require_super_admin
@api_response
def get_vehicle_tags_for_bulk_print(request):
    """
    Get vehicle tags for bulk print (range selection)
    Accepts from_id and to_id parameters
    Returns tags in range for PDF generation
    """
    try:
        from_id = int(request.GET.get('from_id'))
        to_id = int(request.GET.get('to_id'))
        
        if from_id > to_id:
            return error_response(
                message='from_id must be less than or equal to to_id',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # Get tags in range
        tags = VehicleTag.objects.filter(
            id__gte=from_id,
            id__lte=to_id
        ).select_related('user').order_by('id')
        
        if not tags.exists():
            return error_response(
                message='No tags found in the specified range',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Serialize
        serializer = VehicleTagListSerializer(tags, many=True, context={'request': request})
        
        return success_response(
            data=serializer.data,
            message=f'Retrieved {tags.count()} vehicle tag(s) for bulk print'
        )
        
    except ValueError:
        return error_response(
            message='Invalid from_id or to_id. Must be integers.',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )


@api_view(['GET'])
def get_vehicle_tag_qr_image(request, vtid):
    """
    Get QR code image for a vehicle tag
    Returns PNG image
    Public access - no authentication required (needed for QR code scanning)
    Note: No @api_response decorator as this returns HttpResponse, not JSON
    """
    try:
        try:
            tag = VehicleTag.objects.get(vtid=vtid)
        except VehicleTag.DoesNotExist:
            return error_response(
                message=f'Vehicle tag with VTID {vtid} not found',
                status_code=HTTP_STATUS['NOT_FOUND']
            )
        
        # Generate QR code image
        img_io = generate_tag_image(tag.vtid)
        
        # Return image response directly (not JSON)
        response = HttpResponse(img_io.getvalue(), content_type='image/png')
        response['Content-Disposition'] = f'inline; filename="vehicle_tag_{vtid}.png"'
        return response
        
    except Exception as e:
        # For errors, return JSON error response
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

