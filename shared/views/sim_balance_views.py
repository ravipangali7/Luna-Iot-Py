from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.core.paginator import Paginator
import os

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS
from api_common.utils.exception_utils import handle_api_exception

from shared.models import SimBalance
from shared.serializers.sim_balance_serializers import (
    SimBalanceSerializer, SimBalanceListSerializer, SimBalanceImportResponseSerializer
)
from shared.services.sim_balance_importer import SimBalanceImporter
from device.models import Device


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
@require_role(['Super Admin'])
def upload_sim_data(request):
    """
    Upload and import SIM data from CSV/XLSX file
    """
    try:
        if 'file' not in request.FILES:
            return error_response('No file provided', HTTP_STATUS['BAD_REQUEST'])
        
        uploaded_file = request.FILES['file']
        file_name = uploaded_file.name.lower()
        
        # Determine file type
        if file_name.endswith('.csv'):
            file_type = 'csv'
        elif file_name.endswith('.xlsx') or file_name.endswith('.xls'):
            file_type = 'xlsx'
        else:
            return error_response('Unsupported file type. Please upload CSV or XLSX file.', HTTP_STATUS['BAD_REQUEST'])
        
        # Validate file size (max 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            return error_response('File size exceeds 10MB limit', HTTP_STATUS['BAD_REQUEST'])
        
        # Import data
        importer = SimBalanceImporter()
        result = importer.import_sim_data(uploaded_file, file_type)
        
        if result.get('success', False):
            return success_response(result, 'SIM data imported successfully')
        else:
            return error_response(
                result.get('error', 'Import failed'),
                HTTP_STATUS['BAD_REQUEST'],
                data=result
            )
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_sim_balances(request):
    """
    Get all SIM balances
    """
    try:
        user = request.user
        
        # Super Admin: all access
        if user.role.name == 'Super Admin':
            sim_balances = SimBalance.objects.select_related('device').prefetch_related('free_resources').all().order_by('-created_at')
        # Dealer: only view SIM balances for assigned devices
        elif user.role.name == 'Dealer':
            sim_balances = SimBalance.objects.filter(
                device__userdevice__user=user
            ).select_related('device').prefetch_related('free_resources').distinct().order_by('-created_at')
        # Customer: no access
        else:
            return error_response('Access denied. Customers cannot view SIM balances', HTTP_STATUS['FORBIDDEN'])
        
        serializer = SimBalanceSerializer(sim_balances, many=True)
        return success_response(serializer.data, 'SIM balances retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_sim_balances_with_pagination(request):
    """
    Get SIM balances with pagination
    """
    try:
        user = request.user
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        
        # Apply filters
        phone_number = request.GET.get('phone_number')
        state = request.GET.get('state')
        device_id = request.GET.get('device_id')
        min_balance = request.GET.get('min_balance')
        max_balance = request.GET.get('max_balance')
        
        # Super Admin: all access
        if user.role.name == 'Super Admin':
            sim_balances_query = SimBalance.objects.select_related('device').prefetch_related('free_resources').all()
        # Dealer: only view SIM balances for assigned devices
        elif user.role.name == 'Dealer':
            sim_balances_query = SimBalance.objects.filter(
                device__userdevice__user=user
            ).select_related('device').prefetch_related('free_resources').distinct()
        # Customer: no access
        else:
            return error_response('Access denied. Customers cannot view SIM balances', HTTP_STATUS['FORBIDDEN'])
        
        # Apply filters
        if phone_number:
            sim_balances_query = sim_balances_query.filter(phone_number__icontains=phone_number)
        if state:
            sim_balances_query = sim_balances_query.filter(state=state)
        if device_id:
            sim_balances_query = sim_balances_query.filter(device_id=device_id)
        if min_balance:
            sim_balances_query = sim_balances_query.filter(balance__gte=min_balance)
        if max_balance:
            sim_balances_query = sim_balances_query.filter(balance__lte=max_balance)
        
        # Order by created_at descending
        sim_balances_query = sim_balances_query.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(sim_balances_query, limit)
        page_obj = paginator.get_page(page)
        
        serializer = SimBalanceSerializer(page_obj, many=True)
        
        result = {
            'sim_balances': serializer.data,
            'pagination': {
                'page': page,
                'limit': limit,
                'total': paginator.count,
                'pages': paginator.num_pages
            }
        }
        
        return success_response(result, 'SIM balances retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_sim_balance_by_id(request, id):
    """
    Get SIM balance by ID
    """
    try:
        user = request.user
        
        # Super Admin: can access any SIM balance
        if user.role.name == 'Super Admin':
            try:
                sim_balance = SimBalance.objects.select_related('device').prefetch_related('free_resources').get(id=id)
            except SimBalance.DoesNotExist:
                return error_response('SIM balance not found', HTTP_STATUS['NOT_FOUND'])
        # Dealer: can only access SIM balances for assigned devices
        elif user.role.name == 'Dealer':
            try:
                sim_balance = SimBalance.objects.filter(
                    id=id,
                    device__userdevice__user=user
                ).select_related('device').prefetch_related('free_resources').get()
            except SimBalance.DoesNotExist:
                return error_response('SIM balance not found or access denied', HTTP_STATUS['NOT_FOUND'])
        # Customer: no access
        else:
            return error_response('Access denied. Customers cannot view SIM balances', HTTP_STATUS['FORBIDDEN'])
        
        serializer = SimBalanceSerializer(sim_balance)
        return success_response(serializer.data, 'SIM balance retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_sim_balance_by_device(request, device_id):
    """
    Get SIM balance by device ID
    """
    try:
        user = request.user
        
        # Check if device exists and user has access
        if user.role.name == 'Super Admin':
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                return error_response('Device not found', HTTP_STATUS['NOT_FOUND'])
        elif user.role.name == 'Dealer':
            try:
                device = Device.objects.filter(
                    id=device_id,
                    userdevice__user=user
                ).get()
            except Device.DoesNotExist:
                return error_response('Device not found or access denied', HTTP_STATUS['NOT_FOUND'])
        else:
            return error_response('Access denied', HTTP_STATUS['FORBIDDEN'])
        
        # Get SIM balance for device
        try:
            sim_balance = SimBalance.objects.select_related('device').prefetch_related('free_resources').get(device_id=device_id)
        except SimBalance.DoesNotExist:
            return error_response('SIM balance not found for this device', HTTP_STATUS['NOT_FOUND'])
        
        serializer = SimBalanceSerializer(sim_balance)
        return success_response(serializer.data, 'SIM balance retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_sim_balance_by_phone(request, phone):
    """
    Get SIM balance by phone number
    """
    try:
        user = request.user
        
        # Super Admin: can access any SIM balance
        if user.role.name == 'Super Admin':
            try:
                sim_balance = SimBalance.objects.select_related('device').prefetch_related('free_resources').get(phone_number=phone)
            except SimBalance.DoesNotExist:
                return error_response('SIM balance not found', HTTP_STATUS['NOT_FOUND'])
        # Dealer: can only access SIM balances for assigned devices
        elif user.role.name == 'Dealer':
            try:
                sim_balance = SimBalance.objects.filter(
                    phone_number=phone,
                    device__userdevice__user=user
                ).select_related('device').prefetch_related('free_resources').get()
            except SimBalance.DoesNotExist:
                return error_response('SIM balance not found or access denied', HTTP_STATUS['NOT_FOUND'])
        # Customer: no access
        else:
            return error_response('Access denied. Customers cannot view SIM balances', HTTP_STATUS['FORBIDDEN'])
        
        serializer = SimBalanceSerializer(sim_balance)
        return success_response(serializer.data, 'SIM balance retrieved successfully')
    
    except Exception as e:
        return handle_api_exception(e)


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_sim_balance(request, id):
    """
    Delete SIM balance and related resources
    """
    try:
        try:
            sim_balance = SimBalance.objects.get(id=id)
        except SimBalance.DoesNotExist:
            return error_response('SIM balance not found', HTTP_STATUS['NOT_FOUND'])
        
        with transaction.atomic():
            sim_balance.delete()
        
        return success_response(None, 'SIM balance deleted successfully')
    
    except Exception as e:
        return handle_api_exception(e)

