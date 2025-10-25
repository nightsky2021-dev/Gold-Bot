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
    
    coin_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه",
        help_text="موجودی سکه تمام بهار آزادی"
    )
    
    dollar_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار",
        help_text="موجودی دلار آمریکا"
    )
    
    # Frozen balances for pending transactions
    frozen_rial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی ریالی مسدود شده",
        help_text="موجودی ریالی در انتظار تکمیل تراکنش"
    )
    
    frozen_gold_balance = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی طلای مسدود شده",
        help_text="موجودی طلای در انتظار تکمیل تراکنش"
    )
    
    frozen_coin_balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه مسدود شده",
        help_text="موجودی سکه در انتظار تکمیل تراکنش"
    )
    
    frozen_dollar_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار مسدود شده",
        help_text="موجودی دلار در انتظار تکمیل تراکنش"
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
    
    def has_sufficient_coin_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient coin balance."""
        return self.coin_balance >= amount
    
    def has_sufficient_dollar_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient dollar balance."""
        return self.dollar_balance >= amount
    
    def get_available_balance(self, currency_type: str) -> Decimal:
        """Get available (non-frozen) balance for a currency type."""
        balance_map = {
            'RIAL': self.rial_balance - self.frozen_rial_balance,
            'GOLD': self.gold_balance_grams - self.frozen_gold_balance,
            'COIN': self.coin_balance - self.frozen_coin_balance,
            'DOLLAR': self.dollar_balance - self.frozen_dollar_balance,
        }
        return balance_map.get(currency_type, Decimal('0'))


class BankAccount(models.Model):
    """Bank account information for users."""
    
    # Iranian banks list
    BANK_CHOICES = [
        ('ملی ایران', 'بانک ملی ایران'),
        ('ملت', 'بانک ملت'),
        ('تجارت', 'بانک تجارت'),
        ('صادرات', 'بانک صادرات'),
        ('سپه', 'بانک سپه'),
        ('رفاه', 'بانک رفاه'),
        ('پاسارگاد', 'بانک پاسارگاد'),
        ('پارسیان', 'بانک پارسیان'),
        ('اقتصاد نوین', 'بانک اقتصاد نوین'),
        ('سامان', 'بانک سامان'),
        ('سینا', 'بانک سینا'),
        ('کارآفرین', 'بانک کارآفرین'),
        ('آینده', 'بانک آینده'),
        ('شهر', 'بانک شهر'),
        ('دی', 'بانک دی'),
        ('صنعت و معدن', 'بانک صنعت و معدن'),
        ('توسعه تعاون', 'بانک توسعه تعاون'),
        ('قوامین', 'بانک قوامین'),
        ('مهر اقتصاد', 'بانک مهر اقتصاد'),
        ('حکمت ایرانیان', 'بانک حکمت ایرانیان'),
    ]
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name="پروفایل"
    )
    
    account_holder_name = models.CharField(
        max_length=200,
        verbose_name="نام صاحب حساب",
        help_text="نام کامل صاحب حساب"
    )
    
    bank_name = models.CharField(
        max_length=50,
        choices=BANK_CHOICES,
        verbose_name="نام بانک"
    )
    
    account_number = models.CharField(
        max_length=50,
        verbose_name="شماره حساب/کارت",
        help_text="شماره شبا یا شماره کارت 16 رقمی"
    )
    
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="تایید شده",
        help_text="آیا توسط ادمین تایید شده است؟"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال",
        help_text="آیا این حساب برای واریز/برداشت فعال است؟"
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
        verbose_name = "حساب بانکی"
        verbose_name_plural = "حساب‌های بانکی"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', 'is_verified']),
            models.Index(fields=['is_verified', 'is_active']),
        ]
    
    def __str__(self) -> str:
        """Return string representation."""
        masked_account = self.get_masked_account_number()
        return f"{self.bank_name} - {masked_account} ({self.profile.get_display_name()})"
    
    def get_masked_account_number(self) -> str:
        """Return masked account number (last 4 digits visible)."""
        if len(self.account_number) >= 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number
    
    def can_be_used_for_transactions(self) -> bool:
        """Check if account can be used for transactions."""
        return self.is_verified and self.is_active
