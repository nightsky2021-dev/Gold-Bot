"""
Trading models for the gold trading system.

This module contains Product and Order models for managing
gold products and user orders.
"""

from typing import Optional, cast, TYPE_CHECKING
from decimal import Decimal

from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils import timezone

from users.models import Profile

if TYPE_CHECKING:
    from django.db.models import Manager


class Product(models.Model):
    """
    Represents a tradeable gold product.
    
    Stores product information including name, prices, and availability.
    Prices are updated periodically via management command.
    """
    
    # Type annotations for auto-generated Django fields
    id: int
    
    if TYPE_CHECKING:
        # Reverse relationship from Order model
        orders: 'Manager["Order"]'
    
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
    
    # Pricing calculation parameters (what admins configure)
    buy_margin = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="مارجین خرید (ریال)",
        help_text="مارجین خرید از مشتری - این مقدار از قیمت بازار کم می‌شود تا قیمت خرید محاسبه شود"
    )
    
    sell_margin = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        default=Decimal('0'),
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="مارجین فروش (ریال)",
        help_text="مارجین فروش به مشتری - این مقدار به قیمت بازار اضافه می‌شود تا قیمت فروش محاسبه شود"
    )
    
    weight_grams = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=Decimal('1'),
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="وزن واحد (گرم)",
        help_text="وزن یک واحد محصول به گرم - برای طلا و دلار = 1، برای سکه = 8.133 یا به تناسب نوع سکه"
    )
    
    # Calculated prices (auto-updated from API + margins)
    buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت خرید ما از مشتری",
        help_text="قیمت محاسبه شده - به صورت خودکار از API + مارجین‌ها محاسبه می‌شود"
    )
    
    sell_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت فروش ما به مشتری",
        help_text="قیمت محاسبه شده - به صورت خودکار از API + مارجین‌ها محاسبه می‌شود"
    )
    
    base_price_api = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        null=True,
        blank=True,
        verbose_name="قیمت پایه از API",
        help_text="آخرین قیمت دریافتی از API (قبل از اعمال مارجین)"
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
    
    def calculate_prices_from_base(self, base_price: Decimal) -> tuple[Decimal, Decimal]:
        """
        Calculate buy and sell prices from a base market price.
        
        Args:
            base_price: The base price from API (per gram or unit)
            
        Returns:
            Tuple of (buy_price, sell_price) calculated with margins
        """
        # For products with weight > 1 gram (like coins), multiply base by weight
        adjusted_base = base_price * self.weight_grams
        
        buy_price = (adjusted_base - self.buy_margin).quantize(Decimal('1'))
        sell_price = (adjusted_base + self.sell_margin).quantize(Decimal('1'))
        
        return buy_price, sell_price
    
    def update_prices_from_api(self, api_base_price: Decimal) -> None:
        """
        Update prices based on API base price and configured margins.
        
        Args:
            api_base_price: Base price from API (per gram)
        """
        self.base_price_api = api_base_price
        self.buy_price, self.sell_price = self.calculate_prices_from_base(api_base_price)
    
    def get_price_spread(self) -> Decimal:
        """Calculate the price spread (difference between sell and buy)."""
        return self.sell_price - self.buy_price
    
    def get_total_margin(self) -> Decimal:
        """Get total margin (buy + sell)."""
        return self.buy_margin + self.sell_margin
    
    def get_price_spread_percentage(self) -> Decimal:
        """Calculate the price spread as a percentage of buy price."""
        if self.buy_price > 0:
            return (self.get_price_spread() / self.buy_price) * 100
        return Decimal('0')
    
    def get_margin_info_display(self) -> str:
        """Get formatted string showing margin configuration."""
        return (
            f"مارجین خرید: {self.buy_margin:,} ریال | "
            f"مارجین فروش: {self.sell_margin:,} ریال | "
            f"مجموع: {self.get_total_margin():,} ریال"
        )
    
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
    
    Orders are executed instantly with atomic balance updates.
    All orders are created directly in COMPLETED or REJECTED status.
    """
    
    # Type annotations for auto-generated Django fields
    id: int
    
    class OrderType(models.TextChoices):
        BUY = 'BUY', 'خرید از ما'
        SELL = 'SELL', 'فروش به ما'

    class OrderStatus(models.TextChoices):
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'
        REJECTED = 'REJECTED', 'رد شده'

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
    
    def is_rejected(self) -> bool:
        """Check if order is rejected."""
        return self.status == self.OrderStatus.REJECTED
    
    def is_completed(self) -> bool:
        """Check if order is completed."""
        return self.status == self.OrderStatus.COMPLETED
    
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == self.OrderStatus.CANCELLED
    
    def can_be_cancelled(self) -> bool:
        """Check if order can be cancelled (instant orders cannot be cancelled)."""
        return False  # Orders are instant and cannot be cancelled after execution
    
    def get_order_type_display(self) -> str:
        """Get display value for order_type field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.OrderType.choices).get(self.order_type, self.order_type))
    
    def get_status_display(self) -> str:
        """Get display value for status field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.OrderStatus.choices).get(self.status, self.status))


class Transaction(models.Model):
    """
    Represents a financial transaction (deposit/withdraw/buy/sell).
    
    Tracks all balance changes with full audit trail.
    """
    
    # Type annotations for auto-generated Django fields
    id: int
    
    class TransactionType(models.TextChoices):
        DEPOSIT = 'DEPOSIT', 'واریز'
        WITHDRAW = 'WITHDRAW', 'برداشت'
        BUY = 'BUY', 'خرید'
        SELL = 'SELL', 'فروش'
        ADJUSTMENT = 'ADJUSTMENT', 'تعدیل'
    
    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'
        REJECTED = 'REJECTED', 'رد شده'
    
    class CurrencyType(models.TextChoices):
        RIAL = 'RIAL', 'ریال'
        GOLD = 'GOLD', 'طلا'
        COIN = 'COIN', 'سکه'
        DOLLAR = 'DOLLAR', 'دلار'
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name="پروفایل کاربر",
        help_text="کاربر مربوط به این تراکنش"
    )
    
    transaction_type = models.CharField(
        max_length=15,
        choices=TransactionType.choices,
        verbose_name="نوع تراکنش",
        help_text="نوع عملیات انجام شده"
    )
    
    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        verbose_name="ارز",
        help_text="نوع ارز تراکنش"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="مقدار",
        help_text="مقدار تراکنش"
    )
    
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت فعلی تراکنش"
    )
    
    bank_account = models.ForeignKey(
        'users.BankAccount',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name="حساب بانکی",
        help_text="حساب بانکی مرتبط (برای واریز/برداشت)"
    )
    
    receipt_image = models.ImageField(
        upload_to='receipts/%Y/%m/',
        null=True,
        blank=True,
        verbose_name="تصویر رسید",
        help_text="تصویر رسید واریز (فقط برای واریز ریالی)"
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
    
    description = models.TextField(
        blank=True,
        verbose_name="توضیحات",
        help_text="توضیحات تراکنش"
    )
    
    admin_notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌های مدیر",
        help_text="یادداشت‌های داخلی برای مدیر"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ایجاد"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی"
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
        ]

    def __str__(self) -> str:
        """Return string representation of the transaction."""
        return f"تراکنش {self.id} – {self.get_transaction_type_display()} – {self.profile.get_display_name()}"
    
    def is_pending(self) -> bool:
        """Check if transaction is pending."""
        return self.status == self.TransactionStatus.PENDING
    
    def is_completed(self) -> bool:
        """Check if transaction is completed."""
        return self.status == self.TransactionStatus.COMPLETED
    
    def get_currency_display_name(self) -> str:
        """Get Persian display name for currency."""
        currency_names = {
            'RIAL': 'ریال',
            'GOLD': 'گرم طلا',
            'COIN': 'سکه',
            'DOLLAR': 'دلار'
        }
        return cast(str, currency_names.get(self.currency, self.currency))
    
    def get_transaction_type_display(self) -> str:
        """Get display value for transaction_type field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.TransactionType.choices).get(self.transaction_type, self.transaction_type))
    
    def get_currency_display(self) -> str:
        """Get display value for currency field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.CurrencyType.choices).get(self.currency, self.currency))
    
    def get_status_display(self) -> str:
        """Get display value for status field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.TransactionStatus.choices).get(self.status, self.status))


