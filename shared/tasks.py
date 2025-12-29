"""
Background tasks for shared module
"""
from django.core.cache import cache
from shared.services.ntc_m2m_service import automate_ntc_m2m_download
import logging
import threading
import uuid

logger = logging.getLogger(__name__)

# Try to import Celery, but make it optional
try:
    from celery import shared_task
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    logger.warning("Celery not available, using threading fallback for background tasks")


def _run_ntc_m2m_task(task_id):
    """
    Internal function to run the NTC M2M report fetch task.
    This is used by both Celery and threading implementations.
    """
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


if CELERY_AVAILABLE:
    @shared_task(bind=True)
    def fetch_ntc_m2m_report_task(self):
        """
        Celery task to fetch NTC M2M report asynchronously.
        This task runs the browser automation in the background.
        
        Returns:
            dict: Task result with success status and data or error
        """
        task_id = self.request.id
        return _run_ntc_m2m_task(task_id)
else:
    # Fallback: Create a wrapper that mimics Celery's .delay() interface
    class MockTask:
        def __init__(self, task_id):
            self.id = task_id
    
    class TaskWrapper:
        """Wrapper that mimics Celery task interface using threading"""
        def delay(self):
            """
            Start the task in a background thread and return a mock task object.
            This mimics Celery's .delay() interface.
            """
            task_id = str(uuid.uuid4())
            
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
            
            # Run in a background thread
            thread = threading.Thread(target=_run_ntc_m2m_task, args=(task_id,), daemon=True)
            thread.start()
            
            return MockTask(task_id)
    
    fetch_ntc_m2m_report_task = TaskWrapper()

