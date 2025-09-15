"""
Exception Utilities
Handles custom exceptions
"""
from django.http import JsonResponse
from api_common.utils.response_utils import error_response


class APIException(Exception):
    """
    Base API exception
    """
    def __init__(self, message, status_code=500, data=None):
        self.message = message
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)


class ValidationError(APIException):
    """
    Validation error exception
    """
    def __init__(self, message, data=None):
        super().__init__(message, status_code=400, data=data)


class AuthenticationError(APIException):
    """
    Authentication error exception
    """
    def __init__(self, message="Authentication required", data=None):
        super().__init__(message, status_code=401, data=data)


class AuthorizationError(APIException):
    """
    Authorization error exception
    """
    def __init__(self, message="Access denied", data=None):
        super().__init__(message, status_code=403, data=data)


class NotFoundError(APIException):
    """
    Not found error exception
    """
    def __init__(self, message="Resource not found", data=None):
        super().__init__(message, status_code=404, data=data)


class ConflictError(APIException):
    """
    Conflict error exception
    """
    def __init__(self, message="Resource conflict", data=None):
        super().__init__(message, status_code=409, data=data)


class ServiceUnavailableError(APIException):
    """
    Service unavailable error exception
    """
    def __init__(self, message="Service unavailable", data=None):
        super().__init__(message, status_code=503, data=data)


def handle_api_exception(exception):
    """
    Handle API exception and return appropriate response
    Args:
        exception: APIException instance
    Returns:
        JsonResponse: Error response
    """
    return error_response(
        message=exception.message,
        status_code=exception.status_code,
        data=exception.data
    )