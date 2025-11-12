"""
Security features for user accounts.

This module handles account security including login tracking,
session management, and suspicious activity detection.
"""

import logging
from typing import Optional, Dict, Any
from datetime import timedelta
from django.utils import timezone
from django.db import models, transaction
from django.contrib.auth.models import User

from .models import Profile

logger = logging.getLogger('users.security')


class LoginAttempt(models.Model):
    """Track login attempts for security monitoring."""
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='login_attempts',
        verbose_name="پروفایل"
    )
    
    telegram_id = models.CharField(
        max_length=20,
        db_index=True,
        verbose_name="شناسه تلگرام"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="آدرس IP"
    )
    
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="User Agent"
    )
    
    success = models.BooleanField(
        default=False,
        verbose_name="موفق"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان"
    )
    
    class Meta:
        verbose_name = "تلاش ورود"
        verbose_name_plural = "تلاش‌های ورود"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['telegram_id', '-timestamp']),
            models.Index(fields=['profile', '-timestamp']),
        ]
    
    def __str__(self):
        status = "موفق" if self.success else "ناموفق"
        return f"{self.telegram_id} - {status} - {self.timestamp}"


class SecurityEvent(models.Model):
    """Track security-related events for audit trail."""
    
    class EventType(models.TextChoices):
        LOGIN = 'LOGIN', 'ورود'
        LOGOUT = 'LOGOUT', 'خروج'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'تغییر رمز عبور'
        PROFILE_UPDATE = 'PROFILE_UPDATE', 'به‌روزرسانی پروفایل'
        BANK_ACCOUNT_ADD = 'BANK_ACCOUNT_ADD', 'افزودن حساب بانکی'
        BANK_ACCOUNT_UPDATE = 'BANK_ACCOUNT_UPDATE', 'به‌روزرسانی حساب بانکی'
        SUSPICIOUS_ACTIVITY = 'SUSPICIOUS', 'فعالیت مشکوک'
        BALANCE_CHANGE = 'BALANCE_CHANGE', 'تغییر موجودی'
        WITHDRAWAL = 'WITHDRAWAL', 'برداشت'
        DEPOSIT = 'DEPOSIT', 'واریز'
    
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name='security_events',
        verbose_name="پروفایل"
    )
    
    event_type = models.CharField(
        max_length=30,
        choices=EventType.choices,
        db_index=True,
        verbose_name="نوع رویداد"
    )
    
    description = models.TextField(
        verbose_name="توضیحات"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="اطلاعات اضافی"
    )
    
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name="آدرس IP"
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name="زمان"
    )
    
    class Meta:
        verbose_name = "رویداد امنیتی"
        verbose_name_plural = "رویدادهای امنیتی"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['profile', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.profile.user.username} - {self.get_event_type_display()} - {self.timestamp}"


