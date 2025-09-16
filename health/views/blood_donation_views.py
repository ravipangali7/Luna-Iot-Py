from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
import json

from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import HTTP_STATUS_CODES
from api_common.utils.validation_utils import validate_required_fields
from api_common.utils.exception_utils import handle_exception

from health.models import BloodDonation


@csrf_exempt
@require_http_methods(["GET"])
def get_all_blood_donations(request):
    """
    Get all blood donations
    """
    try:
        apply_type = request.GET.get('applyType')
        blood_group = request.GET.get('bloodGroup')
        search = request.GET.get('search')
        
        blood_donations_query = BloodDonation.objects.all()
        
        # Apply filters
        if search:
            blood_donations_query = blood_donations_query.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(address__icontains=search)
            )
        
        if apply_type:
            blood_donations_query = blood_donations_query.filter(apply_type=apply_type)
        
        if blood_group:
            blood_donations_query = blood_donations_query.filter(blood_group=blood_group)
        
        blood_donations = blood_donations_query.order_by('-created_at')
        
        blood_donations_data = []
        for blood_donation in blood_donations:
            blood_donation_data = {
                'id': blood_donation.id,
                'name': blood_donation.name,
                'phone': blood_donation.phone,
                'address': blood_donation.address,
                'bloodGroup': blood_donation.blood_group,
                'applyType': blood_donation.apply_type,
                'status': blood_donation.status,
                'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
                'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
                'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
            }
            blood_donations_data.append(blood_donation_data)
        
        return success_response(blood_donations_data, 'Blood donations retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve blood donations')


@csrf_exempt
@require_http_methods(["GET"])
def get_blood_donation_by_id(request, id):
    """
    Get blood donation by ID
    """
    try:
        try:
            blood_donation = BloodDonation.objects.get(id=id)
        except BloodDonation.DoesNotExist:
            return error_response('Blood donation not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        blood_donation_data = {
            'id': blood_donation.id,
            'name': blood_donation.name,
            'phone': blood_donation.phone,
            'address': blood_donation.address,
            'bloodGroup': blood_donation.blood_group,
            'applyType': blood_donation.apply_type,
            'status': blood_donation.status,
            'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
            'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
            'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
        }
        
        return success_response(blood_donation_data, 'Blood donation retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve blood donation')


