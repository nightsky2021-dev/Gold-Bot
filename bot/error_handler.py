"""
Enhanced error handling for Telegram bot operations.

This module provides comprehensive error handling with user-friendly
messages and proper logging for debugging.
"""

import logging
from typing import Optional, Tuple
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.db import IntegrityError, DatabaseError

logger = logging.getLogger('bot.errors')


class BotError(Exception):
    """Base exception for bot-specific errors."""
    
    def __init__(self, message: str, user_message: Optional[str] = None):
        """
        Initialize bot error.
        
        Args:
            message: Technical error message for logging.
            user_message: User-friendly message in Persian.
        """
        self.message = message
        self.user_message = user_message or self._default_user_message()
        super().__init__(self.message)
    
    def _default_user_message(self) -> str:
        """Get default user-friendly message."""
        return "❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید."


class InsufficientBalanceError(BotError):
    """Raised when user doesn't have sufficient balance."""
    
    def _default_user_message(self) -> str:
        return "❌ موجودی شما کافی نیست."


class InvalidAmountError(BotError):
    """Raised when amount is invalid."""
    
    def _default_user_message(self) -> str:
        return "❌ مقدار وارد شده نامعتبر است."


class UserNotApprovedError(BotError):
    """Raised when user is not approved."""
    
    def _default_user_message(self) -> str:
        return "❌ حساب شما هنوز تأیید نشده است. لطفاً منتظر تأیید ادمین باشید."


class ProductNotFoundError(BotError):
    """Raised when product is not found."""
    
    def _default_user_message(self) -> str:
        return "❌ محصول مورد نظر یافت نشد."


class BankAccountError(BotError):
    """Raised for bank account related errors."""
    
    def _default_user_message(self) -> str:
        return "❌ خطا در عملیات حساب بانکی."


class ValidationError(BotError):
    """Raised for validation errors."""
    
    def _default_user_message(self) -> str:
        return "❌ اطلاعات وارد شده نامعتبر است."


