"""
Authentication Utilities
Handles token generation and validation
"""
import secrets
import hashlib
from datetime import datetime, timedelta
from django.conf import settings


def generate_token():
    """
    Generate random token
    Matches Node.js AuthController.generateToken function
    Returns:
        str: 64-character hex token
    """
    return secrets.token_hex(32)


def generate_otp():
    """
    Generate OTP
    Matches Node.js AuthController.generateOTP function
    Returns:
        str: 6-digit OTP
    """
    import random
    return str(random.randint(100000, 999999))


def hash_password(password):
    """
    Hash password using bcrypt
    Matches Node.js bcrypt.hash functionality
    Args:
        password: Plain text password
    Returns:
        str: Hashed password
    """
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')


def verify_password(password, hashed_password):
    """
    Verify password against hash
    Matches Node.js bcrypt.compare functionality
    Args:
        password: Plain text password
        hashed_password: Hashed password
    Returns:
        bool: True if password matches
    """
    import bcrypt
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))


def is_token_valid(token, created_at, expiry_hours=24):
    """
    Check if token is still valid
    Args:
        token: Token to check
        created_at: When token was created
        expiry_hours: Token expiry in hours
    Returns:
        bool: True if token is valid
    """
    if not token or not created_at:
        return False
    
    expiry_time = created_at + timedelta(hours=expiry_hours)
    return datetime.now() < expiry_time
