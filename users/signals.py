"""
سیگنال‌های مربوط به کاربران

این ماژول سیگنال‌های مختلف مربوط به کاربران را مدیریت می‌کند:
- ایجاد پروفایل
- اطلاع‌رسانی تأیید حساب
- و غیره
"""
import logging
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Profile

logger = logging.getLogger('users.signals')


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


@receiver(pre_save, sender=Profile)
def track_approval_change(sender, instance: Profile, **kwargs):
    """
    Track changes to is_approved field before saving.
    Store the old value for comparison in post_save signal.
    """
    if instance.pk:  # Only for existing profiles
        try:
            old_profile = Profile.objects.get(pk=instance.pk)
            instance._old_is_approved = old_profile.is_approved
        except Profile.DoesNotExist:
            instance._old_is_approved = None
    else:
        instance._old_is_approved = None


@receiver(post_save, sender=Profile)
def notify_user_on_approval(sender, instance: Profile, created: bool, **kwargs):
    """
    Send notification to user when their account is approved or disapproved.
    
    This signal triggers after a Profile is saved and checks if the
    is_approved status has changed.
    """
    if created:
        # Skip notification for new profiles
        return
    
    # Check if is_approved changed
    old_is_approved = getattr(instance, '_old_is_approved', None)
    
    if old_is_approved is not None and old_is_approved != instance.is_approved:
        # Status changed
        try:
            from bot.notification_service import TelegramNotificationService
            
            if instance.is_approved:
                # User was approved
                logger.info(f"User {instance.telegram_id} was approved, sending notification")
                success = TelegramNotificationService.notify_user_approved(instance)
                if success:
                    logger.info(f"Approval notification sent to user {instance.telegram_id}")
                else:
                    logger.warning(f"Failed to send approval notification to user {instance.telegram_id}")
            else:
                # User was disapproved
                logger.info(f"User {instance.telegram_id} was disapproved, sending notification")
                success = TelegramNotificationService.notify_user_disapproved(instance)
                if success:
                    logger.info(f"Disapproval notification sent to user {instance.telegram_id}")
                else:
                    logger.warning(f"Failed to send disapproval notification to user {instance.telegram_id}")
                    
        except Exception as e:
            logger.error(f"Error sending approval notification: {str(e)}")
    
    # Clean up temporary attribute
    if hasattr(instance, '_old_is_approved'):
        delattr(instance, '_old_is_approved')

