"""
Admin interface for PriceHistory model.

Provides read-only access to historical price data for analysis and auditing.
"""

from typing import Any

from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html

from rangefilter.filters import DateRangeFilter  # type: ignore[import-untyped]

from ..models import PriceHistory
from .mixins import FormattingMixin, ReadOnlyAdminMixin


class PriceHistoryAdmin(ReadOnlyAdminMixin, FormattingMixin, admin.ModelAdmin):
    """
    Admin interface for PriceHistory model.
    
    Features:
    - View-only interface for audit trail
    - Price change tracking
    - Historical trend analysis
    - Product-based filtering
    
    Note: Price history is automatically created by management commands.
    Manual entry is disabled to maintain data integrity.
    """
    
    list_display = (
        'id',
        'product',
        'buy_price_display',
        'sell_price_display',
        'price_change',
        'recorded_at'
    )
    
    list_filter = (
        'product',
        ('recorded_at', DateRangeFilter),
    )
    
    search_fields = ('product__name',)
    
    readonly_fields = (
        'product',
        'base_price_api',
        'buy_price',
        'sell_price',
        'buy_margin',
        'sell_margin',
        'recorded_at'
    )
    
    date_hierarchy = 'recorded_at'
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """
        Override mixin to allow superusers to delete price history.
        
        This is occasionally needed for data cleanup.
        """
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def buy_price_display(self, obj: PriceHistory) -> str:
        """Display buy price with formatting and color."""
        formatted_price = self.format_currency(obj.buy_price, 'ریال', 0)
        return format_html(
            '<span style="color: #2e7d32; font-weight: bold;">{}</span>',
            formatted_price
        )
    
    buy_price_display.short_description = 'قیمت خرید'  # type: ignore
    buy_price_display.admin_order_field = 'buy_price'  # type: ignore
    
    def sell_price_display(self, obj: PriceHistory) -> str:
        """Display sell price with formatting and color."""
        formatted_price = self.format_currency(obj.sell_price, 'ریال', 0)
        return format_html(
            '<span style="color: #c62828; font-weight: bold;">{}</span>',
            formatted_price
        )
    
    sell_price_display.short_description = 'قیمت فروش'  # type: ignore
    sell_price_display.admin_order_field = 'sell_price'  # type: ignore
    
    def price_change(self, obj: PriceHistory) -> str:
        """
        Display price change from previous record.
        
        Shows percentage change with color coding:
        - Green for increases
        - Red for decreases
        - Gray for no change
        """
        change = obj.get_price_change_from_previous()
        
        if not change:
            return format_html('<span style="color: #999;">—</span>')
        
        buy_change, sell_change = change
        avg_change = (buy_change + sell_change) / 2
        
        # Determine color and emoji based on change direction
        if avg_change > 0:
            color = '#28a745'
            emoji = '📈'
        elif avg_change < 0:
            color = '#dc3545'
            emoji = '📉'
        else:
            color = '#6c757d'
            emoji = '➡️'
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            emoji,
            f'{avg_change:+.2f}%'
        )
    
    price_change.short_description = 'تغییر قیمت'  # type: ignore
    
    def get_queryset(self, request: HttpRequest) -> Any:
        """
        Optimize queryset with select_related.
        
        Reduces database queries by prefetching related product data.
        """
        qs = super().get_queryset(request)
        return qs.select_related('product')


__all__ = ['PriceHistoryAdmin']

