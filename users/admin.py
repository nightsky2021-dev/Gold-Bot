"""
Django admin configuration for users app.

Provides a comprehensive admin interface for managing user profiles.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Q
from typing import Optional

from .models import Profile, BankAccount


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile in User admin."""
    model = Profile
    can_delete = False
    verbose_name = 'پروفایل'
    verbose_name_plural = 'پروفایل‌ها'
    fields = (
        'telegram_id', 'telegram_username', 'phone_number',
        'is_approved', 'rial_balance', 'gold_balance_grams',
        'coin_balance', 'dollar_balance'
    )
    readonly_fields = ('telegram_id', 'telegram_username', 'phone_number')


class CustomUserAdmin(BaseUserAdmin):
    """Extended User admin with Profile inline."""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')


# Unregister the original User admin and register the custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for Profile model.
    
    Provides filtering, searching, and bulk actions for user profiles.
    """
    
    list_display = (
        'get_user_display',
        'phone_number',
        'telegram_username',
        'approval_status',
        'formatted_rial_balance',
        'formatted_gold_balance',
        'formatted_coin_balance',
        'formatted_dollar_balance',
        'created_at'
    )
    
    list_filter = (
        'is_approved',
        'created_at',
        'updated_at'
    )
    
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'phone_number',
        'telegram_id',
        'telegram_username'
    )
    
    list_editable = ('is_approved',)
    
    readonly_fields = (
        'telegram_id',
        'created_at',
        'updated_at',
        'get_total_orders',
        'get_pending_orders'
    )
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('اطلاعات تلگرام', {
            'fields': ('telegram_id', 'telegram_username')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone_number',)
        }),
        ('وضعیت حساب', {
            'fields': ('is_approved',)
        }),
        ('موجودی‌ها', {
            'fields': ('rial_balance', 'gold_balance_grams', 'coin_balance', 'dollar_balance'),
            'classes': ('wide',)
        }),
        ('موجودی‌های مسدود', {
            'fields': ('frozen_rial_balance', 'frozen_gold_balance', 'frozen_coin_balance', 'frozen_dollar_balance'),
            'classes': ('wide',)
        }),
        ('آمار', {
            'fields': ('get_total_orders', 'get_pending_orders'),
            'classes': ('collapse',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_users', 'disapprove_users']
    
    def get_user_display(self, obj: Profile) -> str:
        """Display user's full name or username."""
        full_name = obj.user.get_full_name()
        if full_name:
            return full_name
        return obj.user.username
    get_user_display.short_description = 'نام کاربر'
    
    def approval_status(self, obj: Profile) -> str:
        """Display approval status with color."""
        if obj.is_approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ تأیید شده</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ تأیید نشده</span>'
        )
    approval_status.short_description = 'وضعیت تأیید'
    
    def formatted_rial_balance(self, obj: Profile) -> str:
        """Format Rial balance with thousand separators."""
        return f"{obj.rial_balance:,.0f} ریال"
    formatted_rial_balance.short_description = 'موجودی ریالی'
    formatted_rial_balance.admin_order_field = 'rial_balance'
    
    def formatted_gold_balance(self, obj: Profile) -> str:
        """Format gold balance."""
        return f"{obj.gold_balance_grams} گرم"
    formatted_gold_balance.short_description = 'موجودی طلا'
    formatted_gold_balance.admin_order_field = 'gold_balance_grams'
    
    def formatted_coin_balance(self, obj: Profile) -> str:
        """Format coin balance."""
        return f"{obj.coin_balance:,.4f} سکه"
    formatted_coin_balance.short_description = 'موجودی سکه'
    formatted_coin_balance.admin_order_field = 'coin_balance'
    
    def formatted_dollar_balance(self, obj: Profile) -> str:
        """Format dollar balance."""
        return f"${obj.dollar_balance:,.2f}"
    formatted_dollar_balance.short_description = 'موجودی دلار'
    formatted_dollar_balance.admin_order_field = 'dollar_balance'
    
    def get_total_orders(self, obj: Profile) -> int:
        """Get total number of orders."""
        return obj.orders.count()
    get_total_orders.short_description = 'تعداد کل سفارشات'
    
    def get_pending_orders(self, obj: Profile) -> int:
        """Get number of pending orders."""
        return obj.orders.filter(status='PENDING').count()
    get_pending_orders.short_description = 'سفارشات در انتظار'
    
    def approve_users(self, request, queryset):
        """Bulk action to approve selected users."""
        updated = queryset.update(is_approved=True)
        self.message_user(
            request,
            f'{updated} کاربر با موفقیت تأیید شدند.'
        )
    approve_users.short_description = 'تأیید کاربران انتخاب شده'
    
    def disapprove_users(self, request, queryset):
        """Bulk action to disapprove selected users."""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f'تأیید {updated} کاربر لغو شد.'
        )
    disapprove_users.short_description = 'لغو تأیید کاربران انتخاب شده'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """
    Admin interface for BankAccount model.
    
    Provides filtering, searching, and bulk actions for bank accounts.
    """
    
    list_display = (
        'get_user_display',
        'account_holder_name',
        'bank_name',
        'get_masked_account_number_display',
        'account_type',
        'verification_status',
        'is_active',
        'created_at'
    )
    
    list_filter = (
        'bank_name',
        'account_type',
        'is_verified',
        'is_active',
        'created_at'
    )
    
    search_fields = (
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__user__username',
        'account_holder_name',
        'account_number',
        'bank_name'
    )
    
    list_editable = ('is_verified', 'is_active')
    
    readonly_fields = (
        'created_at',
        'updated_at',
        'get_masked_account_number_display'
    )
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('profile',)
        }),
        ('اطلاعات حساب بانکی', {
            'fields': ('account_holder_name', 'bank_name', 'account_type', 'account_number')
        }),
        ('وضعیت حساب', {
            'fields': ('is_verified', 'is_active')
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_accounts', 'unverify_accounts', 'activate_accounts', 'deactivate_accounts']
    
    def get_user_display(self, obj: BankAccount) -> str:
        """Display user's full name or username."""
        full_name = obj.profile.user.get_full_name()
        if full_name:
            return full_name
        return obj.profile.user.username
    get_user_display.short_description = 'نام کاربر'
    
    def verification_status(self, obj: BankAccount) -> str:
        """Display verification status with color."""
        if obj.is_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ تأیید شده</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ تأیید نشده</span>'
        )
    verification_status.short_description = 'وضعیت تأیید'
    
    def get_masked_account_number_display(self, obj: BankAccount) -> str:
        """Display masked account number."""
        return obj.get_masked_account_number()
    get_masked_account_number_display.short_description = 'شماره حساب (مخفی)'
    
    def verify_accounts(self, request, queryset):
        """Bulk action to verify selected accounts."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            f'{updated} حساب بانکی با موفقیت تأیید شدند.'
        )
    verify_accounts.short_description = 'تأیید حساب‌های انتخاب شده'
    
    def unverify_accounts(self, request, queryset):
        """Bulk action to unverify selected accounts."""
        updated = queryset.update(is_verified=False)
        self.message_user(
            request,
            f'تأیید {updated} حساب بانکی لغو شد.'
        )
    unverify_accounts.short_description = 'لغو تأیید حساب‌های انتخاب شده'
    
    def activate_accounts(self, request, queryset):
        """Bulk action to activate selected accounts."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} حساب بانکی فعال شدند.'
        )
    activate_accounts.short_description = 'فعال کردن حساب‌های انتخاب شده'
    
    def deactivate_accounts(self, request, queryset):
        """Bulk action to deactivate selected accounts."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} حساب بانکی غیرفعال شدند.'
        )
    deactivate_accounts.short_description = 'غیرفعال کردن حساب‌های انتخاب شده'
