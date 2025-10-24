"""
تنظیمات پنل ادمین برای مدیریت کاربران
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


class ProfileInline(admin.StackedInline):
    """نمایش پروفایل در صفحه ویرایش User"""
    model = Profile
    can_delete = False
    verbose_name = 'پروفایل'
    verbose_name_plural = 'پروفایل'
    readonly_fields = ('created_at', 'updated_at')
    fields = (
        'telegram_id', 'telegram_username', 'phone_number',
        'is_approved', 'rial_balance', 'gold_balance_grams',
        'created_at', 'updated_at'
    )


# Unregister the default User admin
admin.site.unregister(User)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """ادمین سفارشی برای User با نمایش پروفایل"""
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_is_approved')
    
    def get_is_approved(self, obj):
        """نمایش وضعیت تایید کاربر"""
        if hasattr(obj, 'profile'):
            return obj.profile.is_approved
        return False
    get_is_approved.short_description = 'تایید شده'
    get_is_approved.boolean = True


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """پنل مدیریت پروفایل‌ها"""
    list_display = (
        '__str__',
        'phone_number',
        'telegram_username',
        'is_approved',
        'rial_balance',
        'gold_balance_grams',
        'created_at'
    )
    list_filter = ('is_approved', 'created_at')
    search_fields = (
        'user__first_name',
        'user__last_name',
        'phone_number',
        'telegram_id',
        'telegram_username'
    )
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
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
        ('وضعیت و تایید', {
            'fields': ('is_approved',)
        }),
        ('موجودی‌ها', {
            'fields': ('rial_balance', 'gold_balance_grams'),
            'classes': ('collapse',)
        }),
        ('زمان‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

