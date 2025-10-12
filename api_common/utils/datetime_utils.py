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
    from datetime import timedelta
    now = datetime.now()
    # Convert from CST (UTC+8) to Nepal time (UTC+5:45)
    # Nepal is 2 hours 15 minutes behind CST
    nepal_time = now - timedelta(hours=2, minutes=15)
    return nepal_time


def get_nepal_datetime(given_date=None):
    """
    Get Nepal datetime for given date
    Matches Node.js datetimeService.getNepalDateTime function
    Args:
        given_date: Date to convert (optional)
    Returns:
        datetime: Nepal time datetime
    """
    from datetime import timedelta
    
    if given_date is None:
        now = datetime.now()
        # Convert from CST (UTC+8) to Nepal time (UTC+5:45)
        nepal_time = now - timedelta(hours=2, minutes=15)
        return nepal_time
    
    if isinstance(given_date, str):
        # Parse string to datetime
        try:
            parsed_date = datetime.fromisoformat(given_date.replace('Z', ''))
        except ValueError:
            try:
                parsed_date = datetime.strptime(given_date, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                parsed_date = datetime.strptime(given_date, '%Y-%m-%dT%H:%M:%S')
    else:
        parsed_date = given_date if isinstance(given_date, datetime) else datetime(given_date)
    
    # Convert from CST (UTC+8) to Nepal time (UTC+5:45)
    nepal_time = parsed_date - timedelta(hours=2, minutes=15)
    return nepal_time


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