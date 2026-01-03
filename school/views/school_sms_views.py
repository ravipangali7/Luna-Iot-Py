"""
School SMS Views
Handles school SMS management endpoints
"""
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
from api_common.exceptions.api_exceptions import NotFoundError
from api_common.utils.sms_service import sms_service
from api_common.utils.sms_cost_utils import calculate_sms_cost
from finance.models import Wallet
from core.models import MySetting, Institute

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
def create_school_sms(request, institute_id):
    """Create new school SMS and send SMS to all phone numbers"""
    try:
        # 1. Validate institute_id from URL parameter (already validated by URL router, but add safety check)
        if institute_id <= 0:
            return error_response(
                message="Institute ID must be a positive integer",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # 2. Fetch Institute instance
        try:
            institute = Institute.objects.get(id=institute_id)
        except Institute.DoesNotExist:
            return error_response(
                message=f"Institute with ID {institute_id} does not exist",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # 3. Prepare data for serializer (explicitly filter out unwanted fields)
        serializer_data = {
            'message': request.data.get('message'),
            'phone_numbers': request.data.get('phone_numbers')
        }
        
        # Explicitly remove any id or institute fields if they exist
        # (defensive programming - shouldn't be needed but ensures safety)
        if 'id' in request.data:
            print(f"[WARNING] Request data contains 'id' field: {request.data.get('id')} - ignoring")
        if 'institute' in request.data:
            print(f"[WARNING] Request data contains 'institute' field: {request.data.get('institute')} - ignoring (using URL parameter)")
        
        # 4. Validate message and phone_numbers using serializer
        serializer = SchoolSMSCreateSerializer(data=serializer_data)
        
        if not serializer.is_valid():
            return error_response(
                message=ERROR_MESSAGES.get('VALIDATION_ERROR', 'Validation error'),
                data=serializer.errors,
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        # 5. Create SchoolSMS directly with Institute instance
        # Use manual instance creation to avoid any automatic field processing
        print(f"[INFO] Creating SchoolSMS: institute_id={institute.id}, message_length={len(serializer.validated_data['message'])}, phone_count={len(serializer.validated_data['phone_numbers'])}")
        print(f"[DEBUG] Request data keys: {list(request.data.keys())}")
        print(f"[DEBUG] Request data: {request.data}")
        
        # Double-check that institute is valid and has a valid id
        if not institute or not hasattr(institute, 'id') or institute.id <= 0:
            print(f"[ERROR] Invalid institute: {institute}, id: {getattr(institute, 'id', 'NO_ID')}")
            return error_response(
                message="Invalid institute instance",
                status_code=HTTP_STATUS['BAD_REQUEST']
            )
        
        print(f"[DEBUG] Institute validation passed - institute.id: {institute.id}, type: {type(institute.id)}")
        
        # Use objects.create() with explicit fields only - this is the safest way
        # Django will handle the id field automatically
        try:
            print(f"[DEBUG] About to create SchoolSMS with: institute_id={institute.id}, message length={len(serializer.validated_data['message'])}, phone_count={len(serializer.validated_data['phone_numbers'])}")
            school_sms = SchoolSMS.objects.create(
                institute_id=institute.id,  # Use institute_id instead of institute to be explicit
                message=serializer.validated_data['message'],
                phone_numbers=serializer.validated_data['phone_numbers']
            )
            print(f"[INFO] SchoolSMS created successfully with id: {school_sms.id}")
        except Exception as create_error:
            print(f"[ERROR] Error during SchoolSMS.objects.create(): {str(create_error)}")
            print(f"[ERROR] Exception type: {type(create_error)}")
            import traceback
            print(f"[ERROR] Full traceback:\n{traceback.format_exc()}")
            raise
        
        # 6. Send SMS to all phone numbers
        phone_numbers = school_sms.phone_numbers if school_sms.phone_numbers else []
        message = school_sms.message
        sent_count = 0
        failed_count = 0
        sms_results = []
        
        print(f"[DEBUG] After SchoolSMS creation - phone_numbers count: {len(phone_numbers)}")
        
        if phone_numbers:
            # Validate and fix user.id before Wallet operations
            print(f"[DEBUG] About to get/create wallet for user.id: {request.user.id}")
            if not hasattr(request.user, 'id') or not request.user.id or request.user.id <= 0:
                print(f"[WARNING] Invalid user.id: {getattr(request.user, 'id', 'NO_ID_ATTR')} - attempting to re-fetch user")
                
                # Re-fetch user from database using phone and token from headers
                phone = (
                    request.META.get('HTTP_X_PHONE') or
                    request.META.get('X-PHONE') or
                    request.META.get('x-phone') or
                    (request.headers.get('X-PHONE') if hasattr(request, 'headers') else None)
                )
                token = (
                    request.META.get('HTTP_X_TOKEN') or
                    request.META.get('X-TOKEN') or
                    request.META.get('x-token') or
                    (request.headers.get('X-TOKEN') if hasattr(request, 'headers') else None)
                )
                
                if phone and token:
                    try:
                        from core.models.user import User
                        user = User.objects.get(phone=phone)
                        if user.token == token and user.is_active:
                            request.user = user
                            print(f"[INFO] User re-fetched successfully: user.id={user.id}")
                        else:
                            print(f"[ERROR] Token mismatch or user inactive after re-fetch")
                            return error_response(
                                message="Invalid user authentication. Please log in again.",
                                status_code=HTTP_STATUS.get('UNAUTHORIZED', 401)
                            )
                    except User.DoesNotExist:
                        print(f"[ERROR] User not found with phone: {phone}")
                        return error_response(
                            message="User not found. Please log in again.",
                            status_code=HTTP_STATUS.get('UNAUTHORIZED', 401)
                        )
                    except Exception as e:
                        print(f"[ERROR] Error re-fetching user: {str(e)}")
                        import traceback
                        print(f"[ERROR] Re-fetch traceback:\n{traceback.format_exc()}")
                        return error_response(
                            message="Authentication error. Please log in again.",
                            status_code=HTTP_STATUS.get('UNAUTHORIZED', 401)
                        )
                else:
                    print(f"[ERROR] Cannot re-fetch user - missing phone/token headers")
                    return error_response(
                        message="Invalid user ID. Please ensure you are properly authenticated.",
                        status_code=HTTP_STATUS['BAD_REQUEST']
                    )
                
                # Verify user.id is now valid
                if not request.user.id or request.user.id <= 0:
                    print(f"[ERROR] User.id is still invalid after re-fetch: {request.user.id}")
                    return error_response(
                        message="Invalid user ID. Please log in again.",
                        status_code=HTTP_STATUS.get('UNAUTHORIZED', 401)
                    )
            
            # Get or create wallet for logged-in user
            try:
                print(f"[DEBUG] Calling Wallet.objects.get_or_create for user.id: {request.user.id}")
                wallet, created = Wallet.objects.get_or_create(
                    user=request.user,
                    defaults={'balance': Decimal('0.00')}
                )
                print(f"[INFO] Wallet retrieved/created: id={wallet.id if hasattr(wallet, 'id') else 'NO_ID'}, created={created}")
            except Exception as wallet_error:
                print(f"[ERROR] Wallet get_or_create failed: {str(wallet_error)}")
                print(f"[ERROR] Exception type: {type(wallet_error)}")
                import traceback
                print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
                raise
            
            # Get MySetting for SMS price and character price
            print(f"[DEBUG] About to get MySetting")
            try:
                my_setting = MySetting.objects.first()
                print(f"[DEBUG] MySetting retrieved: id={my_setting.id if my_setting else 'None'}")
            except Exception as e:
                print(f"[WARNING] Error getting MySetting: {str(e)}")
                import traceback
                print(f"[WARNING] MySetting traceback:\n{traceback.format_exc()}")
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
            print(f"[DEBUG] About to subtract balance: {total_cost} from wallet.id: {wallet.id}")
            print(f"[DEBUG] performed_by user.id: {request.user.id if hasattr(request.user, 'id') else 'NO_ID'}")
            try:
                success = wallet.subtract_balance(
                    amount=total_cost,
                    description=f"School SMS to {len(phone_numbers)} recipients",
                    performed_by=request.user
                )
                print(f"[INFO] subtract_balance completed: success={success}")
            except Exception as balance_error:
                print(f"[ERROR] subtract_balance failed: {str(balance_error)}")
                print(f"[ERROR] Exception type: {type(balance_error)}")
                import traceback
                print(f"[ERROR] Traceback:\n{traceback.format_exc()}")
                raise
            
            if not success:
                return error_response(
                    message="Failed to deduct from wallet balance. Please try again.",
                    status_code=HTTP_STATUS['INTERNAL_ERROR']
                )
            
            print(f"[INFO] Deducted {total_cost} from wallet for user {request.user.id} before sending {len(phone_numbers)} SMS (Message: {character_count} chars, {sms_parts} SMS parts)")
            
            print(f"[INFO] Starting SMS sending for school SMS {school_sms.id} to {len(phone_numbers)} recipients")
            
            for phone_number in phone_numbers:
                try:
                    # Clean phone number (remove spaces, etc.)
                    clean_phone = str(phone_number).strip()
                    if not clean_phone:
                        continue
                        
                    sms_result = sms_service.send_sms(clean_phone, message)
                    
                    if sms_result.get('success'):
                        sent_count += 1
                        print(f"[INFO] SMS sent successfully to {clean_phone} for school SMS {school_sms.id}")
                    else:
                        failed_count += 1
                        print(f"[WARNING] Failed to send SMS to {clean_phone} for school SMS {school_sms.id}: {sms_result.get('message')}")
                    
                    sms_results.append({
                        'phone_number': clean_phone,
                        'success': sms_result.get('success', False),
                        'message': sms_result.get('message', 'Unknown error')
                    })
                except Exception as e:
                    failed_count += 1
                    print(f"[ERROR] Error sending SMS to {phone_number} for school SMS {school_sms.id}: {str(e)}")
                    sms_results.append({
                        'phone_number': str(phone_number),
                        'success': False,
                        'message': str(e)
                    })
            
            print(f"[INFO] SMS sending completed for school SMS {school_sms.id}: {sent_count} sent, {failed_count} failed")
        else:
            print(f"[WARNING] No phone numbers provided for school SMS {school_sms.id}")
        
        # Build response (regardless of whether phone numbers exist)
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
    except Exception as e:
        print(f"[ERROR] Error creating school SMS: {str(e)}")
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

