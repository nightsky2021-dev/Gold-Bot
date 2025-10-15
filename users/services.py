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
