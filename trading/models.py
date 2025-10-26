"""
مدل‌های مربوط به محصولات و سفارشات
"""
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from decimal import Decimal
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models import Manager
    from datetime import datetime


class Product(models.Model):
    """مدل محصول (انواع طلا)"""
    
    if TYPE_CHECKING:
        objects: 'Manager'
        DoesNotExist: type[Exception]
    
    # کدهای محصول برای شناسایی خودکار
    PRODUCT_CODE_GOLD = 'GOLD_ABSHODEH'
    PRODUCT_CODE_COIN = 'COIN_FULL'
    PRODUCT_CODE_DOLLAR = 'DOLLAR'
    
    PRODUCT_CODE_CHOICES = [
        (PRODUCT_CODE_GOLD, 'طلای آبشده'),
        (PRODUCT_CODE_COIN, 'سکه تمام غیربانکی'),
        (PRODUCT_CODE_DOLLAR, 'دلار آمریکا'),
    ]
    
    product_code = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        choices=PRODUCT_CODE_CHOICES,
        verbose_name="کد محصول",
        help_text="کد یکتا برای شناسایی خودکار محصول"
    )
    name = models.CharField(  # pyright: ignore
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
    buy_price = models.DecimalField(  # pyright: ignore
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت خرید ما از مشتری",
        help_text="قیمتی که ما طلا را از مشتری می‌خریم (به ریال)"
    )
    sell_price = models.DecimalField(  # pyright: ignore
        max_digits=12,
        decimal_places=0,
        validators=[MinValueValidator(0)],
        verbose_name="قیمت فروش ما به مشتری",
        help_text="قیمتی که ما طلا را به مشتری می‌فروشیم (به ریال)"
    )
    is_active = models.BooleanField(
        default=True,  # pyright: ignore
        verbose_name="فعال برای معامله"
    )
    updated_at = models.DateTimeField(  # pyright: ignore
        auto_now=True,
        verbose_name="آخرین به‌روزرسانی قیمت"
    )

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ['name']

    def save(self, *args, **kwargs):
        """ایجاد خودکار slug از روی نام"""
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name  # pyright: ignore
    
    @classmethod
    def get_active_products(cls) -> List['Product']:
        """دریافت لیست محصولات فعال"""
        return list(cls.objects.filter(is_active=True))
    
    @classmethod
    def get_by_code(cls, product_code: str) -> 'Product':
        """دریافت محصول براساس کد"""
        return cls.objects.get(product_code=product_code)


class Order(models.Model):
    """مدل سفارش خرید/فروش"""
    
    if TYPE_CHECKING:
        from users.models import Profile
        
        objects: 'Manager'
        DoesNotExist: type[Exception]
        # Type hints for fields accessed in methods
        id: int
        profile: 'Profile'
        quantity_grams: Decimal
        price_per_gram: Decimal
        total_amount: Decimal
        
        # Django auto-generated methods
        def get_order_type_display(self) -> str: ...
        def get_status_display(self) -> str: ...
    
    class OrderType(models.TextChoices):
        BUY = 'BUY', 'خرید از ما'
        SELL = 'SELL', 'فروش به ما'

    class OrderStatus(models.TextChoices):
        PENDING = 'PENDING', 'در انتظار بررسی'
        COMPLETED = 'COMPLETED', 'تکمیل شده'
        CANCELLED = 'CANCELLED', 'لغو شده'

    profile = models.ForeignKey(  # pyright: ignore
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
    quantity_grams = models.DecimalField(  # pyright: ignore
        max_digits=10,
        decimal_places=4,
        validators=[MinValueValidator(Decimal('0.0001'))],
        verbose_name="مقدار (گرم)"
    )
    price_per_gram = models.DecimalField(  # pyright: ignore
        max_digits=12,
        decimal_places=0,
        verbose_name="قیمت هر گرم (لحظه ثبت)"
    )
    total_amount = models.DecimalField(  # pyright: ignore
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
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
        verbose_name="شماره فاکتور",
        help_text="شماره یونیک فاکتور"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاریخ ثبت"
    )
    notes = models.TextField(
        blank=True,
        verbose_name="یادداشت‌ها"
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
        return f"سفارش {self.id} – {self.profile.user.get_full_name()} – {self.get_order_type_display()}"
    
    def save(self, *args, **kwargs):
        """محاسبه خودکار مبلغ کل"""
        if not self.total_amount:
            self.total_amount = self.quantity_grams * self.price_per_gram
        super().save(*args, **kwargs)

