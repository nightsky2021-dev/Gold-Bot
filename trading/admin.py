"""
Admin configuration for trading app.

This module contains Django admin configurations for Product and Order models.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Product, Order
from .services import OrderService


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model.
    
    Provides comprehensive product management with filtering and search capabilities.
    """
    
    list_display = (
        'name',
        'product_code',
        'formatted_buy_price',
        'formatted_sell_price',
        'is_active',
        'updated_at',
    )
    
    list_filter = (
        'is_active',
        'product_code',
        'updated_at',
    )
    
    search_fields = (
        'name',
        'product_code',
    )
    
    readonly_fields = (
        'slug',
        'updated_at',
    )
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('name', 'product_code', 'slug')
        }),
        ('قیمت‌گذاری', {
            'fields': ('buy_price', 'sell_price')
        }),
        ('وضعیت', {
            'fields': ('is_active', 'updated_at')
        }),
    )
    
    ordering = ('name',)
    
    actions = ['activate_products', 'deactivate_products']
    
    def formatted_buy_price(self, obj):
        """Format buy price with currency."""
        return f"{obj.buy_price:,.0f} ریال"
    formatted_buy_price.short_description = 'قیمت خرید'
    
    def formatted_sell_price(self, obj):
        """Format sell price with currency."""
        return f"{obj.sell_price:,.0f} ریال"
    formatted_sell_price.short_description = 'قیمت فروش'
    
    def activate_products(self, request, queryset):
        """Activate selected products."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} محصول فعال شد.'
        )
    activate_products.short_description = 'فعال کردن محصولات انتخاب شده'
    
    def deactivate_products(self, request, queryset):
        """Deactivate selected products."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} محصول غیرفعال شد.'
        )
    deactivate_products.short_description = 'غیرفعال کردن محصولات انتخاب شده'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model.
    
    Provides comprehensive order management with filtering and bulk actions.
    """
    
    list_display = (
        'id',
        'get_user_display',
        'get_product_display',
        'order_type_display',
        'formatted_quantity',
        'formatted_price',
        'formatted_total',
        'status_display',
        'created_at',
    )
    
    list_filter = (
        'order_type',
        'status',
        'created_at',
        'product',
    )
    
    search_fields = (
        'id',
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'product__name',
    )
    
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('profile', 'product', 'order_type', 'status')
        }),
        ('جزئیات معامله', {
            'fields': ('quantity_grams', 'price_per_gram', 'total_amount')
        }),
        ('یادداشت‌ها', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('زمان‌بندی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ('-created_at',)
    
    actions = ['complete_orders', 'cancel_orders']
    
    def get_user_display(self, obj):
        """Display user information."""
        return f"{obj.profile.user.get_full_name()} ({obj.profile.phone_number})"
    get_user_display.short_description = 'کاربر'
    
    def get_product_display(self, obj):
        """Display product information."""
        return obj.product.name
    get_product_display.short_description = 'محصول'
    
    def order_type_display(self, obj):
        """Display order type with icon."""
        icons = {
            'BUY': '💰',
            'SELL': '🛒',
        }
        return f"{icons.get(obj.order_type, '❓')} {obj.get_order_type_display()}"
    order_type_display.short_description = 'نوع سفارش'
    
    def formatted_quantity(self, obj):
        """Format quantity with unit."""
        return f"{obj.quantity_grams} گرم"
    formatted_quantity.short_description = 'مقدار'
    
    def formatted_price(self, obj):
        """Format price per gram."""
        return f"{obj.price_per_gram:,.0f} ریال"
    formatted_price.short_description = 'قیمت هر گرم'
    
    def formatted_total(self, obj):
        """Format total amount."""
        return f"{obj.total_amount:,.0f} ریال"
    formatted_total.short_description = 'مجموع'
    
    def status_display(self, obj):
        """Display status with color coding."""
        colors = {
            'PENDING': '🟡',
            'COMPLETED': '🟢',
            'CANCELLED': '🔴',
        }
        return f"{colors.get(obj.status, '❓')} {obj.get_status_display()}"
    status_display.short_description = 'وضعیت'
    
    def complete_orders(self, request, queryset):
        """Complete selected orders."""
        completed_count = 0
        
        for order in queryset.filter(status='PENDING'):
            try:
                OrderService.complete_order(order.id)
                completed_count += 1
            except Exception as e:
                order.notes = f"خطا در تکمیل: {str(e)}"
                order.save()
        
        self.message_user(
            request,
            f'{completed_count} سفارش تکمیل شد.'
        )
    complete_orders.short_description = 'تکمیل سفارشات انتخاب شده'
    
    def cancel_orders(self, request, queryset):
        """Cancel selected orders."""
        updated = queryset.filter(status='PENDING').update(status='CANCELLED')
        self.message_user(
            request,
            f'{updated} سفارش لغو شد.'
        )
    cancel_orders.short_description = 'لغو سفارشات انتخاب شده'


# Import extended admin registrations
from .admin_extensions import TransactionAdmin, WithdrawRequestAdmin