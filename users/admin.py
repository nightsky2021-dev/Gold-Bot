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
from django.utils import timezone
from typing import Optional
from rangefilter.filters import DateRangeFilter, NumericRangeFilter
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionMixin

from .models import Profile, BankAccount


# ============================================
# CUSTOM FILTERS
# ============================================

class PendingApprovalFilter(admin.SimpleListFilter):
    """Custom filter for pending approval status."""
    title = 'وضعیت تأیید'
    parameter_name = 'approval_status'
    
    def lookups(self, request, model_admin):
        return (
            ('pending', '⏳ در انتظار تأیید'),
            ('approved', '✅ تأیید شده'),
            ('new_registrations', '🆕 ثبت‌نام‌های جدید (24 ساعت اخیر)'),
            ('incomplete_profile', '⚠️ پروفایل ناقص (بدون کد ملی)'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'pending':
            return queryset.filter(is_approved=False)
        elif self.value() == 'approved':
            return queryset.filter(is_approved=True)
        elif self.value() == 'new_registrations':
            last_24h = timezone.now() - timezone.timedelta(hours=24)
            return queryset.filter(created_at__gte=last_24h, is_approved=False)
        elif self.value() == 'incomplete_profile':
            return queryset.filter(Q(national_code__isnull=True) | Q(national_code=''))
        return queryset


class ProfileCompletenessFilter(admin.SimpleListFilter):
    """Filter for profile completeness."""
    title = 'تکمیل پروفایل'
    parameter_name = 'profile_complete'
    
    def lookups(self, request, model_admin):
        return (
            ('complete', '✅ کامل'),
            ('incomplete', '❌ ناقص'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'complete':
            return queryset.exclude(Q(national_code__isnull=True) | Q(national_code=''))
        elif self.value() == 'incomplete':
            return queryset.filter(Q(national_code__isnull=True) | Q(national_code=''))
        return queryset


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
            'telegram_username', 'phone_number', 'national_code', 'is_approved',
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


class BankAccountInline(admin.TabularInline):
    """Inline admin for BankAccount in Profile admin."""
    model = BankAccount
    extra = 0
    verbose_name = 'حساب بانکی'
    verbose_name_plural = 'حساب‌های بانکی'
    fields = (
        'bank_name', 'account_holder_name', 'get_masked_account_number',
        'account_type', 'is_verified'
    )
    readonly_fields = ('get_masked_account_number',)
    
    def get_masked_account_number(self, obj):
        """Display masked account number."""
        if obj.pk:
            return obj.get_masked_account_number()
        return '-'
    get_masked_account_number.short_description = 'شماره حساب'


class ProfileInline(admin.StackedInline):
    """Inline admin for Profile in User admin."""
    model = Profile
    can_delete = False
    verbose_name = 'پروفایل'
    verbose_name_plural = 'پروفایل‌ها'
    fields = (
        'telegram_id', 'telegram_username', 'phone_number', 'national_code',
        'is_approved', 
        'rial_balance', 'frozen_rial_balance',
        'gold_balance_grams', 'frozen_gold_balance',
        'coin_balance', 'frozen_coin_balance',
        'dollar_balance', 'frozen_dollar_balance'
    )
    readonly_fields = ('telegram_id', 'telegram_username', 'phone_number')


class CustomUserAdmin(BaseUserAdmin):
    """Extended User admin with Profile inline."""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')


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
    
    inlines = [BankAccountInline]
    
    list_display = (
        'id',
        'approval_status_badge',
        'get_user_display',
        'national_code_display',
        'phone_number',
        'profile_completeness_badge',
        'telegram_username',
        'formatted_rial_balance',
        'formatted_gold_balance',
        'total_orders_count',
        'registration_time_badge',
        'quick_actions',
    )
    
    list_display_links = ('id', 'get_user_display')
    
    list_filter = (
        PendingApprovalFilter,
        ProfileCompletenessFilter,
        ('created_at', DateRangeFilter),
        ('updated_at', DateRangeFilter),
        ('rial_balance', NumericRangeFilter),
        ('gold_balance_grams', NumericRangeFilter),
        ('coin_balance', NumericRangeFilter),
        ('dollar_balance', NumericRangeFilter),
    )
    
    search_fields = (
        'user__first_name',
        'user__last_name',
        'user__username',
        'user__email',
        'phone_number',
        'national_code',
        'telegram_id',
        'telegram_username'
    )
    
    autocomplete_fields = ('user',)
    
    date_hierarchy = 'created_at'
    
    list_per_page = 50
    
    readonly_fields = (
        'telegram_id',
        'telegram_username',
        'phone_number',
        'created_at',
        'updated_at',
        'get_total_orders',
        'get_pending_orders',
        'registration_details_display',
    )
    
    fieldsets = (
        ('🔍 خلاصه ثبت‌نام', {
            'fields': ('registration_details_display',),
            'classes': ('wide',),
            'description': 'اطلاعات کامل ثبت‌نام کاربر برای بررسی و تأیید'
        }),
        ('👤 اطلاعات کاربر', {
            'fields': ('user',)
        }),
        ('📱 اطلاعات تلگرام', {
            'fields': ('telegram_id', 'telegram_username')
        }),
        ('📋 اطلاعات تماس و هویت', {
            'fields': ('phone_number', 'national_code'),
            'description': 'اطلاعات تماس و احراز هویت کاربر'
        }),
        ('✅ وضعیت حساب', {
            'fields': ('is_approved',),
            'description': '⚠️ با تأیید این گزینه، کاربر قادر به استفاده از ربات خواهد بود'
        }),
        ('موجودی‌ها', {
            'fields': (
                'rial_balance', 'frozen_rial_balance',
                'gold_balance_grams', 'frozen_gold_balance',
                'coin_balance', 'frozen_coin_balance',
                'dollar_balance', 'frozen_dollar_balance'
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
    
    actions = ['approve_users', 'disapprove_users', 'send_test_notification']
    
    def get_user_display(self, obj: Profile) -> str:
        """Display user's full name or username with enhanced styling."""
        full_name = obj.user.get_full_name()
        display_name = full_name if full_name else obj.user.username
        
        # Add new badge if registered in last 24 hours
        if obj.created_at:
            time_since = timezone.now() - obj.created_at
            if time_since.total_seconds() < 86400:  # 24 hours
                return format_html(
                    '{} <span style="background: #ff6b6b; color: white; padding: 2px 6px; border-radius: 8px; font-size: 10px; font-weight: bold;">جدید</span>',
                    display_name
                )
        return display_name
    get_user_display.short_description = 'نام کاربر'
    
    def national_code_display(self, obj: Profile) -> str:
        """Display national code with verification status."""
        if obj.national_code:
            return format_html(
                '<span style="font-family: monospace; background: #e8f5e9; padding: 3px 8px; border-radius: 4px; color: #2e7d32;">{}</span>',
                obj.national_code
            )
        return format_html(
            '<span style="color: #ff9800; font-weight: bold;">❌ ثبت نشده</span>'
        )
    national_code_display.short_description = 'کد ملی'
    national_code_display.admin_order_field = 'national_code'
    
    def profile_completeness_badge(self, obj: Profile) -> str:
        """Display profile completeness status."""
        has_national_code = bool(obj.national_code)
        has_name = bool(obj.user.first_name and obj.user.last_name)
        
        if has_national_code and has_name:
            return format_html(
                '<span style="background: #4caf50; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">✓ کامل</span>'
            )
        else:
            missing = []
            if not has_name:
                missing.append('نام')
            if not has_national_code:
                missing.append('کد ملی')
            return format_html(
                '<span style="background: #ff9800; color: white; padding: 4px 10px; border-radius: 12px; font-size: 11px;">⚠ ناقص: {}</span>',
                '، '.join(missing)
            )
    profile_completeness_badge.short_description = '📋 تکمیل پروفایل'
    
    def registration_time_badge(self, obj: Profile) -> str:
        """Display registration time with smart formatting."""
        if not obj.created_at:
            return '-'
        
        time_since = timezone.now() - obj.created_at
        
        if time_since.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(time_since.total_seconds() / 60)
            return format_html(
                '<span style="background: #f44336; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px; font-weight: bold;">🔥 {} دقیقه پیش</span>',
                minutes
            )
        elif time_since.total_seconds() < 86400:  # Less than 24 hours
            hours = int(time_since.total_seconds() / 3600)
            return format_html(
                '<span style="background: #ff9800; color: white; padding: 3px 8px; border-radius: 8px; font-size: 10px;">⏰ {} ساعت پیش</span>',
                hours
            )
        elif time_since.days < 7:
            return format_html(
                '<span style="color: #666;">{} روز پیش</span>',
                time_since.days
            )
        else:
            return obj.created_at.strftime('%Y/%m/%d')
    registration_time_badge.short_description = '📅 زمان ثبت‌نام'
    registration_time_badge.admin_order_field = 'created_at'
    
    def quick_actions(self, obj: Profile) -> str:
        """Quick action buttons."""
        if not obj.is_approved:
            approve_url = reverse('admin:users_profile_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background: #4caf50; color: white; padding: 5px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; display: inline-block;">✓ تأیید</a>',
                approve_url
            )
        else:
            detail_url = reverse('admin:users_profile_change', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background: #2196f3; color: white; padding: 5px 12px; border-radius: 4px; text-decoration: none; font-size: 12px; display: inline-block;">👁 مشاهده</a>',
                detail_url
            )
    quick_actions.short_description = 'عملیات'
    
    def registration_details_display(self, obj: Profile) -> str:
        """Display comprehensive registration details for review."""
        full_name = obj.user.get_full_name() or 'نامشخص'
        telegram_username = f"@{obj.telegram_username}" if obj.telegram_username else 'ندارد'
        national_code = obj.national_code or '❌ ثبت نشده'
        approval_status = '✅ تأیید شده' if obj.is_approved else '⏳ در انتظار تأیید'
        
        # Calculate time since registration
        time_since = timezone.now() - obj.created_at if obj.created_at else None
        if time_since:
            if time_since.total_seconds() < 3600:
                time_str = f"{int(time_since.total_seconds() / 60)} دقیقه پیش"
            elif time_since.total_seconds() < 86400:
                time_str = f"{int(time_since.total_seconds() / 3600)} ساعت پیش"
            else:
                time_str = f"{time_since.days} روز پیش"
        else:
            time_str = 'نامشخص'
        
        html = f'''
        <div style="background: #f5f5f5; padding: 20px; border-radius: 8px; border-left: 4px solid #2196f3;">
            <h3 style="margin-top: 0; color: #2196f3;">📝 اطلاعات ثبت‌نام کاربر</h3>
            
            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px; font-weight: bold; width: 200px;">👤 نام و نام خانوادگی:</td>
                    <td style="padding: 10px;"><strong style="font-size: 16px; color: #333;">{full_name}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd; background: #fafafa;">
                    <td style="padding: 10px; font-weight: bold;">🆔 کد ملی:</td>
                    <td style="padding: 10px;"><strong style="font-size: 16px; font-family: monospace; color: #1976d2;">{national_code}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px; font-weight: bold;">📱 شماره تماس:</td>
                    <td style="padding: 10px;"><strong style="font-size: 14px; direction: ltr; text-align: right;">{obj.phone_number}</strong></td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd; background: #fafafa;">
                    <td style="padding: 10px; font-weight: bold;">✈️ نام کاربری تلگرام:</td>
                    <td style="padding: 10px;">{telegram_username}</td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd;">
                    <td style="padding: 10px; font-weight: bold;">🔢 شناسه تلگرام:</td>
                    <td style="padding: 10px;"><code>{obj.telegram_id}</code></td>
                </tr>
                <tr style="border-bottom: 1px solid #ddd; background: #fafafa;">
                    <td style="padding: 10px; font-weight: bold;">⏰ زمان ثبت‌نام:</td>
                    <td style="padding: 10px;">{obj.created_at.strftime('%Y/%m/%d - %H:%M:%S')} <span style="color: #666;">({time_str})</span></td>
                </tr>
                <tr>
                    <td style="padding: 10px; font-weight: bold;">✅ وضعیت:</td>
                    <td style="padding: 10px;"><strong style="color: {'#4caf50' if obj.is_approved else '#ff9800'};">{approval_status}</strong></td>
                </tr>
            </table>
            
            <div style="margin-top: 20px; padding: 15px; background: {'#e8f5e9' if obj.is_approved else '#fff3e0'}; border-radius: 4px;">
                <strong style="color: {'#2e7d32' if obj.is_approved else '#e65100'};">
                    {'✅ این کاربر تأیید شده و می‌تواند از ربات استفاده کند.' if obj.is_approved else '⚠️ این کاربر هنوز تأیید نشده است. لطفاً اطلاعات را بررسی کرده و در صورت صحیح بودن، گزینه "تأیید شده" را فعال کنید.'}
                </strong>
            </div>
        </div>
        '''
        return mark_safe(html)
    registration_details_display.short_description = 'جزئیات ثبت‌نام'
    
    def user_tier_badge(self, obj: Profile) -> str:
        """Display user tier badge."""
        return obj.get_tier_badge_html()
    user_tier_badge.short_description = '🏆 سطح کاربر'
    
    def total_trade_volume(self, obj: Profile) -> str:
        """Display total trade volume."""
        volume = obj.get_total_trade_volume()
        # Convert Decimal to float for formatting
        volume_millions = float(volume) / 1000000
        # Format the number first, then pass to format_html
        formatted_volume = f"{volume_millions:,.0f}"
        return format_html(
            '<span style="font-weight: bold; color: #007bff;">{} میلیون</span>',
            formatted_volume
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
        url = reverse('admin:trading_order_changelist') + f'?profile__id__exact={obj.pk}'
        return format_html(
            '<a href="{}" style="color: #007bff; font-weight: bold;">{} سفارش</a>',
            url, count
        )
    total_orders_count.short_description = 'تعداد سفارشات'
    
    def view_user_details(self, obj: Profile) -> str:
        """Quick view link."""
        url = reverse('admin:users_profile_change', args=[obj.pk])
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
    
    def formatted_coin_balance(self, obj: Profile) -> str:
        """Format coin balance."""
        return f"{obj.coin_balance:,.0f} سکه"
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
        """Bulk action to approve selected users with automatic notification."""
        count = 0
        notified = 0
        
        for profile in queryset.filter(is_approved=False):
            profile.is_approved = True
            profile.save(update_fields=['is_approved'])
            count += 1
            
            # Notification is automatically sent via signal
            # We just log success here
            try:
                # Small delay to allow signal to process
                import time
                time.sleep(0.1)
                notified += 1
            except Exception as e:
                logger.warning(f"Issue during approval of user {profile.telegram_id}: {str(e)}")
        
        self.message_user(
            request,
            f'✅ {count} کاربر با موفقیت تأیید شدند. اطلاع‌رسانی به کاربران ارسال شد.',
            level='success'
        )
    approve_users.short_description = '✅ تأیید کاربران انتخاب شده'
    
    def disapprove_users(self, request, queryset):
        """Bulk action to disapprove selected users."""
        updated = queryset.update(is_approved=False)
        self.message_user(
            request,
            f'⚠️ تأیید {updated} کاربر لغو شد.',
            level='warning'
        )
    disapprove_users.short_description = '❌ لغو تأیید کاربران انتخاب شده'
    
    def send_test_notification(self, request, queryset):
        """Send a test notification to selected users."""
        count = 0
        failed = 0
        
        for profile in queryset:
            try:
                from bot.notification_service import TelegramNotificationService
                message = (
                    "🔔 *پیام آزمایشی*\n\n"
                    "این یک پیام آزمایشی از پنل مدیریت است.\n"
                    "ربات به درستی کار می‌کند! ✅"
                )
                success = TelegramNotificationService.send_message(
                    telegram_id=profile.telegram_id,
                    message=message
                )
                if success:
                    count += 1
                else:
                    failed += 1
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send test notification to {profile.telegram_id}: {str(e)}")
        
        if failed > 0:
            self.message_user(
                request,
                f'📤 پیام به {count} کاربر ارسال شد. {failed} پیام ناموفق بود.',
                level='warning'
            )
        else:
            self.message_user(
                request,
                f'✅ پیام آزمایشی به {count} کاربر با موفقیت ارسال شد.',
                level='success'
            )
    send_test_notification.short_description = '📤 ارسال پیام آزمایشی'
    
    def changelist_view(self, request, extra_context=None):
        """Enhanced changelist view with statistics."""
        extra_context = extra_context or {}
        
        # Calculate statistics
        total_users = Profile.objects.count()
        pending_approval = Profile.objects.filter(is_approved=False).count()
        approved_users = Profile.objects.filter(is_approved=True).count()
        incomplete_profiles = Profile.objects.filter(
            Q(national_code__isnull=True) | Q(national_code='')
        ).count()
        
        # New registrations (last 24 hours)
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        new_registrations = Profile.objects.filter(created_at__gte=last_24h).count()
        
        extra_context['total_users'] = total_users
        extra_context['pending_approval'] = pending_approval
        extra_context['approved_users'] = approved_users
        extra_context['incomplete_profiles'] = incomplete_profiles
        extra_context['new_registrations'] = new_registrations
        
        return super().changelist_view(request, extra_context=extra_context)


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
