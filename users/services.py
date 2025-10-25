"""
Business logic services for users app
"""
from typing import Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile


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


# Bank Account Service

def add_bank_account(
    profile: Profile,
    account_holder_name: str,
    bank_name: str,
    account_number: str
) -> Tuple['BankAccount', str]:
    """
    افزودن حساب بانکی جدید
    
    Args:
        profile: پروفایل کاربر
        account_holder_name: نام صاحب حساب
        bank_name: نام بانک
        account_number: شماره حساب/کارت
    
    Returns:
        Tuple[BankAccount, str]: حساب بانکی ایجاد شده و پیام
    
    Raises:
        ValueError: اگر اطلاعات نامعتبر باشد
    """
    from .models import BankAccount
    
    # Validate account holder name matches user's name
    user_full_name = f"{profile.user.first_name} {profile.user.last_name}".strip()
    if user_full_name and account_holder_name.strip() != user_full_name:
        # Allow some flexibility but warn
        pass
    
    # Check for duplicate account number
    if BankAccount.objects.filter(account_number=account_number).exists():
        raise ValueError("این شماره حساب قبلاً ثبت شده است.")
    
    # Create bank account
    bank_account = BankAccount.objects.create(
        profile=profile,
        account_holder_name=account_holder_name,
        bank_name=bank_name,
        account_number=account_number,
        is_verified=False,
        is_active=True
    )
    
    return bank_account, "حساب بانکی با موفقیت اضافه شد و در انتظار تایید ادمین است."


def get_user_bank_accounts(
    profile: Profile,
    only_verified: bool = False
) -> list:
    """
    دریافت لیست حساب‌های بانکی کاربر
    
    Args:
        profile: پروفایل کاربر
        only_verified: فقط حساب‌های تایید شده
    
    Returns:
        لیست حساب‌های بانکی
    """
    from .models import BankAccount
    
    queryset = BankAccount.objects.filter(profile=profile, is_active=True)
    
    if only_verified:
        queryset = queryset.filter(is_verified=True)
    
    return list(queryset.order_by('-created_at'))


def verify_bank_account(
    bank_account_id: int,
    admin_user: Optional[User] = None
) -> Tuple[bool, str]:
    """
    تایید حساب بانکی توسط ادمین
    
    Args:
        bank_account_id: شناسه حساب بانکی
        admin_user: کاربر ادمین
    
    Returns:
        Tuple[bool, str]: موفقیت و پیام
    """
    from .models import BankAccount
    
    try:
        bank_account = BankAccount.objects.get(id=bank_account_id)
        bank_account.is_verified = True
        bank_account.save(update_fields=['is_verified', 'updated_at'])
        
        return True, "حساب بانکی با موفقیت تایید شد."
    except BankAccount.DoesNotExist:
        return False, "حساب بانکی یافت نشد."


def remove_bank_account(
    bank_account_id: int,
    profile: Profile
) -> Tuple[bool, str]:
    """
    حذف حساب بانکی
    
    Args:
        bank_account_id: شناسه حساب بانکی
        profile: پروفایل کاربر
    
    Returns:
        Tuple[bool, str]: موفقیت و پیام
    """
    from .models import BankAccount
    
    try:
        bank_account = BankAccount.objects.get(id=bank_account_id, profile=profile)
        
        # Check if there are pending transactions
        if hasattr(bank_account, 'transactions') and bank_account.transactions.filter(status='PENDING').exists():
            return False, "نمی‌توان حساب بانکی با تراکنش‌های در حال انجام را حذف کرد."
        
        if hasattr(bank_account, 'withdraw_requests') and bank_account.withdraw_requests.filter(status='PENDING').exists():
            return False, "نمی‌توان حساب بانکی با درخواست‌های برداشت در حال انجام را حذف کرد."
        
        # Soft delete by deactivating
        bank_account.is_active = False
        bank_account.save(update_fields=['is_active', 'updated_at'])
        
        return True, "حساب بانکی با موفقیت حذف شد."
    except BankAccount.DoesNotExist:
        return False, "حساب بانکی یافت نشد."
