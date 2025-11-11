"""
Admin interface for Product model.

Manages gold products, prices, margins, and trading configurations.
"""

from typing import Any
from datetime import timedelta
from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Sum, Q, Count, Subquery, OuterRef
from django.http import HttpRequest
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.shortcuts import render
from django import forms

from rangefilter.filters import DateRangeFilter, NumericRangeFilter  # type: ignore[import-untyped]
from import_export.admin import ImportExportModelAdmin  # type: ignore[import-untyped]
from django.contrib.admin import SimpleListFilter, helpers as admin_helpers

from ..models import Product, Order, PriceHistory
from ..utils import (
    to_persian_numbers,
    format_price_persian,
    format_percentage_change,
    get_trend_color
)
from .resources import ProductResource
from .mixins import FormattingMixin


class BulkMarginUpdateForm(forms.Form):
    """Form for bulk updating product margins."""
    
    buy_margin = forms.DecimalField(
        label='مارجین خرید جدید (ریال)',
        required=False,
        min_value=Decimal('0'),
        max_digits=12,
        decimal_places=0,
        help_text='در صورت خالی گذاشتن، تغییری اعمال نمی‌شود'
    )
    
    sell_margin = forms.DecimalField(
        label='مارجین فروش جدید (ریال)',
        required=False,
        min_value=Decimal('0'),
        max_digits=12,
        decimal_places=0,
        help_text='در صورت خالی گذاشتن، تغییری اعمال نمی‌شود'
    )
    
    update_prices = forms.BooleanField(
        label='آپدیت خودکار قیمت‌ها بعد از تغییر',
        required=False,
        initial=True,
        help_text='در صورت فعال بودن، قیمت‌ها با مارجین جدید محاسبه می‌شوند'
    )


class ProductCategoryFilter(SimpleListFilter):
    """Custom filter for product categories."""
    
    title = 'دسته‌بندی محصول'
    parameter_name = 'category'
    
    def lookups(self, request, model_admin):
        """Return filter options."""
        return (
            ('currency', '💵 ارزها'),
            ('coin', '🪙 سکه‌ها'),
            ('gold', '✨ طلا'),
        )
    
    def queryset(self, request, queryset):
        """Filter queryset based on selected category."""
        if self.value() == 'currency':
            return queryset.filter(
                product_code__in=[
                    'dollar_usa', 'euro', 'pound_uk', 
                    'yuan_china', 'lira_turkey', 'dirham_uae'
                ]
            )
        elif self.value() == 'coin':
            return queryset.filter(
                product_code__in=['coin_full', 'coin_half', 'coin_quarter']
            )
        elif self.value() == 'gold':
            return queryset.filter(
                product_code__in=['gold_abshodeh', 'gold']
            )
        return queryset


class PriceRangeFilter(SimpleListFilter):
    """Custom filter for price ranges."""
    
    title = 'محدوده قیمت فروش'
    parameter_name = 'price_range'
    
    def lookups(self, request, model_admin):
        """Return filter options."""
        return (
            ('low', 'کمتر از ۱ میلیون'),
            ('medium', '۱ تا ۱۰ میلیون'),
            ('high', '۱۰ تا ۱۰۰ میلیون'),
            ('very_high', 'بیشتر از ۱۰۰ میلیون'),
        )
    
    def queryset(self, request, queryset):
        """Filter queryset based on selected price range."""
        if self.value() == 'low':
            return queryset.filter(sell_price__lt=1000000)
        elif self.value() == 'medium':
            return queryset.filter(sell_price__gte=1000000, sell_price__lt=10000000)
        elif self.value() == 'high':
            return queryset.filter(sell_price__gte=10000000, sell_price__lt=100000000)
        elif self.value() == 'very_high':
            return queryset.filter(sell_price__gte=100000000)
        return queryset


