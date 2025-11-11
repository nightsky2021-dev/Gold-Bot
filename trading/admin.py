"""
Django admin configuration for trading app.

Provides admin interfaces for Product and Order models.
Enhanced with import/export, advanced filters, and analytics.
"""

from django.contrib import admin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db import transaction as db_transaction
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, Avg, Q
from django.http import HttpRequest
from django.template.response import TemplateResponse
from typing import Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export import resources, fields  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin, ExportActionMixin  # type: ignore[import-untyped]

from .models import Product, Order, Transaction, WithdrawRequest, PriceHistory
from users.models import Profile
from .reporting import BusinessReportService
from .utils import (
    to_persian_numbers, 
    format_price_persian, 
    get_tier_badge_html,
    format_percentage_change,
    get_trend_color
)


# ============================================
# IMPORT/EXPORT RESOURCES
# ============================================

class ProductResource(resources.ModelResource):
    """Resource for importing/exporting Product data."""
    
    price_spread = fields.Field(
        column_name='اختلاف قیمت',
        readonly=True
    )
    
    def dehydrate_price_spread(self, product):
        return product.get_price_spread()
    
    class Meta:
        model = Product
        fields = (
            'id', 'product_code', 'name', 'slug', 'buy_price', 
            'sell_price', 'price_spread', 'is_active', 
            'updated_at', 'created_at'
        )
        export_order = fields


class OrderResource(resources.ModelResource):
    """Resource for importing/exporting Order data."""
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    product_name = fields.Field(
        column_name='نام محصول',
        attribute='product__name',
        readonly=True
    )
    
    class Meta:
        model = Order
        fields = (
            'id', 'user_name', 'product_name', 'order_type', 
            'quantity_grams', 'price_per_gram', 'total_amount',
            'status', 'created_at', 'completed_at'
        )
        export_order = fields


class TransactionResource(resources.ModelResource):
    """Resource for importing/exporting Transaction data."""
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    class Meta:
        model = Transaction
        fields = (
            'id', 'user_name', 'transaction_type', 'currency', 
            'amount', 'status', 'description', 'created_at', 
            'completed_at'
        )
        export_order = fields


class WithdrawRequestResource(resources.ModelResource):
    """Resource for importing/exporting WithdrawRequest data."""
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    class Meta:
        model = WithdrawRequest
        fields = (
            'id', 'user_name', 'currency', 'amount', 'status',
            'rejection_reason', 'created_at', 'completed_at'
        )
        export_order = fields


