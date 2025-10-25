"""
Django admin configuration for trading app.

Provides admin interfaces for Product and Order models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction
from django.utils import timezone
from typing import Optional
from decimal import Decimal

from .models import Product, Order, Transaction, WithdrawRequest, TransferRequest
from .services import DepositService, WithdrawService


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.
    
    Allows easy management of gold products and their prices.
    """
    
    list_display = (
        'name',
        'formatted_buy_price',
        'formatted_sell_price',
        'price_spread_display',
        'active_status',
        'updated_at'
    )
    
    list_editable = ('buy_price', 'sell_price', 'is_active')
    
    list_filter = ('is_active', 'updated_at')
    
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
    
    def formatted_buy_price(self, obj: Product) -> str:
        """Format buy price with thousand separators."""
        return f"{obj.buy_price:,.0f} ریال"
    formatted_buy_price.short_description = 'قیمت خرید (ما از مشتری)'
    formatted_buy_price.admin_order_field = 'buy_price'
    
    def formatted_sell_price(self, obj: Product) -> str:
        """Format sell price with thousand separators."""
        return f"{obj.sell_price:,.0f} ریال"
    formatted_sell_price.short_description = 'قیمت فروش (ما به مشتری)'
    formatted_sell_price.admin_order_field = 'sell_price'
    
    def price_spread_display(self, obj: Product) -> str:
        """Display price spread."""
        spread = obj.get_price_spread()
        percentage = obj.get_price_spread_percentage()
        return f"{spread:,.0f} ریال ({percentage:.2f}%)"
    price_spread_display.short_description = 'اختلاف قیمت'
    
    def active_status(self, obj: Product) -> str:
        """Display active status with color."""
        if obj.is_active:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ فعال</span>'
            )
        return format_html(
            '<span style="color: gray;">✗ غیرفعال</span>'
        )
    active_status.short_description = 'وضعیت'
    active_status.admin_order_field = 'is_active'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    
    Provides comprehensive order management with filtering and bulk actions.
    """
    
    list_display = (
        'id',
        'get_user_display',
        'product',
        'order_type_display',
        'status_display',
        'formatted_quantity',
        'formatted_total',
        'created_at'
    )
    
    list_filter = (
        'status',
        'order_type',
        'product',
        'created_at',
        'updated_at'
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
    
    def order_type_display(self, obj: Order) -> str:
        """Display order type with color."""
        if obj.order_type == Order.OrderType.BUY:
            return format_html(
                '<span style="color: green;">📈 {}</span>',
                obj.get_order_type_display()
            )
        return format_html(
            '<span style="color: blue;">📉 {}</span>',
            obj.get_order_type_display()
        )
    order_type_display.short_description = 'نوع سفارش'
    order_type_display.admin_order_field = 'order_type'
    
    def status_display(self, obj: Order) -> str:
        """Display status with color."""
        colors = {
            Order.OrderStatus.PENDING: 'orange',
            Order.OrderStatus.COMPLETED: 'green',
            Order.OrderStatus.CANCELLED: 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    status_display.admin_order_field = 'status'
    
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
    
    @transaction.atomic
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
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model."""
    
    list_display = (
        'transaction_number',
        'get_user_display',
        'transaction_type',
        'currency_type',
        'formatted_amount',
        'status_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'transaction_type',
        'currency_type',
        'created_at'
    )
    
    search_fields = (
        'transaction_number',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number'
    )
    
    readonly_fields = (
        'transaction_number',
        'balance_before',
        'balance_after',
        'created_at',
        'completed_at'
    )
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': ('transaction_number', 'profile', 'transaction_type', 'currency_type', 'amount')
        }),
        ('موجودی‌ها', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('روابط', {
            'fields': ('related_bank_account', 'related_user', 'related_order'),
            'classes': ('collapse',)
        }),
        ('یادداشت‌ها', {
            'fields': ('admin_note', 'user_note')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['complete_transactions', 'cancel_transactions']
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: Transaction) -> str:
        """Display user name."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    
    def formatted_amount(self, obj: Transaction) -> str:
        """Format amount."""
        currency_map = {'RIAL': 'ریال', 'GOLD': 'گرم', 'COIN': 'عدد', 'DOLLAR': 'دلار'}
        unit = currency_map.get(obj.currency_type, '')
        return f"{obj.amount:,.4f} {unit}"
    formatted_amount.short_description = 'مقدار'
    
    def status_display(self, obj: Transaction) -> str:
        """Display status with color."""
        colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
            'FAILED': 'darkred',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def complete_transactions(self, request, queryset):
        """Bulk action to complete transactions."""
        pending = queryset.filter(status='PENDING', transaction_type='DEPOSIT')
        completed_count = 0
        
        for txn in pending:
            success, msg = DepositService.approve_deposit(txn.id, request.user)
            if success:
                completed_count += 1
        
        self.message_user(request, f'{completed_count} تراکنش تکمیل شد.')
    complete_transactions.short_description = 'تکمیل واریزهای انتخاب شده'
    
    def cancel_transactions(self, request, queryset):
        """Bulk action to cancel transactions."""
        from .services import TransactionService
        pending = queryset.filter(status='PENDING')
        cancelled_count = 0
        
        for txn in pending:
            success, msg = TransactionService.cancel_transaction(txn.id, 'لغو توسط ادمین', request.user)
            if success:
                cancelled_count += 1
        
        self.message_user(request, f'{cancelled_count} تراکنش لغو شد.')
    cancel_transactions.short_description = 'لغو تراکنش‌های انتخاب شده'


@admin.register(WithdrawRequest)
class WithdrawRequestAdmin(admin.ModelAdmin):
    """Admin interface for WithdrawRequest model."""
    
    list_display = (
        'request_number',
        'get_user_display',
        'currency_type',
        'formatted_amount',
        'get_bank_info',
        'status_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'currency_type',
        'created_at'
    )
    
    search_fields = (
        'request_number',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number'
    )
    
    readonly_fields = (
        'request_number',
        'created_at',
        'processed_at',
        'completed_at'
    )
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': ('request_number', 'profile', 'currency_type', 'amount')
        }),
        ('حساب بانکی مقصد', {
            'fields': ('bank_account',)
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note')
        }),
        ('تراکنش مرتبط', {
            'fields': ('related_transaction',),
            'classes': ('collapse',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_withdraws', 'reject_withdraws']
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: WithdrawRequest) -> str:
        """Display user name."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    
    def formatted_amount(self, obj: WithdrawRequest) -> str:
        """Format amount."""
        currency_map = {'RIAL': 'ریال', 'GOLD': 'گرم', 'COIN': 'عدد', 'DOLLAR': 'دلار'}
        unit = currency_map.get(obj.currency_type, '')
        return f"{obj.amount:,.4f} {unit}"
    formatted_amount.short_description = 'مقدار'
    
    def get_bank_info(self, obj: WithdrawRequest) -> str:
        """Display bank account info."""
        return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
    get_bank_info.short_description = 'حساب بانکی'
    
    def status_display(self, obj: WithdrawRequest) -> str:
        """Display status with color."""
        colors = {
            'PENDING': 'orange',
            'APPROVED': 'blue',
            'COMPLETED': 'green',
            'REJECTED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def approve_withdraws(self, request, queryset):
        """Bulk action to approve withdrawals."""
        pending = queryset.filter(status='PENDING')
        approved_count = 0
        
        for wd in pending:
            success, msg = WithdrawService.approve_withdraw(wd.id, request.user)
            if success:
                approved_count += 1
        
        self.message_user(request, f'{approved_count} درخواست برداشت تایید شد.')
    approve_withdraws.short_description = 'تایید برداشت‌های انتخاب شده'
    
    def reject_withdraws(self, request, queryset):
        """Bulk action to reject withdrawals."""
        pending = queryset.filter(status='PENDING')
        rejected_count = 0
        
        for wd in pending:
            success, msg = WithdrawService.reject_withdraw(wd.id, 'رد توسط ادمین', request.user)
            if success:
                rejected_count += 1
        
        self.message_user(request, f'{rejected_count} درخواست برداشت رد شد.')
    reject_withdraws.short_description = 'رد برداشت‌های انتخاب شده'


@admin.register(TransferRequest)
class TransferRequestAdmin(admin.ModelAdmin):
    """Admin interface for TransferRequest model."""
    
    list_display = (
        'request_number',
        'get_sender_display',
        'get_receiver_display',
        'currency_type',
        'formatted_amount',
        'status_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'currency_type',
        'created_at'
    )
    
    search_fields = (
        'request_number',
        'sender_profile__user__first_name',
        'sender_profile__user__last_name',
        'receiver_profile__user__first_name',
        'receiver_profile__user__last_name',
        'receiver_phone'
    )
    
    readonly_fields = (
        'request_number',
        'created_at',
        'completed_at'
    )
    
    fieldsets = (
        ('اطلاعات انتقال', {
            'fields': ('request_number', 'currency_type', 'amount', 'description')
        }),
        ('فرستنده و گیرنده', {
            'fields': ('sender_profile', 'receiver_profile', 'receiver_phone')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('تراکنش‌های مرتبط', {
            'fields': ('sender_transaction', 'receiver_transaction'),
            'classes': ('collapse',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    date_hierarchy = 'created_at'
    
    def get_sender_display(self, obj: TransferRequest) -> str:
        """Display sender name."""
        return obj.sender_profile.get_display_name()
    get_sender_display.short_description = 'فرستنده'
    
    def get_receiver_display(self, obj: TransferRequest) -> str:
        """Display receiver name."""
        return obj.receiver_profile.get_display_name()
    get_receiver_display.short_description = 'گیرنده'
    
    def formatted_amount(self, obj: TransferRequest) -> str:
        """Format amount."""
        currency_map = {'RIAL': 'ریال', 'GOLD': 'گرم', 'COIN': 'عدد', 'DOLLAR': 'دلار'}
        unit = currency_map.get(obj.currency_type, '')
        return f"{obj.amount:,.4f} {unit}"
    formatted_amount.short_description = 'مقدار'
    
    def status_display(self, obj: TransferRequest) -> str:
        """Display status with color."""
        colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
