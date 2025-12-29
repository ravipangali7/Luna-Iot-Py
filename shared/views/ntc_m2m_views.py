"""
NTC M2M Portal Views
"""
from rest_framework.decorators import api_view
from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from shared.services.ntc_m2m_service import automate_ntc_m2m_download
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@require_auth
@api_response
def fetch_ntc_m2m_report(request):
    """
    Fetch report from NTC M2M portal
    POST /api/shared/ntc-m2m/fetch-report/
    """
    try:
        logger.info("NTC M2M report fetch requested by user: %s", request.user)
        
        # Call automation service
        result = automate_ntc_m2m_download()
        
        if result['success']:
            return success_response(
                message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Report fetched successfully'),
                data={
                    'records': result['data'],
                    'total_records': result['total_records'],
                    'columns': result['columns']
                }
            )
        else:
            return error_response(
                message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Failed to fetch report'),
                data={'error': result.get('error', 'Unknown error')},
                status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
            )
            
    except Exception as e:
        logger.error(f"Error in fetch_ntc_m2m_report: {str(e)}", exc_info=True)
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data={'error': str(e)},
            status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
        )

