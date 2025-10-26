"""
Trading models for the gold trading system.

This module contains Product and Order models for managing
gold products and user orders.
"""

from typing import Optional
from decimal import Decimal
from datetime import datetime

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils import timezone

from users.models import Profile


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
    Financial transaction record for all wallet operations.
    
    Tracks all financial movements including deposits, withdrawals,
    and trading operations.
    """
    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'واریز'
        WITHDRAW = 'WITHDRAW', 'برداشت'
        TRANSFER_SEND = 'TRANSFER_SEND', 'انتقال - ارسال'
        TRANSFER_RECEIVE = 'TRANSFER_RECEIVE', 'انتقال - دریافت'
        BUY = 'BUY', 'خرید'
        SELL = 'SELL', 'فروش'
    
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
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="شماره تراکنش",
        help_text="شماره یونیک تراکنش"
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="پروفایل",
        help_text="کاربر صاحب تراکنش"
    )
    
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        db_index=True,
        verbose_name="نوع تراکنش",
        help_text="نوع تراکنش"
    )
    
    currency_type = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        db_index=True,
        verbose_name="نوع ارز",
        help_text="نوع ارز"
    )
    
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="مقدار",
        help_text="مقدار تراکنش"
    )
    
    balance_before = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        verbose_name="موجودی قبل",
        help_text="موجودی قبل از تراکنش"
    )
    
    balance_after = models.DecimalField(
        max_digits=20,
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
        help_text="وضعیت تراکنش"
    )
    
    related_bank_account = models.ForeignKey(
        'users.BankAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="حساب بانکی مرتبط",
        help_text="حساب بانکی مرتبط (برای واریز/برداشت)"
    )
    
    related_order = models.ForeignKey(
        Order,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="سفارش مرتبط",
        help_text="سفارش مرتبط (برای خرید/فروش)"
    )
    
    admin_note = models.TextField(
        blank=True,
        verbose_name="یادداشت ادمین",
        help_text="یادداشت داخلی ادمین"
    )
    
    user_note = models.TextField(
        blank=True,
        verbose_name="یادداشت کاربر",
        help_text="یادداشت کاربر"
    )
    
    receipt_image = models.ImageField(
        upload_to='transaction_receipts/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="تصویر رسید",
        help_text="تصویر رسید (برای واریز)"
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
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
    )

    class Meta:
        verbose_name = "تراکنش"
        verbose_name_plural = "تراکنش‌ها"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['currency_type', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation of the transaction."""
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - {self.amount} {self.get_currency_type_display()}"
    
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == self.TransactionStatus.PENDING
    
    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == self.TransactionStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if transaction is cancelled."""
        return self.status == self.TransactionStatus.CANCELLED
    
    @classmethod
    def generate_transaction_number(cls) -> str:
        """Generate a unique transaction number."""
        from django.utils import timezone
        now = timezone.now()
        date_str = now.strftime('%Y%m%d')
        
        # Get count of transactions today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count = cls.objects.filter(created_at__gte=today_start).count() + 1
        
        return f"TXN-{date_str}-{count:04d}"


class WithdrawRequest(models.Model):
    """
    Withdrawal request from user.
    
    Users create withdrawal requests which must be approved by admin.
    Balance is frozen during the approval process.
    """
    
    class RequestStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار بررسی'
        APPROVED = 'APPROVED', 'تایید شده'
        REJECTED = 'REJECTED', 'رد شده'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
    
    request_number = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name="شماره درخواست",
        help_text="شماره یونیک درخواست"
    )
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='withdraw_requests',
        verbose_name="پروفایل",
        help_text="کاربر درخواست‌کننده"
    )
    
    bank_account = models.ForeignKey(
        'users.BankAccount',
        on_delete=models.PROTECT,
        related_name='withdraw_requests',
        verbose_name="حساب بانکی مقصد",
        help_text="حساب بانکی مقصد برای واریز"
    )
    
    currency_type = models.CharField(
        max_length=10,
        choices=Transaction.CurrencyType.choices,
        db_index=True,
        verbose_name="نوع ارز",
        help_text="نوع ارز"
    )
    
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="مقدار",
        help_text="مقدار درخواستی"
    )
    
    status = models.CharField(
        max_length=10,
        choices=RequestStatus.choices,
        default=RequestStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت درخواست"
    )
    
    related_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdraw_request',
        verbose_name="تراکنش مرتبط",
        help_text="تراکنش مرتبط با این درخواست"
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
        help_text="زمان تکمیل نهایی"
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
        """Return string representation of the withdrawal request."""
        return f"{self.request_number} - {self.profile.get_display_name()} - {self.amount} {self.get_currency_type_display()}"
    
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == self.RequestStatus.PENDING
    
    def is_approved(self) -> bool:
        """Check if request is approved."""
        return self.status == self.RequestStatus.APPROVED
    
    def is_rejected(self) -> bool:
        """Check if request is rejected."""
        return self.status == self.RequestStatus.REJECTED
    
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == self.RequestStatus.COMPLETED
    
    @classmethod
    def generate_request_number(cls) -> str:
        """Generate a unique request number."""
        from django.utils import timezone
        now = timezone.now()
        date_str = now.strftime('%Y%m%d')
        
        # Get count of requests today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        count = cls.objects.filter(created_at__gte=today_start).count() + 1
        
        return f"WDR-{date_str}-{count:04d}"
