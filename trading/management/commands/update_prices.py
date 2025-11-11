"""
Management command برای به‌روزرسانی قیمت‌های محصولات

این کامند می‌تواند توسط Cron Job به صورت دوره‌ای اجرا شود.
مثال:
    python manage.py update_prices
    python manage.py update_prices --show-details
"""
from django.core.management.base import BaseCommand
from trading.services import TradingService
from trading.models import Product
from trading.price_providers import get_active_provider
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'به‌روزرسانی قیمت‌های محصولات از API Navasan'

    def add_arguments(self, parser):
        parser.add_argument(
            '--show-details',
            action='store_true',
            help='نمایش جزئیات کامل قیمت‌ها',
        )

    def handle(self, *args, **options):
        show_details = options['show_details']
        
        self.stdout.write('🔄 شروع به‌روزرسانی قیمت‌ها از API...\n')
        
        try:
            # نمایش قیمت‌های قبلی
            if show_details:
                self._show_current_prices()
            
            # به‌روزرسانی قیمت‌ها
            success = TradingService.update_all_prices()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS('\n✅ قیمت‌ها با موفقیت به‌روزرسانی شد!')
                )
                
                # نمایش قیمت‌های جدید
                if show_details:
                    self.stdout.write('\n' + '='*50)
                    self._show_current_prices()
                else:
                    self._show_summary()
            else:
                self.stdout.write(
                    self.style.ERROR('❌ خطا در به‌روزرسانی قیمت‌ها. لطفاً لاگ‌ها را بررسی کنید.')
                )
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطای غیرمنتظره: {str(e)}')
            )
            logger.error(f'خطا در اجرای update_prices: {e}', exc_info=True)
    
    def _show_current_prices(self):
        """نمایش قیمت‌های فعلی محصولات"""
        self.stdout.write(self.style.WARNING('\n📊 قیمت‌های فعلی:\n'))
        
        products = Product.objects.filter(is_active=True).order_by('product_code')
        
        for product in products:
            self.stdout.write(
                f'  🔸 {product.name}:\n'
                f'     💰 خرید ما از مشتری: {product.buy_price:,} ریال\n'
                f'     💵 فروش ما به مشتری: {product.sell_price:,} ریال\n'
            )
    
    def _show_summary(self):
        """نمایش خلاصه قیمت‌ها"""
        self.stdout.write('\n📊 خلاصه قیمت‌ها:\n')
        
        try:
            gold = Product.get_by_code(Product.PRODUCT_CODE_GOLD)
            self.stdout.write(f'  🪙 طلای آبشده: خرید {gold.buy_price:,} | فروش {gold.sell_price:,}')
        except Product.DoesNotExist:
            pass
        
        try:
            coin = Product.get_by_code(Product.PRODUCT_CODE_COIN)
            self.stdout.write(f'  🥇 سکه تمام: خرید {coin.buy_price:,} | فروش {coin.sell_price:,}')
        except Product.DoesNotExist:
            pass
        
        try:
            dollar = Product.get_by_code(Product.PRODUCT_CODE_DOLLAR)
            self.stdout.write(f'  💵 دلار: خرید {dollar.buy_price:,} | فروش {dollar.sell_price:,}')
        except Product.DoesNotExist:
            pass