@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    """
    Admin interface for Product model.
    
    Allows easy management of gold products and their prices.
    Enhanced with import/export and analytics.
    """
    
    resource_class = ProductResource
    
    list_display = (
        'name',
        'product_code',
        'margin_display',
        'calculated_buy_price',
        'calculated_sell_price',
        'price_trend_24h',
        'base_api_price_display',
        'is_active',
        'order_count',
        'total_volume_30d',
        'updated_at'
    )
    
    list_editable = ('is_active',)
    
    list_filter = (
        'is_active', 
        'product_code',
        ('updated_at', DateRangeFilter),
        ('buy_price', NumericRangeFilter),
        ('sell_price', NumericRangeFilter),
    )
    
    search_fields = ('name', 'slug', 'product_code')
    
    readonly_fields = (
        'slug', 
        'buy_price', 
        'sell_price', 
        'base_price_api',
        'calculated_price_preview',
        'updated_at', 
        'created_at'
    )
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('product_code', 'name', 'slug')
        }),
        ('⚙️ تنظیمات محاسبه قیمت (این قسمت را تنظیم کنید)', {
            'fields': ('buy_margin', 'sell_margin', 'weight_grams'),
            'description': (
                '<div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0;">'
                '<h3 style="margin-top:0; color: #1976d2;">📖 راهنمای محاسبه قیمت:</h3>'
                '<p><strong>مارجین خرید:</strong> این مقدار از قیمت بازار <strong>کم</strong> می‌شود تا قیمت خرید از مشتری محاسبه شود.</p>'
                '<p><strong>مارجین فروش:</strong> این مقدار به قیمت بازار <strong>اضافه</strong> می‌شود تا قیمت فروش به مشتری محاسبه شود.</p>'
                '<p><strong>وزن واحد:</strong> برای طلا و دلار = 1 گرم، برای سکه = وزن واقعی سکه (مثلاً 8.133 گرم)</p>'
                '<hr style="margin: 15px 0;">'
                '<p style="color: #ff6f00;"><strong>⚡ توجه:</strong> با تغییر این مقادیر، قیمت‌ها به صورت خودکار در هنگام اجرای دستور <code>update_prices</code> محاسبه می‌شوند.</p>'
                '</div>'
            )
        }),
        ('📊 قیمت‌های محاسبه شده (فقط‌خواندنی)', {
            'fields': ('calculated_price_preview', 'base_price_api', 'buy_price', 'sell_price'),
            'description': 'این قیمت‌ها به صورت خودکار از API و مارجین‌های بالا محاسبه می‌شوند.'
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_count(self, obj: Product) -> str:
        """Display order count."""
        count = obj.orders.count()
        return format_html(
            '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">{} سفارش</span>',
            count
        )
    order_count.short_description = 'تعداد سفارشات'
    
    def active_status_badge(self, obj: Product) -> str:
        """Display active status with badge."""
        if obj.is_active:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ فعال</span>'
            )
        return format_html(
            '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">✗ غیرفعال</span>'
        )
    active_status_badge.short_description = 'وضعیت'
    active_status_badge.admin_order_field = 'is_active'
    
    def formatted_buy_price(self, obj: Product) -> str:
        """Format buy price with thousand separators."""
        return f"{obj.buy_price:,.0f} ریال"
    formatted_buy_price.short_description = 'قیمت خرید'
    formatted_buy_price.admin_order_field = 'buy_price'
    
    def formatted_sell_price(self, obj: Product) -> str:
        """Format sell price with thousand separators."""
        return f"{obj.sell_price:,.0f} ریال"
    formatted_sell_price.short_description = 'قیمت فروش'
    formatted_sell_price.admin_order_field = 'sell_price'
    
    def price_spread_display(self, obj: Product) -> str:
        """Display price spread."""
        spread = obj.get_price_spread()
        percentage = obj.get_price_spread_percentage()
        return f"{spread:,.0f} ریال ({percentage:.2f}%)"
    price_spread_display.short_description = 'اختلاف قیمت'
    
    def margin_display(self, obj: Product) -> str:
        """Display margin configuration."""
        # Format numbers as strings first to avoid format_html SafeString issues
        buy_margin_formatted = f"{float(obj.buy_margin):,.0f}"
        sell_margin_formatted = f"{float(obj.sell_margin):,.0f}"
        total_margin_formatted = f"{float(obj.get_total_margin()):,.0f}"
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '🟢 خرید: <strong>{}</strong><br>'
            '🔴 فروش: <strong>{}</strong><br>'
            '💰 مجموع: <strong>{}</strong>'
            '</div>',
            buy_margin_formatted,
            sell_margin_formatted,
            total_margin_formatted
        )
    margin_display.short_description = 'مارجین‌ها (ریال)'
    
    def calculated_buy_price(self, obj: Product) -> str:
        """Display calculated buy price."""
        buy_price_formatted = f"{float(obj.buy_price):,.0f}"
        return format_html(
            '<span style="color: #2e7d32; font-weight: bold;">{} ریال</span>',
            buy_price_formatted
        )
    calculated_buy_price.short_description = '💰 قیمت خرید'
    calculated_buy_price.admin_order_field = 'buy_price'
    
    def calculated_sell_price(self, obj: Product) -> str:
        """Display calculated sell price."""
        sell_price_formatted = f"{float(obj.sell_price):,.0f}"
        return format_html(
            '<span style="color: #c62828; font-weight: bold;">{} ریال</span>',
            sell_price_formatted
        )
    calculated_sell_price.short_description = '💵 قیمت فروش'
    calculated_sell_price.admin_order_field = 'sell_price'
    
    def base_api_price_display(self, obj: Product) -> str:
        """Display base price from API."""
        if obj.base_price_api:
            base_price_formatted = f"{float(obj.base_price_api):,.0f}"
            return format_html(
                '<span style="color: #1976d2;">{} ریال</span>',
                base_price_formatted
            )
        return format_html('<span style="color: #999;">—</span>')
    base_api_price_display.short_description = '📡 قیمت API'
    
    def calculated_price_preview(self, obj: Product) -> str:
        """Show a preview of how prices are calculated."""
        if obj.base_price_api:
            adjusted_base = obj.base_price_api * obj.weight_grams
            # Format all numbers as strings first to avoid format_html SafeString issues
            base_price_formatted = f"{float(obj.base_price_api):,.0f}"
            adjusted_base_formatted = f"{float(adjusted_base):,.0f}"
            buy_margin_formatted = f"{float(obj.buy_margin):,.0f}"
            buy_price_formatted = f"{float(obj.buy_price):,.0f}"
            sell_margin_formatted = f"{float(obj.sell_margin):,.0f}"
            sell_price_formatted = f"{float(obj.sell_price):,.0f}"
            
            return format_html(
                '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-family: monospace;">'
                '<strong>فرمول محاسبه:</strong><br><br>'
                '🔹 قیمت پایه API: <strong>{}</strong> ریال<br>'
                '🔹 وزن واحد: <strong>{}</strong> گرم<br>'
                '🔹 قیمت تعدیل شده: <strong>{}</strong> ریال<br>'
                '<hr style="margin: 10px 0;">'
                '✅ قیمت خرید = {} - {} = <strong style="color: #2e7d32;">{}</strong> ریال<br>'
                '✅ قیمت فروش = {} + {} = <strong style="color: #c62828;">{}</strong> ریال'
                '</div>',
                base_price_formatted,
                obj.weight_grams,
                adjusted_base_formatted,
                adjusted_base_formatted,
                buy_margin_formatted,
                buy_price_formatted,
                adjusted_base_formatted,
                sell_margin_formatted,
                sell_price_formatted
            )
        return format_html(
            '<div style="background: #fff3cd; padding: 10px; border-radius: 5px;">'
            '⚠️ هنوز قیمت از API دریافت نشده است.<br>'
            'لطفاً دستور <code>python manage.py update_prices</code> را اجرا کنید.'
            '</div>'
        )
    calculated_price_preview.short_description = '📊 پیش‌نمای محاسبه'
    
    def price_trend_24h(self, obj: Product) -> str:
        """Show price trend for last 24 hours."""
        from django.utils import timezone
        
        # Get price from 24 hours ago
        time_24h_ago = timezone.now() - timedelta(hours=24)
        old_price = PriceHistory.objects.filter(
            product=obj,
            recorded_at__lte=time_24h_ago
        ).order_by('-recorded_at').first()
        
        if not old_price:
            return format_html('<span style="color: #999;">—</span>')
        
        # Calculate change
        change_pct, trend = format_percentage_change(obj.sell_price, old_price.sell_price)
        color = get_trend_color(obj.sell_price - old_price.sell_price)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            trend,
            change_pct
        )
    price_trend_24h.short_description = '📈 روند ۲۴ ساعت'
    
    def total_volume_30d(self, obj: Product) -> str:
        """Show total trade volume for last 30 days."""
        from django.utils import timezone
        
        time_30d_ago = timezone.now() - timedelta(days=30)
        volume = obj.orders.filter(
            status=Order.OrderStatus.COMPLETED,
            created_at__gte=time_30d_ago
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0')
        
        # Format with Persian numbers
        volume_formatted = format_price_persian(volume, include_currency=False)
        
        return format_html(
            '<span style="font-weight: bold;">{} میلیون</span>',
            to_persian_numbers(f"{float(volume / 1000000):.1f}")
        )
    total_volume_30d.short_description = '💰 حجم معاملات ۳۰ روز'
    


@admin.register(Order)
class OrderAdmin(ImportExportModelAdmin):
    """
    Admin interface for Order model.
    
    Provides comprehensive order management with filtering and bulk actions.
    Enhanced with import/export, advanced filters, and quick actions.
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
    
    def get_user_display(self, obj: Order) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    get_user_display.admin_order_field = 'profile__user__first_name'
    
    def order_type_badge(self, obj: Order) -> str:
        """Display order type with badge."""
        if obj.order_type == Order.OrderType.BUY:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">📈 خرید</span>'
            )
        return format_html(
            '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">📉 فروش</span>'
        )
    order_type_badge.short_description = 'نوع'
    order_type_badge.admin_order_field = 'order_type'
    
    def status_badge(self, obj: Order) -> str:
        """Display status with badge."""
        badges = {
            Order.OrderStatus.COMPLETED: '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تکمیل</span>',
            Order.OrderStatus.CANCELLED: '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">✗ لغو</span>',
            Order.OrderStatus.REJECTED: '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">✗ رد</span>',
        }
        return format_html(badges.get(obj.status, ''))
    status_badge.short_description = 'وضعیت'
    status_badge.admin_order_field = 'status'
    
    def user_balance_indicator(self, obj: Order) -> str:
        """Show user balance sufficiency."""
        profile = obj.profile
        if obj.order_type == Order.OrderType.BUY:
            has_balance = profile.has_sufficient_rial_balance(obj.total_amount)
            if has_balance:
                return format_html('<span style="color: green;">✓</span>')
            return format_html('<span style="color: red;" title="موجودی ناکافی">✗</span>')
        else:  # SELL
            has_balance = profile.has_sufficient_gold_balance(obj.quantity_grams)
            if has_balance:
                return format_html('<span style="color: green;">✓</span>')
            return format_html('<span style="color: red;" title="موجودی ناکافی">✗</span>')
    user_balance_indicator.short_description = 'موجودی کافی'
    
    def formatted_quantity(self, obj: Order) -> str:
        """Format quantity."""
        return f"{obj.quantity_grams} گرم"
    formatted_quantity.short_description = 'مقدار'
    formatted_quantity.admin_order_field = 'quantity_grams'
    
    def formatted_total(self, obj: Order) -> str:
        """Format total amount."""
        return f"{obj.total_amount:,.0f} ریال"
    formatted_total.short_description = 'مبلغ کل'
    formatted_total.admin_order_field = 'total_amount'
    
    def get_readonly_fields(self, request, obj=None):
        """Make all fields readonly since orders are executed instantly."""
        if obj:  # Editing existing order
            return [f.name for f in self.model._meta.fields]
        return self.readonly_fields
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Allow adding transactions for manual adjustments by superusers."""
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def has_delete_permission(self, request, obj=None):
        """Disable deleting completed orders for audit trail."""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Add live trade feed statistics to the changelist view."""
        extra_context = extra_context or {}
        
        # Get statistics for the dashboard
        from django.db.models import Count, Sum
        from datetime import timedelta
        
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


@admin.register(Transaction)
class TransactionAdmin(ImportExportModelAdmin):
    """
    Admin interface for Transaction model.
    
    Manages all wallet transactions including deposits, withdrawals, and trades.
    Enhanced with import/export, receipt viewing, and quick actions.
    """
    
    resource_class = TransactionResource
    
    list_display = (
        'id',
        'get_user_display',
        'transaction_type_badge',
        'currency_badge',
        'formatted_amount',
        'status_badge',
        'receipt_preview',
        'bank_account_display',
        'quick_actions',
        'created_at'
    )
    
    list_filter = (
        'status',
        'transaction_type',
        'currency',
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
        ('amount', NumericRangeFilter),
    )
    
    search_fields = (
        'id',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'description',
        'admin_notes'
    )
    
    autocomplete_fields = ('profile', 'bank_account', 'related_order')
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'completed_at'
    )
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('profile', 'transaction_type', 'currency', 'amount'),
            'description': '⚠️ برای تعدیل دستی موجودی، نوع تراکنش را "تعدیل" انتخاب کنید و دلیل را در توضیحات بنویسید.'
        }),
        ('جزئیات', {
            'fields': ('bank_account', 'related_order', 'receipt_image', 'description')
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_notes'),
            'description': 'برای تعدیل دستی، وضعیت باید "تکمیل شده" باشد.'
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_transactions', 'reject_transactions', 'create_manual_adjustment']
    
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: Transaction) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    get_user_display.admin_order_field = 'profile__user__first_name'
    
    def transaction_type_badge(self, obj: Transaction) -> str:
        """Display transaction type with badge."""
        badges = {
            'DEPOSIT': '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">📥 واریز</span>',
            'WITHDRAW': '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">📤 برداشت</span>',
            'BUY': '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">📈 خرید</span>',
            'SELL': '<span class="badge badge-primary" style="background-color: #007bff; color: white; padding: 5px 10px; border-radius: 12px;">📉 فروش</span>',
            'ADJUSTMENT': '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">⚙️ تعدیل</span>'
        }
        return format_html(badges.get(obj.transaction_type, ''))
    transaction_type_badge.short_description = 'نوع'
    transaction_type_badge.admin_order_field = 'transaction_type'
    
    def currency_badge(self, obj: Transaction) -> str:
        """Display currency with badge."""
        badges = {
            'RIAL': '<span class="badge" style="background-color: #6f42c1; color: white; padding: 5px 10px; border-radius: 12px;">ریال</span>',
            'GOLD': '<span class="badge" style="background-color: #ffd700; color: black; padding: 5px 10px; border-radius: 12px;">طلا</span>',
            'COIN': '<span class="badge" style="background-color: #ff8c00; color: white; padding: 5px 10px; border-radius: 12px;">سکه</span>',
            'DOLLAR': '<span class="badge" style="background-color: #20c997; color: white; padding: 5px 10px; border-radius: 12px;">دلار</span>',
        }
        return format_html(badges.get(obj.currency, obj.get_currency_display()))
    currency_badge.short_description = 'ارز'
    currency_badge.admin_order_field = 'currency'
    
    def formatted_amount(self, obj: Transaction) -> str:
        """Format amount."""
        return f"{obj.amount:,.2f}"
    formatted_amount.short_description = 'مقدار'
    formatted_amount.admin_order_field = 'amount'
    
    def status_badge(self, obj: Transaction) -> str:
        """Display status with badge."""
        badges = {
            'PENDING': '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">⏳ در انتظار</span>',
            'COMPLETED': '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تکمیل</span>',
            'CANCELLED': '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">✗ لغو</span>',
            'REJECTED': '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">✗ رد</span>',
        }
        return format_html(badges.get(obj.status, ''))
    status_badge.short_description = 'وضعیت'
    status_badge.admin_order_field = 'status'
    
    def receipt_preview(self, obj: Transaction) -> str:
        """Show receipt preview if available."""
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none;">📷 مشاهده رسید</a>',
                obj.receipt_image.url
            )
        return format_html('<span style="color: gray;">-</span>')
    receipt_preview.short_description = 'رسید'
    
    def bank_account_display(self, obj: Transaction) -> str:
        """Display bank account."""
        if obj.bank_account:
            return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
        return '-'
    bank_account_display.short_description = 'حساب بانکی'
    
    def quick_actions(self, obj: Transaction) -> str:
        """Display quick action buttons for pending transactions."""
        if obj.status == Transaction.TransactionStatus.PENDING and obj.transaction_type == Transaction.TransactionType.DEPOSIT:
            approve_url = reverse('admin:trading_transaction_changelist')
            return format_html(
                '<div style="white-space: nowrap;">'
                '<button class="button" style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer; margin-right: 3px;" '
                'onclick="if(confirm(\'آیا از تأیید این تراکنش مطمئن هستید؟\')) {{ '
                'fetch(\'/admin/trading/transaction/{}/change/\', {{method: \'POST\', headers: {{\'X-CSRFToken\': document.querySelector(\'[name=csrfmiddlewaretoken]\').value}}, '
                'body: new URLSearchParams({{\'action\': \'approve\'}}) }}).then(() => location.reload()); '
                '}}">✓ تأیید</button>'
                '<button class="button" style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer;" '
                'onclick="if(confirm(\'آیا از رد این تراکنش مطمئن هستید؟\')) {{ '
                'fetch(\'/admin/trading/transaction/{}/change/\', {{method: \'POST\', headers: {{\'X-CSRFToken\': document.querySelector(\'[name=csrfmiddlewaretoken]\').value}}, '
                'body: new URLSearchParams({{\'action\': \'reject\'}}) }}).then(() => location.reload()); '
                '}}">✗ رد</button>'
                '</div>',
                obj.id,
                obj.id
            )
        return format_html('<span style="color: #999;">—</span>')
    quick_actions.short_description = '⚡ عملیات سریع'
    
    def save_model(self, request, obj, form, change):
        """
        Override save to handle manual adjustments.
        For ADJUSTMENT type transactions, automatically update user balance.
        """
        is_new = obj.pk is None
        
        # Save the transaction first
        super().save_model(request, obj, form, change)
        
        # If it's a new ADJUSTMENT transaction with COMPLETED status, update balance
        if is_new and obj.transaction_type == Transaction.TransactionType.ADJUSTMENT and obj.status == Transaction.TransactionStatus.COMPLETED:
            from users.services import WalletService
            
            # Log the admin who made the adjustment
            username = getattr(request.user, 'username', 'unknown')
            obj.admin_notes = f"Manual adjustment by {username} at {timezone.now()}\n{obj.admin_notes}"
            
            # Update user balance
            try:
                WalletService.add_balance(
                    obj.profile,
                    obj.currency,
                    obj.amount
                )
                obj.completed_at = timezone.now()
                obj.save()
                
                self.message_user(
                    request,
                    f'تعدیل دستی با موفقیت اعمال شد. موجودی {obj.profile.get_display_name()} به‌روزرسانی گردید.',
                    level='success'
                )
            except Exception as e:
                obj.status = Transaction.TransactionStatus.REJECTED
                obj.admin_notes += f"\nError: {str(e)}"
                obj.save()
                
                self.message_user(
                    request,
                    f'خطا در اعمال تعدیل: {str(e)}',
                    level='error'
                )
    
    @db_transaction.atomic
    def approve_transactions(self, request, queryset):
        """Approve pending deposit transactions and credit user balances."""
        from users.services import WalletService
        
        pending_txns = queryset.filter(
            status='PENDING',
            transaction_type='DEPOSIT'
        )
        approved_count = 0
        
        for txn in pending_txns:
            try:
                # Add balance to user
                WalletService.add_balance(
                    txn.profile,
                    txn.currency,
                    txn.amount
                )
                
                # Mark transaction as completed
                txn.status = 'COMPLETED'
                txn.completed_at = timezone.now()
                txn.save()
                
                approved_count += 1
            except Exception as e:
                txn.admin_notes += f"\n[{timezone.now()}] خطا: {str(e)}"
                txn.save()
        
        self.message_user(
            request,
            f'{approved_count} تراکنش تأیید و موجودی کاربران به‌روزرسانی شد.'
        )
    approve_transactions.short_description = 'تأیید واریزهای انتخاب شده'
    
    def reject_transactions(self, request, queryset):
        """Reject pending transactions."""
        pending_txns = queryset.filter(status='PENDING')
        updated = pending_txns.update(status='REJECTED')
        
        self.message_user(
            request,
            f'{updated} تراکنش رد شد.'
        )
    reject_transactions.short_description = 'رد تراکنش‌های انتخاب شده'
    
    def create_manual_adjustment(self, request: HttpRequest, queryset: Any) -> None:
        """
        Create manual balance adjustments with mandatory reason.
        This is for exceptional circumstances only and requires superuser permission.
        """
        if not getattr(request.user, 'is_superuser', False):
            self.message_user(
                request,
                'فقط مدیران کل می‌توانند تعدیل دستی ایجاد کنند.',
                level='error'
            )
            return
        
        # Redirect to a custom form for manual adjustment
        # For now, display a message that this requires custom implementation
        self.message_user(
            request,
            'برای ایجاد تعدیل دستی، از بخش "افزودن تراکنش" استفاده کنید و نوع را "تعدیل" انتخاب کنید.',
            level='info'
        )
    create_manual_adjustment.short_description = '⚙️ ایجاد تعدیل دستی موجودی'


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(ImportExportModelAdmin):
    """
    Admin interface for WithdrawRequest model.
    
    Manages withdrawal requests with balance freezing and processing.
    Enhanced with import/export, advanced filters, and quick processing.
    """
    
    resource_class = WithdrawRequestResource
    
    list_display = (
        'id',
        'get_user_display',
        'currency_badge',
        'formatted_amount',
        'status_badge',
        'bank_account_display',
        'user_balance_check',
        'quick_actions',
        'created_at'
    )
    
    list_filter = (
        'status',
        'currency',
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
        ('amount', NumericRangeFilter),
    )
    
    search_fields = (
        'id',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number'
    )
    
    autocomplete_fields = ('profile', 'bank_account', 'related_transaction')
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'completed_at'
    )
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('profile', 'currency', 'amount', 'bank_account')
        }),
        ('وضعیت', {
            'fields': ('status', 'rejection_reason', 'admin_notes', 'related_transaction')
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['process_withdrawals', 'reject_withdrawals', 'cancel_withdrawals']
    
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: WithdrawRequest) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    get_user_display.admin_order_field = 'profile__user__first_name'
    
    def currency_badge(self, obj: WithdrawRequest) -> str:
        """Display currency with badge."""
        badges = {
            'RIAL': '<span class="badge" style="background-color: #6f42c1; color: white; padding: 5px 10px; border-radius: 12px;">ریال</span>',
            'GOLD': '<span class="badge" style="background-color: #ffd700; color: black; padding: 5px 10px; border-radius: 12px;">طلا</span>',
            'COIN': '<span class="badge" style="background-color: #ff8c00; color: white; padding: 5px 10px; border-radius: 12px;">سکه</span>',
            'DOLLAR': '<span class="badge" style="background-color: #20c997; color: white; padding: 5px 10px; border-radius: 12px;">دلار</span>',
        }
        return format_html(badges.get(obj.currency, obj.get_currency_display()))
    currency_badge.short_description = 'ارز'
    currency_badge.admin_order_field = 'currency'
    
    def formatted_amount(self, obj: WithdrawRequest) -> str:
        """Format amount."""
        return f"{obj.amount:,.2f}"
    formatted_amount.short_description = 'مقدار'
    formatted_amount.admin_order_field = 'amount'
    
    def status_badge(self, obj: WithdrawRequest) -> str:
        """Display status with badge."""
        badges = {
            'PENDING': '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">⏳ در انتظار</span>',
            'PROCESSING': '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">⚙️ در حال پردازش</span>',
            'COMPLETED': '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تکمیل</span>',
            'CANCELLED': '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">✗ لغو</span>',
            'REJECTED': '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">✗ رد</span>',
        }
        return format_html(badges.get(obj.status, ''))
    status_badge.short_description = 'وضعیت'
    status_badge.admin_order_field = 'status'
    
    def user_balance_check(self, obj: WithdrawRequest) -> str:
        """Check if user has sufficient frozen balance."""
        profile = obj.profile
        if obj.currency == 'RIAL':
            frozen = profile.frozen_rial_balance
        elif obj.currency == 'GOLD':
            frozen = profile.frozen_gold_balance
        elif obj.currency == 'COIN':
            frozen = profile.frozen_coin_balance
        else:  # DOLLAR
            frozen = profile.frozen_dollar_balance
        
        if frozen >= obj.amount:
            return format_html('<span style="color: green; font-weight: bold;">✓</span>')
        return format_html('<span style="color: red; font-weight: bold;" title="موجودی مسدود شده ناکافی">✗</span>')
    user_balance_check.short_description = 'موجودی مسدود'
    
    def bank_account_display(self, obj: WithdrawRequest) -> str:
        """Display bank account."""
        return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
    bank_account_display.short_description = 'حساب بانکی'
    
    def quick_actions(self, obj: WithdrawRequest) -> str:
        """Display quick action buttons for pending withdrawal requests."""
        if obj.status == 'PENDING':
            return format_html(
                '<div style="white-space: nowrap;">'
                '<button class="button" style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer; margin-right: 3px;" '
                'title="پردازش و تکمیل برداشت">✓ پردازش</button>'
                '<button class="button" style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer;" '
                'title="رد درخواست برداشت">✗ رد</button>'
                '</div>'
            )
        return format_html('<span style="color: #999;">—</span>')
    quick_actions.short_description = '⚡ عملیات سریع'
    
    @db_transaction.atomic
    def process_withdrawals(self, request, queryset):
        """Process pending withdrawal requests and deduct balances."""
        from users.services import WalletService
        
        pending_requests = queryset.filter(status='PENDING')
        processed_count = 0
        
        for req in pending_requests:
            try:
                # Process the withdrawal (deduct from total and frozen)
                WalletService.process_withdrawal(
                    req.profile,
                    req.currency,
                    req.amount
                )
                
                # Create transaction record
                txn = Transaction.objects.create(
                    profile=req.profile,
                    transaction_type='WITHDRAW',
                    currency=req.currency,
                    amount=req.amount,
                    bank_account=req.bank_account,
                    status='COMPLETED',
                    description=f"برداشت شماره {req.id}",
                    completed_at=timezone.now()
                )
                
                # Mark request as completed
                req.status = 'COMPLETED'
                req.related_transaction = txn
                req.completed_at = timezone.now()
                req.save()
                
                processed_count += 1
            except Exception as e:
                req.admin_notes += f"\n[{timezone.now()}] خطا: {str(e)}"
                req.save()
        
        self.message_user(
            request,
            f'{processed_count} درخواست برداشت پردازش شد.'
        )
    process_withdrawals.short_description = 'پردازش برداشت‌های انتخاب شده'
    
    @db_transaction.atomic
    def reject_withdrawals(self, request, queryset):
        """Reject withdrawal requests and unfreeze balances."""
        from users.services import WalletService
        
        pending_requests = queryset.filter(status='PENDING')
        rejected_count = 0
        
        for req in pending_requests:
            try:
                # Unfreeze balance
                WalletService.unfreeze_balance(
                    req.profile,
                    req.currency,
                    req.amount
                )
                
                # Mark as rejected
                req.status = 'REJECTED'
                req.save()
                
                rejected_count += 1
            except Exception as e:
                req.admin_notes += f"\n[{timezone.now()}] خطا: {str(e)}"
                req.save()
        
        self.message_user(
            request,
            f'{rejected_count} درخواست برداشت رد شد.'
        )
    reject_withdrawals.short_description = 'رد برداشت‌های انتخاب شده'
    
    def cancel_withdrawals(self, request, queryset):
        """Cancel withdrawal requests."""
        pending_requests = queryset.filter(status='PENDING')
        updated = pending_requests.update(status='CANCELLED')
        
        self.message_user(
            request,
            f'{updated} درخواست برداشت لغو شد.'
        )
    cancel_withdrawals.short_description = 'لغو برداشت‌های انتخاب شده'


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """
    Admin interface for PriceHistory model.
    
    View-only interface for price history tracking.
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
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding price history manually."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete price history."""
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def buy_price_display(self, obj: PriceHistory) -> str:
        """Display buy price."""
        return format_html(
            '<span style="color: #2e7d32; font-weight: bold;">{:,.0f} ریال</span>',
            obj.buy_price
        )
    buy_price_display.short_description = 'قیمت خرید'
    buy_price_display.admin_order_field = 'buy_price'
    
    def sell_price_display(self, obj: PriceHistory) -> str:
        """Display sell price."""
        return format_html(
            '<span style="color: #c62828; font-weight: bold;">{:,.0f} ریال</span>',
            obj.sell_price
        )
    sell_price_display.short_description = 'قیمت فروش'
    sell_price_display.admin_order_field = 'sell_price'
    
    def price_change(self, obj: PriceHistory) -> str:
        """Display price change from previous."""
        change = obj.get_price_change_from_previous()
        
        if not change:
            return format_html('<span style="color: #999;">—</span>')
        
        buy_change, sell_change = change
        avg_change = (buy_change + sell_change) / 2
        
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
            '<span style="color: {}; font-weight: bold;">{} {:+.2f}%</span>',
            color,
            emoji,
            avg_change
        )
    price_change.short_description = 'تغییر قیمت'


