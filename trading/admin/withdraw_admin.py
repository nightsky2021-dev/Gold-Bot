"""
Admin interface for WithdrawRequest model.

Manages withdrawal requests with balance freezing and processing workflows.
"""

from typing import Any

from django.contrib import admin
from django.db import transaction as db_transaction
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils import timezone

from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin  # type: ignore[import-untyped]

from ..models import WithdrawRequest, Transaction
from .resources import WithdrawRequestResource
from .mixins import FormattingMixin, UserDisplayMixin


class WithdrawRequestAdmin(ImportExportModelAdmin, FormattingMixin, UserDisplayMixin):
    """
    Admin interface for WithdrawRequest model.
    
    Features:
    - Withdrawal request processing
    - Balance freeze/unfreeze management
    - Bank account verification
    - Bulk approval/rejection
    - Import/export functionality
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
    
    def currency_badge(self, obj: WithdrawRequest) -> str:
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
    
    def formatted_amount(self, obj: WithdrawRequest) -> str:
        """Format withdrawal amount."""
        return f"{obj.amount:,.2f}"
    
    formatted_amount.short_description = 'مقدار'  # type: ignore
    formatted_amount.admin_order_field = 'amount'  # type: ignore
    
    def status_badge(self, obj: WithdrawRequest) -> str:
        """Display withdrawal status with color-coded badge."""
        status_map = {
            'PENDING': ('⏳ در انتظار', '#ffc107', 'black'),
            'PROCESSING': ('⚙️ در حال پردازش', '#17a2b8', 'white'),
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
    
    def user_balance_check(self, obj: WithdrawRequest) -> str:
        """
        Check if user has sufficient frozen balance for withdrawal.
        
        This verifies the amount is properly frozen and available for processing.
        """
        profile = obj.profile
        
        # Get frozen balance for the currency
        frozen_balance_map = {
            'RIAL': profile.frozen_rial_balance,
            'GOLD': profile.frozen_gold_balance,
            'COIN': profile.frozen_coin_balance,
            'DOLLAR': profile.frozen_dollar_balance,
        }
        
        frozen = frozen_balance_map.get(obj.currency, 0)
        
        if frozen >= obj.amount:
            return format_html(
                '<span style="color: green; font-size: 16px; font-weight: bold;">✓</span>'
            )
        
        return format_html(
            '<span style="color: red; font-size: 16px; font-weight: bold;" title="موجودی مسدود شده ناکافی">✗</span>'
        )
    
    user_balance_check.short_description = 'موجودی مسدود'  # type: ignore
    
    def bank_account_display(self, obj: WithdrawRequest) -> str:
        """Display bank account information."""
        return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
    
    bank_account_display.short_description = 'حساب بانکی'  # type: ignore
    
    def quick_actions(self, obj: WithdrawRequest) -> str:
        """
        Display quick action buttons for pending requests.
        
        Provides one-click processing and rejection for pending withdrawals.
        """
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
    
    quick_actions.short_description = '⚡ عملیات سریع'  # type: ignore
    
    @db_transaction.atomic
    def process_withdrawals(self, request: HttpRequest, queryset: Any) -> None:
        """
        Process pending withdrawal requests.
        
        Steps:
        1. Verify frozen balance
        2. Deduct from total and frozen balance
        3. Create transaction record
        4. Mark request as completed
        """
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
                req.admin_notes = f"{req.admin_notes or ''}\n[{timezone.now()}] خطا: {str(e)}"
                req.save()
        
        self.message_user(
            request,
            f'{processed_count} درخواست برداشت پردازش شد.'
        )
    
    process_withdrawals.short_description = 'پردازش برداشت‌های انتخاب شده'  # type: ignore
    
    @db_transaction.atomic
    def reject_withdrawals(self, request: HttpRequest, queryset: Any) -> None:
        """
        Reject withdrawal requests and unfreeze balances.
        
        Steps:
        1. Unfreeze the balance
        2. Mark request as rejected
        """
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
                req.admin_notes = f"{req.admin_notes or ''}\n[{timezone.now()}] خطا: {str(e)}"
                req.save()
        
        self.message_user(
            request,
            f'{rejected_count} درخواست برداشت رد شد و موجودی آزاد گردید.'
        )
    
    reject_withdrawals.short_description = 'رد برداشت‌های انتخاب شده'  # type: ignore
    
    def cancel_withdrawals(self, request: HttpRequest, queryset: Any) -> None:
        """
        Cancel withdrawal requests.
        
        Simple status update to CANCELLED without balance changes.
        """
        pending_requests = queryset.filter(status='PENDING')
        updated = pending_requests.update(status='CANCELLED')
        
        self.message_user(
            request,
            f'{updated} درخواست برداشت لغو شد.'
        )
    
    cancel_withdrawals.short_description = 'لغو برداشت‌های انتخاب شده'  # type: ignore


__all__ = ['WithdrawRequestAdmin']