class WithdrawRequest(models.Model):
    """
    Represents a withdrawal request from user's balance.
    
    User initiates withdrawal, balance is frozen, admin processes it.
    """
    
    # Type annotations for auto-generated Django fields
    id: int
    
    class WithdrawStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار'
        PROCESSING = 'PROCESSING', 'در حال پردازش'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'
        REJECTED = 'REJECTED', 'رد شده'
    
    class CurrencyType(models.TextChoices):
        RIAL = 'RIAL', 'ریال'
        GOLD = 'GOLD', 'طلا'
        COIN = 'COIN', 'سکه'
        DOLLAR = 'DOLLAR', 'دلار'
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.PROTECT,
        related_name='withdraw_requests',
        verbose_name="پروفایل کاربر",
        help_text="کاربر درخواست‌کننده"
    )
    
    currency = models.CharField(
        max_length=10,
        choices=CurrencyType.choices,
        verbose_name="ارز",
        help_text="نوع ارز برداشت"
    )
    
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        verbose_name="مقدار",
        help_text="مقدار برداشت"
    )
    
    bank_account = models.ForeignKey(
        'users.BankAccount',
        on_delete=models.PROTECT,
        related_name='withdraw_requests',
        verbose_name="حساب بانکی مقصد",
        help_text="حساب بانکی که باید به آن واریز شود"
    )
    
    status = models.CharField(
        max_length=15,
        choices=WithdrawStatus.choices,
        default=WithdrawStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت",
        help_text="وضعیت فعلی درخواست"
    )
    
    related_transaction = models.OneToOneField(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='withdraw_request',
        verbose_name="تراکنش مرتبط",
        help_text="تراکنش ثبت شده برای این برداشت"
    )
    
    rejection_reason = models.TextField(
        blank=True,
        verbose_name="دلیل رد",
        help_text="دلیل رد درخواست (در صورت رد)"
    )
    
    admin_notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌های مدیر",
        help_text="یادداشت‌های داخلی برای مدیر"
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
        help_text="زمان تکمیل درخواست"
    )

    class Meta:
        verbose_name = "درخواست برداشت"
        verbose_name_plural = "درخواست‌های برداشت"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profile', '-created_at']),
            models.Index(fields=['status', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation of the withdraw request."""
        return f"برداشت {self.id} – {self.amount} {self.get_currency_display()} – {self.profile.get_display_name()}"
    
    def is_pending(self) -> bool:
        """Check if request is pending."""
        return self.status == self.WithdrawStatus.PENDING
    
    def is_completed(self) -> bool:
        """Check if request is completed."""
        return self.status == self.WithdrawStatus.COMPLETED
    
    def can_be_cancelled(self) -> bool:
        """Check if request can be cancelled."""
        return self.status in [self.WithdrawStatus.PENDING, self.WithdrawStatus.PROCESSING]
    
    def get_currency_display(self) -> str:
        """Get display value for currency field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.CurrencyType.choices).get(self.currency, self.currency))
    
    def get_status_display(self) -> str:
        """Get display value for status field (Django auto-generated method stub for type checking)."""
        return cast(str, dict(self.WithdrawStatus.choices).get(self.status, self.status))


