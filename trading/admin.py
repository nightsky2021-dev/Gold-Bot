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

from .models import Product, Order, Transaction, WithdrawRequest


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
    """
    Admin interface for Transaction model.
    
    Manages all wallet transactions including deposits, withdrawals, and trades.
    """
    
    list_display = (
        'id',
        'get_user_display',
        'transaction_type_display',
        'currency_display',
        'formatted_amount',
        'status_display',
        'bank_account_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'transaction_type',
        'currency',
        'created_at'
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
    
    def transaction_type_display(self, obj: Transaction) -> str:
        """Display transaction type with emoji."""
        emojis = {
            'DEPOSIT': '📥',
            'WITHDRAW': '📤',
            'BUY': '📈',
            'SELL': '📉',
            'ADJUSTMENT': '⚙️'
        }
        emoji = emojis.get(obj.transaction_type, '💳')
        return f"{emoji} {obj.get_transaction_type_display()}"
    transaction_type_display.short_description = 'نوع'
    transaction_type_display.admin_order_field = 'transaction_type'
    
    def currency_display(self, obj: Transaction) -> str:
        """Display currency."""
        return obj.get_currency_display()
    currency_display.short_description = 'ارز'
    currency_display.admin_order_field = 'currency'
    
    def formatted_amount(self, obj: Transaction) -> str:
        """Format amount."""
        return f"{obj.amount:,.2f}"
    formatted_amount.short_description = 'مقدار'
    formatted_amount.admin_order_field = 'amount'
    
    def status_display(self, obj: Transaction) -> str:
        """Display status with color."""
        colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': 'gray',
            'REJECTED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    status_display.admin_order_field = 'status'
    
    def bank_account_display(self, obj: Transaction) -> str:
        """Display bank account."""
        if obj.bank_account:
            return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
        return '-'
    bank_account_display.short_description = 'حساب بانکی'
    
    @transaction.atomic
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
                    float(txn.amount)
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
class WithdrawRequestAdmin(admin.ModelAdmin):
    """
    Admin interface for WithdrawRequest model.
    
    Manages withdrawal requests with balance freezing and processing.
    """
    
    list_display = (
        'id',
        'get_user_display',
        'currency_display',
        'formatted_amount',
        'status_display',
        'bank_account_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'currency',
        'created_at'
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
    
    def currency_display(self, obj: WithdrawRequest) -> str:
        """Display currency."""
        return obj.get_currency_display()
    currency_display.short_description = 'ارز'
    currency_display.admin_order_field = 'currency'
    
    def formatted_amount(self, obj: WithdrawRequest) -> str:
        """Format amount."""
        return f"{obj.amount:,.2f}"
    formatted_amount.short_description = 'مقدار'
    formatted_amount.admin_order_field = 'amount'
    
    def status_display(self, obj: WithdrawRequest) -> str:
        """Display status with color."""
        colors = {
            'PENDING': 'orange',
            'PROCESSING': 'blue',
            'COMPLETED': 'green',
            'CANCELLED': 'gray',
            'REJECTED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    status_display.admin_order_field = 'status'
    
    def bank_account_display(self, obj: WithdrawRequest) -> str:
        """Display bank account."""
        return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
    bank_account_display.short_description = 'حساب بانکی'
    
    @transaction.atomic
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
                    float(req.amount)
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
    
    @transaction.atomic
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
                    float(req.amount)
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
