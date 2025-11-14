"""
Phone Call Campaign Views
Handles all campaign management endpoints
"""
import json
from rest_framework.decorators import api_view
from django.http import HttpResponse
from phone_call.services.tingting_service import tingting_service
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth


# Voice Models
@api_view(['GET'])
@require_auth
@api_response
def get_voice_models(request):
    """Get available voice models"""
    try:
        result = tingting_service.get_voice_models()
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Voice models retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve voice models'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


# Phone Numbers
@api_view(['GET'])
@require_auth
@api_response
def get_active_phone_numbers(request):
    """Get active phone numbers"""
    try:
        result = tingting_service.get_active_phone_numbers()
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Active phone numbers retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve phone numbers'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


# Campaigns
@api_view(['GET'])
@require_auth
@api_response
def get_campaigns(request):
    """Get all campaigns with optional pagination"""
    try:
        page = request.GET.get('page')
        page_num = int(page) if page and page.isdigit() else None
        
        result = tingting_service.get_campaigns(page=page_num)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Campaigns retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve campaigns'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_campaign(request, campaign_id):
    """Get campaign by ID"""
    try:
        result = tingting_service.get_campaign(campaign_id)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Campaign retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve campaign'),
                status_code=result.get('status_code', HTTP_STATUS['NOT_FOUND'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def create_campaign(request):
    """Create a new campaign"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.create_campaign(data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('CREATED', 'Campaign created successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to create campaign'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def update_campaign(request, campaign_id):
    """Update an existing campaign"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.update_campaign(campaign_id, data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Campaign updated successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to update campaign'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_campaign(request, campaign_id):
    """Delete a campaign"""
    try:
        result = tingting_service.delete_campaign(campaign_id)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DELETED', 'Campaign deleted successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to delete campaign'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_campaign_details(request, campaign_id):
    """Get campaign details (contact list)"""
    try:
        page = request.GET.get('page')
        page_num = int(page) if page and page.isdigit() else None
        
        result = tingting_service.get_campaign_details(campaign_id, page=page_num)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Campaign details retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve campaign details'),
                status_code=result.get('status_code', HTTP_STATUS['NOT_FOUND'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def run_campaign(request, campaign_id):
    """Run/execute a campaign immediately"""
    try:
        result = tingting_service.run_campaign(campaign_id)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Campaign execution started')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to run campaign'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
def download_report(request, campaign_id):
    """Download campaign report as CSV"""
    try:
        result = tingting_service.download_report(campaign_id)
        if result['success']:
            response = HttpResponse(
                result['data']['content'],
                content_type=result['data']['content_type']
            )
            response['Content-Disposition'] = f'attachment; filename="{result["data"]["filename"]}"'
            return response
        else:
            return error_response(
                message=result.get('error', 'Failed to download report'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


# Contacts
@api_view(['POST'])
@require_auth
@api_response
def add_contact(request, campaign_id):
    """Add individual contact to campaign"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.add_contact(campaign_id, data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('CREATED', 'Contact added successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to add contact'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def add_bulk_contacts(request, campaign_id):
    """Add bulk contacts to campaign via file upload"""
    try:
        if 'file' not in request.FILES:
            return error_response(
                message='No file provided',
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        uploaded_file = request.FILES['file']
        file_content = uploaded_file.read()
        file_name = uploaded_file.name
        
        result = tingting_service.add_bulk_contacts(campaign_id, file_name, file_content)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('CREATED', 'Bulk contacts added successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to add bulk contacts'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_auth
@api_response
def delete_contact(request, contact_id):
    """Delete a contact"""
    try:
        result = tingting_service.delete_contact(contact_id)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DELETED', 'Contact deleted successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to delete contact'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_contact_info(request, contact_id):
    """Get contact information"""
    try:
        result = tingting_service.get_contact_info(contact_id)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Contact information retrieved successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to retrieve contact information'),
                status_code=result.get('status_code', HTTP_STATUS['NOT_FOUND'])
            )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PATCH'])
@require_auth
@api_response
def update_contact_attributes(request, contact_id):
    """Update contact attributes"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.update_contact_attributes(contact_id, data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Contact attributes updated successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to update contact attributes'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def update_contact(request, contact_id):
    """Update contact"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.update_contact(contact_id, data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Contact updated successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to update contact'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


# Testing
@api_view(['POST'])
@require_auth
@api_response
def test_voice(request):
    """Test voice synthesis"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.test_voice(data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Voice test completed successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to test voice'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_auth
@api_response
def demo_call(request):
    """Make a demo call"""
    try:
        data = json.loads(request.body) if request.body else {}
        
        result = tingting_service.demo_call(data)
        if result['success']:
            return success_response(
                data=result['data'],
                message=SUCCESS_MESSAGES.get('UPDATED', 'Demo call initiated successfully')
            )
        else:
            return error_response(
                message=result.get('error', 'Failed to initiate demo call'),
                status_code=result.get('status_code', HTTP_STATUS['BAD_REQUEST'])
            )
    except json.JSONDecodeError:
        return error_response(
            message='Invalid JSON in request body',
            status_code=HTTP_STATUS['BAD_REQUEST']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )

