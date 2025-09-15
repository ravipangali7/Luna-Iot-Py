"""
Authentication Constants
Contains authentication-related constants
"""

# Token Configuration
TOKEN_CONFIG = {
    'LENGTH': 64,
    'EXPIRY_HOURS': 24,
    'HEADER_NAME': 'x-token',
    'PHONE_HEADER_NAME': 'x-phone',
}

# OTP Configuration
OTP_CONFIG = {
    'LENGTH': 6,
    'EXPIRY_MINUTES': 10,
    'MAX_ATTEMPTS': 3,
    'RESEND_COOLDOWN_MINUTES': 1,
}

# Password Configuration
PASSWORD_CONFIG = {
    'MIN_LENGTH': 6,
    'MAX_LENGTH': 128,
    'BCRYPT_ROUNDS': 12,
    'REQUIRE_SPECIAL_CHARS': False,
    'REQUIRE_NUMBERS': False,
    'REQUIRE_UPPERCASE': False,
}

# User Status
USER_STATUS = {
    'ACTIVE': 'ACTIVE',
    'INACTIVE': 'INACTIVE',
    'SUSPENDED': 'SUSPENDED',
    'PENDING': 'PENDING',
}

# Role Names
ROLES = {
    'SUPER_ADMIN': 'Super Admin',
    'DEALER': 'Dealer',
    'CUSTOMER': 'Customer',
}

# Permission Names
PERMISSIONS = {
    'USER_MANAGEMENT': 'user_management',
    'DEVICE_MANAGEMENT': 'device_management',
    'VEHICLE_MANAGEMENT': 'vehicle_management',
    'GEOFENCE_MANAGEMENT': 'geofence_management',
    'NOTIFICATION_MANAGEMENT': 'notification_management',
    'POPUP_MANAGEMENT': 'popup_management',
    'RECHARGE_MANAGEMENT': 'recharge_management',
    'BLOOD_DONATION_MANAGEMENT': 'blood_donation_management',
    'ROLE_MANAGEMENT': 'role_management',
    'PERMISSION_MANAGEMENT': 'permission_management',
    'RELAY_CONTROL': 'relay_control',
    'LOCATION_ACCESS': 'location_access',
    'STATUS_ACCESS': 'status_access',
    'REPORT_ACCESS': 'report_access',
}

# Auth Error Codes
AUTH_ERROR_CODES = {
    'INVALID_CREDENTIALS': 401,
    'TOKEN_EXPIRED': 401,
    'TOKEN_INVALID': 401,
    'ACCOUNT_INACTIVE': 777,
    'ACCOUNT_SUSPENDED': 777,
    'ACCESS_DENIED': 403,
    'INSUFFICIENT_PERMISSIONS': 403,
    'RATE_LIMIT_EXCEEDED': 429,
}

# Public Routes (No Authentication Required)
PUBLIC_ROUTES = [
    '/api/core/auth/login',
    '/api/core/auth/register/send-otp',
    '/api/core/auth/register/verify-otp',
    '/api/core/auth/register/resend-otp',
    '/api/core/auth/forgot-password/send-otp',
    '/api/core/auth/forgot-password/verify-otp',
    '/api/core/auth/forgot-password/reset-password',
    '/api/health/blood-donation',
    '/api/shared/popup/active',
]

# Role-based Access Control
ROLE_ACCESS = {
    'Super Admin': {
        'can_access': ['all'],
        'can_create': ['all'],
        'can_update': ['all'],
        'can_delete': ['all'],
    },
    'Dealer': {
        'can_access': ['device', 'vehicle', 'location', 'status', 'recharge'],
        'can_create': ['device', 'vehicle', 'recharge'],
        'can_update': ['device', 'vehicle'],
        'can_delete': [],
    },
    'Customer': {
        'can_access': ['vehicle', 'location', 'status'],
        'can_create': [],
        'can_update': [],
        'can_delete': [],
    },
}