"""
API Constants
Contains API response codes, messages, and other constants
Matches Node.js response patterns
"""

# Success Messages
SUCCESS_MESSAGES = {
    'LOGIN_SUCCESS': 'Login successful',
    'LOGOUT_SUCCESS': 'Logout successful',
    'REGISTRATION_SUCCESS': 'User registered successfully',
    'OTP_SENT': 'OTP sent successfully',
    'OTP_VERIFIED': 'OTP verified successfully',
    'PASSWORD_RESET': 'Password reset successfully',
    'USER_CREATED': 'User created successfully',
    'USER_UPDATED': 'User updated successfully',
    'USER_DELETED': 'User deleted successfully',
    'DEVICE_CREATED': 'Device created successfully',
    'DEVICE_UPDATED': 'Device updated successfully',
    'DEVICE_DELETED': 'Device deleted successfully',
    'DEVICES_RETRIEVED': 'Devices retrieved successfully',
    'DEVICE_RETRIEVED': 'Device retrieved successfully',
    'VEHICLE_CREATED': 'Vehicle created successfully',
    'VEHICLE_UPDATED': 'Vehicle updated successfully',
    'VEHICLE_DELETED': 'Vehicle deleted successfully',
    'VEHICLES_RETRIEVED': 'Vehicles retrieved successfully',
    'LOCATION_RETRIEVED': 'Location history retrieved successfully',
    'STATUS_RETRIEVED': 'Status history retrieved successfully',
    'GEOFENCE_CREATED': 'Geofence created successfully',
    'GEOFENCE_UPDATED': 'Geofence updated successfully',
    'GEOFENCE_DELETED': 'Geofence deleted successfully',
    'GEOFENCES_RETRIEVED': 'Geofences retrieved successfully',
    'NOTIFICATION_CREATED': 'Notification created successfully',
    'NOTIFICATION_DELETED': 'Notification deleted successfully',
    'NOTIFICATIONS_RETRIEVED': 'Notifications retrieved successfully',
    'POPUP_CREATED': 'Popup created successfully',
    'POPUP_UPDATED': 'Popup updated successfully',
    'POPUP_DELETED': 'Popup deleted successfully',
    'POPUPS_RETRIEVED': 'Popups retrieved successfully',
    'RECHARGE_CREATED': 'Recharge created successfully',
    'RECHARGE_DELETED': 'Recharge deleted successfully',
    'RECHARGES_RETRIEVED': 'Recharges retrieved successfully',
    'BLOOD_DONATION_CREATED': 'Blood donation created successfully',
    'BLOOD_DONATION_UPDATED': 'Blood donation updated successfully',
    'BLOOD_DONATION_DELETED': 'Blood donation deleted successfully',
    'BLOOD_DONATIONS_RETRIEVED': 'Blood donations retrieved successfully',
    'ROLE_UPDATED': 'Role permissions updated successfully',
    'ROLES_RETRIEVED': 'Roles retrieved successfully',
    'PERMISSIONS_RETRIEVED': 'Permissions retrieved successfully',
    'PERMISSION_ASSIGNED': 'Permission assigned to user successfully',
    'PERMISSION_REMOVED': 'Permission removed from user successfully',
    'RELAY_ON': 'Relay turned ON successfully',
    'RELAY_OFF': 'Relay turned OFF successfully',
    'RELAY_STATUS': 'Relay status retrieved successfully',
    'SERVER_POINT_SENT': 'Server point command sent successfully',
    'RESET_SENT': 'Reset command sent successfully',
    'USER_RETRIEVED': 'User information retrieved successfully',
    'USERS_RETRIEVED': 'Users retrieved successfully',
}

# Error Messages
ERROR_MESSAGES = {
    'AUTH_REQUIRED': 'Authentication required',
    'INVALID_TOKEN': 'Invalid token or phone',
    'USER_NOT_FOUND': 'User not found',
    'USER_EXISTS': 'User already exists',
    'INVALID_CREDENTIALS': 'Invalid credentials',
    'ACCOUNT_INACTIVE': 'User account is not active',
    'ACCESS_DENIED': 'Access denied',
    'INSUFFICIENT_PERMISSIONS': 'Access denied. Insufficient permissions',
    'SUPER_ADMIN_ONLY': 'Access denied. Only Super Admin can perform this action',
    'DEALER_OR_ADMIN_ONLY': 'Access denied. Only Super Admin and Dealers can perform this action',
    'CUSTOMER_ACCESS_DENIED': 'Access denied. Customers cannot perform this action',
    'DEVICE_NOT_FOUND': 'Device not found',
    'DEVICE_EXISTS': 'Device with this IMEI already exists',
    'VEHICLE_NOT_FOUND': 'Vehicle not found',
    'VEHICLE_EXISTS': 'Vehicle with this IMEI already exists',
    'GEOFENCE_NOT_FOUND': 'Geofence not found',
    'NOTIFICATION_NOT_FOUND': 'Notification not found',
    'POPUP_NOT_FOUND': 'Popup not found',
    'RECHARGE_NOT_FOUND': 'Recharge not found',
    'BLOOD_DONATION_NOT_FOUND': 'Blood donation not found',
    'ROLE_NOT_FOUND': 'Role not found',
    'PERMISSION_NOT_FOUND': 'Permission not found',
    'MISSING_FIELDS': 'Missing required fields',
    'INVALID_PHONE': 'Invalid phone number format',
    'INVALID_EMAIL': 'Invalid email format',
    'INVALID_IMEI': 'IMEI must be exactly 15 digits',
    'INVALID_BLOOD_GROUP': 'Invalid blood group',
    'INVALID_APPLY_TYPE': 'Apply type must be either "need" or "donate"',
    'INVALID_AMOUNT': 'Amount must be a positive number',
    'DEVICE_NOT_CONNECTED': 'Vehicle not connected. Please try again later.',
    'RELAY_COMMAND_FAILED': 'Device did not confirm relay change',
    'TOPUP_FAILED': 'Top-up failed',
    'SMS_FAILED': 'Failed to send SMS',
    'FIREBASE_FAILED': 'Failed to send notification',
    'INTERNAL_ERROR': 'Internal server error',
    'VALIDATION_ERROR': 'Validation error',
    'CONFLICT_ERROR': 'Resource conflict',
    'NOT_FOUND': 'Resource not found',
    'SERVICE_UNAVAILABLE': 'Service unavailable',
}

