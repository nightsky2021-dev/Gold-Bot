"""
Admin configuration for trading app
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model
    """
    list_display = (
        'name',
        'buy_price',
        'sell_price',
        'display_spread',
        'is_active',
        'updated_at'
    )
    list_editable = ('buy_price', 'sell_price', 'is_active')
    readonly_fields = ('updated_at', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active', 'updated_at')
    search_fields = ('name', 'slug')
    autocomplete_fields = []  # No autocomplete needed for Product
    
    fieldsets = (
        ('اطلاعات محصول', {
            'fields': ('name', 'slug')
        }),
        ('قیمت‌گذاری', {
            'fields': ('buy_price', 'sell_price'),
            'description': 'قیمت خرید: قیمتی که شما از مشتری می‌خرید | قیمت فروش: قیمتی که شما به مشتری می‌فروشید'
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('آخرین به‌روزرسانی', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def display_buy_price(self, obj):
        return f"{obj.get_formatted_buy_price()} ریال"
    display_buy_price.short_description = 'قیمت خرید'

    def display_sell_price(self, obj):
        return f"{obj.get_formatted_sell_price()} ریال"
    display_sell_price.short_description = 'قیمت فروش'

    def display_spread(self, obj):
        spread = obj.sell_price - obj.buy_price
        spread_percent = (spread / obj.buy_price * 100) if obj.buy_price > 0 else 0
        return f"{int(spread):,} ریال ({spread_percent:.2f}%)"
    display_spread.short_description = 'اسپرد (تفاوت)'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin interface for Order model
    """
    list_display = (
        'id',
        'display_user',
        'product',
        'display_order_type',
        'display_quantity',
        'display_total_amount',
        'display_status',
        'created_at'
    )
    list_filter = ('status', 'order_type', 'product', 'created_at')
    search_fields = (
        'profile__user__first_name',
        'profile__user__last_name',
        'profile__phone_number',
        'id'
    )
    raw_id_fields = ('profile', 'product')  # Use raw_id instead of autocomplete
    readonly_fields = ('created_at', 'total_amount', 'price_per_gram')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('profile', 'product', 'order_type')
        }),
        ('جزئیات مالی', {
            'fields': ('quantity_grams', 'price_per_gram', 'total_amount')
        }),
        ('وضعیت', {
            'fields': ('status',)
        }),
        ('تاریخ', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_orders', 'cancel_orders']

    def get_queryset(self, request):
        """
        Optimize queryset with select_related
        """
        queryset = super().get_queryset(request)
        return queryset.select_related('profile__user', 'product')

    def display_user(self, obj):
        user_name = obj.profile.user.get_full_name() or obj.profile.user.username
        return f"{user_name} ({obj.profile.phone_number})"
    display_user.short_description = 'کاربر'

    def display_order_type(self, obj):
        colors = {
            'BUY': 'green',
            'SELL': 'orange'
        }
        color = colors.get(obj.order_type, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_order_type_display()
        )
    display_order_type.short_description = 'نوع سفارش'

    def display_quantity(self, obj):
        return f"{obj.get_formatted_quantity()} گرم"
    display_quantity.short_description = 'مقدار'

    def display_total_amount(self, obj):
        return f"{obj.get_formatted_total_amount()} ریال"
    display_total_amount.short_description = 'مبلغ کل'

    def display_status(self, obj):
        colors = {
            'PENDING': 'orange',
            'COMPLETED': 'green',
            'CANCELLED': 'red'
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    display_status.short_description = 'وضعیت'

    def approve_orders(self, request, queryset):
        """
        Action to approve selected orders
        """
        from trading.services import process_order
        
        count = 0
        for order in queryset.filter(status=Order.OrderStatus.PENDING):
            try:
                process_order(order)
                count += 1
            except Exception as e:
                self.message_user(request, f"خطا در پردازش سفارش {order.id}: {str(e)}", level='ERROR')
        
        self.message_user(request, f"{count} سفارش با موفقیت تایید و پردازش شد.")
    approve_orders.short_description = "تایید و پردازش سفارشات انتخاب شده"

    def cancel_orders(self, request, queryset):
        """
        Action to cancel selected orders
        """
        updated = queryset.filter(status=Order.OrderStatus.PENDING).update(
            status=Order.OrderStatus.CANCELLED
        )
        self.message_user(request, f"{updated} سفارش لغو شد.")
    cancel_orders.short_description = "لغو سفارشات انتخاب شده"


# Customize admin site headers
admin.site.site_header = "پنل مدیریت سیستم معاملات طلا"
admin.site.site_title = "مدیریت طلا"
admin.site.index_title = "خوش آمدید به پنل مدیریت"
