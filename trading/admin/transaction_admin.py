"""
Admin interface for Transaction model.

Manages wallet transactions including deposits, withdrawals, and trades.
"""

from typing import Any

from django.contrib import admin
from django.db import transaction as db_transaction
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone

from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin  # type: ignore[import-untyped]

from ..models import Transaction
from .resources import TransactionResource
from .mixins import FormattingMixin, UserDisplayMixin


class TransactionAdmin(ImportExportModelAdmin, FormattingMixin, UserDisplayMixin):
    """
    Admin interface for Transaction model.
    
    Features:
    - Deposit/withdrawal approval workflow
    - Manual balance adjustments
    - Receipt viewing
    - Transaction history tracking
    - Import/export functionality
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
    
    actions = ['approve_transactions', 'reject_transactions']
    
    date_hierarchy = 'created_at'
    
    def transaction_type_badge(self, obj: Transaction) -> str:
        """Display transaction type with color-coded badge."""
        type_map = {
            'DEPOSIT': ('📥 واریز', '#28a745', 'white'),
            'WITHDRAW': ('📤 برداشت', '#ffc107', 'black'),
            'BUY': ('📈 خرید', '#17a2b8', 'white'),
            'SELL': ('📉 فروش', '#007bff', 'white'),
            'ADJUSTMENT': ('⚙️ تعدیل', '#6c757d', 'white'),
        }
        
        if obj.transaction_type in type_map:
            text, bg_color, text_color = type_map[obj.transaction_type]
            return format_html(
                '<span class="badge" style="background-color: {}; color: {}; padding: 5px 10px; border-radius: 12px;">{}</span>',
                bg_color,
                text_color,
                text
            )
        
        return format_html('<span style="color: #999;">—</span>')
    
    transaction_type_badge.short_description = 'نوع'  # type: ignore
    transaction_type_badge.admin_order_field = 'transaction_type'  # type: ignore
    
    def currency_badge(self, obj: Transaction) -> str:
        """Display currency with color-coded badge."""
        currency_map = {
            'RIAL': ('ریال', '#6f42c1', 'white'),
            'GOLD': ('طلا', '#ffd700', 'black'),
            'COIN': ('سکه', '#ff8c00', 'white'),
            'DOLLAR': ('دلار', '#20c997', 'white'),
        }
        
        if obj.currency in currency_map:
            text, bg_color, text_color = currency_map[obj.currency]
            return format_html(
                '<span class="badge" style="background-color: {}; color: {}; padding: 5px 10px; border-radius: 12px;">{}</span>',
                bg_color,
                text_color,
                text
            )
        
        return obj.get_currency_display()
    
    currency_badge.short_description = 'ارز'  # type: ignore
    currency_badge.admin_order_field = 'currency'  # type: ignore
    
    def formatted_amount(self, obj: Transaction) -> str:
        """Format transaction amount."""
        return f"{obj.amount:,.2f}"
    
    formatted_amount.short_description = 'مقدار'  # type: ignore
    formatted_amount.admin_order_field = 'amount'  # type: ignore
    
    def status_badge(self, obj: Transaction) -> str:
        """Display transaction status with color-coded badge."""
        status_map = {
            'PENDING': ('⏳ در انتظار', '#ffc107', 'black'),
            'COMPLETED': ('✓ تکمیل', '#28a745', 'white'),
            'CANCELLED': ('✗ لغو', '#6c757d', 'white'),
            'REJECTED': ('✗ رد', '#dc3545', 'white'),
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
    
    def receipt_preview(self, obj: Transaction) -> str:
        """Show receipt preview button if available."""
        if obj.receipt_image:
            return format_html(
                '<a href="{}" target="_blank" class="button" style="background-color: #007bff; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none;">📷 مشاهده رسید</a>',
                obj.receipt_image.url
            )
        return format_html('<span style="color: gray;">—</span>')
    
    receipt_preview.short_description = 'رسید'  # type: ignore
    
    def bank_account_display(self, obj: Transaction) -> str:
        """Display associated bank account information."""
        if obj.bank_account:
            return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
        return '—'
    
    bank_account_display.short_description = 'حساب بانکی'  # type: ignore
    
    def quick_actions(self, obj: Transaction) -> str:
        """
        Display quick action buttons for pending transactions.
        
        Note: These buttons use inline JavaScript for immediate action.
        In production, consider implementing proper AJAX endpoints.
        """
        if obj.status == Transaction.TransactionStatus.PENDING and obj.transaction_type == Transaction.TransactionType.DEPOSIT:
            return format_html(
                '<div style="white-space: nowrap;">'
                '<button class="button" style="background-color: #28a745; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer; margin-right: 3px;" '
                'title="تأیید تراکنش">✓ تأیید</button>'
                '<button class="button" style="background-color: #dc3545; color: white; padding: 3px 10px; border-radius: 4px; border: none; cursor: pointer;" '
                'title="رد تراکنش">✗ رد</button>'
                '</div>'
            )
        return format_html('<span style="color: #999;">—</span>')
    
    quick_actions.short_description = '⚡ عملیات سریع'  # type: ignore
    
    def save_model(self, request: HttpRequest, obj: Transaction, form: Any, change: bool) -> None:
        """
        Handle save operations with special logic for manual adjustments.
        
        When creating ADJUSTMENT type transactions, automatically update user balance.
        """
        is_new = obj.pk is None
        
        # Save the transaction first
        super().save_model(request, obj, form, change)
        
        # Handle manual adjustments
        if is_new and obj.transaction_type == Transaction.TransactionType.ADJUSTMENT and obj.status == Transaction.TransactionStatus.COMPLETED:
            from users.services import WalletService
            
            # Log the admin who made the adjustment
            username = getattr(request.user, 'username', 'unknown')
            obj.admin_notes = f"Manual adjustment by {username} at {timezone.now()}\n{obj.admin_notes or ''}"
            
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
    def approve_transactions(self, request: HttpRequest, queryset: Any) -> None:
        """
        Bulk approve pending deposit transactions.
        
        Credits user balances and marks transactions as completed.
        """
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
                txn.admin_notes = f"{txn.admin_notes or ''}\n[{timezone.now()}] خطا: {str(e)}"
                txn.save()
        
        self.message_user(
            request,
            f'{approved_count} تراکنش تأیید و موجودی کاربران به‌روزرسانی شد.'
        )
    
    approve_transactions.short_description = 'تأیید واریزهای انتخاب شده'  # type: ignore
    
    def reject_transactions(self, request: HttpRequest, queryset: Any) -> None:
        """
        Bulk reject pending transactions.
        
        Sets status to REJECTED without affecting user balances.
        """
        pending_txns = queryset.filter(status='PENDING')
        updated = pending_txns.update(status='REJECTED')
        
        self.message_user(
            request,
            f'{updated} تراکنش رد شد.'
        )
    
    reject_transactions.short_description = 'رد تراکنش‌های انتخاب شده'  # type: ignore
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """
        Allow manual transaction creation for superusers only.
        
        This is typically used for manual balance adjustments.
        """
        return bool(request.user and getattr(request.user, 'is_superuser', False))


__all__ = ['TransactionAdmin']

