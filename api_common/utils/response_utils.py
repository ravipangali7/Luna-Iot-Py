"""
Response Utilities
Handles API response formatting
Matches Node.js response_handler.js functionality
"""
from django.http import JsonResponse
from datetime import datetime


def success_response(data=None, message="Success", status_code=200):
    """
    Create success response
    Matches Node.js successResponse function
    """
    response_data = {
        'success': True,
        'message': message,
        'data': data,
        'timestamp': datetime.now().isoformat()
    }
    return JsonResponse(response_data, status=status_code)


def error_response(message="Error", status_code=500, data=None):
    """
    Create error response
    Matches Node.js errorResponse function
    """
    response_data = {
        'success': False,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    if data is not None:
        response_data['data'] = data
    return JsonResponse(response_data, status=status_code)


def format_response(data=None, message="Success", status_code=200, success=True):
    """
    Format response based on success/error
    """
    if success:
        return success_response(data=data, message=message, status_code=status_code)
    else:
        return error_response(message=message, status_code=status_code, data=data)