# ============================================
# ADMIN REPORTING DASHBOARD
# ============================================

class ReportingDashboard(admin.ModelAdmin):
    """
    Custom admin view for Business Intelligence and Reporting.
    
    Provides comprehensive reporting tools for administrators including:
    - Profit & Loss statements
    - User activity reports
    - Balance sheet aggregates
    - Export capabilities
    """
    
    def changelist_view(self, request, extra_context=None):
        """
        Custom changelist view that displays reporting dashboard.
        """
        from datetime import timedelta
        
        extra_context = extra_context or {}
        
        # Get date ranges
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Profit & Loss Reports
        pl_7d = BusinessReportService.get_profit_loss_report(start_date=last_7d)
        pl_30d = BusinessReportService.get_profit_loss_report(start_date=last_30d)
        pl_this_month = BusinessReportService.get_profit_loss_report(start_date=this_month_start)
        
        # Balance Sheet
        balance_sheet = BusinessReportService.get_balance_sheet()
        
        # User Activity
        user_activity_30d = BusinessReportService.get_user_activity_report(days=30)
        
        # Recent high-value transactions
        high_value_orders = Order.objects.filter(
            status=Order.OrderStatus.COMPLETED,
            total_amount__gte=10000000  # 10 million Rial
        ).order_by('-created_at')[:10]
        
        # Pending approvals count
        pending_deposits = Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            transaction_type=Transaction.TransactionType.DEPOSIT
        ).count()
        
        pending_withdrawals = WithdrawRequest.objects.filter(
            status='PENDING'
        ).count()
        
        extra_context.update({
            # Profit & Loss
            'pl_7d': pl_7d,
            'pl_30d': pl_30d,
            'pl_this_month': pl_this_month,
            
            # Balance Sheet
            'balance_sheet': balance_sheet,
            
            # User Activity
            'user_activity': user_activity_30d,
            
            # Recent Activity
            'high_value_orders': high_value_orders,
            
            # Pending Items
            'pending_deposits': pending_deposits,
            'pending_withdrawals': pending_withdrawals,
            
            # Page title
            'title': 'Business Intelligence Dashboard',
            'subtitle': 'Comprehensive reports and analytics for trading operations'
        })
        
        return super().changelist_view(request, extra_context=extra_context)
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """No add permission for reporting dashboard."""
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """View-only dashboard."""
        return True
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """No delete permission for reporting dashboard."""
        return False


