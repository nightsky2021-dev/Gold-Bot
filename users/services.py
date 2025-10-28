"""
Business logic services for users app
"""
from typing import Optional, Tuple, List, cast, TYPE_CHECKING
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Profile, BankAccount
import logging

if TYPE_CHECKING:
    from django.db.models import QuerySet

logger = logging.getLogger('users')


class UserService:
    """Service class for managing user profiles and operations."""
    
    @staticmethod
    def get_or_create_profile(
        telegram_id: str,
        phone_number: str,
        first_name: str = "",
        last_name: str = "",
        telegram_username: Optional[str] = None
    ) -> Tuple[Profile, bool]:
        """
        Get or create user profile by Telegram ID.
        
        Args:
            telegram_id: Telegram numeric ID
            phone_number: User's phone number
            first_name: User's first name
            last_name: User's last name
            telegram_username: Telegram username (optional)
            
        Returns:
            Tuple[Profile, bool]: Profile instance and whether it was created
        """
        return get_or_create_profile_by_telegram(
            telegram_id=telegram_id,
            phone_number=phone_number,
            first_name=first_name,
            last_name=last_name,
            telegram_username=telegram_username
        )
    
    @staticmethod
    def get_profile(telegram_id: str) -> Optional[Profile]:
        """
        Get profile by Telegram ID.
        
        Args:
            telegram_id: Telegram numeric ID
            
        Returns:
            Profile instance or None
        """
        return get_profile_by_telegram_id(telegram_id)
    
    @staticmethod
    def is_approved(telegram_id: str) -> bool:
        """
        Check if user is approved by admin.
        
        Args:
            telegram_id: Telegram numeric ID
            
        Returns:
            bool: Whether user is approved
        """
        return is_user_approved(telegram_id)
    
    @staticmethod
    def update_balance(
        profile: Profile,
        rial_change: float = 0,
        gold_change: float = 0
    ) -> Profile:
        """
        Update user balance (should be used within a transaction).
        
        Args:
            profile: User profile
            rial_change: Rial balance change (positive or negative)
            gold_change: Gold balance change (positive or negative)
            
        Returns:
            Updated Profile instance
            
        Raises:
            ValueError: If balance becomes negative
        """
        return update_user_balance(
            profile=profile,
            rial_change=rial_change,
            gold_change=gold_change
        )
    
    @staticmethod
    async def acheck_user_approval_status(telegram_id: str) -> Tuple[bool, Optional[Profile]]:
        """
        Async wrapper to check user approval status.
        
        Args:
            telegram_id: Telegram numeric ID
            
        Returns:
            Tuple[bool, Optional[Profile]]: (is_approved, profile)
        """
        from asgiref.sync import sync_to_async
        
        profile = await sync_to_async(get_profile_by_telegram_id)(telegram_id)
        is_approved = bool(profile and profile.is_approved)
        
        return is_approved, profile
    
    @staticmethod
    @transaction.atomic
    def create_user_from_telegram(
        telegram_id: str,
        phone_number: str,
        first_name: str = "",
        last_name: str = "",
        telegram_username: Optional[str] = None,
        national_code: Optional[str] = None
    ) -> Tuple[User, Profile, bool]:
        """
        Create a new user and profile from Telegram registration.
        
        Args:
            telegram_id: Telegram numeric ID
            phone_number: User's phone number
            first_name: User's first name
            last_name: User's last name
            telegram_username: Telegram username (optional)
            national_code: National code (optional)
            
        Returns:
            Tuple[User, Profile, bool]: (user, profile, created)
        """
        try:
            # Check if profile already exists
            profile = Profile.objects.select_related('user').get(telegram_id=telegram_id)
            created = False
            
            # Update if telegram_username changed
            if telegram_username and profile.telegram_username != telegram_username:
                profile.telegram_username = telegram_username
                profile.save(update_fields=['telegram_username'])
            
            return profile.user, profile, created
            
        except Profile.DoesNotExist:
            # Create new user and profile
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
            
            logger.info(
                f"New user created: {username} (Telegram ID: {telegram_id}, "
                f"Phone: {phone_number})"
            )
            
            return user, profile, True


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
    return bool(profile.is_approved) if profile else False


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
    new_rial_balance = float(profile.rial_balance) + rial_change
    new_gold_balance = float(profile.gold_balance_grams) + gold_change
    
    if new_rial_balance < 0:
        raise ValueError("موجودی ریالی کافی نیست.")
    
    if new_gold_balance < 0:
        raise ValueError("موجودی طلا کافی نیست.")
    
    profile.rial_balance = new_rial_balance
    profile.gold_balance_grams = new_gold_balance
    profile.save(update_fields=['rial_balance', 'gold_balance_grams'])
    
    return profile


