"""
SMS Cost Calculation Utilities
Handles character-based SMS cost calculation
"""
import math
from decimal import Decimal
from typing import Tuple


def calculate_sms_cost(message: str, sms_price: Decimal, sms_character_price: int, num_recipients: int) -> Tuple[Decimal, int, int]:
    """
    Calculate SMS cost based on character count.
    
    Args:
        message: The SMS message content (all characters will be counted)
        sms_price: Price per SMS part
        sms_character_price: Number of characters per SMS part (default: 160)
        num_recipients: Number of recipients
    
    Returns:
        Tuple containing:
        - total_cost: Total cost for all recipients (Decimal)
        - character_count: Number of characters in the message (int)
        - sms_parts: Number of SMS parts needed (int)
    """
    # Count all characters in the message
    character_count = len(message)
    
    # Calculate number of SMS parts needed (always round up)
    if character_count == 0:
        sms_parts = 1  # At least 1 SMS part even for empty message
    else:
        sms_parts = math.ceil(character_count / sms_character_price)
    
    # Calculate cost per recipient
    cost_per_recipient = sms_price * Decimal(str(sms_parts))
    
    # Calculate total cost for all recipients
    total_cost = cost_per_recipient * Decimal(str(num_recipients))
    
    return total_cost, character_count, sms_parts
