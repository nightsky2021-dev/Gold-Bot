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
