"""
Business Intelligence and Reporting Dashboard.

Provides comprehensive reporting tools for administrators including:
- Profit & Loss statements
- User activity reports
- Balance sheet aggregates
- Export capabilities
"""

from typing import Any, Optional
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib import admin
from django.db.models import Count, Sum
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils import timezone

from ..models import Order, Transaction, WithdrawRequest
from ..reporting import BusinessReportService


class BusinessReportingAdmin(admin.ModelAdmin):
    """
    Proxy admin for business reporting dashboard.
    
    This provides a dedicated section in admin for viewing reports without
    being tied to a specific model.
    
    Features:
    - Profit & Loss reports (7d, 30d, monthly, custom range)
    - Balance sheet overview
    - User activity metrics
    - High-value transaction tracking
    - Pending approval monitoring
    - Daily statistics visualization
    """
    
    change_list_template = 'admin/trading/reporting_dashboard.html'
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """No add permission for reporting dashboard."""
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """View-only dashboard - accessible to all staff."""
        return bool(request.user and getattr(request.user, 'is_staff', False))
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """No delete permission for reporting dashboard."""
        return False
    
    def has_module_permission(self, request: HttpRequest) -> bool:
        """Dashboard visible to all staff members."""
        return bool(request.user and getattr(request.user, 'is_staff', False))
    
    def changelist_view(self, request: HttpRequest, extra_context: Optional[dict] = None) -> TemplateResponse:
        """
        Display comprehensive reporting dashboard.
        
        Aggregates data from multiple sources:
        - Orders (trading activity)
        - Transactions (deposits/withdrawals)
        - Withdrawal requests (pending actions)
        - Price history (market trends)
        """
        extra_context = extra_context or {}
        
        # Get date ranges
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Parse custom date range from request
        custom_start = self._parse_date(request.GET.get('start_date'))
        custom_end = self._parse_date(request.GET.get('end_date'))
        
        # Generate Profit & Loss Reports
        pl_7d = BusinessReportService.get_profit_loss_report(start_date=last_7d)
        pl_30d = BusinessReportService.get_profit_loss_report(start_date=last_30d)
        pl_this_month = BusinessReportService.get_profit_loss_report(start_date=this_month_start)
        
        pl_custom = None
        if custom_start or custom_end:
            pl_custom = BusinessReportService.get_profit_loss_report(
                start_date=custom_start,
                end_date=custom_end
            )
        
        # Balance Sheet
        balance_sheet = BusinessReportService.get_balance_sheet()
        
        # User Activity
        user_activity_7d = BusinessReportService.get_user_activity_report(days=7)
        user_activity_30d = BusinessReportService.get_user_activity_report(days=30)
        
        # Recent High-Value Orders
        high_value_orders = self._get_high_value_orders()
        
        # Pending Approvals
        pending_deposits = self._get_pending_deposits()
        pending_withdrawals = self._get_pending_withdrawals()
        
        # Daily Statistics
        daily_stats = self._generate_daily_stats(now, days=30)
        
        # Build context
        context = {
            # Reports
            'pl_7d': pl_7d,
            'pl_30d': pl_30d,
            'pl_this_month': pl_this_month,
            'pl_custom': pl_custom,
            'balance_sheet': balance_sheet,
            'user_activity_7d': user_activity_7d,
            'user_activity_30d': user_activity_30d,
            'daily_stats': daily_stats,
            
            # Recent Activity
            'high_value_orders': high_value_orders,
            'pending_deposits': pending_deposits,
            'pending_withdrawals': pending_withdrawals,
            
            # Filter Parameters
            'custom_start': custom_start.strftime('%Y-%m-%d') if custom_start else '',
            'custom_end': custom_end.strftime('%Y-%m-%d') if custom_end else '',
            
            # Admin Context
            'title': '📊 Business Intelligence Dashboard',
            'site_title': 'Gold Trading Admin',
            'site_header': 'Gold Trading Administration',
            'has_permission': True,
        }
        
        context.update(extra_context or {})
        
        return TemplateResponse(
            request,
            'admin/trading/reporting_dashboard.html',
            context
        )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string from request parameters.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            datetime object or None if invalid/missing
        """
        if not date_str:
            return None
        
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None
    
    def _get_high_value_orders(self, limit: int = 20) -> Any:
        """
        Get recent high-value orders.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            QuerySet of high-value orders
        """
        return Order.objects.filter(
            status=Order.OrderStatus.COMPLETED,
            total_amount__gte=10000000  # 10 million Rial threshold
        ).select_related('profile', 'product').order_by('-created_at')[:limit]
    
    def _get_pending_deposits(self, limit: int = 10) -> Any:
        """
        Get pending deposit transactions.
        
        Args:
            limit: Maximum number of transactions to return
            
        Returns:
            QuerySet of pending deposits
        """
        return Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            transaction_type=Transaction.TransactionType.DEPOSIT
        ).select_related('profile').order_by('-created_at')[:limit]
    
    def _get_pending_withdrawals(self, limit: int = 10) -> Any:
        """
        Get pending withdrawal requests.
        
        Args:
            limit: Maximum number of requests to return
            
        Returns:
            QuerySet of pending withdrawals
        """
        return WithdrawRequest.objects.filter(
            status='PENDING'
        ).select_related('profile', 'bank_account').order_by('-created_at')[:limit]
    
    def _generate_daily_stats(self, end_date: datetime, days: int = 30) -> list:
        """
        Generate daily statistics for the specified period.
        
        Args:
            end_date: End date for the period
            days: Number of days to include
            
        Returns:
            List of daily statistics dictionaries
        """
        daily_stats = []
        
        for i in range(days):
            day = end_date - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            # Get orders for the day
            day_orders = Order.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end,
                status=Order.OrderStatus.COMPLETED
            )
            
            # Calculate revenue from spreads
            day_revenue = Decimal('0')
            for order in day_orders:
                spread = order.product.get_price_spread()
                day_revenue += (order.quantity_grams * spread)
            
            # Aggregate volume
            day_volume = day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or Decimal('0')
            
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'orders': day_orders.count(),
                'volume': float(day_volume),
                'revenue': float(day_revenue)
            })
        
        # Reverse to get chronological order
        daily_stats.reverse()
        
        return daily_stats


__all__ = ['BusinessReportingAdmin']

