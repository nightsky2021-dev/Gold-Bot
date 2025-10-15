"""
Admin configuration for users app
"""
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Profile


class ProfileInline(admin.StackedInline):
    """
    Inline admin for Profile to show in User admin
    """
    model = Profile
    can_delete = False
    verbose_name_plural = 'پروفایل'
    fk_name = 'user'
    fields = (
        'telegram_id',
        'telegram_username',
        'phone_number',
        'is_approved',
        'rial_balance',
        'gold_balance_grams',
        'created_at',
        'updated_at'
    )
    readonly_fields = ('created_at', 'updated_at')


class CustomUserAdmin(BaseUserAdmin):
    """
    Extended User admin with Profile inline
    """
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone_number', 'get_is_approved')

    def get_phone_number(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.phone_number
        return '-'
    get_phone_number.short_description = 'شماره تماس'

    def get_is_approved(self, obj):
        if hasattr(obj, 'profile'):
            return obj.profile.is_approved
        return False
    get_is_approved.short_description = 'تایید شده'
    get_is_approved.boolean = True


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for Profile model
    """
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
        'user__username',
        'phone_number',
        'telegram_id',
        'telegram_username'
    )
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = []  # No autocomplete needed for Profile
    
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
        ('وضعیت', {
            'fields': ('is_approved',)
        }),
        ('موجودی‌ها', {
            'fields': ('rial_balance', 'gold_balance_grams')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('user')


# Unregister the default User admin and register our custom one
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
