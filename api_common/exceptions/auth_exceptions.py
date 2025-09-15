"""
Authentication Exceptions
Contains authentication-related exceptions
"""
from api_common.exceptions.api_exceptions import APIException


class TokenExpiredError(APIException):
    """
    Token expired error exception
    """
    def __init__(self, message="Token has expired", data=None):
        super().__init__(message, status_code=401, data=data)


class InvalidTokenError(APIException):
    """
    Invalid token error exception
    """
    def __init__(self, message="Invalid token", data=None):
        super().__init__(message, status_code=401, data=data)


class InvalidCredentialsError(APIException):
    """
    Invalid credentials error exception
    """
    def __init__(self, message="Invalid credentials", data=None):
        super().__init__(message, status_code=401, data=data)


class AccountInactiveError(APIException):
    """
    Account inactive error exception
    """
    def __init__(self, message="User account is not active", data=None):
        super().__init__(message, status_code=777, data=data)


class AccountSuspendedError(APIException):
    """
    Account suspended error exception
    """
    def __init__(self, message="User account is suspended", data=None):
        super().__init__(message, status_code=777, data=data)


class InsufficientPermissionsError(APIException):
    """
    Insufficient permissions error exception
    """
    def __init__(self, message="Insufficient permissions", data=None):
        super().__init__(message, status_code=403, data=data)


class RoleAccessDeniedError(APIException):
    """
    Role access denied error exception
    """
    def __init__(self, message="Access denied for this role", data=None):
        super().__init__(message, status_code=403, data=data)


class OTPExpiredError(APIException):
    """
    OTP expired error exception
    """
    def __init__(self, message="OTP has expired", data=None):
        super().__init__(message, status_code=400, data=data)


class InvalidOTPError(APIException):
    """
    Invalid OTP error exception
    """
    def __init__(self, message="Invalid OTP", data=None):
        super().__init__(message, status_code=400, data=data)


class OTPAttemptsExceededError(APIException):
    """
    OTP attempts exceeded error exception
    """
    def __init__(self, message="Maximum OTP attempts exceeded", data=None):
        super().__init__(message, status_code=429, data=data)