"""
Django admin configuration for trading app.

Provides admin interfaces for Product and Order models.
Enhanced with import/export, advanced filters, and analytics.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction as db_transaction
from django.utils import timezone
from django.urls import reverse
from django.db.models import Count, Sum, Avg, Q
from typing import Optional
from decimal import Decimal
from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export import resources, fields  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin, ExportActionMixin  # type: ignore[import-untyped]

from .models import Product, Order, Transaction, WithdrawRequest


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
        'buy_price',
        'sell_price',
        'price_spread_display',
        'is_active',
        'order_count',
        'updated_at'
    )
    
    list_editable = ('buy_price', 'sell_price', 'is_active')
    
    list_filter = (
        'is_active', 
        'product_code',
        ('updated_at', DateRangeFilter),
        ('buy_price', NumericRangeFilter),
        ('sell_price', NumericRangeFilter),
    )
    
    search_fields = ('name', 'slug')
    
    readonly_fields = ('slug', 'updated_at', 'created_at')
    
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('name', 'slug')
        }),
        ('قیمت‌گذاری', {
            'fields': ('buy_price', 'sell_price'),
            'description': 'قیمت‌ها به ریال برای هر گرم است.'
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
    
    actions = ['complete_orders', 'cancel_orders']
    
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
            Order.OrderStatus.PENDING: '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">⏳ در انتظار</span>',
            Order.OrderStatus.COMPLETED: '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تکمیل</span>',
            Order.OrderStatus.CANCELLED: '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">✗ لغو</span>',
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
    
    @db_transaction.atomic
    def complete_orders(self, request, queryset):
        """
        Bulk action to complete selected pending orders.
        
        Updates user balances atomically.
        """
        pending_orders = queryset.filter(status=Order.OrderStatus.PENDING)
        completed_count = 0
        
        for order in pending_orders:
            try:
                profile = order.profile
                
                if order.order_type == Order.OrderType.BUY:
                    # User buys gold from us
                    # Deduct Rial, add Gold
                    if profile.has_sufficient_rial_balance(order.total_amount):
                        profile.rial_balance -= order.total_amount
                        profile.gold_balance_grams += order.quantity_grams
                        profile.save()
                        
                        order.status = Order.OrderStatus.COMPLETED
                        order.completed_at = timezone.now()
                        order.save()
                        completed_count += 1
                    else:
                        order.notes += f"\n[{timezone.now()}] موجودی ریالی ناکافی."
                        order.save()
                        
                elif order.order_type == Order.OrderType.SELL:
                    # User sells gold to us
                    # Deduct Gold, add Rial
                    if profile.has_sufficient_gold_balance(order.quantity_grams):
                        profile.gold_balance_grams -= order.quantity_grams
                        profile.rial_balance += order.total_amount
                        profile.save()
                        
                        order.status = Order.OrderStatus.COMPLETED
                        order.completed_at = timezone.now()
                        order.save()
                        completed_count += 1
                    else:
                        order.notes += f"\n[{timezone.now()}] موجودی طلا ناکافی."
                        order.save()
                        
            except Exception as e:
                order.notes += f"\n[{timezone.now()}] خطا: {str(e)}"
                order.save()
        
        self.message_user(
            request,
            f'{completed_count} سفارش با موفقیت تکمیل شد.'
        )
    complete_orders.short_description = 'تکمیل سفارشات انتخاب شده'
    
    def cancel_orders(self, request, queryset):
        """Bulk action to cancel selected pending orders."""
        pending_orders = queryset.filter(status=Order.OrderStatus.PENDING)
        updated = pending_orders.update(status=Order.OrderStatus.CANCELLED)
        
        self.message_user(
            request,
            f'{updated} سفارش لغو شد.'
        )
    cancel_orders.short_description = 'لغو سفارشات انتخاب شده'


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
            'fields': ('profile', 'transaction_type', 'currency', 'amount')
        }),
        ('جزئیات', {
            'fields': ('bank_account', 'related_order', 'receipt_image', 'description')
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_notes')
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_transactions', 'reject_transactions']
    
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