class ProductAdminForm(forms.ModelForm):
    """Custom form for Product admin with validation."""
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def clean(self):
        """Validate that calculated prices won't be negative."""
        cleaned_data = super().clean()
        
        # Ensure cleaned_data is not None (can happen if parent validation fails)
        if not cleaned_data:
            return cleaned_data
        
        buy_margin = cleaned_data.get('buy_margin')
        sell_margin = cleaned_data.get('sell_margin')
        weight_grams = cleaned_data.get('weight_grams')
        base_price_api = cleaned_data.get('base_price_api')
        
        if all([buy_margin, weight_grams, base_price_api]):
            # Calculate what the buy price would be
            # Type checker: these are guaranteed to be non-None by the all() check
            assert base_price_api is not None and weight_grams is not None
            adjusted_base = base_price_api * weight_grams
            calculated_buy_price = adjusted_base - buy_margin
            
            if calculated_buy_price < 0:
                raise forms.ValidationError(
                    f'⚠️ خطا: مارجین خرید ({buy_margin:,.0f} ریال) بیش از حد بزرگ است! '
                    f'قیمت خرید محاسبه شده منفی می‌شود ({calculated_buy_price:,.0f} ریال). '
                    f'قیمت پایه تعدیل شده: {adjusted_base:,.0f} ریال. '
                    f'حداکثر مارجین خرید مجاز: {adjusted_base:,.0f} ریال'
                )
        
        if all([sell_margin, weight_grams, base_price_api]):
            # Calculate what the sell price would be
            # Type checker: these are guaranteed to be non-None by the all() check
            assert base_price_api is not None and weight_grams is not None
            adjusted_base = base_price_api * weight_grams
            calculated_sell_price = adjusted_base + sell_margin
            
            # Sell price should always be positive, but let's check for sanity
            if calculated_sell_price < 0:
                raise forms.ValidationError(
                    f'⚠️ خطا: قیمت فروش محاسبه شده منفی است ({calculated_sell_price:,.0f} ریال)!'
                )
        
        # Validate that buy and sell margins make business sense
        if buy_margin and sell_margin:
            total_margin = buy_margin + sell_margin
            
            if weight_grams and base_price_api:
                adjusted_base = base_price_api * weight_grams
                margin_percentage = (total_margin / adjusted_base * 100) if adjusted_base > 0 else 0
                
                # Warning if margin is too high (>20% of base price)
                if margin_percentage > 20:
                    self.add_error(
                        None,
                        forms.ValidationError(
                            f'⚠️ هشدار: مارجین کل ({total_margin:,.0f} ریال) معادل {margin_percentage:.1f}% قیمت پایه است. '
                            f'این مارجین بسیار بالا به نظر می‌رسد. لطفاً بررسی کنید.',
                            code='high_margin'
                        )
                    )
        
        return cleaned_data
    
    def clean_buy_margin(self):
        """Validate buy margin."""
        buy_margin = self.cleaned_data.get('buy_margin')
        
        if buy_margin and buy_margin < 0:
            raise forms.ValidationError('مارجین خرید نمی‌تواند منفی باشد.')
        
        return buy_margin
    
    def clean_sell_margin(self):
        """Validate sell margin."""
        sell_margin = self.cleaned_data.get('sell_margin')
        
        if sell_margin and sell_margin < 0:
            raise forms.ValidationError('مارجین فروش نمی‌تواند منفی باشد.')
        
        return sell_margin


