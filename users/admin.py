"""
Django admin configuration for users app.

Provides a comprehensive admin interface for managing user profiles.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.db.models import Q, Count, Sum, Avg
from django.urls import reverse
from django.utils.safestring import mark_safe
from typing import Optional
from rangefilter.filters import DateRangeFilter, NumericRangeFilter
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from .models import Profile, BankAccount


# ============================================
# IMPORT/EXPORT RESOURCES
# ============================================

class ProfileResource(resources.ModelResource):
    """Resource for importing/exporting Profile data."""
    
    user_full_name = fields.Field(
        column_name='نام کامل',
        attribute='user',
        readonly=True
    )
    user_email = fields.Field(
        column_name='ایمیل',
        attribute='user__email',
        readonly=True
    )
    
    class Meta:
        model = Profile
        fields = (
            'id', 'user_full_name', 'user_email', 'telegram_id', 
            'telegram_username', 'phone_number', 'is_approved',
            'rial_balance', 'gold_balance_grams', 'coin_balance', 'dollar_balance',
            'frozen_rial_balance', 'frozen_gold_balance', 'frozen_coin_balance', 
            'frozen_dollar_balance', 'created_at', 'updated_at'
        )
        export_order = fields


class BankAccountResource(resources.ModelResource):
    """Resource for importing/exporting BankAccount data."""
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    class Meta:
        model = BankAccount
        fields = (
            'id', 'user_name', 'bank_name', 'account_holder_name',
            'account_number', 'iban', 'account_type', 'is_verified',
            'created_at', 'updated_at'
        )
        export_order = fields


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile in User admin."""
    model = Profile
    can_delete = False
    verbose_name = 'پروفایل'
    verbose_name_plural = 'پروفایل‌ها'
    fields = (
        'telegram_id', 'telegram_username', 'phone_number',
        'is_approved', 'rial_balance', 'gold_balance_grams',
        'frozen_rial_balance', 'frozen_gold_balance'
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
class ProfileAdmin(ImportExportModelAdmin):
    """
    Admin interface for Profile model.
    
    Provides filtering, searching, and bulk actions for user profiles.
    Enhanced with import/export, advanced filters, and analytics.
    """
    
    resource_class = ProfileResource
    
    list_display = (
        'get_user_display',
        'phone_number',
        'user_tier_badge',
        'telegram_username',
        'is_approved',
        'formatted_rial_balance',
        'formatted_gold_balance',
        'total_orders_count',
        'total_trade_volume',
        'view_user_details',
        'created_at'
    )
    
    list_filter = (
        'is_approved',
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
        ('rial_balance', NumericRangeFilter),
        ('gold_balance_grams', NumericRangeFilter),
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
            'fields': (
                'rial_balance', 'gold_balance_grams',
                'frozen_rial_balance', 'frozen_gold_balance'
            ),
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
    
    def user_tier_badge(self, obj: Profile) -> str:
        """Display user tier badge."""
        return obj.get_tier_badge_html()
    user_tier_badge.short_description = '🏆 سطح کاربر'
    
    def total_trade_volume(self, obj: Profile) -> str:
        """Display total trade volume."""
        volume = obj.get_total_trade_volume()
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{:,.0f} میلیون</span>',
            volume / 1000000
        )
    total_trade_volume.short_description = '💰 حجم معاملات'
    
    def approval_status_badge(self, obj: Profile) -> str:
        """Display approval status with badge."""
        if obj.is_approved:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تأیید شده</span>'
            )
        return format_html(
            '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">⏳ در انتظار</span>'
        )
    approval_status_badge.short_description = 'وضعیت'
    
    def total_orders_count(self, obj: Profile) -> str:
        """Display total orders with link."""
        count = obj.orders.count()
        url = reverse('admin:trading_order_changelist') + f'?profile__id__exact={obj.id}'
        return format_html(
            '<a href="{}" style="color: #007bff; font-weight: bold;">{} سفارش</a>',
            url, count
        )
    total_orders_count.short_description = 'تعداد سفارشات'
    
    def view_user_details(self, obj: Profile) -> str:
        """Quick view link."""
        url = reverse('admin:users_profile_change', args=[obj.id])
        return format_html(
            '<a class="button" href="{}" style="background-color: #17a2b8; color: white; padding: 3px 8px; border-radius: 4px; text-decoration: none;">مشاهده</a>',
            url
        )
    view_user_details.short_description = 'عملیات'
    
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
    
    def get_total_orders(self, obj: Profile) -> int:
        """Get total number of orders."""
        return obj.order_set.count()  # type: ignore[attr-defined]
    get_total_orders.short_description = 'تعداد کل سفارشات'
    
    def get_pending_orders(self, obj: Profile) -> int:
        """Get number of pending orders."""
        return obj.order_set.filter(status='PENDING').count()  # type: ignore[attr-defined]
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
class BankAccountAdmin(ImportExportModelAdmin):
    """
    Admin interface for BankAccount model.
    
    Manages user bank accounts and verification.
    Enhanced with import/export and advanced filters.
    """
    
    resource_class = BankAccountResource
    
    list_display = (
        'id',
        'get_user_display',
        'bank_name',
        'account_holder_name',
        'masked_account_number',
        'is_verified',
        'account_type',
        'pending_txns_indicator',
        'created_at'
    )
    
    list_filter = (
        'is_verified',
        'account_type',
        'bank_name',
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
    )
    
    search_fields = (
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'account_holder_name',
        'account_number',
        'iban'
    )
    
    list_editable = ('is_verified',)
    
    autocomplete_fields = ('profile',)
    
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('profile',)
        }),
        ('اطلاعات بانکی', {
            'fields': (
                'bank_name',
                'account_holder_name',
                'account_number',
                'iban',
                'account_type'
            )
        }),
        ('وضعیت', {
            'fields': ('is_verified',)
        }),
        ('تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_accounts', 'unverify_accounts']
    
    def get_user_display(self, obj: BankAccount) -> str:
        """Display user information."""
        return obj.profile.get_display_name()
    get_user_display.short_description = 'کاربر'
    get_user_display.admin_order_field = 'profile__user__first_name'
    
    def masked_account_number(self, obj: BankAccount) -> str:
        """Display masked account number."""
        return obj.get_masked_account_number()
    masked_account_number.short_description = 'شماره حساب'
    
    def verification_status_badge(self, obj: BankAccount) -> str:
        """Display verification status with badge."""
        if obj.is_verified:
            return format_html(
                '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">✓ تأیید شده</span>'
            )
        return format_html(
            '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">⏳ در انتظار</span>'
        )
    verification_status_badge.short_description = 'وضعیت'
    verification_status_badge.admin_order_field = 'is_verified'
    
    def pending_txns_indicator(self, obj: BankAccount) -> str:
        """Show if account has pending transactions."""
        if obj.has_pending_transactions():
            return format_html(
                '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">⚠ دارد</span>'
            )
        return format_html(
            '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">✓ ندارد</span>'
        )
    pending_txns_indicator.short_description = 'تراکنش‌های در انتظار'
    
    def verify_accounts(self, request, queryset):
        """Bulk action to verify bank accounts."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            f'{updated} حساب بانکی تأیید شد.'
        )
    verify_accounts.short_description = 'تأیید حساب‌های بانکی انتخاب شده'
    
    def unverify_accounts(self, request, queryset):
        """Bulk action to unverify bank accounts."""
        updated = queryset.update(is_verified=False)
        self.message_user(
            request,
            f'تأیید {updated} حساب بانکی لغو شد.'
        )
    unverify_accounts.short_description = 'لغو تأیید حساب‌های بانکی انتخاب شده'
