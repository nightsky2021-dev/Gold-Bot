"""
لایه سرویس برای منطق تجاری مربوط به کاربران
"""
from typing import Optional, Tuple
from django.contrib.auth.models import User
from django.db import transaction
from .models import Profile


class UserService:
    """سرویس مدیریت کاربران و پروفایل‌ها"""
    
    @staticmethod
    @transaction.atomic
    def create_user_from_telegram(
        telegram_id: str,
        phone_number: str,
        telegram_username: Optional[str] = None,
        first_name: str = "",
        last_name: str = ""
    ) -> Tuple[User, Profile, bool]:
        """
        ایجاد کاربر و پروفایل از طریق تلگرام
        
        Returns:
            Tuple[User, Profile, bool]: کاربر، پروفایل و وضعیت ایجاد (True اگر جدید باشد)
        """
        # بررسی وجود کاربر قبلی
        existing_profile = Profile.get_by_telegram_id(telegram_id)
        if existing_profile:
            return existing_profile.user, existing_profile, False
        
        # ایجاد کاربر جدید
        # استفاده از telegram_id به عنوان username اولیه
        username = f"tg_{telegram_id}"
        
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        
        # ایجاد پروفایل
        profile = Profile.objects.create(
            user=user,
            telegram_id=telegram_id,
            telegram_username=telegram_username,
            phone_number=phone_number,
            is_approved=False
        )
        
        return user, profile, True
    
    @staticmethod
    def check_user_approval_status(telegram_id: str) -> Tuple[bool, Optional[Profile]]:
        """
        بررسی وضعیت تایید کاربر
        
        Returns:
            Tuple[bool, Optional[Profile]]: وضعیت تایید و پروفایل
        """
        profile = Profile.get_by_telegram_id(telegram_id)
        if not profile:
            return False, None
        
        return profile.is_approved, profile
