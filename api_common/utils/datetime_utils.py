"""
DateTime Utilities
Handles date and time operations
Matches Node.js datetime_service.js functionality
"""
from datetime import datetime
import pytz


def nepal_time_date():
    """
    Get current Nepal time
    Matches Node.js datetimeService.nepalTimeDate function
    Returns:
        datetime: Current Nepal time
    """
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    return datetime.now(nepal_tz)


def get_nepal_datetime(given_date=None):
    """
    Get Nepal datetime for given date
    Matches Node.js datetimeService.getNepalDateTime function
    Args:
        given_date: Date to convert (optional)
    Returns:
        datetime: Nepal time datetime
    """
    nepal_tz = pytz.timezone('Asia/Kathmandu')
    
    if given_date is None:
        return datetime.now(nepal_tz)
    
    if isinstance(given_date, str):
        # Handle different string formats
        if given_date.endswith('Z'):
            # Remove Z and treat as Nepal time (not UTC)
            given_date = given_date[:-1]
            return nepal_tz.localize(datetime.fromisoformat(given_date))
        else:
            # Try to parse as ISO format
            try:
                given_date = datetime.fromisoformat(given_date.replace('Z', '+00:00'))
            except ValueError:
                # If that fails, try other common formats
                try:
                    given_date = datetime.strptime(given_date, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    given_date = datetime.strptime(given_date, '%Y-%m-%dT%H:%M:%S')
    
    # Convert to Nepal timezone
    if given_date.tzinfo is None:
        # If no timezone info, assume it's already in Nepal time
        return nepal_tz.localize(given_date)
    else:
        # Convert from whatever timezone to Nepal time
        return given_date.astimezone(nepal_tz)


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