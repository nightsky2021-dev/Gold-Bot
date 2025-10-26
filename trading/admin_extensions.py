"""
Extended admin registrations for Transaction and WithdrawRequest models.

This file is imported at the end of admin.py to keep the admin configuration organized.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db import transaction as db_transaction

from .models import Transaction, WithdrawRequest


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin interface for Transaction model."""
    
    list_display = (
        'transaction_number',
        'get_user_display',
        'transaction_type_display',
        'currency_type',
        'formatted_amount',
        'status_display',
        'created_at'
    )
    
    list_filter = (
        'status',
        'transaction_type',
        'currency_type',
        'created_at',
        'completed_at'
    )
    
    search_fields = (
        'transaction_number',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'profile__telegram_id'
    )
    
    readonly_fields = (
        'transaction_number',
        'balance_before',
        'balance_after',
        'created_at',
        'updated_at',
        'completed_at'
    )
    
    autocomplete_fields = ('profile', 'related_bank_account', 'related_order')
    
    fieldsets = (
        ('اطلاعات تراکنش', {
            'fields': (
                'transaction_number',
                'profile',
                'transaction_type',
                'currency_type',
                'amount'
            )
        }),
        ('موجودی', {
            'fields': ('balance_before', 'balance_after')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('روابط', {
            'fields': ('related_bank_account', 'related_order'),
            'classes': ('collapse',)
        }),
        ('یادداشت‌ها', {
            'fields': ('user_note', 'admin_note'),
            'classes': ('collapse',)
        }),
        ('تصاویر', {
            'fields': ('receipt_image',),
            'classes': ('collapse',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'completed_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['complete_transactions', 'cancel_transactions']
    
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: Transaction) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    
    def transaction_type_display(self, obj: Transaction) -> str:
        """Display transaction type with icon."""
        icons = {
            Transaction.TransactionType.DEPOSIT: '🟢',
            Transaction.TransactionType.WITHDRAW: '🔴',
            Transaction.TransactionType.BUY: '📈',
            Transaction.TransactionType.SELL: '📉',
            Transaction.TransactionType.TRANSFER_SEND: '↗️',
            Transaction.TransactionType.TRANSFER_RECEIVE: '↙️',
        }
        icon = icons.get(obj.transaction_type, '📝')
        return format_html(
            '{} {}',
            icon,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'نوع تراکنش'
    
    def formatted_amount(self, obj: Transaction) -> str:
        """Format amount."""
        return f"{obj.amount} {obj.get_currency_type_display()}"
    formatted_amount.short_description = 'مبلغ'
    
    def status_display(self, obj: Transaction) -> str:
        """Display status with color."""
        colors = {
            Transaction.TransactionStatus.PENDING: 'orange',
            Transaction.TransactionStatus.COMPLETED: 'green',
            Transaction.TransactionStatus.CANCELLED: 'red',
            Transaction.TransactionStatus.FAILED: 'darkred',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def complete_transactions(self, request, queryset):
        """Bulk action to complete selected transactions."""
        from .services import TransactionService
        
        pending = queryset.filter(status=Transaction.TransactionStatus.PENDING)
        completed_count = 0
        
        for txn in pending:
            try:
                TransactionService.complete_transaction(
                    transaction_id=txn.id,
                    admin_user=request.user
                )
                completed_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'خطا در تکمیل تراکنش {txn.transaction_number}: {str(e)}',
                    level='ERROR'
                )
        
        if completed_count > 0:
            self.message_user(
                request,
                f'{completed_count} تراکنش با موفقیت تکمیل شد.'
            )
    complete_transactions.short_description = 'تکمیل تراکنش‌های انتخاب شده'
    
    def cancel_transactions(self, request, queryset):
        """Bulk action to cancel selected transactions."""
        from .services import TransactionService
        
        pending = queryset.filter(status=Transaction.TransactionStatus.PENDING)
        cancelled_count = 0
        
        for txn in pending:
            try:
                TransactionService.cancel_transaction(
                    transaction_id=txn.id,
                    reason='لغو شده توسط ادمین',
                    admin_user=request.user
                )
                cancelled_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'خطا در لغو تراکنش {txn.transaction_number}: {str(e)}',
                    level='ERROR'
                )
        
        if cancelled_count > 0:
            self.message_user(
                request,
                f'{cancelled_count} تراکنش لغو شد.'
            )
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
        'created_at',
        'processed_at'
    )
    
    search_fields = (
        'request_number',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'bank_account__account_number'
    )
    
    readonly_fields = (
        'request_number',
        'created_at',
        'processed_at',
        'completed_at'
    )
    
    autocomplete_fields = ('profile', 'bank_account', 'related_transaction')
    
    fieldsets = (
        ('اطلاعات درخواست', {
            'fields': (
                'request_number',
                'profile',
                'currency_type',
                'amount'
            )
        }),
        ('حساب مقصد', {
            'fields': ('bank_account',)
        }),
        ('وضعیت', {
            'fields': ('status', 'admin_note')
        }),
        ('روابط', {
            'fields': ('related_transaction',),
            'classes': ('collapse',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'processed_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_requests', 'reject_requests']
    
    date_hierarchy = 'created_at'
    
    def get_user_display(self, obj: WithdrawRequest) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    
    def formatted_amount(self, obj: WithdrawRequest) -> str:
        """Format amount."""
        return f"{obj.amount} {obj.get_currency_type_display()}"
    formatted_amount.short_description = 'مبلغ'
    
    def get_bank_info(self, obj: WithdrawRequest) -> str:
        """Display bank account info."""
        return f"{obj.bank_account.bank_name} - {obj.bank_account.get_masked_account_number()}"
    get_bank_info.short_description = 'حساب مقصد'
    
    def status_display(self, obj: WithdrawRequest) -> str:
        """Display status with color."""
        colors = {
            WithdrawRequest.RequestStatus.PENDING: 'orange',
            WithdrawRequest.RequestStatus.APPROVED: 'blue',
            WithdrawRequest.RequestStatus.REJECTED: 'red',
            WithdrawRequest.RequestStatus.COMPLETED: 'green',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    
    def approve_requests(self, request, queryset):
        """Bulk action to approve selected withdraw requests."""
        from .services import WithdrawService
        
        pending = queryset.filter(status=WithdrawRequest.RequestStatus.PENDING)
        approved_count = 0
        
        for req in pending:
            try:
                WithdrawService.approve_withdraw(
                    withdraw_request_id=req.id,
                    admin_user=request.user
                )
                approved_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'خطا در تأیید درخواست {req.request_number}: {str(e)}',
                    level='ERROR'
                )
        
        if approved_count > 0:
            self.message_user(
                request,
                f'{approved_count} درخواست برداشت با موفقیت تأیید شد.'
            )
    approve_requests.short_description = 'تأیید درخواست‌های انتخاب شده'
    
    def reject_requests(self, request, queryset):
        """Bulk action to reject selected withdraw requests."""
        from .services import WithdrawService
        
        pending = queryset.filter(status=WithdrawRequest.RequestStatus.PENDING)
        rejected_count = 0
        
        for req in pending:
            try:
                WithdrawService.reject_withdraw(
                    withdraw_request_id=req.id,
                    reason='رد شده توسط ادمین',
                    admin_user=request.user
                )
                rejected_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f'خطا در رد درخواست {req.request_number}: {str(e)}',
                    level='ERROR'
                )
        
        if rejected_count > 0:
            self.message_user(
                request,
                f'{rejected_count} درخواست برداشت رد شد.'
            )
    reject_requests.short_description = 'رد درخواست‌های انتخاب شده'
