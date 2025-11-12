"""
Validators for users app.

This module contains validation functions for user-related data including
phone numbers, national codes, and bank account information.
"""

import re
from typing import Tuple
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_iranian_phone_number(phone: str) -> None:
    """
    Validate Iranian phone number format.
    
    Args:
        phone: Phone number string to validate.
        
    Raises:
        ValidationError: If phone number format is invalid.
    """
    # Remove spaces, dashes, and plus signs
    cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Check if contains only digits
    if not cleaned.isdigit():
        raise ValidationError(_('شماره تماس فقط باید شامل اعداد باشد.'))
    
    # Check Iranian phone number patterns
    # Pattern 1: 09xxxxxxxxx (11 digits starting with 09)
    # Pattern 2: 989xxxxxxxxx (12 digits starting with 989)
    if not (
        (len(cleaned) == 11 and cleaned.startswith('09')) or
        (len(cleaned) == 12 and cleaned.startswith('989'))
    ):
        raise ValidationError(
            _('شماره تماس باید با 09 شروع شود و 11 رقم یا با 989 شروع شود و 12 رقم باشد.')
        )


def validate_iranian_national_code(national_code: str) -> None:
    """
    Validate Iranian national code (کد ملی) with checksum verification.
    
    Args:
        national_code: 10-digit national code string.
        
    Raises:
        ValidationError: If national code format or checksum is invalid.
    """
    # Remove spaces and dashes
    cleaned = national_code.replace(' ', '').replace('-', '')
    
    # Check if contains only digits
    if not cleaned.isdigit():
        raise ValidationError(_('کد ملی فقط باید شامل اعداد باشد.'))
    
    # Check length
    if len(cleaned) != 10:
        raise ValidationError(_('کد ملی باید 10 رقم باشد.'))
    
    # Check for invalid patterns (all same digits)
    if len(set(cleaned)) == 1:
        raise ValidationError(_('کد ملی نامعتبر است.'))
    
    # Verify checksum using Iranian national code algorithm
    check_digit = int(cleaned[9])
    sum_digits = sum(int(cleaned[i]) * (10 - i) for i in range(9))
    remainder = sum_digits % 11
    
    if not (
        (remainder < 2 and check_digit == remainder) or
        (remainder >= 2 and check_digit == 11 - remainder)
    ):
        raise ValidationError(_('کد ملی نامعتبر است (چک‌سام اشتباه).'))


def validate_iranian_iban(iban: str) -> None:
    """
    Validate Iranian IBAN (Sheba) format.
    
    Args:
        iban: IBAN string to validate (with or without IR prefix).
        
    Raises:
        ValidationError: If IBAN format is invalid.
    """
    # Remove spaces and dashes
    cleaned = iban.replace(' ', '').replace('-', '').upper()
    
    # Check for IR prefix
    if cleaned.startswith('IR'):
        cleaned = cleaned[2:]
    
    # Check if contains only digits
    if not cleaned.isdigit():
        raise ValidationError(_('شماره شبا فقط باید شامل اعداد باشد.'))
    
    # Iranian IBAN should be 24 digits (after IR prefix)
    if len(cleaned) != 24:
        raise ValidationError(_('شماره شبا باید 24 رقم باشد (بدون IR).'))
    
    # Validate IBAN checksum (mod 97 algorithm)
    # Move first 4 chars to end, convert IR to numbers (I=18, R=27)
    rearranged = cleaned[4:] + '1827' + cleaned[:4]
    
    # Convert to integer and check mod 97
    try:
        if int(rearranged) % 97 != 1:
            raise ValidationError(_('شماره شبا نامعتبر است (چک‌سام اشتباه).'))
    except ValueError:
        raise ValidationError(_('شماره شبا نامعتبر است.'))


def validate_bank_account_number(account_number: str) -> None:
    """
    Validate Iranian bank account number format.
    
    Args:
        account_number: Bank account number string.
        
    Raises:
        ValidationError: If account number format is invalid.
    """
    # Remove spaces and dashes
    cleaned = account_number.replace(' ', '').replace('-', '')
    
    # Check if contains only digits
    if not cleaned.isdigit():
        raise ValidationError(_('شماره حساب فقط باید شامل اعداد باشد.'))
    
    # Iranian bank account numbers are typically 16 digits
    if len(cleaned) != 16:
        raise ValidationError(_('شماره حساب باید 16 رقم باشد.'))


def validate_bank_card_number(card_number: str) -> None:
    """
    Validate Iranian bank card number using Luhn algorithm.
    
    Args:
        card_number: 16-digit bank card number.
        
    Raises:
        ValidationError: If card number format or checksum is invalid.
    """
    # Remove spaces and dashes
    cleaned = card_number.replace(' ', '').replace('-', '')
    
    # Check if contains only digits
    if not cleaned.isdigit():
        raise ValidationError(_('شماره کارت فقط باید شامل اعداد باشد.'))
    
    # Check length (Iranian bank cards are 16 digits)
    if len(cleaned) != 16:
        raise ValidationError(_('شماره کارت باید 16 رقم باشد.'))
    
    # Verify Luhn checksum
    def luhn_checksum(card: str) -> bool:
        """Calculate Luhn checksum."""
        digits = [int(d) for d in card]
        checksum = 0
        
        # Double every second digit from right to left
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        
        return sum(digits) % 10 == 0
    
    if not luhn_checksum(cleaned):
        raise ValidationError(_('شماره کارت نامعتبر است (چک‌سام اشتباه).'))


def check_phone_number_format(phone: str) -> Tuple[bool, str]:
    """
    Check phone number format without raising exception.
    
    Args:
        phone: Phone number string to check.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        validate_iranian_phone_number(phone)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)


def check_national_code_format(national_code: str) -> Tuple[bool, str]:
    """
    Check national code format without raising exception.
    
    Args:
        national_code: National code string to check.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        validate_iranian_national_code(national_code)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)


def check_iban_format(iban: str) -> Tuple[bool, str]:
    """
    Check IBAN format without raising exception.
    
    Args:
        iban: IBAN string to check.
        
    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        validate_iranian_iban(iban)
        return True, ""
    except ValidationError as e:
        return False, str(e.message)


def normalize_phone_number(phone: str) -> str:
    """
    Normalize phone number to standard format (989xxxxxxxxx).
    
    Args:
        phone: Phone number in any accepted format.
        
    Returns:
        Normalized phone number string.
    """
    cleaned = phone.replace(' ', '').replace('-', '').replace('+', '')
    
    # Convert 09xxxxxxxxx to 989xxxxxxxxx
    if cleaned.startswith('09'):
        return '98' + cleaned[1:]
    
    return cleaned


def normalize_iban(iban: str) -> str:
    """
    Normalize IBAN to standard format (IR + 24 digits).
    
    Args:
        iban: IBAN in any accepted format.
        
    Returns:
        Normalized IBAN string.
    """
    cleaned = iban.replace(' ', '').replace('-', '').upper()
    
    # Add IR prefix if not present
    if not cleaned.startswith('IR'):
        return 'IR' + cleaned
    
    return cleaned


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """
    Mask sensitive data showing only last N characters.
    
    Args:
        data: Sensitive data string.
        visible_chars: Number of characters to show at the end.
        
    Returns:
        Masked string.
    """
    if len(data) <= visible_chars:
        return '*' * len(data)
    
    return '*' * (len(data) - visible_chars) + data[-visible_chars:]

