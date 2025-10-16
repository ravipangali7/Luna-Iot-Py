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
        print(f"Creating geofence for user: {user.id}, data: {data}")
        
        # Validate required fields
        required_fields = ['title', 'type', 'boundary']
        validation_result = validate_required_fields(data, required_fields)
        if not validation_result['is_valid']:
            return error_response(validation_result['message'], HTTP_STATUS['BAD_REQUEST'])
        
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
        print(f"Creating geofence with title: {title}, type: {geofence_type}, boundary: {boundary}")
        with transaction.atomic():
            geofence = Geofence.objects.create(
                title=title,
                type=geofence_type,
                boundary=boundary
            )
            print(f"Geofence created with ID: {geofence.id}")
            
            # Assign to vehicles if provided
            if vehicle_ids and isinstance(vehicle_ids, list) and len(vehicle_ids) > 0:
                print(f"Assigning vehicles: {vehicle_ids}")
                actual_vehicle_ids = []
                
                for vehicle_id in vehicle_ids:
                    # Check if this is an IMEI (15 digits) or actual vehicle ID
                    if len(str(vehicle_id)) == 15:
                        # This is an IMEI, find the corresponding vehicle ID
                        try:
                            vehicle = Vehicle.objects.get(imei=vehicle_id)
                            actual_vehicle_ids.append(vehicle.id)
                            print(f"✓ Found vehicle with IMEI {vehicle_id}, ID: {vehicle.id}")
                        except Vehicle.DoesNotExist:
                            print(f"✗ Vehicle with IMEI {vehicle_id} not found - skipping")
                            continue
                    else:
                        # This is already a vehicle ID
                        try:
                            vehicle_id_int = int(vehicle_id)
                            # Verify the vehicle exists
                            vehicle = Vehicle.objects.get(id=vehicle_id_int)
                            actual_vehicle_ids.append(vehicle_id_int)
                            print(f"✓ Found vehicle with ID {vehicle_id}")
                        except (ValueError, TypeError):
                            print(f"✗ Invalid vehicle ID format: {vehicle_id}")
                            continue
                        except Vehicle.DoesNotExist:
                            print(f"✗ Vehicle with ID {vehicle_id} not found - skipping")
                            continue
                
                if actual_vehicle_ids:
                    print(f"Creating GeofenceVehicle relationships for {len(actual_vehicle_ids)} vehicles")
                    for vehicle_id in actual_vehicle_ids:
                        try:
                            vehicle = Vehicle.objects.get(id=vehicle_id)
                            GeofenceVehicle.objects.create(
                                geofence=geofence,
                                vehicle=vehicle
                            )
                            print(f"✓ Created GeofenceVehicle for vehicle {vehicle.name} (ID: {vehicle_id})")
                        except Vehicle.DoesNotExist:
                            print(f"✗ Vehicle with ID {vehicle_id} not found")
                        except Exception as e:
                            print(f"✗ Error creating GeofenceVehicle for vehicle {vehicle_id}: {e}")
                else:
                    print("No valid vehicles found to assign")
            
            # Always assign the current user to the geofence (creator)
            try:
                GeofenceUser.objects.create(
                    geofence=geofence,
                    user=user
                )
                print(f"✓ Created GeofenceUser for creator {user.name} (ID: {user.id})")
            except Exception as e:
                print(f"✗ Error creating GeofenceUser for creator: {e}")
            
            # Assign to additional users if provided
            if user_ids and isinstance(user_ids, list) and len(user_ids) > 0:
                # Filter out invalid user IDs and the current user (to avoid duplicates)
                valid_user_ids = [uid for uid in user_ids if isinstance(uid, int) and uid > 0 and uid != user.id]
                
                for user_id in valid_user_ids:
                    try:
                        user_obj = User.objects.get(id=user_id)
                        GeofenceUser.objects.create(
                            geofence=geofence,
                            user=user_obj
                        )
                        print(f"✓ Created GeofenceUser for user {user_obj.name} (ID: {user_id})")
                    except User.DoesNotExist:
                        print(f"✗ User with ID {user_id} not found - skipping")
                    except Exception as e:
                        print(f"✗ Error creating GeofenceUser for user {user_id}: {e}")
        
        # Get updated geofence with assignments
        print("Building response data...")
        try:
            print("About to build response...")
            # Get vehicles data safely
            vehicles_data = []
            for gv in geofence.vehicles.all():
                try:
                    vehicles_data.append({
                        'id': gv.vehicle.id, 
                        'imei': gv.vehicle.imei, 
                        'name': gv.vehicle.name
                    })
                except Exception as e:
                    print(f"Error building vehicle data: {e}")
                    continue
            
            # Get users data safely
            users_data = []
            for gu in geofence.users.all():
                try:
                    users_data.append({
                        'id': gu.user.id, 
                        'name': gu.user.name, 
                        'phone': gu.user.phone
                    })
                except Exception as e:
                    print(f"Error building user data: {e}")
                    continue
            
            geofence_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
                'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
                'vehicles': vehicles_data,
                'users': users_data
            }
            
            print(f"✓ Geofence creation completed successfully! ID: {geofence.id}")
            print(f"Response data: {geofence_data}")
            print("Calling success_response...")
            
            # Build complete response with vehicles and users
            complete_response_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
                'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
                'vehicles': vehicles_data,
                'users': users_data
            }
            
            response = success_response(complete_response_data, 'Geofence created successfully', 201)
            print(f"Success response created: {type(response)}")
            return response
            
        except Exception as e:
            print(f"Error building response data: {e}")
            # Return a simple response if there's an error
            simple_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'vehicles': [],
                'users': []
            }
            print("Using fallback simple response...")
            response = success_response(simple_data, 'Geofence created successfully', 201)
            print(f"Fallback response created: {type(response)}")
            return response
    
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
            geofences = Geofence.objects.prefetch_related('vehicles__vehicle', 'users__user').all()
        else:
            # Dealer/Customer: only view assigned geofences
            geofences = Geofence.objects.filter(
                users__user=user
            ).prefetch_related('vehicles__vehicle', 'users__user').distinct()
        
        geofences_data = []
        for geofence in geofences:
            geofence_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
                'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
                'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.vehicles.all()],
                'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.users.all()]
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
            geofence = Geofence.objects.prefetch_related('vehicles__vehicle', 'users__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.users.filter(user=user).exists():
                return error_response('Access denied to this geofence', HTTP_STATUS['FORBIDDEN'])
        
        geofence_data = {
            'id': geofence.id,
            'title': geofence.title,
            'type': geofence.type,
            'boundary': geofence.boundary,
            'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
            'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
            'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.vehicles.all()],
            'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.users.all()]
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
            vehicles__vehicle__imei=imei
        ).prefetch_related('vehicles__vehicle', 'users__user').distinct()
        
        # Filter based on user access
        if user.role.name != 'Super Admin':
            # Filter to only show geofences assigned to this user
            geofences = geofences.filter(users__user=user).distinct()
        
        geofences_data = []
        for geofence in geofences:
            geofence_data = {
                'id': geofence.id,
                'title': geofence.title,
                'type': geofence.type,
                'boundary': geofence.boundary,
                'createdAt': geofence.createdAt.isoformat() if geofence.createdAt else None,
                'updatedAt': geofence.updatedAt.isoformat() if geofence.updatedAt else None,
                'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.vehicles.all()],
                'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.users.all()]
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
            geofence = Geofence.objects.prefetch_related('users__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.users.filter(user=user).exists():
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
            'vehicles': [{'id': gv.vehicle.id, 'imei': gv.vehicle.imei, 'name': gv.vehicle.name} for gv in geofence.vehicles.all()],
            'users': [{'id': gu.user.id, 'name': gu.user.name, 'phone': gu.user.phone} for gu in geofence.users.all()]
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
            geofence = Geofence.objects.prefetch_related('users__user').get(id=id)
        except Geofence.DoesNotExist:
            return error_response('Geofence not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check access based on role
        if user.role.name != 'Super Admin':
            # Check if user has access to this geofence
            if not geofence.users.filter(user=user).exists():
                return error_response('Access denied to this geofence', HTTP_STATUS['FORBIDDEN'])
        
        # Delete geofence
        geofence.delete()
        
        return success_response(None, 'Geofence deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


# ==================== GEOFENCE EVENT VIEWS ====================

@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_events(request):
    """
    Get all geofence events with optional filters
    """
    try:
        from django.db import connection
        
        user = request.user
        
        # Get query parameters
        vehicle_id = request.GET.get('vehicleId')
        geofence_id = request.GET.get('geofenceId')
        imei = request.GET.get('imei')
        is_inside = request.GET.get('isInside')
        event_type = request.GET.get('eventType')
        start_date = request.GET.get('startDate')
        end_date = request.GET.get('endDate')
        
        # Build SQL query with JOINs
        sql = """
            SELECT 
                ge.id,
                ge.vehicle_id,
                ge.geofence_id,
                ge.is_inside,
                ge.last_event_type,
                ge.last_event_at,
                ge.created_at,
                ge.updated_at,
                v.name as vehicle_name,
                v.vehicle_no,
                v.imei as vehicle_imei,
                g.title as geofence_title,
                g.type as geofence_type
            FROM geofence_events ge
            LEFT JOIN vehicles v ON ge.vehicle_id = v.id
            LEFT JOIN geofences g ON ge.geofence_id = g.id
            WHERE 1=1
        """
        params = []
        
        # Add filters
        if vehicle_id:
            sql += " AND ge.vehicle_id = %s"
            params.append(vehicle_id)
        
        if geofence_id:
            sql += " AND ge.geofence_id = %s"
            params.append(geofence_id)
        
        if imei:
            sql += " AND v.imei = %s"
            params.append(imei)
        
        if is_inside is not None:
            sql += " AND ge.is_inside = %s"
            params.append(1 if is_inside.lower() == 'true' else 0)
        
        if event_type:
            sql += " AND ge.last_event_type = %s"
            params.append(event_type)
        
        if start_date:
            sql += " AND ge.last_event_at >= %s"
            params.append(start_date)
        
        if end_date:
            sql += " AND ge.last_event_at <= %s"
            params.append(end_date)
        
        # Role-based access control
        if user.role.name != 'Super Admin':
            # Only show events for vehicles the user has access to
            sql += """
                AND ge.vehicle_id IN (
                    SELECT uv.vehicle_id 
                    FROM user_vehicles uv 
                    WHERE uv.user_id = %s
                )
            """
            params.append(user.id)
        
        sql += " ORDER BY ge.last_event_at DESC LIMIT 1000"
        
        # Execute query
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format response
        events_data = []
        for row in results:
            event_data = {
                'id': row['id'],
                'vehicleId': row['vehicle_id'],
                'geofenceId': row['geofence_id'],
                'isInside': bool(row['is_inside']),
                'lastEventType': row['last_event_type'],
                'lastEventAt': row['last_event_at'].isoformat() if row['last_event_at'] else None,
                'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
                'updatedAt': row['updated_at'].isoformat() if row['updated_at'] else None,
                'vehicle': {
                    'name': row['vehicle_name'],
                    'vehicleNo': row['vehicle_no'],
                    'imei': row['vehicle_imei']
                } if row['vehicle_name'] else None,
                'geofence': {
                    'title': row['geofence_title'],
                    'type': row['geofence_type']
                } if row['geofence_title'] else None
            }
            events_data.append(event_data)
        
        return success_response(events_data, 'Geofence events retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_event_by_id(request, id):
    """
    Get geofence event by ID
    """
    try:
        from django.db import connection
        
        user = request.user
        
        # Build SQL query with JOINs
        sql = """
            SELECT 
                ge.id,
                ge.vehicle_id,
                ge.geofence_id,
                ge.is_inside,
                ge.last_event_type,
                ge.last_event_at,
                ge.created_at,
                ge.updated_at,
                v.name as vehicle_name,
                v.vehicle_no,
                v.imei as vehicle_imei,
                g.title as geofence_title,
                g.type as geofence_type
            FROM geofence_events ge
            LEFT JOIN vehicles v ON ge.vehicle_id = v.id
            LEFT JOIN geofences g ON ge.geofence_id = g.id
            WHERE ge.id = %s
        """
        params = [id]
        
        # Role-based access control
        if user.role.name != 'Super Admin':
            sql += """
                AND ge.vehicle_id IN (
                    SELECT uv.vehicle_id 
                    FROM user_vehicles uv 
                    WHERE uv.user_id = %s
                )
            """
            params.append(user.id)
        
        # Execute query
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            row = cursor.fetchone()
        
        if not row:
            return error_response('Geofence event not found or access denied', HTTP_STATUS['NOT_FOUND'])
        
        result = dict(zip(columns, row))
        
        # Format response
        event_data = {
            'id': result['id'],
            'vehicleId': result['vehicle_id'],
            'geofenceId': result['geofence_id'],
            'isInside': bool(result['is_inside']),
            'lastEventType': result['last_event_type'],
            'lastEventAt': result['last_event_at'].isoformat() if result['last_event_at'] else None,
            'createdAt': result['created_at'].isoformat() if result['created_at'] else None,
            'updatedAt': result['updated_at'].isoformat() if result['updated_at'] else None,
            'vehicle': {
                'name': result['vehicle_name'],
                'vehicleNo': result['vehicle_no'],
                'imei': result['vehicle_imei']
            } if result['vehicle_name'] else None,
            'geofence': {
                'title': result['geofence_title'],
                'type': result['geofence_type']
            } if result['geofence_title'] else None
        }
        
        return success_response(event_data, 'Geofence event retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_events_by_vehicle(request, vehicle_id):
    """
    Get geofence events by vehicle ID
    """
    try:
        from django.db import connection
        
        user = request.user
        
        # Check access
        if user.role.name != 'Super Admin':
            # Check if user has access to this vehicle
            sql_check = """
                SELECT COUNT(*) FROM user_vehicles 
                WHERE user_id = %s AND vehicle_id = %s
            """
            with connection.cursor() as cursor:
                cursor.execute(sql_check, [user.id, vehicle_id])
                has_access = cursor.fetchone()[0] > 0
            
            if not has_access:
                return error_response('Access denied to this vehicle', HTTP_STATUS['FORBIDDEN'])
        
        # Get events
        sql = """
            SELECT 
                ge.id,
                ge.vehicle_id,
                ge.geofence_id,
                ge.is_inside,
                ge.last_event_type,
                ge.last_event_at,
                ge.created_at,
                ge.updated_at,
                v.name as vehicle_name,
                v.vehicle_no,
                v.imei as vehicle_imei,
                g.title as geofence_title,
                g.type as geofence_type
            FROM geofence_events ge
            LEFT JOIN vehicles v ON ge.vehicle_id = v.id
            LEFT JOIN geofences g ON ge.geofence_id = g.id
            WHERE ge.vehicle_id = %s
            ORDER BY ge.last_event_at DESC
        """
        
        with connection.cursor() as cursor:
            cursor.execute(sql, [vehicle_id])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format response
        events_data = []
        for row in results:
            event_data = {
                'id': row['id'],
                'vehicleId': row['vehicle_id'],
                'geofenceId': row['geofence_id'],
                'isInside': bool(row['is_inside']),
                'lastEventType': row['last_event_type'],
                'lastEventAt': row['last_event_at'].isoformat() if row['last_event_at'] else None,
                'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
                'updatedAt': row['updated_at'].isoformat() if row['updated_at'] else None,
                'vehicle': {
                    'name': row['vehicle_name'],
                    'vehicleNo': row['vehicle_no'],
                    'imei': row['vehicle_imei']
                } if row['vehicle_name'] else None,
                'geofence': {
                    'title': row['geofence_title'],
                    'type': row['geofence_type']
                } if row['geofence_title'] else None
            }
            events_data.append(event_data)
        
        return success_response(events_data, 'Vehicle geofence events retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_events_by_geofence(request, geofence_id):
    """
    Get geofence events by geofence ID
    """
    try:
        from django.db import connection
        
        user = request.user
        
        # Build SQL query
        sql = """
            SELECT 
                ge.id,
                ge.vehicle_id,
                ge.geofence_id,
                ge.is_inside,
                ge.last_event_type,
                ge.last_event_at,
                ge.created_at,
                ge.updated_at,
                v.name as vehicle_name,
                v.vehicle_no,
                v.imei as vehicle_imei,
                g.title as geofence_title,
                g.type as geofence_type
            FROM geofence_events ge
            LEFT JOIN vehicles v ON ge.vehicle_id = v.id
            LEFT JOIN geofences g ON ge.geofence_id = g.id
            WHERE ge.geofence_id = %s
        """
        params = [geofence_id]
        
        # Role-based access control
        if user.role.name != 'Super Admin':
            sql += """
                AND ge.vehicle_id IN (
                    SELECT uv.vehicle_id 
                    FROM user_vehicles uv 
                    WHERE uv.user_id = %s
                )
            """
            params.append(user.id)
        
        sql += " ORDER BY ge.last_event_at DESC"
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format response
        events_data = []
        for row in results:
            event_data = {
                'id': row['id'],
                'vehicleId': row['vehicle_id'],
                'geofenceId': row['geofence_id'],
                'isInside': bool(row['is_inside']),
                'lastEventType': row['last_event_type'],
                'lastEventAt': row['last_event_at'].isoformat() if row['last_event_at'] else None,
                'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
                'updatedAt': row['updated_at'].isoformat() if row['updated_at'] else None,
                'vehicle': {
                    'name': row['vehicle_name'],
                    'vehicleNo': row['vehicle_no'],
                    'imei': row['vehicle_imei']
                } if row['vehicle_name'] else None,
                'geofence': {
                    'title': row['geofence_title'],
                    'type': row['geofence_type']
                } if row['geofence_title'] else None
            }
            events_data.append(event_data)
        
        return success_response(events_data, 'Geofence events retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_geofence_events_by_imei(request, imei):
    """
    Get geofence events by vehicle IMEI
    """
    try:
        from django.db import connection
        
        user = request.user
        
        # Build SQL query
        sql = """
            SELECT 
                ge.id,
                ge.vehicle_id,
                ge.geofence_id,
                ge.is_inside,
                ge.last_event_type,
                ge.last_event_at,
                ge.created_at,
                ge.updated_at,
                v.name as vehicle_name,
                v.vehicle_no,
                v.imei as vehicle_imei,
                g.title as geofence_title,
                g.type as geofence_type
            FROM geofence_events ge
            LEFT JOIN vehicles v ON ge.vehicle_id = v.id
            LEFT JOIN geofences g ON ge.geofence_id = g.id
            WHERE v.imei = %s
        """
        params = [imei]
        
        # Role-based access control
        if user.role.name != 'Super Admin':
            sql += """
                AND ge.vehicle_id IN (
                    SELECT uv.vehicle_id 
                    FROM user_vehicles uv 
                    WHERE uv.user_id = %s
                )
            """
            params.append(user.id)
        
        sql += " ORDER BY ge.last_event_at DESC"
        
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        # Format response
        events_data = []
        for row in results:
            event_data = {
                'id': row['id'],
                'vehicleId': row['vehicle_id'],
                'geofenceId': row['geofence_id'],
                'isInside': bool(row['is_inside']),
                'lastEventType': row['last_event_type'],
                'lastEventAt': row['last_event_at'].isoformat() if row['last_event_at'] else None,
                'createdAt': row['created_at'].isoformat() if row['created_at'] else None,
                'updatedAt': row['updated_at'].isoformat() if row['updated_at'] else None,
                'vehicle': {
                    'name': row['vehicle_name'],
                    'vehicleNo': row['vehicle_no'],
                    'imei': row['vehicle_imei']
                } if row['vehicle_name'] else None,
                'geofence': {
                    'title': row['geofence_title'],
                    'type': row['geofence_type']
                } if row['geofence_title'] else None
            }
            events_data.append(event_data)
        
        return success_response(events_data, 'Vehicle geofence events retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)