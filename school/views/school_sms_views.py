"""
School SMS Views
Handles school SMS management endpoints
"""
import json
import logging
from decimal import Decimal
from rest_framework.decorators import api_view
from django.core.paginator import Paginator
from django.db.models import Q
from school.models import SchoolSMS
from school.serializers import (
    SchoolSMSSerializer,
    SchoolSMSCreateSerializer,
    SchoolSMSListSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin, require_school_module_access
from school.models import SchoolSMS
from api_common.exceptions.api_exceptions import NotFoundError
from api_common.utils.sms_service import sms_service
from api_common.utils.sms_cost_utils import calculate_sms_cost
from finance.models import Wallet
from core.models import MySetting

logger = logging.getLogger(__name__)


@api_view(['GET'])
@require_auth
@api_response
def get_all_school_sms(request):
    """Get all school SMS with pagination and filtering"""
    try:
        search_query = request.GET.get('search', '').strip()
        institute_filter = request.GET.get('institute_id', '').strip()
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        
        school_sms = SchoolSMS.objects.select_related('institute').all()
        
        if search_query:
            school_sms = school_sms.filter(
                Q(message__icontains=search_query) |
                Q(institute__name__icontains=search_query)
            )
        
        if institute_filter:
            school_sms = school_sms.filter(institute_id=institute_filter)
        
        school_sms = school_sms.order_by('-created_at')
        
        paginator = Paginator(school_sms, page_size)
        page_obj = paginator.get_page(page)
        
        serializer = SchoolSMSListSerializer(page_obj.object_list, many=True)
        
        return success_response(
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School SMS retrieved successfully'),
            data={
                'school_sms': serializer.data,
                'pagination': {
                    'current_page': page_obj.number,
                    'total_pages': paginator.num_pages,
                    'total_items': paginator.count,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                }
            }
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_sms_by_id(request, sms_id):
    """Get school SMS by ID"""
    try:
        try:
            school_sms = SchoolSMS.objects.select_related('institute').get(id=sms_id)
        except SchoolSMS.DoesNotExist:
            raise NotFoundError("School SMS not found")
        
        serializer = SchoolSMSSerializer(school_sms)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School SMS retrieved successfully')
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_school_sms_by_institute(request, institute_id):
    """Get school SMS by institute"""
    try:
        school_sms = SchoolSMS.objects.select_related('institute').filter(
            institute_id=institute_id
        ).order_by('-created_at')
        
        serializer = SchoolSMSListSerializer(school_sms, many=True)
        
        return success_response(
            data=serializer.data,
            message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'School SMS retrieved successfully')
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['POST'])
@require_school_module_access()
@api_response
def create_school_sms(request):
    """Create new school SMS and send SMS to all phone numbers"""
    try:
        # Early validation: check if institute is 0 or missing before serializer
        institute_value = request.data.get('institute')
        if institute_value is None:
            return error_response(
                message="Institute is required",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        try:
            institute_id = int(institute_value)
            if institute_id == 0:
                return error_response(
                    message="Institute ID cannot be 0",
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
        except (ValueError, TypeError):
            return error_response(
                message="Institute must be a valid integer",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        serializer = SchoolSMSCreateSerializer(data=request.data)
        
        # #region agent log
        with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"school_sms_views.py:141","message":"Serializer validation result","data":{"is_valid":serializer.is_valid(),"errors":dict(serializer.errors) if not serializer.is_valid() else None},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        # #endregion
        
        if serializer.is_valid():
            # Additional validation: ensure institute is valid before saving
            institute_id = serializer.validated_data.get('institute')
            
            # #region agent log
            with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"school_sms_views.py:149","message":"Institute ID from validated_data","data":{"institute_id":institute_id,"type":str(type(institute_id))},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            
            if institute_id is None or institute_id == 0:
                return error_response(
                    message="Invalid institute ID. Institute is required and cannot be 0.",
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
            
            # #region agent log
            with open('c:\\Mine\\Projects\\Luna_IOT\\LUNA\\.cursor\\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"school_sms_views.py:157","message":"About to call serializer.save()","data":{"institute_id":institute_id},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            # #endregion
            
            school_sms = serializer.save()
            
            # Send SMS to all phone numbers
            phone_numbers = school_sms.phone_numbers if school_sms.phone_numbers else []
            message = school_sms.message
            sent_count = 0
            failed_count = 0
            sms_results = []
            
            if phone_numbers:
                # Get or create wallet for logged-in user
                wallet, created = Wallet.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': Decimal('0.00')}
                )
                
                # Get MySetting for SMS price and character price
                try:
                    my_setting = MySetting.objects.first()
                except Exception as e:
                    logger.warning(f"Error getting MySetting: {str(e)}")
                    my_setting = None
                
                # Determine SMS price: use wallet-specific price if available, otherwise use default from MySetting
                sms_price = wallet.sms_price
                if sms_price is None or sms_price == Decimal('0.00'):
                    if my_setting and my_setting.sms_price:
                        sms_price = Decimal(str(my_setting.sms_price))
                    else:
                        sms_price = Decimal('0.00')
                
                # Get SMS character price from MySetting (default: 160)
                sms_character_price = 160  # Default value
                if my_setting and my_setting.sms_character_price:
                    sms_character_price = int(my_setting.sms_character_price)
                
                # Calculate total cost based on character count
                total_cost, character_count, sms_parts = calculate_sms_cost(
                    message=message,
                    sms_price=sms_price,
                    sms_character_price=sms_character_price,
                    num_recipients=len(phone_numbers)
                )
                
                # Check if wallet balance is sufficient
                if wallet.balance < total_cost:
                    return error_response(
                        message=f"Insufficient wallet balance. Required: {total_cost}, Available: {wallet.balance}. Please top up your wallet first.",
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                
                # Deduct balance before sending SMS
                success = wallet.subtract_balance(
                    amount=total_cost,
                    description=f"School SMS to {len(phone_numbers)} recipients",
                    performed_by=request.user
                )
                
                if not success:
                    return error_response(
                        message="Failed to deduct from wallet balance. Please try again.",
                        status_code=HTTP_STATUS['INTERNAL_ERROR']
                    )
                
                logger.info(f"Deducted {total_cost} from wallet for user {request.user.id} before sending {len(phone_numbers)} SMS (Message: {character_count} chars, {sms_parts} SMS parts)")
                
                logger.info(f"Starting SMS sending for school SMS {school_sms.id} to {len(phone_numbers)} recipients")
                
                for phone_number in phone_numbers:
                    try:
                        # Clean phone number (remove spaces, etc.)
                        clean_phone = str(phone_number).strip()
                        if not clean_phone:
                            continue
                            
                        sms_result = sms_service.send_sms(clean_phone, message)
                        
                        if sms_result.get('success'):
                            sent_count += 1
                            logger.info(f"SMS sent successfully to {clean_phone} for school SMS {school_sms.id}")
                        else:
                            failed_count += 1
                            logger.warning(f"Failed to send SMS to {clean_phone} for school SMS {school_sms.id}: {sms_result.get('message')}")
                        
                        sms_results.append({
                            'phone_number': clean_phone,
                            'success': sms_result.get('success', False),
                            'message': sms_result.get('message', 'Unknown error')
                        })
                    except Exception as e:
                        failed_count += 1
                        logger.error(f"Error sending SMS to {phone_number} for school SMS {school_sms.id}: {str(e)}")
                        sms_results.append({
                            'phone_number': str(phone_number),
                            'success': False,
                            'message': str(e)
                        })
                
                logger.info(f"SMS sending completed for school SMS {school_sms.id}: {sent_count} sent, {failed_count} failed")
            else:
                logger.warning(f"No phone numbers provided for school SMS {school_sms.id}")
            
            response_serializer = SchoolSMSSerializer(school_sms)
            response_data = response_serializer.data
            
            # Add SMS sending results to response
            response_data['sms_sending_results'] = {
                'total_recipients': len(phone_numbers),
                'sent_count': sent_count,
                'failed_count': failed_count,
                'results': sms_results
            }
            
            message = SUCCESS_MESSAGES.get('DATA_CREATED', 'School SMS created successfully')
            if sent_count > 0:
                message = f"School SMS created and sent to {sent_count} recipient(s)"
                if failed_count > 0:
                    message += f", {failed_count} failed"
            
            return success_response(
                data=response_data,
                message=message,
                status_code=HTTP_STATUS['CREATED']
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except Exception as e:
        logger.error(f"Error creating school SMS: {str(e)}")
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['PUT'])
@require_school_module_access(model_class=SchoolSMS, id_param_name='sms_id')
@api_response
def update_school_sms(request, sms_id):
    """Update school SMS"""
    try:
        try:
            school_sms = SchoolSMS.objects.get(id=sms_id)
        except SchoolSMS.DoesNotExist:
            raise NotFoundError("School SMS not found")
        
        serializer = SchoolSMSCreateSerializer(school_sms, data=request.data)
        
        if serializer.is_valid():
            school_sms = serializer.save()
            response_serializer = SchoolSMSSerializer(school_sms)
            
            return success_response(
                data=response_serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_UPDATED', 'School SMS updated successfully')
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )


@api_view(['DELETE'])
@require_school_module_access(model_class=SchoolSMS, id_param_name='sms_id')
@api_response
def delete_school_sms(request, sms_id):
    """Delete school SMS"""
    try:
        try:
            school_sms = SchoolSMS.objects.get(id=sms_id)
        except SchoolSMS.DoesNotExist:
            raise NotFoundError("School SMS not found")
        
        institute_name = school_sms.institute.name
        school_sms.delete()
        
        return success_response(
            data={'id': sms_id},
            message=f"School SMS for '{institute_name}' deleted successfully"
        )
    except NotFoundError as e:
        return error_response(
            message=str(e),
            status_code=HTTP_STATUS['NOT_FOUND']
        )
    except Exception as e:
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data=str(e)
        )

