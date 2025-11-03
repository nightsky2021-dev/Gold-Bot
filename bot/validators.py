"""
Input validators for bot handlers.
"""

from decimal import Decimal, InvalidOperation
from typing import Tuple, Optional


def validate_amount(amount_str: str) -> Tuple[bool, Optional[Decimal], str]:
    """
    Validate amount input.
    
    Returns:
        Tuple of (is_valid, amount, error_message)
    """
    try:
        amount = Decimal(amount_str.replace(',', ''))
        
        if amount <= 0:
            return False, None, "مقدار باید بزرگتر از صفر باشد."
        
        return True, amount, ""
        
    except (ValueError, InvalidOperation):
        return False, None, "مقدار وارد شده نامعتبر است."


def validate_account_number(account_number: str) -> Tuple[bool, str]:
    """
    Validate Iranian bank account number.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    cleaned = account_number.replace(' ', '').replace('-', '')
    
    if not cleaned.isdigit():
        return False, "شماره حساب باید فقط شامل اعداد باشد."
    
    if len(cleaned) != 16:
        return False, "شماره حساب باید 16 رقم باشد."
    
    return True, ""


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Validate Iranian phone number.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    cleaned = phone.replace('+', '').replace(' ', '')
    
    if not cleaned.isdigit():
        return False, "شماره تماس نامعتبر است."
    
    if not (cleaned.startswith('98') or cleaned.startswith('09')):
        return False, "شماره تماس باید با 98 یا 09 شروع شود."
    
    return True, ""
