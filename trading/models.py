"""
Models for trading app - Products and Orders
"""
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal
from typing import Optional


class Product(models.Model):
    """
    محصولات طلا (انواع مختلف طلا قابل معامله)
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="نام محصول"
    )
    slug = models.SlugField(
        unique=True,
        blank=True,
        help_text="به صورت خودکار از روی نام ساخته می‌شود.",
        verbose_name="اسلاگ"
    )
    buy_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت خرید ما از مشتری",
        help_text="قیمتی که ما از مشتری طلا می‌خریم (به ازای هر گرم)"
    )
    sell_price = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="قیمت فروش ما به مشتری",
        help_text="قیمتی که ما به مشتری طلا می‌فروشیم (به ازای هر گرم)"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="فعال برای معامله"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی قیمت"
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['name']

    def save(self, *args, **kwargs) -> None:
        """
        ایجاد خودکار slug از روی نام محصول
        """
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

    def get_formatted_buy_price(self) -> str:
        """
        بازگرداندن قیمت خرید با فرمت خوانا
        """
        return f"{int(self.buy_price):,}"

    def get_formatted_sell_price(self) -> str:
        """
        بازگرداندن قیمت فروش با فرمت خوانا
        """
        return f"{int(self.sell_price):,}"


class Order(models.Model):
    """
    سفارشات خرید و فروش طلا
    """
    
    class OrderType(models.TextChoices):
        BUY = 'BUY', 'خرید از ما'
        SELL = 'SELL', 'فروش به ما'

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار بررسی'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'

    profile = models.ForeignKey(
        'users.Profile',
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="پروفایل کاربر"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='orders',
        verbose_name="محصول"
    )
    order_type = models.CharField(
        max_length=4,
        choices=OrderType.choices,
        verbose_name="نوع سفارش"
    )
    quantity_grams = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="مقدار (گرم)"
    )
    price_per_gram = models.DecimalField(
        max_digits=12,
        decimal_places=0,
        verbose_name="قیمت هر گرم (لحظه ثبت)"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        verbose_name="مبلغ کل (ریال)"
    )
    status = models.CharField(
        max_length=10,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
        db_index=True,
        verbose_name="وضعیت"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارشات"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
        ]

    def __str__(self) -> str:
        user_name = self.profile.user.get_full_name() or self.profile.user.username
        return f"سفارش {self.id} – {user_name} – {self.get_order_type_display()}"

    def get_formatted_total_amount(self) -> str:
        """
        بازگرداندن مبلغ کل با فرمت خوانا
        """
        return f"{int(self.total_amount):,}"

    def get_formatted_quantity(self) -> str:
        """
        بازگرداندن مقدار با فرمت خوانا
        """
        return f"{float(self.quantity_grams):.4f}"
