"""
Models for users app - User profiles and authentication
"""
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator
from decimal import Decimal


class Profile(models.Model):
    """
    پروفایل کاربر با اطلاعات تکمیلی و موجودی‌ها
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
        verbose_name="شناسه تلگرام"
    )
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="نام کاربری تلگرام"
    )
    phone_number = models.CharField(
        max_length=15,
        unique=True,
        verbose_name="شماره تماس"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="آیا کاربر توسط ادمین تایید شده است؟",
        verbose_name="تأیید شده"
    )
    rial_balance = models.DecimalField(
        max_digits=15,
        decimal_places=0,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی ریالی"
    )
    gold_balance_grams = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(Decimal('0'))],
        verbose_name="موجودی طلا (گرم)"
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

    def __str__(self) -> str:
        full_name = self.user.get_full_name()
        if full_name:
            return f"{full_name} ({self.phone_number})"
        return f"{self.user.username} ({self.phone_number})"

    def get_formatted_rial_balance(self) -> str:
        """
        بازگرداندن موجودی ریالی با فرمت خوانا (با جداکننده هزارگان)
        """
        return f"{int(self.rial_balance):,}"

    def get_formatted_gold_balance(self) -> str:
        """
        بازگرداندن موجودی طلا با فرمت خوانا
        """
        return f"{float(self.gold_balance_grams):.4f}"


# با استفاده از Signals، به محض ساخته شدن یک User، پروفایل آن نیز به صورت خودکار ایجاد می‌شود.
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs) -> None:
    """
    سیگنال برای ایجاد خودکار پروفایل هنگام ساخت کاربر جدید
    """
    if created and not hasattr(instance, 'profile'):
        # Note: Profile will be created when user registers via Telegram
        # with their telegram_id and phone_number
        pass