class BankAccountService:
    """Service class for managing user bank accounts."""
    
    @staticmethod
    @transaction.atomic
    def add_bank_account(
        profile: Profile,
        account_holder_name: str,
        bank_name: str,
        account_number: str,
        account_type: str
    ) -> BankAccount:
        """
        Add a new bank account for user.
        
        Args:
            profile: User profile
            account_holder_name: Name of account holder
            bank_name: Bank name
            account_number: Account/card number
            account_type: Account type (CARD or IBAN)
            
        Returns:
            BankAccount instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for duplicate account number
        if BankAccount.objects.filter(
            profile=profile,
            account_number=account_number
        ).exists():
            raise ValidationError("این شماره حساب قبلاً ثبت شده است.")
        
        # Create bank account (validation happens in model's clean method)
        bank_account = BankAccount(
            profile=profile,
            account_holder_name=account_holder_name.strip(),
            bank_name=bank_name,
            account_number=account_number.strip(),
            account_type=account_type,
            is_verified=False,
            is_active=True
        )
        
        # This will trigger validation
        bank_account.save()
        
        logger.info(
            f"Bank account added for {profile.get_display_name()}: "
            f"{bank_name} - {bank_account.get_masked_account_number()}"
        )
        
        return bank_account
    
    @staticmethod
    def get_user_bank_accounts(
        profile: Profile,
        only_verified: bool = False,
        only_active: bool = False
    ) -> List[BankAccount]:
        """
        Get user's bank accounts.
        
        Args:
            profile: User profile
            only_verified: Filter only verified accounts
            only_active: Filter only active accounts
            
        Returns:
            List of BankAccount instances
        """
        queryset = cast('QuerySet[BankAccount]', profile.bank_accounts).all()
        
        if only_verified:
            queryset = queryset.filter(is_verified=True)
        
        if only_active:
            queryset = queryset.filter(is_active=True)
        
        return list(queryset)
    
    @staticmethod
    @transaction.atomic
    def verify_bank_account(
        bank_account_id: int,
        admin_user: Optional[User] = None
    ) -> BankAccount:
        """
        Verify a bank account (admin action).
        
        Args:
            bank_account_id: Bank account ID
            admin_user: Admin user performing verification
            
        Returns:
            Verified BankAccount instance
            
        Raises:
            BankAccount.DoesNotExist: If account not found
        """
        bank_account = BankAccount.objects.select_related('profile', 'profile__user').get(
            id=bank_account_id
        )
        
        bank_account.is_verified = True
        bank_account.save(update_fields=['is_verified', 'updated_at'])
        
        logger.info(
            f"Bank account {cast(int, bank_account.id)} verified for "
            f"{bank_account.profile.get_display_name()} "
            f"by admin {admin_user.username if admin_user else 'system'}"
        )
        
        # TODO: Send notification to user via Telegram
        
        return bank_account
    
    @staticmethod
    @transaction.atomic
    def reject_bank_account(
        bank_account_id: int,
        reason: str,
        admin_user: Optional[User] = None
    ) -> BankAccount:
        """
        Reject and deactivate a bank account (admin action).
        
        Args:
            bank_account_id: Bank account ID
            reason: Reason for rejection
            admin_user: Admin user performing rejection
        
        Returns:
            Rejected BankAccount instance
            
        Raises:
            BankAccount.DoesNotExist: If account not found
        """
        bank_account = BankAccount.objects.select_related('profile', 'profile__user').get(
            id=bank_account_id
        )
        
        bank_account.is_verified = False
        bank_account.is_active = False
        bank_account.save(update_fields=['is_verified', 'is_active', 'updated_at'])
        
        logger.info(
            f"Bank account {cast(int, bank_account.id)} rejected for "
            f"{bank_account.profile.get_display_name()} "
            f"by admin {admin_user.username if admin_user else 'system'}. "
            f"Reason: {reason}"
        )
        
        # TODO: Send notification to user via Telegram with reason
        
        return bank_account

    @staticmethod
    @transaction.atomic
    def remove_bank_account(
        bank_account_id: int,
        profile: Profile
    ) -> None:
        """
        Remove a bank account (user action).
        
        Args:
            bank_account_id: Bank account ID
            profile: User profile (for authorization)
            
        Raises:
            ValidationError: If account has pending transactions
            BankAccount.DoesNotExist: If account not found or not owned by user
        """
        bank_account = BankAccount.objects.get(
            id=bank_account_id,
            profile=profile
        )
        
        # TODO: Check for pending transactions when Transaction model is implemented
        # if bank_account.transactions.filter(status='PENDING').exists():
        #     raise ValidationError(
        #         "این حساب دارای تراکنش در حال انجام است و نمی‌توان آن را حذف کرد."
        #     )
        
        # TODO: Check for pending withdraw requests when WithdrawRequest model is implemented
        # if bank_account.withdraw_requests.filter(status='PENDING').exists():
        #     raise ValidationError(
        #         "این حساب دارای درخواست برداشت در حال انجام است و نمی‌توان آن را حذف کرد."
        #     )
        
        logger.info(
            f"Bank account {cast(int, bank_account.id)} removed by "
            f"{profile.get_display_name()}"
        )
        
        bank_account.delete()
    
    @staticmethod
    def get_bank_account_by_id(
        bank_account_id: int,
        profile: Optional[Profile] = None
    ) -> Optional[BankAccount]:
        """
        Get a bank account by ID.
        
        Args:
            bank_account_id: Bank account ID
            profile: Optional profile to filter by (for authorization)
            
        Returns:
            BankAccount instance or None
        """
        try:
            queryset = BankAccount.objects.select_related('profile', 'profile__user')
            
            if profile:
                return queryset.get(id=bank_account_id, profile=profile)
            else:
                return queryset.get(id=bank_account_id)
        except BankAccount.DoesNotExist:
            return None
