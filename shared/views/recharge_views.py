from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
import json

from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.auth_decorators import require_auth, require_role
from api_common.constants.api_constants import HTTP_STATUS_CODES
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_exception

from shared.models import Recharge
from device.models import Device
from core.models import User


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_all_recharges(request):
    """
    Get all recharges
    """
    try:
        user = request.user
        
        # Super Admin: all access
        if user.role.name == 'Super Admin':
            recharges = Recharge.objects.select_related('device').all().order_by('-created_at')
        # Dealer: only view recharges for assigned devices
        elif user.role.name == 'Dealer':
            recharges = Recharge.objects.filter(
                device__userdevice__user=user
            ).select_related('device').distinct().order_by('-created_at')
        # Customer: no access to recharges
        else:
            return error_response('Access denied. Customers cannot view recharges', HTTP_STATUS_CODES['FORBIDDEN'])
        
        recharges_data = []
        for recharge in recharges:
            recharge_data = {
                'id': recharge.id,
                'deviceId': recharge.device.id,
                'deviceImei': recharge.device.imei,
                'deviceName': recharge.device.name,
                'amount': float(recharge.amount),
                'createdAt': recharge.created_at.isoformat() if recharge.created_at else None,
                'updatedAt': recharge.updated_at.isoformat() if recharge.updated_at else None
            }
            recharges_data.append(recharge_data)
        
        return success_response(recharges_data, 'Recharges retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve recharges')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_recharges_with_pagination(request):
    """
    Get recharges with pagination
    """
    try:
        user = request.user
        page = int(request.GET.get('page', 1))
        limit = int(request.GET.get('limit', 10))
        device_id = request.GET.get('deviceId')
        
        # Super Admin: all access
        if user.role.name == 'Super Admin':
            recharges_query = Recharge.objects.select_related('device').all()
        # Dealer: only view recharges for assigned devices
        elif user.role.name == 'Dealer':
            recharges_query = Recharge.objects.filter(
                device__userdevice__user=user
            ).select_related('device').distinct()
        # Customer: no access to recharges
        else:
            return error_response('Access denied. Customers cannot view recharges', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Filter by device ID if provided
        if device_id:
            recharges_query = recharges_query.filter(device_id=device_id)
        
        # Order by created_at descending
        recharges_query = recharges_query.order_by('-created_at')
        
        # Paginate
        paginator = Paginator(recharges_query, limit)
        page_obj = paginator.get_page(page)
        
        recharges_data = []
        for recharge in page_obj:
            recharge_data = {
                'id': recharge.id,
                'deviceId': recharge.device.id,
                'deviceImei': recharge.device.imei,
                'deviceName': recharge.device.name,
                'amount': float(recharge.amount),
                'createdAt': recharge.created_at.isoformat() if recharge.created_at else None,
                'updatedAt': recharge.updated_at.isoformat() if recharge.updated_at else None
            }
            recharges_data.append(recharge_data)
        
        result = {
            'recharges': recharges_data,
            'pagination': {
                'currentPage': page_obj.number,
                'totalPages': paginator.num_pages,
                'totalItems': paginator.count,
                'itemsPerPage': limit,
                'hasNext': page_obj.has_next(),
                'hasPrevious': page_obj.has_previous()
            }
        }
        
        return success_response(result, 'Recharges retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve recharges')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_recharge_by_id(request, id):
    """
    Get recharge by ID
    """
    try:
        user = request.user
        
        # Super Admin: can access any recharge
        if user.role.name == 'Super Admin':
            try:
                recharge = Recharge.objects.select_related('device').get(id=id)
            except Recharge.DoesNotExist:
                return error_response('Recharge not found', HTTP_STATUS_CODES['NOT_FOUND'])
        # Dealer: can only access recharges for assigned devices
        elif user.role.name == 'Dealer':
            try:
                recharge = Recharge.objects.filter(
                    id=id,
                    device__userdevice__user=user
                ).select_related('device').get()
            except Recharge.DoesNotExist:
                return error_response('Recharge not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        # Customer: no access to recharges
        else:
            return error_response('Access denied. Customers cannot view recharges', HTTP_STATUS_CODES['FORBIDDEN'])
        
        recharge_data = {
            'id': recharge.id,
            'deviceId': recharge.device.id,
            'deviceImei': recharge.device.imei,
            'deviceName': recharge.device.name,
            'amount': float(recharge.amount),
            'createdAt': recharge.created_at.isoformat() if recharge.created_at else None,
            'updatedAt': recharge.updated_at.isoformat() if recharge.updated_at else None
        }
        
        return success_response(recharge_data, 'Recharge retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve recharge')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_recharges_by_device_id(request, device_id):
    """
    Get recharges by device ID
    """
    try:
        user = request.user
        
        # Check if device exists and user has access
        if user.role.name == 'Super Admin':
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                return error_response('Device not found', HTTP_STATUS_CODES['NOT_FOUND'])
        elif user.role.name == 'Dealer':
            try:
                device = Device.objects.filter(
                    id=device_id,
                    userdevice__user=user
                ).get()
            except Device.DoesNotExist:
                return error_response('Device not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        else:
            return error_response('Access denied. Customers cannot view recharges', HTTP_STATUS_CODES['FORBIDDEN'])
        
        recharges = Recharge.objects.filter(device_id=device_id).order_by('-created_at')
        
        recharges_data = []
        for recharge in recharges:
            recharge_data = {
                'id': recharge.id,
                'deviceId': recharge.device.id,
                'deviceImei': recharge.device.imei,
                'deviceName': recharge.device.name,
                'amount': float(recharge.amount),
                'createdAt': recharge.created_at.isoformat() if recharge.created_at else None,
                'updatedAt': recharge.updated_at.isoformat() if recharge.updated_at else None
            }
            recharges_data.append(recharge_data)
        
        return success_response(recharges_data, 'Device recharges retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve device recharges')


@csrf_exempt
@require_http_methods(["POST"])
@require_auth
@require_role(['Super Admin', 'Dealer'])
def create_recharge(request):
    """
    Create new recharge
    """
    try:
        user = request.user
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['deviceId', 'amount']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        device_id = data['deviceId']
        amount = data['amount']
        
        # Validate amount
        try:
            amount = float(amount)
            if amount <= 0:
                return error_response('Amount must be a positive number', HTTP_STATUS_CODES['BAD_REQUEST'])
        except (ValueError, TypeError):
            return error_response('Amount must be a valid number', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Check if device exists and user has access
        if user.role.name == 'Super Admin':
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                return error_response('Device not found', HTTP_STATUS_CODES['NOT_FOUND'])
        elif user.role.name == 'Dealer':
            try:
                device = Device.objects.filter(
                    id=device_id,
                    userdevice__user=user
                ).get()
            except Device.DoesNotExist:
                return error_response('Device not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Check if device has phone number
        if not device.phone:
            return error_response('Device does not have a phone number for top-up', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Check if device has SIM type
        if not device.sim:
            return error_response('Device does not have SIM type information', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        print(f'Processing recharge: deviceId={device.id}, imei={device.imei}, phone={device.phone}, sim={device.sim}, amount={amount}, userId={user.id}, userRole={user.role.name}')
        
        # Process mobile top-up (you'll need to implement this service)
        try:
            # TODO: Implement mobile top-up service
            # topup_result = mobile_topup_service.process_topup(
            #     device.phone,
            #     amount,
            #     device.sim
            # )
            
            # For now, simulate successful top-up
            topup_result = {
                'success': True,
                'message': 'Top-up successful',
                'simType': device.sim,
                'reference': f'REF_{device.id}_{amount}',
                'statusCode': 200,
                'state': 'completed',
                'data': {
                    'CreditsConsumed': amount,
                    'CreditsAvailable': 1000 - amount,
                    'Id': f'TXN_{device.id}_{amount}'
                }
            }
        except Exception as topup_error:
            print(f'Top-up error: {topup_error}')
            return error_response(f'Top-up failed: {str(topup_error)}', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        print(f'Top-up result: {topup_result}')
        
        # Only create recharge record if top-up is successful
        if not topup_result.get('success', False):
            print(f'Top-up failed, not creating recharge record: {topup_result}')
            return error_response(f"Top-up failed: {topup_result.get('message', 'Unknown error')}", HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Create recharge record only after successful top-up
        with transaction.atomic():
            recharge = Recharge.objects.create(
                device=device,
                amount=amount
            )
        
        # Add top-up result to recharge data
        recharge_data = {
            'id': recharge.id,
            'deviceId': recharge.device.id,
            'deviceImei': recharge.device.imei,
            'deviceName': recharge.device.name,
            'amount': float(recharge.amount),
            'createdAt': recharge.created_at.isoformat() if recharge.created_at else None,
            'updatedAt': recharge.updated_at.isoformat() if recharge.updated_at else None,
            'topupResult': {
                'success': topup_result.get('success', False),
                'message': topup_result.get('message', ''),
                'simType': topup_result.get('simType', ''),
                'reference': topup_result.get('reference', ''),
                'statusCode': topup_result.get('statusCode', 0),
                'state': topup_result.get('state', ''),
                'creditsConsumed': topup_result.get('data', {}).get('CreditsConsumed', 0),
                'creditsAvailable': topup_result.get('data', {}).get('CreditsAvailable', 0),
                'transactionId': topup_result.get('data', {}).get('Id')
            }
        }
        
        print(f'Recharge created successfully after top-up: rechargeId={recharge.id}, deviceId={device.id}, amount={amount}, topupReference={topup_result.get("reference")}')
        
        return success_response(recharge_data, 'Recharge and top-up completed successfully', HTTP_STATUS_CODES['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to create recharge')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_recharge_stats(request, device_id):
    """
    Get recharge statistics for a device
    """
    try:
        user = request.user
        
        # Check if device exists and user has access
        if user.role.name == 'Super Admin':
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                return error_response('Device not found', HTTP_STATUS_CODES['NOT_FOUND'])
        elif user.role.name == 'Dealer':
            try:
                device = Device.objects.filter(
                    id=device_id,
                    userdevice__user=user
                ).get()
            except Device.DoesNotExist:
                return error_response('Device not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        else:
            return error_response('Access denied. Customers cannot view recharge statistics', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Get recharge statistics
        stats = Recharge.objects.filter(device_id=device_id).aggregate(
            total_recharges=Count('id'),
            total_amount=Sum('amount'),
            average_amount=Sum('amount') / Count('id')
        )
        
        # Get latest recharge
        latest_recharge = Recharge.objects.filter(device_id=device_id).order_by('-created_at').first()
        
        stats_data = {
            'deviceId': device_id,
            'deviceImei': device.imei,
            'deviceName': device.name,
            'totalRecharges': stats['total_recharges'] or 0,
            'totalAmount': float(stats['total_amount'] or 0),
            'averageAmount': float(stats['average_amount'] or 0),
            'latestRecharge': {
                'id': latest_recharge.id,
                'amount': float(latest_recharge.amount),
                'createdAt': latest_recharge.created_at.isoformat() if latest_recharge.created_at else None
            } if latest_recharge else None
        }
        
        return success_response(stats_data, 'Recharge statistics retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve recharge statistics')


@csrf_exempt
@require_http_methods(["GET"])
@require_auth
def get_total_recharge(request, device_id):
    """
    Get total recharge amount for a device
    """
    try:
        user = request.user
        
        # Check if device exists and user has access
        if user.role.name == 'Super Admin':
            try:
                device = Device.objects.get(id=device_id)
            except Device.DoesNotExist:
                return error_response('Device not found', HTTP_STATUS_CODES['NOT_FOUND'])
        elif user.role.name == 'Dealer':
            try:
                device = Device.objects.filter(
                    id=device_id,
                    userdevice__user=user
                ).get()
            except Device.DoesNotExist:
                return error_response('Device not found or access denied', HTTP_STATUS_CODES['NOT_FOUND'])
        else:
            return error_response('Access denied. Customers cannot view recharge totals', HTTP_STATUS_CODES['FORBIDDEN'])
        
        # Get total recharge amount
        total_amount = Recharge.objects.filter(device_id=device_id).aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        return success_response({'totalAmount': float(total_amount)}, 'Total recharge amount retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve total recharge amount')


@csrf_exempt
@require_http_methods(["DELETE"])
@require_auth
@require_role(['Super Admin'])
def delete_recharge(request, id):
    """
    Delete recharge (only Super Admin)
    """
    try:
        try:
            recharge = Recharge.objects.get(id=id)
        except Recharge.DoesNotExist:
            return error_response('Recharge not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        recharge.delete()
        
        return success_response(None, 'Recharge deleted successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to delete recharge')