class SecurityService:
    """Service for account security operations."""
    
    @staticmethod
    @transaction.atomic
    def log_login_attempt(
        telegram_id: str,
        profile: Optional[Profile] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> None:
        """
        Log a login attempt for security monitoring.
        
        Args:
            telegram_id: Telegram user ID.
            profile: User profile (if available).
            success: Whether the login was successful.
            ip_address: IP address of the attempt.
            user_agent: User agent string.
        """
        try:
            if not profile:
                # Try to find profile
                try:
                    profile = Profile.objects.get(telegram_id=telegram_id)
                except Profile.DoesNotExist:
                    logger.warning(f"Login attempt for non-existent profile: {telegram_id}")
                    return
            
            LoginAttempt.objects.create(
                profile=profile,
                telegram_id=telegram_id,
                ip_address=ip_address,
                user_agent=user_agent,
                success=success
            )
            
            logger.info(
                f"Login attempt logged: {telegram_id} - "
                f"{'Success' if success else 'Failed'}"
            )
            
            # Check for suspicious activity
            if not success:
                SecurityService._check_failed_login_attempts(profile)
                
        except Exception as e:
            logger.error(f"Error logging login attempt: {str(e)}")
    
    @staticmethod
    def _check_failed_login_attempts(profile: Profile) -> None:
        """
        Check for suspicious failed login attempts.
        
        Args:
            profile: User profile to check.
        """
        # Check last 5 attempts in last hour
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_failed = LoginAttempt.objects.filter(
            profile=profile,
            success=False,
            timestamp__gte=one_hour_ago
        ).count()
        
        if recent_failed >= 5:
            SecurityService.log_security_event(
                profile=profile,
                event_type=SecurityEvent.EventType.SUSPICIOUS_ACTIVITY,
                description=f"5 یا بیشتر تلاش ناموفق ورود در یک ساعت گذشته",
                metadata={'failed_attempts': recent_failed}
            )
            logger.warning(
                f"Suspicious activity: {recent_failed} failed login attempts "
                f"for user {profile.user.username}"
            )
    
    @staticmethod
    @transaction.atomic
    def log_security_event(
        profile: Profile,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> SecurityEvent:
        """
        Log a security event for audit trail.
        
        Args:
            profile: User profile.
            event_type: Type of event.
            description: Event description.
            metadata: Additional event data.
            ip_address: IP address associated with event.
            
        Returns:
            Created SecurityEvent instance.
        """
        event = SecurityEvent.objects.create(
            profile=profile,
            event_type=event_type,
            description=description,
            metadata=metadata or {},
            ip_address=ip_address
        )
        
        logger.info(
            f"Security event logged: {profile.user.username} - "
            f"{event_type} - {description}"
        )
        
        return event
    
    @staticmethod
    def get_recent_security_events(
        profile: Profile,
        limit: int = 10,
        event_type: Optional[str] = None
    ) -> list:
        """
        Get recent security events for a profile.
        
        Args:
            profile: User profile.
            limit: Maximum number of events to return.
            event_type: Optional filter by event type.
            
        Returns:
            List of SecurityEvent instances.
        """
        queryset = SecurityEvent.objects.filter(profile=profile)
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        return list(queryset[:limit])
    
    @staticmethod
    def get_login_history(profile: Profile, limit: int = 10) -> list:
        """
        Get login history for a profile.
        
        Args:
            profile: User profile.
            limit: Maximum number of attempts to return.
            
        Returns:
            List of LoginAttempt instances.
        """
        return list(
            LoginAttempt.objects.filter(
                profile=profile,
                success=True
            ).order_by('-timestamp')[:limit]
        )
    
    @staticmethod
    def check_account_status(profile: Profile) -> Dict[str, Any]:
        """
        Check account security status.
        
        Args:
            profile: User profile.
            
        Returns:
            Dictionary with security status information.
        """
        # Check recent failed login attempts
        one_day_ago = timezone.now() - timedelta(days=1)
        recent_failed = LoginAttempt.objects.filter(
            profile=profile,
            success=False,
            timestamp__gte=one_day_ago
        ).count()
        
        # Check for recent suspicious events
        recent_suspicious = SecurityEvent.objects.filter(
            profile=profile,
            event_type=SecurityEvent.EventType.SUSPICIOUS_ACTIVITY,
            timestamp__gte=one_day_ago
        ).count()
        
        # Get last login
        last_login = LoginAttempt.objects.filter(
            profile=profile,
            success=True
        ).order_by('-timestamp').first()
        
        return {
            'approved': profile.is_approved,
            'recent_failed_logins': recent_failed,
            'recent_suspicious_events': recent_suspicious,
            'last_login': last_login.timestamp if last_login else None,
            'security_level': SecurityService._calculate_security_level(
                profile, recent_failed, recent_suspicious
            )
        }
    
    @staticmethod
    def _calculate_security_level(
        profile: Profile,
        recent_failed: int,
        recent_suspicious: int
    ) -> str:
        """
        Calculate security level based on recent activity.
        
        Returns:
            'high', 'medium', or 'low'
        """
        if recent_suspicious > 0 or recent_failed >= 5:
            return 'low'
        elif recent_failed >= 2:
            return 'medium'
        else:
            return 'high'
    
    @staticmethod
    def format_security_status(status: Dict[str, Any]) -> str:
        """
        Format security status for display.
        
        Args:
            status: Security status dictionary.
            
        Returns:
            Formatted string.
        """
        level_emoji = {
            'high': '🟢',
            'medium': '🟡',
            'low': '🔴'
        }
        
        text = "🔒 *وضعیت امنیتی حساب*\n\n"
        text += f"سطح امنیتی: {level_emoji.get(status['security_level'], '⚪')} "
        
        if status['security_level'] == 'high':
            text += "عالی\n"
        elif status['security_level'] == 'medium':
            text += "متوسط\n"
        else:
            text += "نیاز به توجه\n"
        
        text += f"\nتلاش‌های ناموفق اخیر: {status['recent_failed_logins']}\n"
        text += f"رویدادهای مشکوک: {status['recent_suspicious_events']}\n"
        
        if status['last_login']:
            text += f"\nآخرین ورود: {status['last_login'].strftime('%Y/%m/%d - %H:%M')}\n"
        
        return text

