"""
Settings Views
Handles system settings management endpoints
Super Admin only
"""
from rest_framework.decorators import api_view
from core.models import MySetting
from core.serializers.my_setting_serializers import (
    MySettingSerializer,
    MySettingUpdateSerializer
)
from api_common.utils.response_utils import success_response, error_response
from api_common.constants.api_constants import SUCCESS_MESSAGES, HTTP_STATUS
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth, require_super_admin


@api_view(['GET', 'PUT'])
@require_auth
@require_super_admin
@api_response
def settings_handler(request):
    """
    Handle GET and PUT requests for system settings
    Super Admin only
    """
    try:
        # Get or create settings (should only be one record)
        setting, created = MySetting.objects.get_or_create(
            defaults={
                'mypay_balance': 0.00,
                'vat_percent': 0.00,
                'call_price': 0.00,
                'sms_price': 0.00,
                'parent_price': 0.00
            }
        )
        
        if request.method == 'GET':
            # Get settings
            serializer = MySettingSerializer(setting)
            return success_response(
                data=serializer.data,
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Settings retrieved successfully')
            )
        
        elif request.method == 'PUT':
            # Update settings
            serializer = MySettingUpdateSerializer(setting, data=request.data)
            
            if serializer.is_valid():
                updated_setting = serializer.save()
                response_serializer = MySettingSerializer(updated_setting)
                return success_response(
                    data=response_serializer.data,
                    message="Settings updated successfully"
                )
            else:
                return error_response(
                    message="Validation error",
                    data=serializer.errors,
                    status_code=HTTP_STATUS['BAD_REQUEST']
                )
    
    except Exception as e:
        return error_response(
            message=f"Error processing settings: {str(e)}",
            status_code=HTTP_STATUS['INTERNAL_ERROR']
        )

