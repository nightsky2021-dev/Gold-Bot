"""
Business logic services for users app
"""
from typing import Optional, Tuple
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction
from asgiref.sync import sync_to_async
from .models import Profile, BankAccount


def get_or_create_profile_by_telegram(
    telegram_id: str,
    phone_number: str,
    first_name: str = "",
    last_name: str = "",
    telegram_username: Optional[str] = None
) -> Tuple[Profile, bool]:
    """
    دریافت یا ایجاد پروفایل کاربر بر اساس شناسه تلگرام
    
    Args:
        telegram_id: شناسه عددی تلگرام
        phone_number: شماره تماس کاربر
        first_name: نام کاربر
        last_name: نام خانوادگی کاربر
        telegram_username: نام کاربری تلگرام (اختیاری)
    
    Returns:
        Tuple[Profile, bool]: پروفایل و اینکه آیا جدید ایجاد شده یا خیر
    """
    try:
        # جستجو بر اساس telegram_id
        profile = Profile.objects.select_related('user').get(telegram_id=telegram_id)
        created = False
        
        # به‌روزرسانی نام کاربری تلگرام در صورت تغییر
        if telegram_username and profile.telegram_username != telegram_username:
            profile.telegram_username = telegram_username
            profile.save(update_fields=['telegram_username'])
            
    except Profile.DoesNotExist:
        # ایجاد کاربر و پروفایل جدید
        with transaction.atomic():
            # ایجاد username یکتا از روی telegram_id
            username = f"tg_{telegram_id}"
            
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            
            profile = Profile.objects.create(
                user=user,
                telegram_id=telegram_id,
                telegram_username=telegram_username,
                phone_number=phone_number
            )
            created = True
    
    return profile, created


def get_profile_by_telegram_id(telegram_id: str) -> Optional[Profile]:
    """
    دریافت پروفایل بر اساس شناسه تلگرام
    
    Args:
        telegram_id: شناسه عددی تلگرام
    
    Returns:
        Profile یا None
    """
    try:
        return Profile.objects.select_related('user').get(telegram_id=telegram_id)
    except Profile.DoesNotExist:
        return None


def is_user_approved(telegram_id: str) -> bool:
    """
    بررسی تایید شدن کاربر توسط ادمین
    
    Args:
        telegram_id: شناسه عددی تلگرام
    
    Returns:
        bool: آیا کاربر تایید شده است یا خیر
    """
    profile = get_profile_by_telegram_id(telegram_id)
    return profile.is_approved if profile else False


def update_user_balance(
    profile: Profile,
    rial_change: float = 0,
    gold_change: float = 0
) -> Profile:
    """
    به‌روزرسانی موجودی کاربر (باید در transaction استفاده شود)
    
    Args:
        profile: پروفایل کاربر
        rial_change: تغییر موجودی ریالی (مثبت یا منفی)
        gold_change: تغییر موجودی طلا (مثبت یا منفی)
    
    Returns:
        Profile: پروفایل به‌روزرسانی شده
    
    Raises:
        ValueError: اگر موجودی منفی شود
    """
    new_rial_balance = profile.rial_balance + rial_change
    new_gold_balance = profile.gold_balance_grams + gold_change
    
    if new_rial_balance < 0:
        raise ValueError("موجودی ریالی کافی نیست.")
    
    if new_gold_balance < 0:
        raise ValueError("موجودی طلا کافی نیست.")
    
    profile.rial_balance = new_rial_balance
    profile.gold_balance_grams = new_gold_balance
    profile.save(update_fields=['rial_balance', 'gold_balance_grams'])
    
    return profile


