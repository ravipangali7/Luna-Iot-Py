"""
Background tasks for shared module
"""
from celery import shared_task
from django.core.cache import cache
from shared.services.ntc_m2m_service import automate_ntc_m2m_download
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def fetch_ntc_m2m_report_task(self):
    """
    Celery task to fetch NTC M2M report asynchronously.
    This task runs the browser automation in the background.
    
    Returns:
        dict: Task result with success status and data or error
    """
    task_id = self.request.id
    logger.info(f"Starting NTC M2M report fetch task: {task_id}")
    
    # Update task status in cache
    cache.set(
        f'ntc_m2m_task_{task_id}',
        {
            'status': 'STARTED',
            'message': 'Automation started...',
            'progress': 0
        },
        timeout=600  # 10 minutes
    )
    
    try:
        # Call the automation service
        result = automate_ntc_m2m_download()
        
        # Store result in cache
        task_result = {
            'status': 'SUCCESS' if result['success'] else 'FAILURE',
            'message': 'Report fetched successfully' if result['success'] else 'Failed to fetch report',
            'data': result if result['success'] else None,
            'error': result.get('error') if not result['success'] else None,
            'records': result.get('data', []) if result['success'] else [],
            'total_records': result.get('total_records', 0) if result['success'] else 0,
            'columns': result.get('columns', []) if result['success'] else []
        }
        
        # Store in cache for 10 minutes
        cache.set(f'ntc_m2m_task_{task_id}', task_result, timeout=600)
        
        logger.info(f"NTC M2M report fetch task completed: {task_id}, success: {result['success']}")
        
        return task_result
        
    except Exception as e:
        logger.error(f"Error in fetch_ntc_m2m_report_task {task_id}: {str(e)}", exc_info=True)
        
        # Store error in cache
        task_result = {
            'status': 'FAILURE',
            'message': 'Internal error occurred',
            'error': str(e),
            'data': None,
            'records': [],
            'total_records': 0,
            'columns': []
        }
        
        cache.set(f'ntc_m2m_task_{task_id}', task_result, timeout=600)
        
        return task_result