# HTTP Status Codes
HTTP_STATUS = {
    'OK': 200,
    'CREATED': 201,
    'BAD_REQUEST': 400,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'NOT_FOUND': 404,
    'CONFLICT': 409,
    'INTERNAL_ERROR': 500,
    'SERVICE_UNAVAILABLE': 503,
    'CUSTOM_AUTH_ERROR': 777,  # Custom auth error code from Node.js
}

# Role Names
ROLES = {
    'SUPER_ADMIN': 'Super Admin',
    'DEALER': 'Dealer',
    'CUSTOMER': 'Customer',
}

# User Status
USER_STATUS = {
    'ACTIVE': 'ACTIVE',
    'INACTIVE': 'INACTIVE',
    'SUSPENDED': 'SUSPENDED',
}

# Blood Groups
BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']

# Apply Types
APPLY_TYPES = ['need', 'donate']

# Validation Limits
VALIDATION_LIMITS = {
    'PHONE_MIN_LENGTH': 10,
    'PHONE_MAX_LENGTH': 15,
    'NAME_MIN_LENGTH': 2,
    'NAME_MAX_LENGTH': 100,
    'PASSWORD_MIN_LENGTH': 6,
    'PASSWORD_MAX_LENGTH': 128,
    'IMEI_LENGTH': 15,
    'OTP_LENGTH': 6,
    'TOKEN_LENGTH': 64,
}

# File Upload Limits
FILE_LIMITS = {
    'MAX_FILE_SIZE': 5 * 1024 * 1024,  # 5MB
    'ALLOWED_IMAGE_TYPES': ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'],
    'ALLOWED_IMAGE_EXTENSIONS': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
}

# API Endpoints
API_ENDPOINTS = {
    'AUTH': {
        'LOGIN': '/api/core/auth/login',
        'LOGOUT': '/api/core/auth/logout',
        'REGISTER_SEND_OTP': '/api/core/auth/register/send-otp',
        'REGISTER_VERIFY_OTP': '/api/core/auth/register/verify-otp',
        'REGISTER_RESEND_OTP': '/api/core/auth/register/resend-otp',
        'FORGOT_PASSWORD_SEND_OTP': '/api/core/auth/forgot-password/send-otp',
        'FORGOT_PASSWORD_VERIFY_OTP': '/api/core/auth/forgot-password/verify-otp',
        'FORGOT_PASSWORD_RESET': '/api/core/auth/forgot-password/reset-password',
        'GET_CURRENT_USER': '/api/core/auth/me',
    },
    'USER': {
        'GET_ALL': '/api/core/user/users',
        'GET_BY_PHONE': '/api/core/user/user/{phone}',
        'CREATE': '/api/core/user/user/create',
        'UPDATE': '/api/core/user/user/{phone}',
        'DELETE': '/api/core/user/user/{phone}',
        'UPDATE_FCM': '/api/core/user/fcm-token',
    },
    'DEVICE': {
        'GET_ALL': '/api/device/device',
        'GET_BY_IMEI': '/api/device/device/{imei}',
        'CREATE': '/api/device/device/create',
        'UPDATE': '/api/device/device/update/{imei}',
        'DELETE': '/api/device/device/delete/{imei}',
        'ASSIGN': '/api/device/device/assign',
        'REMOVE_ASSIGNMENT': '/api/device/device/assign',
        'SERVER_POINT': '/api/device/device/server-point',
        'RESET': '/api/device/device/reset',
    },
    'VEHICLE': {
        'GET_ALL': '/api/fleet/vehicle',
        'GET_DETAILED': '/api/fleet/vehicle/detailed',
        'GET_BY_IMEI': '/api/fleet/vehicle/{imei}',
        'CREATE': '/api/fleet/vehicle/create',
        'UPDATE': '/api/fleet/vehicle/update/{imei}',
        'DELETE': '/api/fleet/vehicle/delete/{imei}',
        'ASSIGN_ACCESS': '/api/fleet/vehicle/access',
        'GET_ACCESS_AVAILABLE': '/api/fleet/vehicle/access/available',
        'GET_ACCESS_ASSIGNMENTS': '/api/fleet/vehicle/{imei}/access',
        'UPDATE_ACCESS': '/api/fleet/vehicle/access',
        'REMOVE_ACCESS': '/api/fleet/vehicle/access',
    },
}