class BankAccountService:
    """Service class for bank account operations."""
    
    @staticmethod
    def add_bank_account(
        profile: Profile,
        account_holder_name: str,
        bank_name: str,
        account_number: str,
        account_type: str
    ) -> BankAccount:
        """
        Add a new bank account for a user.
        
        Args:
            profile: User profile.
            account_holder_name: Name of account holder.
            bank_name: Name of the bank.
            account_number: Account number (card or IBAN).
            account_type: Type of account ('CARD' or 'IBAN').
            
        Returns:
            Created BankAccount instance.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Check if account already exists
        if BankAccount.objects.filter(
            profile=profile,
            account_number=account_number
        ).exists():
            raise ValidationError("این حساب بانکی قبلاً ثبت شده است.")
        
        # Validate account holder name matches user name
        user = profile.user
        user_full_name = f"{user.first_name} {user.last_name}".strip()
        if user_full_name and account_holder_name.strip() != user_full_name:
            raise ValidationError(
                f"نام صاحب حساب باید با نام کاربر ({user_full_name}) مطابقت داشته باشد."
            )
        
        # Create bank account
        bank_account = BankAccount.objects.create(
            profile=profile,
            account_holder_name=account_holder_name,
            bank_name=bank_name,
            account_number=account_number,
            account_type=account_type,
            is_verified=False,
            is_active=True
        )
        
        return bank_account
    
    @staticmethod
    def get_user_bank_accounts(profile: Profile, only_verified: bool = False) -> list:
        """
        Get user's bank accounts.
        
        Args:
            profile: User profile.
            only_verified: If True, return only verified accounts.
            
        Returns:
            List of BankAccount instances.
        """
        queryset = profile.bank_accounts.filter(is_active=True)
        
        if only_verified:
            queryset = queryset.filter(is_verified=True)
        
        return list(queryset.order_by('-created_at'))
    
    @staticmethod
    def verify_bank_account(bank_account_id: int, admin_user) -> BankAccount:
        """
        Verify a bank account by admin.
        
        Args:
            bank_account_id: ID of the bank account.
            admin_user: Admin user performing the verification.
            
        Returns:
            Updated BankAccount instance.
            
        Raises:
            BankAccount.DoesNotExist: If account not found.
        """
        bank_account = BankAccount.objects.get(id=bank_account_id)
        bank_account.is_verified = True
        bank_account.save()
        
        # TODO: Send notification to user
        
        return bank_account
    
    @staticmethod
    def remove_bank_account(bank_account_id: int, profile: Profile) -> bool:
        """
        Remove a bank account (soft delete).
        
        Args:
            bank_account_id: ID of the bank account.
            profile: User profile.
            
        Returns:
            True if removed successfully.
            
        Raises:
            BankAccount.DoesNotExist: If account not found.
            ValidationError: If account has pending transactions.
        """
        bank_account = BankAccount.objects.get(
            id=bank_account_id,
            profile=profile
        )
        
        # Check for pending transactions
        if bank_account.transactions.filter(
            status__in=['PENDING', 'COMPLETED']
        ).exists():
            raise ValidationError(
                "این حساب بانکی دارای تراکنش‌های فعال است و نمی‌توان آن را حذف کرد."
            )
        
        # Soft delete
        bank_account.is_active = False
        bank_account.save()
        
        return True


class UserService:
    """Service class for user operations."""
    
    @staticmethod
    async def acheck_user_approval_status(telegram_id: str) -> Tuple[bool, Optional[Profile]]:
        """
        Async version of checking user approval status
        
        Args:
            telegram_id: شناسه عددی تلگرام
        
        Returns:
            Tuple[bool, Optional[Profile]]: (is_approved, profile)
        """
        profile = await sync_to_async(get_profile_by_telegram_id)(telegram_id)
        if profile:
            return profile.is_approved, profile
        return False, None
    
    @staticmethod
    def create_user_from_telegram(
        telegram_id: str,
        phone_number: str,
        telegram_username: Optional[str] = None,
        first_name: str = "",
        last_name: str = "",
        national_code: str = ""
    ) -> Tuple[User, Profile, bool]:
        """
        Create user and profile from telegram data
        
        Args:
            telegram_id: شناسه عددی تلگرام
            phone_number: شماره تماس کاربر
            telegram_username: نام کاربری تلگرام (اختیاری)
            first_name: نام کاربر
            last_name: نام خانوادگی کاربر
            national_code: کد ملی کاربر (currently not stored in model)
        
        Returns:
            Tuple[User, Profile, bool]: (user, profile, created)
        """
        profile, created = get_or_create_profile_by_telegram(
            telegram_id=telegram_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            telegram_username=telegram_username
        )
        
        # Note: national_code field was removed from Profile model in migration 0004
        # The parameter is kept for compatibility but not stored
        
        return profile.user, profile, created
