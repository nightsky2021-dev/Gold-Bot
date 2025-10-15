"""
User models for the gold trading system.

This module contains the Profile model which extends Django's User model
with Telegram-specific and trading-related fields.
"""

from typing import Optional
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class Profile(models.Model):
    """
    Extended user profile for gold trading system.
    
    Stores Telegram-specific information and user balances (Rial and Gold).
    Related to Django's built-in User model via OneToOneField.
    """
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="کاربر"
    )
    
    telegram_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="شناسه تلگرام",
        help_text="شناسه منحصر به فرد کاربر در تلگرام"
    )
    
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="نام کاربری تلگرام",
        help_text="نام کاربری کاربر در تلگرام (اختیاری)"
    )
    
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        db_index=True,
        verbose_name="شماره تماس",
        help_text="شماره تماس کاربر (برای احراز هویت)"
    )
    
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="تأیید شده",
        help_text="آیا کاربر توسط ادمین تایید شده است؟"
    )
    
    rial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی ریالی",
        help_text="موجودی ریالی کاربر (تومان یا ریال)"
    )
    
    gold_balance_grams = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی طلا (گرم)",
        help_text="موجودی طلای کاربر به گرم"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

    class Meta:
        verbose_name = "پروفایل"
        verbose_name_plural = "پروفایل‌ها"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_approved', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation of the profile."""
        full_name = self.user.get_full_name()
        if full_name:
            return f"{full_name} ({self.phone_number})"
        return f"{self.user.username} ({self.phone_number})"
    
    def get_display_name(self) -> str:
        """Get user's display name (full name or username)."""
        full_name = self.user.get_full_name()
        return full_name if full_name else self.user.username
    
    def can_trade(self) -> bool:
        """Check if user is approved and can make trades."""
        return self.is_approved
    
    def has_sufficient_rial_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient Rial balance."""
        return self.rial_balance >= amount
    
    def has_sufficient_gold_balance(self, amount_grams: Decimal) -> bool:
        """Check if user has sufficient gold balance."""
        return self.gold_balance_grams >= amount_grams
