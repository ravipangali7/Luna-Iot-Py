"""
Vehicle Document Views
Handles CRUD operations for vehicle document records
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from datetime import datetime, timedelta

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from fleet.models import Vehicle, VehicleDocument, UserVehicle
from fleet.serializers.vehicle_document_serializers import (
    VehicleDocumentSerializer,
    VehicleDocumentCreateSerializer,
    VehicleDocumentUpdateSerializer,
    VehicleDocumentListSerializer,
    VehicleDocumentRenewSerializer
)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_vehicle_documents(request, imei):
    """Get all document records for a vehicle"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            has_access = vehicle.userVehicles.filter(user=user).exists() or \
                        vehicle.device.userDevices.filter(user=user).exists()
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        documents = VehicleDocument.objects.filter(vehicle=vehicle).order_by('-last_expire_date', '-created_at')
        serializer = VehicleDocumentListSerializer(documents, many=True)
        
        return success_response(serializer.data, 'Document records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
def create_vehicle_document(request, imei):
    """Create a new document record for a vehicle"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Handle multipart form data for image uploads
        data = {}
        files = {}
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            data['vehicle'] = vehicle.id
            data['title'] = request.POST.get('title', '')
            data['last_expire_date'] = request.POST.get('last_expire_date', '')
            expire_in_month_str = request.POST.get('expire_in_month', '')
            if expire_in_month_str:
                try:
                    data['expire_in_month'] = int(expire_in_month_str)
                except (ValueError, TypeError):
                    pass  # Let serializer handle validation
            data['remarks'] = request.POST.get('remarks', '')
            
            if 'document_image_one' in request.FILES:
                files['document_image_one'] = request.FILES['document_image_one']
            if 'document_image_two' in request.FILES:
                files['document_image_two'] = request.FILES['document_image_two']
        else:
            # JSON data
            import json
            data = json.loads(request.body) if request.body else {}
            data['vehicle'] = vehicle.id
        
        serializer = VehicleDocumentCreateSerializer(data=data)
        if serializer.is_valid():
            document = serializer.save(**files)
            response_serializer = VehicleDocumentSerializer(document)
            return success_response(response_serializer.data, 'Document record created successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT", "POST"])  # Accept both PUT and POST
@require_auth
def update_vehicle_document(request, imei, document_id):
    """Update a document record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get document record
        try:
            document = VehicleDocument.objects.get(id=document_id, vehicle=vehicle)
        except VehicleDocument.DoesNotExist:
            return error_response('Document record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Handle multipart form data for image uploads
        data = {}
        files = {}
        
        print(f"Request method: {request.method}")
        print(f"Content-Type: {request.content_type}")
        print(f"request.POST keys: {list(request.POST.keys())}")
        print(f"request.FILES keys: {list(request.FILES.keys())}")
        print(f"request.body length: {len(request.body) if request.body else 0}")
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # For POST requests, Django automatically parses multipart/form-data
            # For PUT requests, we need to manually parse (but we'll use POST for updates with files)
            print(f"Processing multipart/form-data - POST keys: {list(request.POST.keys())}, FILES keys: {list(request.FILES.keys())}")
            
            if 'title' in request.POST:
                data['title'] = request.POST.get('title')
            if 'last_expire_date' in request.POST:
                data['last_expire_date'] = request.POST.get('last_expire_date')
            if 'expire_in_month' in request.POST:
                expire_in_month_str = request.POST.get('expire_in_month')
                if expire_in_month_str:
                    try:
                        data['expire_in_month'] = int(expire_in_month_str)
                    except (ValueError, TypeError):
                        pass  # Let serializer handle validation
            if 'remarks' in request.POST:
                data['remarks'] = request.POST.get('remarks')
            
            if 'document_image_one' in request.FILES:
                files['document_image_one'] = request.FILES['document_image_one']
                print(f"Found document_image_one in FILES: {request.FILES['document_image_one'].name}")
            elif 'delete_image_one' in request.POST and request.POST.get('delete_image_one') == 'true':
                # Signal to delete image_one
                data['document_image_one'] = None
                print("Setting document_image_one to None for deletion")
                
            if 'document_image_two' in request.FILES:
                files['document_image_two'] = request.FILES['document_image_two']
                print(f"Found document_image_two in FILES: {request.FILES['document_image_two'].name}")
            elif 'delete_image_two' in request.POST and request.POST.get('delete_image_two') == 'true':
                # Signal to delete image_two
                data['document_image_two'] = None
                print("Setting document_image_two to None for deletion")
        else:
            # JSON data
            import json
            data = json.loads(request.body) if request.body else {}
            print(f"Parsed JSON data: {data}")
            # Handle image deletion in JSON (if document_image_one/document_image_two is explicitly null)
            if 'document_image_one' in data and data['document_image_one'] is None:
                # Image deletion requested
                pass  # Already set to None
            if 'document_image_two' in data and data['document_image_two'] is None:
                # Image deletion requested
                pass  # Already set to None
        
        # Debug: Print what we're about to save
        print(f"=== UPDATE DOCUMENT {document_id} ===")
        print(f"Files received: {list(files.keys())}")
        print(f"Data keys: {list(data.keys())}")
        print(f"Content-Type: {request.content_type}")
        
        serializer = VehicleDocumentUpdateSerializer(document, data=data, partial=True)
        if serializer.is_valid():
            print(f"Serializer is valid")
            print(f"Validated data keys: {list(serializer.validated_data.keys())}")
            
            # Save with files - DRF should handle file uploads automatically
            document = serializer.save(**files)
            print(f"After serializer.save() - image_one: {document.document_image_one}, image_two: {document.document_image_two}")
            
            # Handle image deletion explicitly after save
            # This ensures images are properly cleared when deletion is requested
            if 'document_image_one' in data and data['document_image_one'] is None:
                print(f"Clearing document_image_one for document {document_id}")
                document.document_image_one = None
                document.save(update_fields=['document_image_one'])
            if 'document_image_two' in data and data['document_image_two'] is None:
                print(f"Clearing document_image_two for document {document_id}")
                document.document_image_two = None
                document.save(update_fields=['document_image_two'])
            
            # If files were provided, ensure they're saved
            # Sometimes DRF doesn't update files properly, so we do it manually
            if 'document_image_one' in files:
                print(f"Manually updating document_image_one from file")
                document.document_image_one = files['document_image_one']
                document.save(update_fields=['document_image_one'])
            if 'document_image_two' in files:
                print(f"Manually updating document_image_two from file")
                document.document_image_two = files['document_image_two']
                document.save(update_fields=['document_image_two'])
            
            # Refresh from database to get updated image URLs
            document.refresh_from_db()
            print(f"Final - image_one: {document.document_image_one}, image_two: {document.document_image_two}")
            print(f"=== END UPDATE DOCUMENT ===")
            
            response_serializer = VehicleDocumentSerializer(document)
            return success_response(response_serializer.data, 'Document record updated successfully')
        else:
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
def delete_vehicle_document(request, imei, document_id):
    """Delete a document record"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get document record
        try:
            document = VehicleDocument.objects.get(id=document_id, vehicle=vehicle)
        except VehicleDocument.DoesNotExist:
            return error_response('Document record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        document.delete()
        return success_response(None, 'Document record deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def check_document_renewal_threshold(request, imei, document_id):
    """Check if document needs renewal based on 25% threshold"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get document record
        try:
            document = VehicleDocument.objects.get(id=document_id, vehicle=vehicle)
        except VehicleDocument.DoesNotExist:
            return error_response('Document record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access to vehicle
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            has_access = vehicle.userVehicles.filter(user=user).exists() or \
                        vehicle.device.userDevices.filter(user=user).exists()
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Calculate threshold: last_expire_date + (expire_in_month * 0.75 months)
        # Manual month calculation
        months_to_add = int(document.expire_in_month * 0.75)
        year = document.last_expire_date.year
        month = document.last_expire_date.month + months_to_add
        day = document.last_expire_date.day
        
        # Handle year overflow
        while month > 12:
            month -= 12
            year += 1
        
        threshold_date = datetime(year, month, day).date()
        current_date = datetime.now().date()
        needs_renewal = current_date >= threshold_date
        
        return success_response({
            'needs_renewal': needs_renewal,
            'current_date': current_date.isoformat(),
            'threshold_date': threshold_date.isoformat(),
            'last_expire_date': document.last_expire_date.isoformat(),
            'expire_in_month': document.expire_in_month
        }, 'Threshold check completed')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["PUT"])
@require_auth
def renew_vehicle_document(request, imei, document_id):
    """Renew a document by updating last_expire_date"""
    try:
        user = request.user
        
        # Get vehicle and check access
        try:
            vehicle = Vehicle.objects.get(imei=imei)
        except Vehicle.DoesNotExist:
            return error_response('Vehicle not found', HTTP_STATUS['NOT_FOUND'])
        
        # Get document record
        try:
            document = VehicleDocument.objects.get(id=document_id, vehicle=vehicle)
        except VehicleDocument.DoesNotExist:
            return error_response('Document record not found', HTTP_STATUS['NOT_FOUND'])
        
        # Check user access
        user_group = user.groups.first()
        has_access = False
        if user_group and user_group.name == 'Super Admin':
            has_access = True
        else:
            user_vehicle = vehicle.userVehicles.filter(user=user).first()
            has_access = user_vehicle and (user_vehicle.allAccess or user_vehicle.edit)
        
        if not has_access:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Parse request data
        import json
        data = json.loads(request.body) if request.body else {}
        
        serializer = VehicleDocumentRenewSerializer(data=data)
        if not serializer.is_valid():
            return error_response(serializer.errors, HTTP_STATUS['BAD_REQUEST'])
        
        # Renew document: Update last_expire_date = last_expire_date + expire_in_month months
        # Manual month calculation
        year = document.last_expire_date.year
        month = document.last_expire_date.month + document.expire_in_month
        day = document.last_expire_date.day
        
        # Handle year overflow
        while month > 12:
            month -= 12
            year += 1
        
        document.last_expire_date = datetime(year, month, day).date()
        document.save()
        
        response_serializer = VehicleDocumentSerializer(document)
        return success_response(response_serializer.data, 'Document renewed successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_owned_vehicle_documents(request):
    """Get all document records for all vehicles where user has isMain=True"""
    try:
        user = request.user
        
        # Get all vehicles where user has isMain=True
        user_group = user.groups.first()
        if user_group and user_group.name == 'Super Admin':
            # Super Admin can see all vehicles
            owned_vehicles = Vehicle.objects.all()
        else:
            # Get vehicles where user has isMain=True
            owned_vehicle_ids = UserVehicle.objects.filter(
                user=user,
                isMain=True
            ).values_list('vehicle_id', flat=True)
            owned_vehicles = Vehicle.objects.filter(id__in=owned_vehicle_ids)
        
        # Group documents by vehicle
        result = {}
        for vehicle in owned_vehicles:
            documents = VehicleDocument.objects.filter(vehicle=vehicle).order_by('-last_expire_date', '-created_at')
            if documents.exists():
                serializer = VehicleDocumentListSerializer(documents, many=True)
                result[str(vehicle.id)] = {
                    'vehicle_id': vehicle.id,
                    'vehicle_name': vehicle.name,
                    'vehicle_imei': vehicle.imei,
                    'documents': serializer.data
                }
        
        return success_response(result, 'All owned vehicle document records retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)

