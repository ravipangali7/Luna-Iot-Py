"""
NTC M2M Portal Views
"""
from rest_framework.decorators import api_view
from django.views.decorators.http import require_http_methods
from api_common.utils.response_utils import success_response, error_response
from api_common.decorators.response_decorators import api_response
from api_common.decorators.auth_decorators import require_auth
from api_common.constants.api_constants import SUCCESS_MESSAGES, ERROR_MESSAGES, HTTP_STATUS
from shared.tasks import fetch_ntc_m2m_report_task
from django.core.cache import cache
import logging

# Try to import Celery, but make it optional
try:
    from celery.result import AsyncResult
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

logger = logging.getLogger(__name__)


@api_view(['POST'])
@require_auth
@api_response
def fetch_ntc_m2m_report(request):
    """
    Start fetching report from NTC M2M portal (async)
    POST /api/shared/ntc-m2m/fetch-report/
    Returns task ID immediately
    """
    try:
        logger.info("NTC M2M report fetch requested by user: %s", request.user)
        
        # Start the Celery task asynchronously
        task = fetch_ntc_m2m_report_task.delay()
        task_id = task.id
        
        logger.info(f"NTC M2M report task started: {task_id}")
        
        # Initialize task status in cache
        cache.set(
            f'ntc_m2m_task_{task_id}',
            {
                'status': 'PENDING',
                'message': 'Task queued, waiting to start...',
                'progress': 0
            },
            timeout=600  # 10 minutes
        )
        
        return success_response(
            message='Report fetch started',
            data={
                'task_id': task_id,
                'status': 'PENDING',
                'message': 'Task has been queued and will start shortly'
            }
        )
            
    except Exception as e:
        logger.error(f"Error in fetch_ntc_m2m_report: {str(e)}", exc_info=True)
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data={'error': str(e)},
            status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
        )


@api_view(['GET'])
@require_auth
@api_response
def get_ntc_m2m_report_status(request, task_id):
    """
    Get status of NTC M2M report fetch task
    GET /api/shared/ntc-m2m/report-status/<task_id>/
    """
    try:
        logger.info(f"Checking NTC M2M report task status: {task_id}")
        
        # Try to get result from Celery (if available)
        celery_state = None
        if CELERY_AVAILABLE:
            try:
                task_result = AsyncResult(task_id)
                celery_state = task_result.state
            except Exception as e:
                logger.warning(f"Could not get Celery task result: {str(e)}")
                celery_state = None
        
        # Get status from cache (more reliable)
        cached_status = cache.get(f'ntc_m2m_task_{task_id}')
        
        if cached_status:
            status = cached_status.get('status', 'UNKNOWN')
            message = cached_status.get('message', 'Status unknown')
            
            # If task is complete, return the full result
            if status == 'SUCCESS':
                return success_response(
                    message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Report fetched successfully'),
                    data={
                        'task_id': task_id,
                        'status': 'SUCCESS',
                        'records': cached_status.get('records', []),
                        'total_records': cached_status.get('total_records', 0),
                        'columns': cached_status.get('columns', [])
                    }
                )
            elif status == 'FAILURE':
                return error_response(
                    message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Failed to fetch report'),
                    data={
                        'task_id': task_id,
                        'status': 'FAILURE',
                        'error': cached_status.get('error', 'Unknown error')
                    },
                    status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
                )
            else:
                # Task is still in progress
                return success_response(
                    message='Task in progress',
                    data={
                        'task_id': task_id,
                        'status': status,
                        'message': message,
                        'progress': cached_status.get('progress', 0)
                    }
                )
        else:
            # Check Celery state if cache is not available and Celery is available
            if CELERY_AVAILABLE and celery_state:
                try:
                    task_result = AsyncResult(task_id)
                    if celery_state == 'SUCCESS':
                        try:
                            result = task_result.get()
                            if result and result.get('status') == 'SUCCESS':
                                return success_response(
                                    message=SUCCESS_MESSAGES.get('DATA_RETRIEVED', 'Report fetched successfully'),
                                    data={
                                        'task_id': task_id,
                                        'status': 'SUCCESS',
                                        'records': result.get('records', []),
                                        'total_records': result.get('total_records', 0),
                                        'columns': result.get('columns', [])
                                    }
                                )
                        except Exception as e:
                            logger.error(f"Error getting task result: {str(e)}")
                    
                    if celery_state == 'FAILURE':
                        try:
                            error_info = task_result.info
                            error_message = str(error_info) if error_info else 'Task failed'
                            return error_response(
                                message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Failed to fetch report'),
                                data={
                                    'task_id': task_id,
                                    'status': 'FAILURE',
                                    'error': error_message
                                },
                                status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
                            )
                        except Exception as e:
                            logger.error(f"Error getting task failure info: {str(e)}")
                    
                    # Task is still running
                    return success_response(
                        message='Task in progress',
                        data={
                            'task_id': task_id,
                            'status': celery_state,
                            'message': f'Task is {celery_state.lower()}'
                        }
                    )
                except Exception as e:
                    logger.warning(f"Error checking Celery state: {str(e)}")
            
            # Task not found
            return error_response(
                message='Task not found',
                data={
                    'task_id': task_id,
                    'status': 'NOT_FOUND',
                    'error': 'Task ID not found. It may have expired or never existed.'
                },
                status_code=HTTP_STATUS.get('NOT_FOUND', 404)
            )
            
    except Exception as e:
        logger.error(f"Error in get_ntc_m2m_report_status: {str(e)}", exc_info=True)
        return error_response(
            message=ERROR_MESSAGES.get('INTERNAL_ERROR', 'Internal server error'),
            data={'error': str(e)},
            status_code=HTTP_STATUS.get('INTERNAL_SERVER_ERROR', 500)
        )

