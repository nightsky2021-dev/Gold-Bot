"""
Trading models for the gold trading system.

This module contains Product and Order models for managing
gold products and user orders.
"""

from typing import Optional
from decimal import Decimal

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils import timezone

from users.models import Profile, BankAccount


class Product(models.Model):
    """
    Represents a tradeable gold product.
    
    Stores product information including name, prices, and availability.
    Prices are updated periodically via management command.
    """
    
    # Product code constants for standardized product identification
    PRODUCT_CODE_GOLD = 'gold'  # طلای آبشده
    PRODUCT_CODE_COIN = 'coin'  # سکه تمام
    PRODUCT_CODE_DOLLAR = 'dollar'  # دلار آمریکا
    
    PRODUCT_CODE_CHOICES = [
        (PRODUCT_CODE_GOLD, 'طلای آبشده'),
        (PRODUCT_CODE_COIN, 'سکه تمام'),
        (PRODUCT_CODE_DOLLAR, 'دلار آمریکا'),
    ]
    
    product_code = models.CharField(
        max_length=20,
        unique=True,
        choices=PRODUCT_CODE_CHOICES,
        verbose_name="کد محصول",
        help_text="کد یکتای محصول برای شناسایی",
        db_index=True
    )
    
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="نام محصول",
        help_text="نام محصول (مثل: سکه بهار آزادی، طلای 18 عیار)"
    )
    
    slug = models.SlugField(
        unique=True,
        blank=True,
        verbose_name="اسلاگ",
        help_text="به صورت خودکار از روی نام ساخته می‌شود"
    )
    
    buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت خرید ما از مشتری",
        help_text="قیمت خرید هر گرم از مشتری (ریال)"
    )
    
    sell_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت فروش ما به مشتری",
        help_text="قیمت فروش هر گرم به مشتری (ریال)"
    )
    
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        verbose_name="فعال برای معامله",
        help_text="آیا این محصول برای معامله فعال است؟"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی قیمت"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ایجاد"
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['name']
        indexes = [
            models.Index(fields=['is_active', 'name']),
        ]

    def save(self, *args, **kwargs):
        """Override save to auto-generate slug from name."""
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        """Return string representation of the product."""
        return self.name
    
    def get_price_spread(self) -> Decimal:
        """Calculate the price spread (difference between sell and buy)."""
        return self.sell_price - self.buy_price
    
    def get_price_spread_percentage(self) -> Decimal:
        """Calculate the price spread as a percentage of buy price."""
        if self.buy_price > 0:
            return (self.get_price_spread() / self.buy_price) * 100
        return Decimal('0')
    
    @classmethod
    def get_by_code(cls, product_code: str) -> 'Product':
        """
        Get a product by its product code.
        
        Args:
            product_code: The product code (e.g., 'gold', 'coin', 'dollar')
            
        Returns:
            Product instance
            
        Raises:
            Product.DoesNotExist: If product not found
        """
        return cls.objects.get(product_code=product_code, is_active=True)