class PortalAccessToken(models.Model):
    """
    Portal access token for secure web portal authentication from Telegram.
    
    Tokens are time-limited and can be configured as single-use or reusable.
    """
    
    # Type annotations for auto-generated Django fields
    id: int
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='portal_tokens',
        verbose_name="پروفایل کاربر",
        help_text="کاربری که این توکن برای اوست"
    )
    
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        verbose_name="توکن دسترسی",
        help_text="توکن یکتای امن برای احراز هویت"
    )
    
    is_used = models.BooleanField(
        default=False,
        verbose_name="استفاده شده",
        help_text="آیا این توکن قبلاً استفاده شده است؟"
    )
    
    expires_at = models.DateTimeField(
        verbose_name="زمان انقضا",
        help_text="زمان انقضای توکن"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="تاریخ ایجاد"
    )
    
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="آخرین استفاده",
        help_text="زمان آخرین استفاده از توکن"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="آدرس IP",
        help_text="آدرس IP که از این توکن استفاده کرده"
    )
    
    user_agent = models.TextField(
        blank=True,
        verbose_name="User Agent",
        help_text="اطلاعات مرورگر"
    )

    class Meta:
        verbose_name = "توکن دسترسی پورتال"
        verbose_name_plural = "توکن‌های دسترسی پورتال"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token', 'expires_at']),
            models.Index(fields=['profile', '-created_at']),
        ]

    def __str__(self) -> str:
        """Return string representation of the token."""
        return f"توکن {self.token[:8]}... - {self.profile.get_display_name()}"
    
    def is_valid(self) -> bool:
        """Check if token is valid (not expired and not used)."""
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()
    
    def mark_as_used(self, ip_address: Optional[str] = None, user_agent: str = "") -> None:
        """Mark token as used."""
        from django.utils import timezone
        self.is_used = True
        self.last_used_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()
