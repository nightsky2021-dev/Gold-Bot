"""
Admin notification system for the trading app.

Provides alerts and notifications for important events
requiring admin attention.
"""

from typing import Optional, List
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger('trading')


class AdminNotificationService:
    """Service for sending notifications to admins."""
    
    # Notification types
    HIGH_VALUE_TRANSACTION = 'high_value_transaction'
    PENDING_APPROVAL = 'pending_approval'
    SUSPICIOUS_ACTIVITY = 'suspicious_activity'
    SYSTEM_ERROR = 'system_error'
    PRICE_ALERT = 'price_alert'
    LOW_BALANCE = 'low_balance'
    
    # Thresholds
    HIGH_VALUE_THRESHOLD = Decimal('50000000')  # 50 million Rial
    PRICE_CHANGE_THRESHOLD = Decimal('5.0')  # 5% change
    
    @staticmethod
    def get_admin_users() -> List[User]:
        """Get all admin/staff users."""
        return list(User.objects.filter(is_staff=True, is_active=True))
    
    @staticmethod
    def notify_high_value_transaction(order, request=None):
        """
        Notify admins of high-value transactions.
        
        Args:
            order: Order instance
            request: HttpRequest object (optional, for in-app messages)
        """
        if order.total_amount >= AdminNotificationService.HIGH_VALUE_THRESHOLD:
            message = (
                f'🚨 معامله با ارزش بالا: {order.profile.get_display_name()} - '
                f'{order.total_amount:,.0f} ریال - '
                f'{order.get_order_type_display()} {order.product.name}'
            )
            
            # Log notification
            logger.warning(message)
            
            # Send in-app message if request is available
            if request:
                messages.warning(request, message)
            
            # Email notification to admins
            AdminNotificationService._send_email_to_admins(
                subject='معامله با ارزش بالا',
                message=message
            )
    
    @staticmethod
    def notify_pending_approvals(count: int, notification_type: str):
        """
        Notify admins of pending approvals.
        
        Args:
            count: Number of pending items
            notification_type: Type of pending items ('transactions', 'withdrawals', 'users')
        """
        if count == 0:
            return
        
        type_labels = {
            'transactions': 'تراکنش',
            'withdrawals': 'درخواست برداشت',
            'users': 'کاربر'
        }
        
        label = type_labels.get(notification_type, 'مورد')
        message = f'⏳ {count} {label} در انتظار بررسی و تأیید'
        
        logger.info(message)
    
    @staticmethod
    def notify_suspicious_activity(profile, reason: str, request=None):
        """
        Notify admins of suspicious user activity.
        
        Args:
            profile: Profile instance
            reason: Reason for suspicion
            request: HttpRequest object (optional)
        """
        message = (
            f'⚠️ فعالیت مشکوک: {profile.get_display_name()} - '
            f'دلیل: {reason}'
        )
        
        logger.warning(message)
        
        if request:
            messages.error(request, message)
        
        # Email notification to admins
        AdminNotificationService._send_email_to_admins(
            subject='فعالیت مشکوک',
            message=message,
            urgent=True
        )
    
    @staticmethod
    def notify_price_change(product, old_price: Decimal, new_price: Decimal):
        """
        Notify admins of significant price changes.
        
        Args:
            product: Product instance
            old_price: Previous price
            new_price: New price
        """
        if old_price == 0:
            return
        
        change_pct = abs((new_price - old_price) / old_price) * 100
        
        if change_pct >= AdminNotificationService.PRICE_CHANGE_THRESHOLD:
            direction = '📈 افزایش' if new_price > old_price else '📉 کاهش'
            message = (
                f'💰 تغییر قیمت قابل توجه: {product.name} - '
                f'{direction} {change_pct:.1f}% - '
                f'از {old_price:,.0f} به {new_price:,.0f} ریال'
            )
            
            logger.info(message)
    
    @staticmethod
    def notify_system_error(error_message: str, context: Optional[dict] = None):
        """
        Notify admins of system errors.
        
        Args:
            error_message: Error description
            context: Additional context information
        """
        message = f'❌ خطای سیستم: {error_message}'
        
        if context:
            message += f'\n\nجزئیات: {context}'
        
        logger.error(message)
        
        # Email notification to admins for critical errors
        AdminNotificationService._send_email_to_admins(
            subject='خطای سیستم',
            message=message,
            urgent=True
        )
    
    @staticmethod
    def notify_api_connection_issue(provider_name: str):
        """
        Notify admins of API connection issues.
        
        Args:
            provider_name: Name of the price provider
        """
        message = f'🔌 مشکل در اتصال به API: {provider_name}'
        
        logger.error(message)
        
        AdminNotificationService._send_email_to_admins(
            subject='مشکل اتصال API',
            message=message,
            urgent=True
        )
    
    @staticmethod
    def notify_user_balance_low(profile):
        """
        Notify when user balance is low (informational).
        
        Args:
            profile: Profile instance
        """
        if profile.rial_balance < 100000:  # Less than 100k Rial
            message = (
                f'💼 موجودی کم: {profile.get_display_name()} - '
                f'{profile.rial_balance:,.0f} ریال'
            )
            
            logger.info(message)
    
    @staticmethod
    def _send_email_to_admins(subject: str, message: str, urgent: bool = False):
        """
        Send email notification to all admin users.
        
        Args:
            subject: Email subject
            message: Email message
            urgent: Whether this is an urgent notification
        """
        try:
            admin_users = AdminNotificationService.get_admin_users()
            admin_emails = [user.email for user in admin_users if user.email]
            
            if not admin_emails:
                logger.warning("No admin emails found for notification")
                return
            
            if urgent:
                subject = f'[URGENT] {subject}'
            
            # Only send email if EMAIL_BACKEND is configured
            if hasattr(settings, 'EMAIL_BACKEND'):
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=admin_emails,
                    fail_silently=True
                )
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    @staticmethod
    def get_dashboard_alerts() -> List[dict]:
        """
        Get current alerts for admin dashboard.
        
        Returns:
            List of alert dictionaries
        """
        from trading.models import Transaction, WithdrawRequest, Order
        from users.models import Profile
        
        alerts = []
        
        # Pending deposits
        pending_deposits = Transaction.objects.filter(
            status='PENDING',
            transaction_type='DEPOSIT'
        ).count()
        
        if pending_deposits > 0:
            alerts.append({
                'type': 'warning',
                'emoji': '💳',
                'message': f'{pending_deposits} واریز در انتظار تأیید',
                'url': '/admin/trading/transaction/?status=PENDING&transaction_type=DEPOSIT',
                'priority': 'high' if pending_deposits > 10 else 'medium'
            })
        
        # Pending withdrawals
        pending_withdrawals = WithdrawRequest.objects.filter(
            status='PENDING'
        ).count()
        
        if pending_withdrawals > 0:
            alerts.append({
                'type': 'warning',
                'emoji': '📤',
                'message': f'{pending_withdrawals} درخواست برداشت در انتظار',
                'url': '/admin/trading/withdrawrequest/?status=PENDING',
                'priority': 'high' if pending_withdrawals > 5 else 'medium'
            })
        
        # Pending user approvals
        pending_users = Profile.objects.filter(is_approved=False).count()
        
        if pending_users > 0:
            alerts.append({
                'type': 'info',
                'emoji': '👤',
                'message': f'{pending_users} کاربر در انتظار تأیید',
                'url': '/admin/users/profile/?is_approved__exact=0',
                'priority': 'low'
            })
        
        # Recent high-value transactions (last 24 hours)
        from django.utils import timezone
        from datetime import timedelta
        
        time_24h_ago = timezone.now() - timedelta(hours=24)
        high_value_orders = Order.objects.filter(
            created_at__gte=time_24h_ago,
            total_amount__gte=AdminNotificationService.HIGH_VALUE_THRESHOLD,
            status='COMPLETED'
        ).count()
        
        if high_value_orders > 0:
            alerts.append({
                'type': 'info',
                'emoji': '💰',
                'message': f'{high_value_orders} معامله با ارزش بالا در ۲۴ ساعت اخیر',
                'url': '/admin/trading/order/?created_at__gte=' + time_24h_ago.strftime('%Y-%m-%d'),
                'priority': 'low'
            })
        
        # Sort by priority
        priority_order = {'high': 0, 'medium': 1, 'low': 2}
        alerts.sort(key=lambda x: priority_order.get(x['priority'], 3))
        
        return alerts


class NotificationPreferences:
    """Store admin notification preferences."""
    
    # This can be extended to use a database model in the future
    # For now, we use simple class attributes
    
    EMAIL_ENABLED = True
    HIGH_VALUE_THRESHOLD = Decimal('50000000')
    PRICE_CHANGE_THRESHOLD = Decimal('5.0')
    
    @classmethod
    def set_high_value_threshold(cls, threshold: Decimal):
        """Set threshold for high-value transaction notifications."""
        cls.HIGH_VALUE_THRESHOLD = threshold
        AdminNotificationService.HIGH_VALUE_THRESHOLD = threshold
    
    @classmethod
    def set_price_change_threshold(cls, threshold: Decimal):
        """Set threshold for price change notifications."""
        cls.PRICE_CHANGE_THRESHOLD = threshold
        AdminNotificationService.PRICE_CHANGE_THRESHOLD = threshold
