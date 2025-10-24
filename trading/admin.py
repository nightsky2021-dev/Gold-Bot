"""
تنظیمات پنل ادمین برای مدیریت محصولات و سفارشات
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """پنل مدیریت محصولات"""
    list_display = (
        'name',
        'buy_price',
        'sell_price',
        'is_active',
        'updated_at'
    )
    list_editable = ('buy_price', 'sell_price', 'is_active')
    readonly_fields = ('updated_at', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'updated_at')
    search_fields = ('name',)
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('name', 'slug', 'is_active')
        }),
        ('قیمت‌گذاری', {
            'fields': ('buy_price', 'sell_price'),
            'description': 'قیمت‌ها به ریال برای هر گرم می‌باشد'
        }),
        ('زمان', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )
    
    def formatted_buy_price(self, obj):
        """نمایش قیمت خرید با فرمت"""
        return f"{obj.buy_price:,} ریال"
    formatted_buy_price.short_description = 'قیمت خرید'
    
    def formatted_sell_price(self, obj):
        """نمایش قیمت فروش با فرمت"""
        return f"{obj.sell_price:,} ریال"
    formatted_sell_price.short_description = 'قیمت فروش'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """پنل مدیریت سفارشات"""
    list_display = (
        'id',
        'get_user_info',
        'product',
        'order_type_badge',
        'status_badge',
        'quantity_grams',
        'formatted_total_amount',
        'created_at'
    )
    list_filter = ('status', 'order_type', 'product', 'created_at')
    search_fields = (
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'id'
    )
    readonly_fields = ('created_at', 'total_amount')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('profile', 'product', 'order_type', 'status')
        }),
        ('جزئیات مالی', {
            'fields': ('quantity_grams', 'price_per_gram', 'total_amount')
        }),
        ('یادداشت‌ها', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('زمان', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'mark_as_cancelled']
    
    def get_user_info(self, obj):
        """نمایش اطلاعات کاربر"""
        return f"{obj.profile.user.get_full_name()} ({obj.profile.phone_number})"
    get_user_info.short_description = 'کاربر'
    
    def order_type_badge(self, obj):
        """نمایش نوع سفارش با رنگ"""
        colors = {
            'BUY': '#28a745',
            'SELL': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.order_type, '#6c757d'),
            obj.get_order_type_display()
        )
    order_type_badge.short_description = 'نوع سفارش'
    
    def status_badge(self, obj):
        """نمایش وضعیت با رنگ"""
        colors = {
            'PENDING': '#ffc107',
            'COMPLETED': '#28a745',
            'CANCELLED': '#dc3545'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#6c757d'),
            obj.get_status_display()
        )
    status_badge.short_description = 'وضعیت'
    
    def formatted_total_amount(self, obj):
        """نمایش مبلغ کل با فرمت"""
        return f"{obj.total_amount:,} ریال"
    formatted_total_amount.short_description = 'مبلغ کل'
    
    def mark_as_completed(self, request, queryset):
        """تغییر وضعیت به تکمیل شده"""
        updated = queryset.update(status='COMPLETED')
        self.message_user(request, f'{updated} سفارش به حالت تکمیل شده تغییر یافت.')
    mark_as_completed.short_description = 'تغییر وضعیت به تکمیل شده'
    
    def mark_as_cancelled(self, request, queryset):
        """تغییر وضعیت به لغو شده"""
        updated = queryset.update(status='CANCELLED')
        self.message_user(request, f'{updated} سفارش لغو شد.')
    mark_as_cancelled.short_description = 'لغو سفارش'

