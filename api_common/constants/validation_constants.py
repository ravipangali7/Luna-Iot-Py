"""
Validation Constants
Contains validation rules and limits
"""

# Field Length Limits
FIELD_LIMITS = {
    'PHONE_MIN_LENGTH': 10,
    'PHONE_MAX_LENGTH': 15,
    'NAME_MIN_LENGTH': 2,
    'NAME_MAX_LENGTH': 100,
    'PASSWORD_MIN_LENGTH': 6,
    'PASSWORD_MAX_LENGTH': 128,
    'IMEI_LENGTH': 15,
    'OTP_LENGTH': 6,
    'TOKEN_LENGTH': 64,
    'ADDRESS_MAX_LENGTH': 500,
    'DESCRIPTION_MAX_LENGTH': 1000,
    'MESSAGE_MAX_LENGTH': 1000,
    'TITLE_MAX_LENGTH': 200,
}

# Regex Patterns
REGEX_PATTERNS = {
    'PHONE': r'^[\+]?[0-9\s\-\(\)]{10,}$',
    'EMAIL': r'^[^\s@]+@[^\s@]+\.[^\s@]+$',
    'IMEI': r'^\d{15}$',
    'OTP': r'^\d{6}$',
    'PASSWORD': r'^.{6,128}$',
    'NAME': r'^[a-zA-Z\s]{2,100}$',
    'VEHICLE_NUMBER': r'^[A-Z0-9\s\-]{3,20}$',
}

# Validation Rules
VALIDATION_RULES = {
    'REQUIRED_FIELDS': {
        'USER_CREATE': ['name', 'phone', 'password', 'roleId'],
        'USER_UPDATE': ['phone'],
        'DEVICE_CREATE': ['imei', 'phone', 'sim'],
        'VEHICLE_CREATE': ['imei', 'name', 'vehicleNo', 'vehicleType'],
        'AUTH_LOGIN': ['phone', 'password'],
        'AUTH_REGISTER': ['name', 'phone', 'password', 'otp'],
        'BLOOD_DONATION_CREATE': ['name', 'phone', 'address', 'bloodGroup', 'applyType'],
        'GEOFENCE_CREATE': ['title', 'type', 'boundary'],
        'NOTIFICATION_CREATE': ['title', 'message', 'type'],
        'POPUP_CREATE': ['title', 'message'],
        'RECHARGE_CREATE': ['deviceId', 'amount'],
    },
    'OPTIONAL_FIELDS': {
        'USER_CREATE': ['status', 'fcmToken'],
        'DEVICE_CREATE': ['status'],
        'VEHICLE_CREATE': ['description', 'status'],
        'BLOOD_DONATION_CREATE': ['status', 'lastDonatedAt'],
        'GEOFENCE_CREATE': ['vehicleIds', 'userIds'],
        'NOTIFICATION_CREATE': ['targetUserIds', 'targetRoleIds'],
        'POPUP_CREATE': ['isActive', 'image'],
        'RECHARGE_CREATE': [],
    },
}

# Enum Values
ENUM_VALUES = {
    'BLOOD_GROUPS': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'APPLY_TYPES': ['need', 'donate'],
    'USER_STATUS': ['ACTIVE', 'INACTIVE', 'SUSPENDED'],
    'ROLES': ['Super Admin', 'Dealer', 'Customer'],
    'NOTIFICATION_TYPES': ['all', 'specific', 'role'],
    'VEHICLE_TYPES': ['Car', 'Bike', 'Truck', 'Bus', 'Van', 'Other'],
    'DEVICE_STATUS': ['ACTIVE', 'INACTIVE', 'MAINTENANCE'],
    'GEOFENCE_TYPES': ['inclusion', 'exclusion'],
}

# File Upload Limits
FILE_UPLOAD_LIMITS = {
    'MAX_FILE_SIZE': 5 * 1024 * 1024,  # 5MB
    'ALLOWED_IMAGE_TYPES': [
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/webp'
    ],
    'ALLOWED_IMAGE_EXTENSIONS': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    'UPLOAD_DIRECTORIES': {
        'POPUP_IMAGES': 'uploads/popups/',
        'USER_AVATARS': 'uploads/avatars/',
        'DEVICE_IMAGES': 'uploads/devices/',
    },
}

# Date/Time Validation
DATE_TIME_VALIDATION = {
    'MAX_DATE_RANGE_DAYS': 90,
    'MIN_DATE_RANGE_DAYS': 1,
    'REPORT_MAX_DAYS': 90,
    'CLEANUP_DAYS': 90,
}

# Business Logic Limits
BUSINESS_LIMITS = {
    'MAX_DEVICES_PER_USER': 100,
    'MAX_VEHICLES_PER_USER': 50,
    'MAX_GEOFENCES_PER_USER': 20,
    'MAX_NOTIFICATIONS_PER_DAY': 100,
    'MAX_RECHARGE_AMOUNT': 50000,
    'MIN_RECHARGE_AMOUNT': 10,
    'OTP_MAX_ATTEMPTS': 3,
    'OTP_RESEND_COOLDOWN_MINUTES': 1,
}
