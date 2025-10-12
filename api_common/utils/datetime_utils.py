"""
DateTime Utilities
Handles date and time operations
Matches Node.js datetime_service.js functionality
"""
from datetime import datetime


def nepal_time_date():
    """
    Get current Nepal time
    Matches Node.js datetimeService.nepalTimeDate function
    Returns:
        datetime: Current Nepal time
    """
    return datetime.now()


def get_nepal_datetime(given_date=None):
    """
    Get Nepal datetime for given date
    Matches Node.js datetimeService.getNepalDateTime function
    Args:
        given_date: Date to convert (optional)
    Returns:
        datetime: Nepal time datetime
    """
    if given_date is None:
        return datetime.now()
    
    if isinstance(given_date, str):
        # Parse string to datetime
        try:
            return datetime.fromisoformat(given_date.replace('Z', ''))
        except ValueError:
            try:
                return datetime.strptime(given_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return datetime.strptime(given_date, '%Y-%m-%dT%H:%M:%S')
    
    return datetime(given_date) if not isinstance(given_date, datetime) else given_date


def format_datetime_for_db(dt):
    """
    Format datetime for database storage
    Args:
        dt: datetime object
    Returns:
        str: Formatted datetime string
    """
    if dt is None:
        return None
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def parse_date_string(date_string):
    """
    Parse date string to datetime
    Args:
        date_string: Date string to parse
    Returns:
        datetime: Parsed datetime object
    """
    if not date_string:
        return None
    
    try:
        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # If none work, try ISO format
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        
    except Exception:
        return None