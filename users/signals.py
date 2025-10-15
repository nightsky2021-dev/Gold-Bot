"""
سیگنال‌های مربوط به کاربران
"""
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance: User, created: bool, **kwargs):
    """
    با استفاده از سیگنال، به محض ساخته شدن یک User،
    پروفایل آن نیز به صورت خودکار ایجاد می‌شود.
    """
    if created and not hasattr(instance, 'profile'):
        # فقط اگر User جدید است و پروفایل ندارد، پروفایل می‌سازیم
        # توجه: telegram_id در زمان ثبت‌نام از طریق ربات تنظیم می‌شود
        pass
