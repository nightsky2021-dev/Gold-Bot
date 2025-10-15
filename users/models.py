"""
مدل‌های مربوط به کاربران و پروفایل‌ها
"""
from django.contrib.auth.models import User
from django.db import models
from django.core.validators import MinValueValidator
from typing import Optional


class Profile(models.Model):
    """
    پروفایل کاربر شامل اطلاعات تکمیلی و موجودی‌ها
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
        validators=[MinValueValidator(0)],
        verbose_name="موجودی ریالی"
    )
    gold_balance_grams = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        default=0,
        validators=[MinValueValidator(0)],
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
        indexes = [
            models.Index(fields=['telegram_id']),
            models.Index(fields=['phone_number']),
        ]

    def __str__(self) -> str:
        full_name = self.user.get_full_name()
        return f"{full_name} ({self.phone_number})" if full_name else self.phone_number
    
    @classmethod
    def get_by_telegram_id(cls, telegram_id: str) -> Optional['Profile']:
        """دریافت پروفایل براساس شناسه تلگرام"""
        try:
            return cls.objects.select_related('user').get(telegram_id=telegram_id)
        except cls.DoesNotExist:
            return None
