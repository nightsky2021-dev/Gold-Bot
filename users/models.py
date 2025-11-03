"""
User models for the gold trading system.

This module contains the Profile model which extends Django's User model
with Telegram-specific and trading-related fields.
"""

from typing import Optional, TYPE_CHECKING
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models import Manager
    from trading.models import Order


class Profile(models.Model):
    """
    Extended user profile for gold trading system.
    
    Stores Telegram-specific information and user balances (Rial and Gold).
    Related to Django's built-in User model via OneToOneField.
    """
    
    if TYPE_CHECKING:
        # Type hints for reverse relationships
        orders: 'Manager[Order]'
    
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
    
    # Frozen balances for pending withdrawals
    frozen_rial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی ریالی مسدود شده",
        help_text="موجودی ریالی که به دلیل برداشت در انتظار مسدود شده"
    )
    
    frozen_gold_balance = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=Decimal('0.0000'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی طلای مسدود شده",
        help_text="موجودی طلا که به دلیل برداشت در انتظار مسدود شده"
    )
    
    # Coin balances
    coin_balance = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه",
        help_text="موجودی سکه کاربر"
    )
    
    frozen_coin_balance = models.DecimalField(
        max_digits=10,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی سکه مسدود شده",
        help_text="موجودی سکه که به دلیل برداشت در انتظار مسدود شده"
    )
    
    # Dollar balances
    dollar_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار",
        help_text="موجودی دلار کاربر"
    )
    
    frozen_dollar_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی دلار مسدود شده",
        help_text="موجودی دلار که به دلیل برداشت در انتظار مسدود شده"
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
    
    def get_available_rial_balance(self) -> Decimal:
        """Get available Rial balance (total - frozen)."""
        return self.rial_balance - self.frozen_rial_balance
    
    def get_available_gold_balance(self) -> Decimal:
        """Get available gold balance (total - frozen)."""
        return self.gold_balance_grams - self.frozen_gold_balance
    
    def has_sufficient_available_rial(self, amount: Decimal) -> bool:
        """Check if user has sufficient available Rial balance."""
        return self.get_available_rial_balance() >= amount
    
    def has_sufficient_available_gold(self, amount_grams: Decimal) -> bool:
        """Check if user has sufficient available gold balance."""
        return self.get_available_gold_balance() >= amount_grams
    
    def get_available_coin_balance(self) -> Decimal:
        """Get available coin balance (total - frozen)."""
        return self.coin_balance - self.frozen_coin_balance
    
    def get_available_dollar_balance(self) -> Decimal:
        """Get available dollar balance (total - frozen)."""
        return self.dollar_balance - self.frozen_dollar_balance
    
    def has_sufficient_coin_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient coin balance."""
        return self.coin_balance >= amount
    
    def has_sufficient_dollar_balance(self, amount: Decimal) -> bool:
        """Check if user has sufficient dollar balance."""
        return self.dollar_balance >= amount
    
    def has_sufficient_available_coin(self, amount: Decimal) -> bool:
        """Check if user has sufficient available coin balance."""
        return self.get_available_coin_balance() >= amount
    
    def has_sufficient_available_dollar(self, amount: Decimal) -> bool:
        """Check if user has sufficient available dollar balance."""
        return self.get_available_dollar_balance() >= amount
    
    def get_available_balance(self, currency_type: str) -> Decimal:
        """
        Get available balance for a given currency type.
        
        Args:
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Available balance amount for the specified currency.
        """
        if currency_type == 'RIAL':
            return self.get_available_rial_balance()
        elif currency_type == 'GOLD':
            return self.get_available_gold_balance()
        elif currency_type == 'COIN':
            return self.get_available_coin_balance()
        elif currency_type == 'DOLLAR':
            return self.get_available_dollar_balance()
        else:
            return Decimal('0')


class BankAccount(models.Model):
    """
    Bank account information for deposits and withdrawals.
    
    Stores user's bank account details for financial transactions.
    Must be verified by admin before use.
    """
    
    class AccountType(models.TextChoices):
        SAVINGS = 'SAVINGS', 'حساب پس‌انداز'
        CURRENT = 'CURRENT', 'حساب جاری'
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='bank_accounts',
        verbose_name="پروفایل کاربر",
        help_text="کاربری که این حساب متعلق به اوست"
    )
    
    bank_name = models.CharField(
        max_length=100,
        verbose_name="نام بانک",
        help_text="نام بانک (مثل: ملی، ملت، سپه)"
    )
    
    account_holder_name = models.CharField(
        max_length=200,
        verbose_name="نام صاحب حساب",
        help_text="نام کامل صاحب حساب"
    )
    
    account_number = models.CharField(
        max_length=16,
        verbose_name="شماره حساب",
        help_text="شماره حساب 16 رقمی"
    )
    
    iban = models.CharField(
        max_length=26,
        blank=True,
        verbose_name="شماره شبا",
        help_text="شماره شبای 26 رقمی (اختیاری)"
    )
    
    account_type = models.CharField(
        max_length=10,
        choices=AccountType.choices,
        default=AccountType.SAVINGS,
        verbose_name="نوع حساب",
        help_text="نوع حساب بانکی"
    )
    
    is_verified = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="تأیید شده",
        help_text="آیا این حساب توسط ادمین تأیید شده است؟"
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
            models.Index(fields=['account_number']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['profile', 'account_number'],
                name='unique_profile_account'
            )
        ]

    def __str__(self) -> str:
        """Return string representation of the bank account."""
        masked_account = self.get_masked_account_number()
        return f"{self.bank_name} - {masked_account} ({self.profile.get_display_name()})"
    
    def get_masked_account_number(self) -> str:
        """Get masked account number for display (show only last 4 digits)."""
        if len(self.account_number) >= 4:
            return f"****{self.account_number[-4:]}"
        return self.account_number
    
    def can_be_used(self) -> bool:
        """Check if account can be used for transactions."""
        return self.is_verified
    
    def has_pending_transactions(self) -> bool:
        """Check if account has pending transactions."""
        # Import here to avoid circular import
        from trading.models import Transaction, WithdrawRequest
        
        pending_deposits = Transaction.objects.filter(
            bank_account=self,
            status='pending'
        ).exists()
        
        pending_withdrawals = WithdrawRequest.objects.filter(
            bank_account=self,
            status='pending'
        ).exists()
        
        return pending_deposits or pending_withdrawals