class Order(models.Model):
    """
    Represents a buy or sell order for gold products.
    
    Orders are created in PENDING status and processed by admin.
    Upon completion, user balances are updated atomically.
    """
    
    class OrderType(models.TextChoices):
        BUY = 'BUY', 'خرید از ما'
        SELL = 'SELL', 'فروش به ما'

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار بررسی'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'

    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="پروفایل کاربر",
        help_text="کاربری که این سفارش را ثبت کرده"
    )
    
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="محصول",
        help_text="محصول مورد معامله"
    )
    
    order_type = models.CharField(
        max_length=4,
        choices=OrderType.choices,
        verbose_name="نوع سفارش",
        help_text="خرید از ما یا فروش به ما"
    )
    
    quantity_grams = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="مقدار (گرم)",
        help_text="مقدار طلا به گرم"
    )
    
    price_per_gram = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="قیمت هر گرم (لحظه ثبت)",
        help_text="قیمت هر گرم در زمان ثبت سفارش (ریال)"
    )
    
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name="مبلغ کل (ریال)",
        help_text="مبلغ کل سفارش (ریال)"
    )
    
    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت فعلی سفارش"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ثبت"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تکمیل",
        help_text="زمان تکمیل سفارش"
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها",
        help_text="یادداشت‌های داخلی برای ادمین"
    )

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['order_type', 'status']),
        ]

    def __str__(self) -> str:
        """Return string representation of the order."""
        return f"سفارش {self.id} – {self.profile.get_display_name()} – {self.get_order_type_display()}"
    
    def calculate_total(self) -> Decimal:
        """Calculate total amount based on quantity and price per gram."""
        return self.quantity_grams * self.price_per_gram
    
    def is_pending(self) -> bool:
        """Check if order is in pending status."""
        return self.status == self.OrderStatus.PENDING
    
    def is_completed(self) -> bool:
        """Check if order is completed."""
        return self.status == self.OrderStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == self.OrderStatus.CANCELLED
    
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled (only pending orders)."""
        return self.is_pending()


class Transaction(models.Model):
    """
    Financial transaction model for tracking all money movements.
    
    Records deposits, withdrawals, transfers, and trading transactions
    with complete audit trail and balance tracking.
    """
    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'واریز وجه'
        WITHDRAW = 'WITHDRAW', 'برداشت وجه'
        TRANSFER_SEND = 'TRANSFER_SEND', 'انتقال وجه (ارسال)'
        TRANSFER_RECEIVE = 'TRANSFER_RECEIVE', 'انتقال وجه (دریافت)'
        BUY = 'BUY', 'خرید محصول'
        SELL = 'SELL', 'فروش محصول'
    
    class CurrencyType(models.TextChoices):
        RIAL = 'RIAL', 'ریال'
        GOLD = 'GOLD', 'طلا'
        COIN = 'COIN', 'سکه'
        DOLLAR = 'DOLLAR', 'دلار'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'
        FAILED = 'FAILED', 'ناموفق'
    
    transaction_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="شماره تراکنش",
        help_text="شماره یکتای تراکنش (مثل: TXN-20241024-001)"
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name="پروفایل",
        help_text="کاربر صاحب تراکنش"
    )
    
    transaction_type = models.CharField(
        max_length=15,
        choices=TransactionType.choices,
        verbose_name="نوع تراکنش",
        help_text="نوع عملیات مالی"
    )
    
    currency_type = models.CharField(
        max_length=6,
        choices=CurrencyType.choices,
        verbose_name="نوع ارز",
        help_text="نوع ارز مورد معامله"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="مقدار",
        help_text="مقدار تراکنش"
    )
    
    balance_before = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="موجودی قبل",
        help_text="موجودی قبل از تراکنش"
    )
    
    balance_after = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="موجودی بعد",
        help_text="موجودی بعد از تراکنش"
    )
    
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت فعلی تراکنش"
    )
    
    related_bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="حساب بانکی مرتبط",
        help_text="حساب بانکی مربوط به واریز/برداشت"
    )
    
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="سفارش مرتبط",
        help_text="سفارش مربوط به خرید/فروش"
    )
    
    admin_note = models.TextField(
        blank=True,
        verbose_name="یادداشت ادمین",
        help_text="یادداشت‌های ادمین"
    )
    
    user_note = models.TextField(
        blank=True,
        verbose_name="یادداشت کاربر",
        help_text="یادداشت‌های کاربر"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ایجاد"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تکمیل",
        help_text="زمان تکمیل تراکنش"
    )

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['currency_type', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation of the transaction."""
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - {self.amount} {self.get_currency_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to generate transaction number if not provided."""
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self) -> str:
        """Generate unique transaction number."""
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        
        # Get count of transactions today
        today_count = Transaction.objects.filter(
            created_at__date=now.date()
        ).count()
        
        return f"TXN-{date_str}-{today_count + 1:03d}"
    
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == self.TransactionStatus.PENDING
    
    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == self.TransactionStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if transaction is cancelled."""
        return self.status == self.TransactionStatus.CANCELLED
    
    def can_be_cancelled(self) -> bool:
        """Check if transaction can be cancelled."""
        return self.is_pending()


class WithdrawRequest(models.Model):
    """
    Withdraw request model for managing user withdrawal requests.
    
    Handles the complete withdrawal workflow from request to completion.
    """
    
    class CurrencyType(models.TextChoices):
        RIAL = 'RIAL', 'ریال'
        GOLD = 'GOLD', 'طلا'
        COIN = 'COIN', 'سکه'
        DOLLAR = 'DOLLAR', 'دلار'
    
    class WithdrawStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار بررسی'
        APPROVED = 'APPROVED', 'تایید شده'
        REJECTED = 'REJECTED', 'رد شده'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
    
    request_number = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        verbose_name="شماره درخواست",
        help_text="شماره یکتای درخواست برداشت"
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='withdraw_requests',
        verbose_name="پروفایل",
        help_text="کاربر درخواست‌دهنده"
    )
    
    bank_account = models.ForeignKey(
        BankAccount,
        on_delete=models.CASCADE,
        related_name='withdraw_requests',
        verbose_name="حساب بانکی مقصد",
        help_text="حساب بانکی برای واریز وجه"
    )
    
    currency_type = models.CharField(
        max_length=6,
        choices=CurrencyType.choices,
        verbose_name="نوع ارز",
        help_text="نوع ارز مورد برداشت"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="مقدار",
        help_text="مقدار درخواستی برای برداشت"
    )
    
    status = models.CharField(
        max_length=10,
        choices=WithdrawStatus.choices,
        default=WithdrawStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت فعلی درخواست"
    )
    
    related_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='withdraw_request',
        null=True,
        blank=True,
        verbose_name="تراکنش مرتبط",
        help_text="تراکنش مربوط به این درخواست"
    )
    
    admin_note = models.TextField(
        blank=True,
        verbose_name="یادداشت ادمین",
        help_text="دلیل رد یا توضیحات ادمین"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ایجاد"
    )
    
    processed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ پردازش",
        help_text="زمان پردازش توسط ادمین"
    )
    
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="تاریخ تکمیل",
        help_text="زمان تکمیل برداشت"
    )

    class Meta:
        verbose_name = "درخواست برداشت"
        verbose_name_plural = "درخواست‌های برداشت"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['currency_type', 'status']),
        ]

    def __str__(self) -> str:
        """Return string representation of the withdraw request."""
        return f"{self.request_number} - {self.profile.get_display_name()} - {self.amount} {self.get_currency_type_display()}"
    
    def save(self, *args, **kwargs):
        """Override save to generate request number if not provided."""
        if not self.request_number:
            self.request_number = self.generate_request_number()
        super().save(*args, **kwargs)
    
    def generate_request_number(self) -> str:
        """Generate unique request number."""
        from datetime import datetime
        now = datetime.now()
        date_str = now.strftime('%Y%m%d')
        
        # Get count of requests today
        today_count = WithdrawRequest.objects.filter(
            created_at__date=now.date()
        ).count()
        
        return f"WDR-{date_str}-{today_count + 1:03d}"
    
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == self.WithdrawStatus.PENDING
    
    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == self.WithdrawStatus.APPROVED
    
    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == self.WithdrawStatus.REJECTED
    
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == self.WithdrawStatus.COMPLETED
    
    def can_be_approved(self) -> bool:
        """Check if request can be approved."""
        return self.is_pending()
    
    def can_be_rejected(self) -> bool:
        """Check if request can be rejected."""
        return self.is_pending()
