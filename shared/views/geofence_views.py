from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
import json
import re

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_api_exception

from shared.models import Geofence, GeofenceUser
from fleet.models import GeofenceVehicle
from fleet.models import Vehicle
from core.models import User


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_geofence(request):
    """
    Create new geofence
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['title', 'type', 'boundary']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        title = data['title']
        geofence_type = data['type']
        boundary = data['boundary']
        vehicle_ids = data.get('vehicleIds', [])
        user_ids = data.get('userIds', [])
        
        # Validate boundary format
        if not isinstance(boundary, list) or len(boundary) < 3:
            return error_response('Boundary must have at least 3 points', HTTP_STATUS['BAD_REQUEST'])
        
        # Validate boundary data structure
        for point in boundary:
            if not isinstance(point, str) or ',' not in point:
                return error_response('Invalid boundary point format. Expected "lat,lng"', HTTP_STATUS['BAD_REQUEST'])
            
            try:
                lat, lng = point.split(',')
                float(lat)
                float(lng)
            except (ValueError, IndexError):
                return error_response('Invalid coordinates in boundary', HTTP_STATUS['BAD_REQUEST'])
        
        # Create geofence
        with transaction.atomic():
            geofence = Geofence.objects.create(
                title=title,
                type=geofence_type,
                boundary=boundary
            )
            
            # Assign to vehicles if provided
            if vehicle_ids and isinstance(vehicle_ids, list) and len(vehicle_ids) > 0:
                actual_vehicle_ids = []
                
                for imei in vehicle_ids:
                    # Check if this is an IMEI (15 digits) or actual vehicle ID
                    if len(str(imei)) == 15:
                        # This is an IMEI, find the corresponding vehicle ID
                        try:
                            vehicle = Vehicle.objects.get(imei=imei)
                            actual_vehicle_ids.append(vehicle.id)
                        except Vehicle.DoesNotExist:
                            print(f"✗ Vehicle with IMEI {imei} not found")
                    else:
                        # This is already a vehicle ID
                        actual_vehicle_ids.append(int(imei))
                
                if actual_vehicle_ids:
                    for vehicle_id in actual_vehicle_ids:
                        GeofenceVehicle.objects.create(
                            geofence=geofence,
                            vehicle_id=vehicle_id
                        )
            
            # Always assign the current user to the geofence (creator)
            GeofenceUser.objects.create(
                geofence=geofence,
                user=user
            )
            
            # Assign to additional users if provided
            if user_ids and isinstance(user_ids, list) and len(user_ids) > 0:
                # Filter out invalid user IDs and the current user (to avoid duplicates)
                valid_user_ids = [uid for uid in user_ids if isinstance(uid, int) and uid > 0 and uid != user.id]
                
                for user_id in valid_user_ids:
                    GeofenceUser.objects.create(
                        geofence=geofence,
                        user_id=user_id
                    )
        
        # Get updated geofence with assignments
        geofence_data = {
            'id': geofence.id,
            'title': geofence.title,
            'type': geofence.type,
            'boundary': geofence.boundary,
            'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
            'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
            'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.geofencevehicle_set.all()],
            'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.geofenceuser_set.all()]
        }
        
        return success_response(geofence_data, 'Geofence created successfully', HTTP_STATUS['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_geofences(request):
    """
    Get all geofences
    """
    try:
        user = request.user
        
        # Super Admin: all access
        if user.role.name == 'Super Admin':
            geofences = Geofence.objects.prefetch_related('geofencevehicle_set__vehicle', 'geofenceuser_set__user').all()
        else:
            # Dealer/Customer: only view assigned geofences
            geofences = Geofence.objects.filter(
                geofenceuser__user=user
            ).prefetch_related('geofencevehicle_set__vehicle', 'geofenceuser_set__user').distinct()
        
        geofences_data = []
        for geofence in geofences:
            geofence_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.created_at.isoformat() if geofence.created_at else None,
                'updatedAt': geofence.updated_at.isoformat() if geofence.updated_at else None,
                'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.geofencevehicle_set.all()],
                'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.geofenceuser_set.all()]
            }
            geofences_data.append(geofence_data)
        
        return success_response(geofences_data, 'Geofences retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_by_id(request, id):
    """
    Get geofence by ID
    """
    try:
        user = request.user
        
        try:
            geofence = Geofence.objects.prefetch_related('geofencevehicle_set__vehicle', 'geofenceuser_set__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.geofenceuser_set.filter(user=user).exists():
                return error_response('Access denied to this geofence', HTTP_STATUS['FORBIDDEN'])
        
        geofence_data = {
            'id': geofence.id,
            'title': geofence.title,
            'type': geofence.type,
            'boundary': geofence.boundary,
            'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
            'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
            'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.geofencevehicle_set.all()],
            'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.geofenceuser_set.all()]
        }
        
        return success_response(geofence_data, 'Geofence retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofences_by_imei(request, imei):
    """
    Get geofences by IMEI
    """
    try:
        user = request.user
        
        # Get geofences by IMEI
        geofences = Geofence.objects.filter(
            geofencevehicle__vehicle__imei=imei
        ).prefetch_related('geofencevehicle_set__vehicle', 'geofenceuser_set__user').distinct()
        
        # Filter based on user access
        if user.role.name != 'Super Admin':
            # Filter to only show geofences assigned to this user
            geofences = geofences.filter(geofenceuser__user=user).distinct()
        
        geofences_data = []
        for geofence in geofences:
            geofence_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.created_at.isoformat() if geofence.created_at else None,
                'updatedAt': geofence.updated_at.isoformat() if geofence.updated_at else None,
                'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.geofencevehicle_set.all()],
                'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.geofenceuser_set.all()]
            }
            geofences_data.append(geofence_data)
        
        return success_response(geofences_data, 'Geofences retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def update_geofence(request, id):
    """
    Update geofence
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Check if geofence exists
        try:
            geofence = Geofence.objects.prefetch_related('geofenceuser_set__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.geofenceuser_set.filter(user=user).exists():
                return error_response('Access denied to this geofence', HTTP_STATUS['FORBIDDEN'])
        
        # Update geofence
        with transaction.atomic():
            if 'title' in data:
                geofence.title = data['title']
            if 'type' in data:
                geofence.type = data['type']
            if 'boundary' in data:
                geofence.boundary = data['boundary']
            
            geofence.save()
            
            # Update vehicle assignments if provided
            if 'vehicleIds' in data and data['vehicleIds']:
                # Clear existing vehicle assignments
                GeofenceVehicle.objects.filter(geofence=geofence).delete()
                
                # Add new vehicle assignments
                for vehicle_id in data['vehicleIds']:
                    GeofenceVehicle.objects.create(
                        geofence=geofence,
                        vehicle_id=vehicle_id
                    )
            
            # Update user assignments if provided
            if 'userIds' in data and data['userIds']:
                # Clear existing user assignments
                GeofenceUser.objects.filter(geofence=geofence).delete()
                
                # Add new user assignments
                for user_id in data['userIds']:
                    GeofenceUser.objects.create(
                        geofence=geofence,
                        user_id=user_id
                    )
        
        # Get final updated geofence
        geofence.refresh_from_db()
        geofence_data = {
            'id': geofence.id,
            'title': geofence.title,
            'type': geofence.type,
            'boundary': geofence.boundary,
            'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
            'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
            'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.geofencevehicle_set.all()],
            'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.geofenceuser_set.all()]
        }
        
        return success_response(geofence_data, 'Geofence updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS['BAD_REQUEST'])
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def delete_geofence(request, id):
    """
    Delete geofence
    """
    try:
        user = request.user
        
        # Check if geofence exists
        try:
            geofence = Geofence.objects.prefetch_related('geofenceuser_set__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.geofenceuser_set.filter(user=user).exists():
                return error_response('Access denied to this geofence', HTTP_STATUS['FORBIDDEN'])
        
        # Delete geofence
        geofence.delete()
        
        return success_response(None, 'Geofence deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)
