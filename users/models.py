"""
User models for the gold trading system.

This module contains the Profile model which extends Django's User model
with Telegram-specific and trading-related fields.
"""

from typing import Optional
from decimal import Decimal
import re

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator, RegexValidator
from django.core.exceptions import ValidationError
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
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه",
        help_text="موجودی سکه تمام کاربر"
    )
    
    dollar_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار",
        help_text="موجودی دلار کاربر"
    )
    
    # Frozen balances for pending transactions
    frozen_rial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی ریالی مسدود شده",
        help_text="موجودی ریالی مسدود شده برای تراکنش‌های در حال انجام"
    )
    
    frozen_gold_balance = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی طلای مسدود شده",
        help_text="موجودی طلای مسدود شده برای تراکنش‌های در حال انجام"
    )
    
    frozen_coin_balance = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه مسدود شده",
        help_text="موجودی سکه مسدود شده برای تراکنش‌های در حال انجام"
    )
    
    frozen_dollar_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار مسدود شده",
        help_text="موجودی دلار مسدود شده برای تراکنش‌های در حال انجام"
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
        """Get available (unfrozen) balance for a currency type."""
        currency_map = {
            'RIAL': self.rial_balance - self.frozen_rial_balance,
            'GOLD': self.gold_balance_grams - self.frozen_gold_balance,
            'COIN': self.coin_balance - self.frozen_coin_balance,
            'DOLLAR': self.dollar_balance - self.frozen_dollar_balance,
        }
        return currency_map.get(currency_type, Decimal('0'))


class BankAccount(models.Model):
    """
    User's bank account for deposits and withdrawals.
    
    Each user can have multiple bank accounts. Only verified accounts
    can be used for financial transactions.
    """
    
    class AccountType(models.TextChoices):
        CARD = 'CARD', 'کارت بانکی'
        IBAN = 'IBAN', 'شماره شبا'
    
    # List of Iranian banks
    IRANIAN_BANKS = [
        ('ملی ایران', 'ملی ایران'),
        ('ملت', 'ملت'),
        ('تجارت', 'تجارت'),
        ('صادرات', 'صادرات'),
        ('سپه', 'سپه'),
        ('رفاه', 'رفاه'),
        ('پاسارگاد', 'پاسارگاد'),
        ('پارسیان', 'پارسیان'),
        ('اقتصاد نوین', 'اقتصاد نوین'),
        ('سامان', 'سامان'),
        ('سینا', 'سینا'),
        ('کارآفرین', 'کارآفرین'),
        ('آینده', 'آینده'),
        ('شهر', 'شهر'),
        ('دی', 'دی'),
        ('صنعت و معدن', 'صنعت و معدن'),
        ('توسعه تعاون', 'توسعه تعاون'),
        ('قوامین', 'قوامین'),
        ('مهر اقتصاد', 'مهر اقتصاد'),
        ('حکمت ایرانیان', 'حکمت ایرانیان'),
    ]
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name="پروفایل",
        help_text="پروفایل صاحب حساب"
    )
    
    account_holder_name = models.CharField(
        max_length=200,
        verbose_name="نام صاحب حساب",
        help_text="نام صاحب حساب (باید با نام کاربر مطابقت داشته باشد)"
    )
    
    bank_name = models.CharField(
        max_length=50,
        choices=IRANIAN_BANKS,
        verbose_name="نام بانک",
        help_text="نام بانک"
    )
    
    account_number = models.CharField(
        max_length=26,
        verbose_name="شماره حساب",
        help_text="شماره کارت 16 رقمی یا شماره شبا (IR + 24 رقم)"
    )
    
    account_type = models.CharField(
        max_length=4,
        choices=AccountType.choices,
        verbose_name="نوع حساب",
        help_text="نوع حساب: کارت بانکی یا شماره شبا"
    )
    
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="تایید شده",
        help_text="آیا این حساب توسط ادمین تایید شده است؟"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
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
        unique_together = [['profile', 'account_number']]

    def __str__(self) -> str:
        """Return string representation of the bank account."""
        masked_number = self.get_masked_account_number()
        return f"{self.bank_name} - {masked_number}"
    
    def clean(self):
        """Validate account number based on account type."""
        super().clean()
        
        if self.account_type == self.AccountType.CARD:
            # Validate 16-digit card number
            if not re.match(r'^\d{16}$', self.account_number):
                raise ValidationError({
                    'account_number': 'شماره کارت باید 16 رقم باشد.'
                })
        elif self.account_type == self.AccountType.IBAN:
            # Validate Iranian IBAN (IR + 24 digits)
            if not re.match(r'^IR\d{24}$', self.account_number.upper()):
                raise ValidationError({
                    'account_number': 'شماره شبا باید به صورت IR و 24 رقم باشد.'
                })
            # Normalize IBAN to uppercase
            self.account_number = self.account_number.upper()
        
        # Validate account holder name matches user's name
        user_full_name = f"{self.profile.user.first_name} {self.profile.user.last_name}".strip()
        if user_full_name and self.account_holder_name.strip() != user_full_name:
            # Allow if either is empty (for cases where user hasn't set name yet)
            if user_full_name and self.account_holder_name.strip():
                raise ValidationError({
                    'account_holder_name': f'نام صاحب حساب باید با نام کاربر ({user_full_name}) مطابقت داشته باشد.'
                })
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_masked_account_number(self) -> str:
        """Return masked account number for display."""
        if len(self.account_number) <= 4:
            return self.account_number
        return f"****{self.account_number[-4:]}"
    
    def can_be_used_for_transaction(self) -> bool:
        """Check if this account can be used for transactions."""
        return self.is_verified and self.is_active
