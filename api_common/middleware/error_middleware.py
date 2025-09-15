"""
Error Middleware
Handles global error handling
"""
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse
from api_common.utils.response_utils import error_response
import logging

logger = logging.getLogger(__name__)


class ErrorMiddleware(MiddlewareMixin):
    """
    Middleware to handle global errors
    """
    
    def process_exception(self, request, exception):
        logger.error(f'Unhandled exception: {exception}', exc_info=True)
        
        return error_response(
            message='Internal server error',
            status_code=500
        )
