"""
Validation Utilities
Handles field validation
Matches Node.js validation.js functionality
"""
import re


def validate_required_fields(data, required_fields):
    """
    Validate required fields in request data
    Matches Node.js validateRequiredFields function
    Args:
        data: The data object to validate
        required_fields: Array of required field names
    Returns:
        dict: {is_valid: bool, message: str}
    """
    missing_fields = []
    
    for field in required_fields:
        if data.get(field) is None or data.get(field) == '':
            missing_fields.append(field)
    
    if missing_fields:
        return {
            'is_valid': False,
            'message': f'Missing required fields: {", ".join(missing_fields)}'
        }
    
    return {
        'is_valid': True,
        'message': 'All required fields are present'
    }


def validate_email(email):
    """
    Validate email format
    Matches Node.js validateEmail function
    Args:
        email: Email to validate
    Returns:
        bool: True if valid email format
    """
    email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
    return bool(re.match(email_regex, email)) if email else False


def validate_phone_number(phone):
    """
    Validate phone number format
    Matches Node.js validatePhone function
    Args:
        phone: Phone number to validate
    Returns:
        bool: True if valid phone format
    """
    if not phone:
        return False
    phone_regex = r'^[\+]?[0-9\s\-\(\)]{10,}$'
    return bool(re.match(phone_regex, phone))


def validate_number(value):
    """
    Validate numeric value
    Matches Node.js validateNumber function
    Args:
        value: Value to validate
    Returns:
        bool: True if valid number
    """
    try:
        float(value)
        return True
    except (ValueError, TypeError):
        return False


def validate_positive_number(value):
    """
    Validate positive number
    Matches Node.js validatePositiveNumber function
    Args:
        value: Value to validate
    Returns:
        bool: True if valid positive number
    """
    if not validate_number(value):
        return False
    return float(value) > 0


def validate_imei(imei):
    """
    Validate IMEI format (15 digits)
    Args:
        imei: IMEI to validate
    Returns:
        bool: True if valid IMEI format
    """
    if not imei:
        return False
    return bool(re.match(r'^\d{15}$', str(imei)))


def validate_blood_group(blood_group):
    """
    Validate blood group format
    Args:
        blood_group: Blood group to validate
    Returns:
        bool: True if valid blood group
    """
    valid_blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    return blood_group in valid_blood_groups


def validate_apply_type(apply_type):
    """
    Validate apply type for blood donation
    Args:
        apply_type: Apply type to validate
    Returns:
        bool: True if valid apply type
    """
    valid_apply_types = ['need', 'donate']
    return apply_type in valid_apply_types