class ErrorHandler:
    """Centralized error handling for bot operations."""
    
    @staticmethod
    def handle_error(error: Exception) -> str:
        """
        Handle any error and return user-friendly message.
        
        Args:
            error: Exception that occurred.
            
        Returns:
            User-friendly error message in Persian.
        """
        # Log the error for debugging
        logger.error(f"Error occurred: {type(error).__name__}: {str(error)}", exc_info=True)
        
        # Handle specific error types
        if isinstance(error, BotError):
            return error.user_message
        
        elif isinstance(error, ValidationError):
            return f"❌ خطای اعتبارسنجی: {str(error)}"
        
        elif isinstance(error, IntegrityError):
            if 'UNIQUE constraint' in str(error):
                return "❌ این اطلاعات قبلاً ثبت شده است."
            return "❌ خطا در ذخیره اطلاعات. لطفاً دوباره تلاش کنید."
        
        elif isinstance(error, DatabaseError):
            return "❌ خطا در ارتباط با پایگاه داده. لطفاً بعداً تلاش کنید."
        
        elif isinstance(error, ValueError):
            return "❌ مقدار وارد شده نامعتبر است."
        
        elif isinstance(error, InvalidOperation):
            return "❌ عملیات نامعتبر است."
        
        else:
            # Generic error message
            return "❌ خطایی رخ داده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
    
    @staticmethod
    def validate_amount(amount_str: str) -> Tuple[bool, Optional[Decimal], str]:
        """
        Validate and parse amount input.
        
        Args:
            amount_str: Amount string to validate.
            
        Returns:
            Tuple of (is_valid, parsed_amount, error_message).
        """
        try:
            # Remove thousand separators
            cleaned = amount_str.replace(',', '').replace('٫', '').strip()
            
            # Try to parse as decimal
            amount = Decimal(cleaned)
            
            # Validate amount
            if amount <= 0:
                return False, None, "❌ مقدار باید بزرگتر از صفر باشد."
            
            if amount > Decimal('999999999999'):
                return False, None, "❌ مقدار بیش از حد مجاز است."
            
            return True, amount, ""
            
        except (ValueError, InvalidOperation):
            return False, None, "❌ مقدار وارد شده نامعتبر است. لطفاً یک عدد معتبر وارد کنید."
    
    @staticmethod
    def format_error_with_support(error_message: str) -> str:
        """
        Format error message with support information.
        
        Args:
            error_message: Base error message.
            
        Returns:
            Formatted error message with support info.
        """
        return (
            f"{error_message}\n\n"
            f"در صورت تکرار مشکل، لطفاً با پشتیبانی تماس بگیرید.\n"
            f"📞 پشتیبانی: @support"
        )
    
    @staticmethod
    def validate_profile_data(
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        national_code: Optional[str] = None,
        phone_number: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate profile data.
        
        Args:
            first_name: User's first name.
            last_name: User's last name.
            national_code: National code.
            phone_number: Phone number.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if first_name is not None:
            if not first_name.strip():
                return False, "❌ نام نمی‌تواند خالی باشد."
            if len(first_name) < 2:
                return False, "❌ نام باید حداقل 2 کاراکتر باشد."
            if len(first_name) > 50:
                return False, "❌ نام نباید بیشتر از 50 کاراکتر باشد."
        
        if last_name is not None:
            if len(last_name) > 50:
                return False, "❌ نام خانوادگی نباید بیشتر از 50 کاراکتر باشد."
        
        if national_code is not None:
            from users.validators import check_national_code_format
            is_valid, error_msg = check_national_code_format(national_code)
            if not is_valid:
                return False, f"❌ {error_msg}"
        
        if phone_number is not None:
            from users.validators import check_phone_number_format
            is_valid, error_msg = check_phone_number_format(phone_number)
            if not is_valid:
                return False, f"❌ {error_msg}"
        
        return True, ""
    
    @staticmethod
    def validate_bank_account_data(
        bank_name: Optional[str] = None,
        account_holder: Optional[str] = None,
        account_number: Optional[str] = None,
        iban: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Validate bank account data.
        
        Args:
            bank_name: Name of the bank.
            account_holder: Account holder's name.
            account_number: Bank account number.
            iban: IBAN/Sheba number.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        if bank_name is not None:
            if not bank_name.strip():
                return False, "❌ نام بانک نمی‌تواند خالی باشد."
        
        if account_holder is not None:
            if not account_holder.strip():
                return False, "❌ نام صاحب حساب نمی‌تواند خالی باشد."
            if len(account_holder) < 3:
                return False, "❌ نام صاحب حساب باید حداقل 3 کاراکتر باشد."
        
        if account_number is not None:
            cleaned = account_number.replace(' ', '').replace('-', '')
            if not cleaned.isdigit():
                return False, "❌ شماره حساب فقط باید شامل اعداد باشد."
            if len(cleaned) != 16:
                return False, "❌ شماره حساب باید 16 رقم باشد."
        
        if iban is not None and iban.strip():
            from users.validators import check_iban_format
            is_valid, error_msg = check_iban_format(iban)
            if not is_valid:
                return False, f"❌ {error_msg}"
        
        return True, ""
    
    @staticmethod
    def safe_decimal_convert(value: str, field_name: str = "مقدار") -> Tuple[bool, Optional[Decimal], str]:
        """
        Safely convert string to Decimal with validation.
        
        Args:
            value: String value to convert.
            field_name: Name of the field for error message.
            
        Returns:
            Tuple of (success, decimal_value, error_message).
        """
        try:
            cleaned = value.replace(',', '').replace('٫', '').strip()
            decimal_value = Decimal(cleaned)
            
            if decimal_value < 0:
                return False, None, f"❌ {field_name} نمی‌تواند منفی باشد."
            
            return True, decimal_value, ""
            
        except (ValueError, InvalidOperation):
            return False, None, f"❌ {field_name} نامعتبر است."