# Note: Transaction is already registered above with @admin.register(Transaction)


# Create a custom admin site section for reporting
class BusinessReportingAdmin(admin.ModelAdmin):
    """
    Proxy admin for business reporting dashboard.
    This provides a dedicated section in admin for viewing reports.
    """
    
    change_list_template = 'admin/trading/reporting_dashboard.html'
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return bool(request.user and getattr(request.user, 'is_staff', False))
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        return False
    
    def has_module_permission(self, request: HttpRequest) -> bool:
        return bool(request.user and getattr(request.user, 'is_staff', False))
    
    def changelist_view(self, request, extra_context=None):
        """Display reporting dashboard."""
        extra_context = extra_context or {}
        
        # Get date ranges
        now = timezone.now()
        last_7d = now - timedelta(days=7)
        last_30d = now - timedelta(days=30)
        this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get date range from request if provided
        custom_start_str = request.GET.get('start_date')
        custom_end_str = request.GET.get('end_date')
        
        custom_start: Optional[datetime] = None
        custom_end: Optional[datetime] = None
        
        if custom_start_str:
            try:
                custom_start = datetime.strptime(custom_start_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        if custom_end_str:
            try:
                custom_end = datetime.strptime(custom_end_str, '%Y-%m-%d')
            except ValueError:
                pass
        
        # Profit & Loss Reports
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
        
        # Recent high-value orders
        high_value_orders = Order.objects.filter(
            status=Order.OrderStatus.COMPLETED,
            total_amount__gte=10000000  # 10 million Rial
        ).select_related('profile', 'product').order_by('-created_at')[:20]
        
        # Pending approvals
        pending_deposits = Transaction.objects.filter(
            status=Transaction.TransactionStatus.PENDING,
            transaction_type=Transaction.TransactionType.DEPOSIT
        ).select_related('profile').order_by('-created_at')[:10]
        
        pending_withdrawals = WithdrawRequest.objects.filter(
            status='PENDING'
        ).select_related('profile', 'bank_account').order_by('-created_at')[:10]
        
        # Daily statistics for the last 30 days
        daily_stats = []
        for i in range(30):
            day = now - timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            day_orders = Order.objects.filter(
                created_at__gte=day_start,
                created_at__lt=day_end,
                status=Order.OrderStatus.COMPLETED
            )
            
            day_revenue = Decimal('0')
            for order in day_orders:
                spread = order.product.get_price_spread()
                day_revenue += (order.quantity_grams * spread)
            
            daily_stats.append({
                'date': day_start.strftime('%Y-%m-%d'),
                'orders': day_orders.count(),
                'volume': float(day_orders.aggregate(Sum('total_amount'))['total_amount__sum'] or 0),
                'revenue': float(day_revenue)
            })
        
        daily_stats.reverse()
        
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
            
            # Filter params
            'custom_start': custom_start.strftime('%Y-%m-%d') if isinstance(custom_start, datetime) else '',
            'custom_end': custom_end.strftime('%Y-%m-%d') if isinstance(custom_end, datetime) else '',
            
            # Admin context
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