@csrf_exempt
@require_http_methods(["POST"])
def create_blood_donation(request):
    """
    Create new blood donation
    """
    try:
        data = json.loads(request.body)
        
        # Validate required fields
        required_fields = ['name', 'phone', 'address', 'bloodGroup', 'applyType']
        validation_error = validate_required_fields(data, required_fields)
        if validation_error:
            return validation_error
        
        name = data['name'].strip()
        phone = data['phone'].strip()
        address = data['address'].strip()
        blood_group = data['bloodGroup'].strip()
        apply_type = data['applyType'].strip()
        status = data.get('status', False)
        last_donated_at = data.get('lastDonatedAt')
        
        # Validate apply type
        if apply_type not in ['need', 'donate']:
            return error_response('Apply type must be either "need" or "donate"', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Validate blood group
        valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in valid_blood_groups:
            return error_response('Invalid blood group', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Create blood donation
        blood_donation = BloodDonation.objects.create(
            name=name,
            phone=phone,
            address=address,
            blood_group=blood_group,
            apply_type=apply_type,
            status=status,
            last_donated_at=last_donated_at
        )
        
        blood_donation_data = {
            'id': blood_donation.id,
            'name': blood_donation.name,
            'phone': blood_donation.phone,
            'address': blood_donation.address,
            'bloodGroup': blood_donation.blood_group,
            'applyType': blood_donation.apply_type,
            'status': blood_donation.status,
            'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
            'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
            'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
        }
        
        return success_response(blood_donation_data, 'Blood donation created successfully', HTTP_STATUS_CODES['CREATED'])
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to create blood donation')


@csrf_exempt
@require_http_methods(["PUT"])
def update_blood_donation(request, id):
    """
    Update blood donation
    """
    try:
        data = json.loads(request.body)
        
        # Get blood donation
        try:
            blood_donation = BloodDonation.objects.get(id=id)
        except BloodDonation.DoesNotExist:
            return error_response('Blood donation not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Validate apply type if provided
        if 'applyType' in data and data['applyType'] not in ['need', 'donate']:
            return error_response('Apply type must be either "need" or "donate"', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Validate blood group if provided
        if 'bloodGroup' in data:
            valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
            if data['bloodGroup'] not in valid_blood_groups:
                return error_response('Invalid blood group', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        # Update blood donation
        if 'name' in data:
            blood_donation.name = data['name'].strip()
        if 'phone' in data:
            blood_donation.phone = data['phone'].strip()
        if 'address' in data:
            blood_donation.address = data['address'].strip()
        if 'bloodGroup' in data:
            blood_donation.blood_group = data['bloodGroup'].strip()
        if 'applyType' in data:
            blood_donation.apply_type = data['applyType'].strip()
        if 'status' in data:
            blood_donation.status = data['status']
        if 'lastDonatedAt' in data:
            blood_donation.last_donated_at = data['lastDonatedAt']
        
        blood_donation.save()
        
        blood_donation_data = {
            'id': blood_donation.id,
            'name': blood_donation.name,
            'phone': blood_donation.phone,
            'address': blood_donation.address,
            'bloodGroup': blood_donation.blood_group,
            'applyType': blood_donation.apply_type,
            'status': blood_donation.status,
            'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
            'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
            'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
        }
        
        return success_response(blood_donation_data, 'Blood donation updated successfully')
    
    except json.JSONDecodeError:
        return error_response('Invalid JSON data', HTTP_STATUS_CODES['BAD_REQUEST'])
    except Exception as e:
        return handle_exception(e, 'Failed to update blood donation')


@csrf_exempt
@require_http_methods(["DELETE"])
def delete_blood_donation(request, id):
    """
    Delete blood donation
    """
    try:
        # Get blood donation
        try:
            blood_donation = BloodDonation.objects.get(id=id)
        except BloodDonation.DoesNotExist:
            return error_response('Blood donation not found', HTTP_STATUS_CODES['NOT_FOUND'])
        
        # Delete blood donation
        blood_donation.delete()
        
        return success_response(None, 'Blood donation deleted successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to delete blood donation')


@csrf_exempt
@require_http_methods(["GET"])
def get_blood_donations_by_type(request, type):
    """
    Get blood donations by apply type
    """
    try:
        if type not in ['need', 'donate']:
            return error_response('Invalid apply type. Must be "need" or "donate"', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        blood_donations = BloodDonation.objects.filter(apply_type=type).order_by('-created_at')
        
        blood_donations_data = []
        for blood_donation in blood_donations:
            blood_donation_data = {
                'id': blood_donation.id,
                'name': blood_donation.name,
                'phone': blood_donation.phone,
                'address': blood_donation.address,
                'bloodGroup': blood_donation.blood_group,
                'applyType': blood_donation.apply_type,
                'status': blood_donation.status,
                'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
                'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
                'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
            }
            blood_donations_data.append(blood_donation_data)
        
        return success_response(blood_donations_data, f'{type} blood donations retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve blood donations by type')


@csrf_exempt
@require_http_methods(["GET"])
def get_blood_donations_by_blood_group(request, blood_group):
    """
    Get blood donations by blood group
    """
    try:
        valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
        if blood_group not in valid_blood_groups:
            return error_response('Invalid blood group', HTTP_STATUS_CODES['BAD_REQUEST'])
        
        blood_donations = BloodDonation.objects.filter(blood_group=blood_group).order_by('-created_at')
        
        blood_donations_data = []
        for blood_donation in blood_donations:
            blood_donation_data = {
                'id': blood_donation.id,
                'name': blood_donation.name,
                'phone': blood_donation.phone,
                'address': blood_donation.address,
                'bloodGroup': blood_donation.blood_group,
                'applyType': blood_donation.apply_type,
                'status': blood_donation.status,
                'lastDonatedAt': blood_donation.last_donated_at.isoformat() if blood_donation.last_donated_at else None,
                'createdAt': blood_donation.created_at.isoformat() if blood_donation.created_at else None,
                'updatedAt': blood_donation.updated_at.isoformat() if blood_donation.updated_at else None
            }
            blood_donations_data.append(blood_donation_data)
        
        return success_response(blood_donations_data, f'Blood donations for {blood_group} retrieved successfully')
    
    except Exception as e:
        return handle_exception(e, 'Failed to retrieve blood donations by blood group')