class ProductAdmin(ImportExportModelAdmin, FormattingMixin):
    """
    Admin interface for Product model.
    
    Features:
    - Price calculation preview
    - Margin configuration
    - Trading statistics
    - Import/export functionality
    - Price trend analysis
    """
    
    form = ProductAdminForm
    resource_class = ProductResource
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Check if user has permission to change products."""
        # Allow view access for all staff
        if not getattr(request.user, 'is_staff', False):
            return False
        
        # Only superusers can change margin-related fields
        # Regular staff can view and change other fields
        return True
    
    def get_readonly_fields(self, request: HttpRequest, obj: Any = None):
        """Make margin fields read-only for non-superusers."""
        readonly = list(super().get_readonly_fields(request, obj))
        
        # If not superuser, make margin fields read-only
        if not getattr(request.user, 'is_superuser', False):
            readonly.extend(['buy_margin', 'sell_margin', 'weight_grams'])
        
        return readonly
    
    def get_queryset(self, request: HttpRequest):
        """
        Override queryset to optimize with select/prefetch related.
        
        This prevents N+1 query issues when displaying list view.
        """
        qs = super().get_queryset(request)
        
        # Annotate with order count to avoid N+1 queries
        qs = qs.annotate(
            orders_count=Count('orders')
        )
        
        # Annotate with 30-day volume to avoid N+1 queries
        time_30d_ago = timezone.now() - timedelta(days=30)
        qs = qs.annotate(
            volume_30d=Sum(
                'orders__total_amount',
                filter=Q(
                    orders__status=Order.OrderStatus.COMPLETED,
                    orders__created_at__gte=time_30d_ago
                )
            )
        )
        
        # Prefetch price history for trend calculations
        qs = qs.prefetch_related('price_history')
        
        return qs
    
    list_display = (
        'product_category_badge',
        'name',
        'product_code_display',
        'margin_display',
        'calculated_buy_price',
        'calculated_sell_price',
        'price_trend_24h',
        'base_api_price_display',
        'is_active',
        'order_count',
        'total_volume_30d',
        'updated_at'
    )
    
    list_editable = ('is_active',)
    
    list_filter = (
        'is_active',
        ProductCategoryFilter,
        PriceRangeFilter,
        'product_code',
        ('updated_at', DateRangeFilter),
        ('buy_price', NumericRangeFilter),
        ('sell_price', NumericRangeFilter),
    )
    
    search_fields = ('name', 'slug', 'product_code')
    
    readonly_fields = (
        'slug',
        'buy_price',
        'sell_price',
        'base_price_api',
        'calculated_price_preview',
        'updated_at',
        'created_at'
    )
    
    fieldsets = (
        ('📋 اطلاعات محصول', {
            'fields': ('product_code', 'name', 'slug'),
            'description': mark_safe(
                '<div style="background: #e3f2fd; padding: 10px; border-radius: 4px; margin-bottom: 10px; border-left: 3px solid #2196f3;">'
                '<strong>💡 نکته:</strong> کد محصول باید با API یکپارچه باشد. '
                'نام محصول در ربات و پنل نمایش داده می‌شود.'
                '</div>'
            )
        }),
        ('✏️ تنظیمات محاسبه قیمت (قابل ویرایش)', {
            'fields': ('buy_margin', 'sell_margin', 'weight_grams'),
            'description': mark_safe(
                '<div style="background: #e8f5e9; padding: 12px; border-radius: 6px; border-left: 3px solid #4caf50; margin: 10px 0;">'
                '<strong>✏️ این فیلدها قابل ویرایش هستند</strong> - '
                'با تغییر مقادیر، قیمت‌های نهایی خودکار محاسبه می‌شوند.'
                '</div>'
                
                '<details style="margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 4px;">'
                '<summary style="cursor: pointer; font-weight: bold; color: #1976d2;">📖 راهنمای تنظیم مارجین‌ها (کلیک کنید)</summary>'
                '<div style="padding: 10px 0;">'
                
                '<div style="background: white; padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid #2e7d32;">'
                '<strong>💵 ارزها (دلار، یورو، پوند، لیر، یوان، درهم):</strong><br>'
                '• فروش: به ازای هر <strong>واحد</strong> (1 دلار، 1 یورو، ...)<br>'
                '• مارجین پیشنهادی: ±1% از قیمت (مثلاً ±7,500 ریال)<br>'
                '• ضریب واحد: <strong style="color: #2e7d32;">1</strong>'
                '</div>'
                
                '<div style="background: white; padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid #ff6f00;">'
                '<strong>🪙 سکه‌ها (تمام، نیم، ربع):</strong><br>'
                '• فروش: به ازای هر <strong>عدد سکه</strong> (نه وزن!)<br>'
                '• API قیمت هر سکه را جداگانه برمی‌گرداند<br>'
                '• مارجین پیشنهادی: ±4,500,000 ریال<br>'
                '• ضریب واحد: <strong style="color: #ff6f00;">1</strong><br>'
                '<small style="color: #d32f2f; font-weight: bold;">⚠️ هشدار: سکه‌ها واحدی هستند! وزن فیزیکی (8.133g) ربطی به قیمت‌گذاری ندارد.</small>'
                '</div>'
                
                '<div style="background: white; padding: 10px; margin: 8px 0; border-radius: 4px; border-left: 3px solid #c2185b;">'
                '<strong>✨ طلای آبشده (18 عیار):</strong><br>'
                '• فروش: به ازای هر <strong>گرم</strong><br>'
                '• مارجین پیشنهادی: ±300,000 ریال<br>'
                '• ضریب واحد: <strong style="color: #c2185b;">1</strong>'
                '</div>'
                
                '<div style="background: #f1f8e9; padding: 10px; margin: 8px 0; border-radius: 4px; font-size: 13px;">'
                '<strong>📐 فرمول محاسبه قیمت:</strong><br>'
                '• قیمت خرید = (قیمت API × ضریب واحد) - مارجین خرید<br>'
                '• قیمت فروش = (قیمت API × ضریب واحد) + مارجین فروش<br>'
                '<strong style="color: #2e7d32;">• برای همه محصولات: ضریب واحد = 1</strong>'
                '</div>'
                
                '<div style="background: #ffebee; padding: 8px; margin: 8px 0; border-radius: 4px; font-size: 12px; color: #c62828;">'
                '<strong>⚡ مهم:</strong> بعد از تغییر: <code>python manage.py update_prices --show-details</code>'
                '</div>'
                
                '</div>'
                '</details>'
            )
        }),
        ('📊 قیمت‌های محاسبه شده (فقط‌خواندنی)', {
            'fields': ('calculated_price_preview', 'base_price_api', 'buy_price', 'sell_price'),
            'description': mark_safe(
                '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; border-left: 3px solid #9e9e9e;">'
                '<strong>ℹ️</strong> این قیمت‌ها از API و مارجین‌های بالا محاسبه می‌شوند (غیرقابل ویرایش).'
                '</div>'
            )
        }),
        ('🎛️ وضعیت', {
            'fields': ('is_active',),
            'description': mark_safe(
                '<div style="background: #e8f5e9; padding: 8px; border-radius: 4px; font-size: 13px;">'
                '<strong>✅</strong> فقط محصولات فعال در ربات و پنل نمایش داده می‌شوند.'
                '</div>'
            )
        }),
        ('📅 تاریخچه', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def order_count(self, obj: Product) -> str:
        """Display total order count for this product."""
        # Use annotated value instead of querying
        count = getattr(obj, 'orders_count', 0)
        return self.format_info_badge(f'{count} سفارش')
    
    order_count.short_description = 'تعداد سفارشات'  # type: ignore
    
    def margin_display(self, obj: Product) -> str:
        """Display margin configuration in a clear format."""
        buy_margin_fmt = f"{float(obj.buy_margin):,.0f}"
        sell_margin_fmt = f"{float(obj.sell_margin):,.0f}"
        total_margin_fmt = f"{float(obj.get_total_margin()):,.0f}"
        
        return format_html(
            '<div style="line-height: 1.8;">'
            '🟢 خرید: <strong>{}</strong><br>'
            '🔴 فروش: <strong>{}</strong><br>'
            '💰 مجموع: <strong>{}</strong>'
            '</div>',
            buy_margin_fmt,
            sell_margin_fmt,
            total_margin_fmt
        )
    
    margin_display.short_description = 'مارجین‌ها (ریال)'  # type: ignore
    
    def calculated_buy_price(self, obj: Product) -> str:
        """Display calculated buy price with color."""
        buy_price_fmt = self.format_currency(obj.buy_price, 'ریال', 0)
        return format_html(
            '<span style="color: #2e7d32; font-weight: bold;">{}</span>',
            buy_price_fmt
        )
    
    calculated_buy_price.short_description = '💰 قیمت خرید'  # type: ignore
    calculated_buy_price.admin_order_field = 'buy_price'  # type: ignore
    
    def calculated_sell_price(self, obj: Product) -> str:
        """Display calculated sell price with color."""
        sell_price_fmt = self.format_currency(obj.sell_price, 'ریال', 0)
        return format_html(
            '<span style="color: #c62828; font-weight: bold;">{}</span>',
            sell_price_fmt
        )
    
    calculated_sell_price.short_description = '💵 قیمت فروش'  # type: ignore
    calculated_sell_price.admin_order_field = 'sell_price'  # type: ignore
    
    def base_api_price_display(self, obj: Product) -> str:
        """Display base price fetched from API."""
        if obj.base_price_api:
            base_price_fmt = self.format_currency(obj.base_price_api, 'ریال', 0)
            return format_html(
                '<span style="color: #1976d2;">{}</span>',
                base_price_fmt
            )
        return format_html('<span style="color: #999;">—</span>')
    
    base_api_price_display.short_description = '📡 قیمت API'  # type: ignore
    
    def calculated_price_preview(self, obj: Product) -> str:
        """Show detailed price calculation preview."""
        if not obj.base_price_api:
            return format_html(
                '<div style="background: #fff3cd; padding: 10px; border-radius: 5px;">'
                '⚠️ هنوز قیمت از API دریافت نشده است.<br>'
                'لطفاً دستور <code>python manage.py update_prices</code> را اجرا کنید.'
                '</div>'
            )
        
        adjusted_base = obj.base_price_api * obj.weight_grams
        
        # Determine product type for better display
        is_coin = obj.product_code in ['coin_full', 'coin_half', 'coin_quarter']
        is_currency = obj.product_code in ['dollar_usa', 'euro', 'pound_uk', 'yuan_china', 'lira_turkey', 'dirham_uae']
        is_gold = obj.product_code == 'gold_abshodeh'
        
        if is_coin:
            unit_text = '🪙 قیمت API به ازای <strong>هر عدد سکه</strong> (نه وزن!)'
            coef_note = '(برای سکه‌ها همیشه = 1، چون قیمت‌گذاری واحدی است)'
        elif is_currency:
            unit_text = '💵 قیمت API به ازای <strong>هر واحد ارز</strong>'
            coef_note = '(برای ارزها همیشه = 1)'
        elif is_gold:
            unit_text = '✨ قیمت API به ازای <strong>هر گرم طلا</strong>'
            coef_note = '(برای طلا همیشه = 1)'
        else:
            unit_text = 'قیمت API به ازای هر واحد'
            coef_note = ''
        
        # Format all values
        base_price_fmt = f"{float(obj.base_price_api):,.0f}"
        adjusted_base_fmt = f"{float(adjusted_base):,.0f}"
        buy_margin_fmt = f"{float(obj.buy_margin):,.0f}"
        buy_price_fmt = f"{float(obj.buy_price):,.0f}"
        sell_margin_fmt = f"{float(obj.sell_margin):,.0f}"
        sell_price_fmt = f"{float(obj.sell_price):,.0f}"
        
        coef_display = f'<strong>{obj.weight_grams}</strong>'
        if coef_note:
            coef_display += f' <small style="color: #666;">{coef_note}</small>'
        
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 5px; font-family: monospace;">'
            '<strong>فرمول محاسبه:</strong><br><br>'
            '🔹 {}: <strong>{}</strong> ریال<br>'
            '🔹 ضریب واحد: {}<br>'
            '🔹 قیمت پایه: <strong>{}</strong> ریال<br>'
            '<hr style="margin: 10px 0;">'
            '✅ قیمت خرید = {} - {} = <strong style="color: #2e7d32;">{}</strong> ریال<br>'
            '✅ قیمت فروش = {} + {} = <strong style="color: #c62828;">{}</strong> ریال'
            '</div>',
            unit_text,
            base_price_fmt,
            mark_safe(coef_display),
            adjusted_base_fmt,
            adjusted_base_fmt,
            buy_margin_fmt,
            buy_price_fmt,
            adjusted_base_fmt,
            sell_margin_fmt,
            sell_price_fmt
        )
    
    calculated_price_preview.short_description = '📊 پیش‌نمای محاسبه'  # type: ignore
    
    def price_trend_24h(self, obj: Product) -> str:
        """Show price trend for last 24 hours."""
        time_24h_ago = timezone.now() - timedelta(hours=24)
        old_price = PriceHistory.objects.filter(
            product=obj,
            recorded_at__lte=time_24h_ago
        ).order_by('-recorded_at').first()
        
        if not old_price:
            return format_html('<span style="color: #999;">—</span>')
        
        # Calculate change
        change_pct, trend = format_percentage_change(obj.sell_price, old_price.sell_price)
        color = get_trend_color(obj.sell_price - old_price.sell_price)
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            trend,
            change_pct
        )
    
    price_trend_24h.short_description = '📈 روند ۲۴ ساعت'  # type: ignore
    
    def total_volume_30d(self, obj: Product) -> str:
        """Show total trade volume for last 30 days."""
        # Use annotated value instead of querying
        volume = getattr(obj, 'volume_30d', None) or Decimal('0')
        
        # Format in millions
        volume_millions = float(volume / 1000000)
        volume_fmt = to_persian_numbers(f"{volume_millions:.1f}")
        
        return format_html(
            '<span style="font-weight: bold;">{} میلیون</span>',
            volume_fmt
        )
    
    total_volume_30d.short_description = '💰 حجم معاملات ۳۰ روز'  # type: ignore
    
    def product_category_badge(self, obj: Product) -> str:
        """Display product category with color-coded badge."""
        code = obj.product_code
        
        # Currency products
        if code in ['dollar_usa', 'euro', 'pound_uk', 'yuan_china', 'lira_turkey', 'dirham_uae']:
            return format_html(
                '<span class="badge" style="background-color: #2e7d32; color: white; padding: 5px 10px; border-radius: 12px; font-weight: bold;">💵 ارز</span>'
            )
        # Coin products
        elif code in ['coin_full', 'coin_half', 'coin_quarter']:
            return format_html(
                '<span class="badge" style="background-color: #ff6f00; color: white; padding: 5px 10px; border-radius: 12px; font-weight: bold;">🪙 سکه</span>'
            )
        # Gold products
        elif code == 'gold_abshodeh' or code == 'gold':
            return format_html(
                '<span class="badge" style="background-color: #c2185b; color: white; padding: 5px 10px; border-radius: 12px; font-weight: bold;">✨ طلا</span>'
            )
        else:
            return format_html(
                '<span class="badge" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">❓ نامشخص</span>'
            )
    
    product_category_badge.short_description = 'دسته'  # type: ignore
    product_category_badge.admin_order_field = 'product_code'  # type: ignore
    
    def product_code_display(self, obj: Product) -> str:
        """Display product code with monospace formatting."""
        return format_html(
            '<code style="background-color: #f5f5f5; padding: 3px 8px; border-radius: 3px; font-size: 11px; color: #d32f2f; font-family: monospace;">{}</code>',
            obj.product_code
        )
    
    product_code_display.short_description = 'کد محصول'  # type: ignore
    product_code_display.admin_order_field = 'product_code'  # type: ignore
    
    # ==================== Custom Admin Actions ====================
    
    actions = ['activate_products', 'deactivate_products', 'bulk_update_margins', 'export_with_margins']
    
    @admin.action(description='🟢 فعال‌سازی محصولات انتخاب شده')
    def activate_products(self, request: HttpRequest, queryset):
        """Bulk activate selected products."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} محصول با موفقیت فعال شد.',
            messages.SUCCESS
        )
    
    @admin.action(description='🔴 غیرفعال‌سازی محصولات انتخاب شده')
    def deactivate_products(self, request: HttpRequest, queryset):
        """Bulk deactivate selected products."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} محصول با موفقیت غیرفعال شد.',
            messages.WARNING
        )
    
    @admin.action(description='✏️ به‌روزرسانی دسته‌جمع مارجین‌ها')
    def bulk_update_margins(self, request: HttpRequest, queryset):
        """Bulk update margins for selected products."""
        if 'apply' in request.POST:
            form = BulkMarginUpdateForm(request.POST)
            
            if form.is_valid():
                buy_margin = form.cleaned_data.get('buy_margin')
                sell_margin = form.cleaned_data.get('sell_margin')
                update_prices = form.cleaned_data.get('update_prices', True)
                
                updated_count = 0
                
                for product in queryset:
                    updated = False
                    
                    if buy_margin is not None:
                        product.buy_margin = buy_margin
                        updated = True
                    
                    if sell_margin is not None:
                        product.sell_margin = sell_margin
                        updated = True
                    
                    if updated:
                        if update_prices and product.base_price_api:
                            # Recalculate prices with new margins
                            product.update_prices_from_api(product.base_price_api)
                        
                        product.save()
                        updated_count += 1
                
                self.message_user(
                    request,
                    f'مارجین‌های {updated_count} محصول با موفقیت به‌روزرسانی شد.',
                    messages.SUCCESS
                )
                
                return None
        
        else:
            form = BulkMarginUpdateForm()
        
        context = {
            'title': 'به‌روزرسانی دسته‌جمع مارجین‌ها',
            'form': form,
            'products': queryset,
            'action_name': 'bulk_update_margins',
            'action_checkbox_name': admin_helpers.ACTION_CHECKBOX_NAME,
        }
        
        return render(request, 'admin/trading/bulk_margin_update.html', context)
    
    @admin.action(description='📤 خروجی اکسل با جزئیات مارجین')
    def export_with_margins(self, request: HttpRequest, queryset):
        """Export selected products with detailed margin information."""
        from django.http import HttpResponse
        import csv
        from datetime import datetime
        
        response = HttpResponse(content_type='text/csv; charset=utf-8-sig')
        response['Content-Disposition'] = f'attachment; filename="products_with_margins_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Add BOM for Excel UTF-8 support
        response.write('\ufeff')
        
        writer = csv.writer(response)
        writer.writerow([
            'کد محصول',
            'نام محصول',
            'ضریب واحد',
            'قیمت پایه API (ریال)',
            'مارجین خرید (ریال)',
            'مارجین فروش (ریال)',
            'قیمت خرید نهایی (ریال)',
            'قیمت فروش نهایی (ریال)',
            'اختلاف قیمت (ریال)',
            'فعال/غیرفعال',
            'تاریخ آخرین به‌روزرسانی'
        ])
        
        for product in queryset:
            writer.writerow([
                product.product_code,
                product.name,
                float(product.weight_grams),
                float(product.base_price_api or 0),
                float(product.buy_margin),
                float(product.sell_margin),
                float(product.buy_price),
                float(product.sell_price),
                float(product.get_price_spread()),
                'فعال' if product.is_active else 'غیرفعال',
                product.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        self.message_user(
            request,
            f'{queryset.count()} محصول با موفقیت خروجی گرفته شد.',
            messages.SUCCESS
        )
        
        return response


__all__ = ['ProductAdmin']

