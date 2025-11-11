"""
Admin interface for Order model.

Manages buy/sell orders with instant execution model.
"""

from typing import Any
from datetime import timedelta

from django.contrib import admin
from django.db.models import Count, Sum
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils import timezone

from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin  # type: ignore[import-untyped]

from ..models import Order
from .resources import OrderResource
from .mixins import FormattingMixin, UserDisplayMixin


class OrderAdmin(ImportExportModelAdmin, FormattingMixin, UserDisplayMixin):
    """
    Admin interface for Order model.
    
    Features:
    - Instant order execution tracking
    - Balance validation indicators
    - Trading statistics
    - Import/export functionality
    - Read-only after creation (audit trail)
    """
    
    resource_class = OrderResource
    
    list_display = (
        'id',
        'get_user_display',
        'product',
        'order_type_badge',
        'status_badge',
        'formatted_quantity',
        'formatted_total',
        'user_balance_indicator',
        'created_at'
    )
    
    list_filter = (
        'status',
        'order_type',
        'product',
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
        ('total_amount', NumericRangeFilter),
        ('quantity_grams', NumericRangeFilter),
    )
    
    search_fields = (
        'id',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'profile__telegram_id'
    )
    
    autocomplete_fields = ('profile', 'product')
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'completed_at',
        'total_amount'
    )
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('profile', 'product', 'order_type')
        }),
        ('جزئیات معامله', {
            'fields': (
                'quantity_grams',
                'price_per_gram',
                'total_amount'
            )
        }),
        ('وضعیت', {
            'fields': ('status', 'notes')
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = []  # Remove bulk actions for instant execution model
    
    date_hierarchy = 'created_at'
    
    def order_type_badge(self, obj: Order) -> str:
        """Display order type with appropriate badge."""
        if obj.order_type == Order.OrderType.BUY:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">📈 خرید</span>'
            )
        return format_html(
            '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">📉 فروش</span>'
        )
    
    order_type_badge.short_description = 'نوع'  # type: ignore
    order_type_badge.admin_order_field = 'order_type'  # type: ignore
    
    def status_badge(self, obj: Order) -> str:
        """Display order status with color-coded badge."""
        status_map = {
            Order.OrderStatus.COMPLETED: ('✓ تکمیل', '#28a745', 'white'),
            Order.OrderStatus.CANCELLED: ('✗ لغو', '#dc3545', 'white'),
            Order.OrderStatus.REJECTED: ('✗ رد', '#ffc107', 'black'),
        }
        
        if obj.status in status_map:
            text, bg_color, text_color = status_map[obj.status]
            return format_html(
                '<span class="badge" style="background-color: {}; color: {}; padding: 5px 10px; border-radius: 12px;">{}</span>',
                bg_color,
                text_color,
                text
            )
        
        return format_html('<span style="color: #999;">—</span>')
    
    status_badge.short_description = 'وضعیت'  # type: ignore
    status_badge.admin_order_field = 'status'  # type: ignore
    
    def user_balance_indicator(self, obj: Order) -> str:
        """
        Show whether user has sufficient balance for the order.
        
        Checks:
        - For BUY orders: Rial balance
        - For SELL orders: Gold/asset balance
        """
        profile = obj.profile
        
        if obj.order_type == Order.OrderType.BUY:
            has_balance = profile.has_sufficient_rial_balance(obj.total_amount)
        else:  # SELL
            has_balance = profile.has_sufficient_gold_balance(obj.quantity_grams)
        
        if has_balance:
            return format_html('<span style="color: green; font-size: 16px;">✓</span>')
        
        return format_html(
            '<span style="color: red; font-size: 16px;" title="موجودی ناکافی">✗</span>'
        )
    
    user_balance_indicator.short_description = 'موجودی کافی'  # type: ignore
    
    def formatted_quantity(self, obj: Order) -> str:
        """Format quantity with unit."""
        return f"{obj.quantity_grams} گرم"
    
    formatted_quantity.short_description = 'مقدار'  # type: ignore
    formatted_quantity.admin_order_field = 'quantity_grams'  # type: ignore
    
    def formatted_total(self, obj: Order) -> str:
        """Format total amount with currency."""
        return self.format_currency(obj.total_amount, 'ریال', 0)
    
    formatted_total.short_description = 'مبلغ کل'  # type: ignore
    formatted_total.admin_order_field = 'total_amount'  # type: ignore
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any = None) -> tuple[str, ...]:
        """
        Make all fields readonly for existing orders.
        
        Orders are executed instantly and shouldn't be modified to maintain audit trail.
        """
        if obj:  # Editing existing order
            return tuple(f.name for f in self.model._meta.fields)
        return tuple(self.readonly_fields)
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Only superusers can create manual orders.
        
        Regular orders are created through the bot/API.
        """
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """
        Disable deleting orders to maintain audit trail.
        
        Orders should remain in the system for compliance and reporting.
        """
        return False
    
    def changelist_view(self, request: HttpRequest, extra_context: dict | None = None) -> Any:
        """
        Add trading statistics to the changelist view.
        
        Shows:
        - Trade volume by time period
        - Buy vs Sell statistics
        - Recent activity metrics
        """
        extra_context = extra_context or {}
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        
        # Trade volume statistics
        stats_24h = Order.objects.filter(
            created_at__gte=last_24h,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(
            count=Count('id'),
            volume=Sum('total_amount')
        )
        
        stats_7d = Order.objects.filter(
            created_at__gte=last_7d,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(
            count=Count('id'),
            volume=Sum('total_amount')
        )
        
        stats_30d = Order.objects.filter(
            created_at__gte=last_30d,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(
            count=Count('id'),
            volume=Sum('total_amount')
        )
        
        # Buy vs Sell statistics
        buy_sell_stats = Order.objects.filter(
            status=Order.OrderStatus.COMPLETED
        ).values('order_type').annotate(
            count=Count('id'),
            volume=Sum('total_amount')
        )
        
        extra_context['trade_stats'] = {
            '24h': stats_24h,
            '7d': stats_7d,
            '30d': stats_30d,
            'buy_sell': list(buy_sell_stats)
        }
        
        return super().changelist_view(request, extra_context=extra_context)


__all__ = ['OrderAdmin']

