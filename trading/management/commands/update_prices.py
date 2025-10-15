"""
Management command برای به‌روزرسانی قیمت‌های محصولات

این کامند می‌تواند توسط Cron Job به صورت دوره‌ای اجرا شود.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from trading.models import Product
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'به‌روزرسانی قیمت‌های محصولات از API خارجی'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش تغییرات بدون ذخیره در دیتابیس',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('⚠️ حالت Dry Run فعال است - تغییرات ذخیره نخواهد شد'))
        
        self.stdout.write('شروع به‌روزرسانی قیمت‌ها...')
        
        try:
            # در اینجا شما می‌توانید از API خارجی قیمت‌ها را دریافت کنید
            # برای مثال:
            # prices = fetch_prices_from_external_api()
            
            # برای نمونه، قیمت‌ها را به صورت دستی تنظیم می‌کنیم
            # در پروداکشن، این قسمت باید با API واقعی جایگزین شود
            
            price_updates = self._fetch_latest_prices()
            
            updated_count = 0
            for product_name, prices in price_updates.items():
                try:
                    product = Product.objects.get(name=product_name)
                    
                    old_buy = product.buy_price
                    old_sell = product.sell_price
                    
                    if not dry_run:
                        product.buy_price = prices['buy']
                        product.sell_price = prices['sell']
                        product.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ {product_name}: '
                            f'خرید: {old_buy:,} -> {prices["buy"]:,} | '
                            f'فروش: {old_sell:,} -> {prices["sell"]:,}'
                        )
                    )
                    updated_count += 1
                    
                except Product.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️ محصول "{product_name}" یافت نشد')
                    )
                    continue
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n📊 {updated_count} محصول قابل به‌روزرسانی است (تغییرات ذخیره نشد)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'\n✅ {updated_count} محصول با موفقیت به‌روزرسانی شد'
                    )
                )
                logger.info(f'قیمت‌ها به‌روزرسانی شد: {updated_count} محصول')
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ خطا در به‌روزرسانی قیمت‌ها: {str(e)}')
            )
            logger.error(f'خطا در به‌روزرسانی قیمت‌ها: {e}', exc_info=True)
    
    def _fetch_latest_prices(self):
        """
        دریافت آخرین قیمت‌ها از API خارجی
        
        TODO: این متد باید با API واقعی پیاده‌سازی شود
        برای مثال می‌توانید از API های زیر استفاده کنید:
        - API سایت‌های معتبر طلا و سکه
        - Websocket برای دریافت قیمت لحظه‌ای
        - RSS Feed
        
        Returns:
            dict: دیکشنری قیمت‌ها به فرمت:
                {
                    'نام محصول': {
                        'buy': قیمت خرید,
                        'sell': قیمت فروش
                    }
                }
        """
        # نمونه قیمت‌ها (باید با API واقعی جایگزین شود)
        return {
            'طلای 18 عیار': {
                'buy': 2_500_000,
                'sell': 2_550_000,
            },
            'طلای 24 عیار': {
                'buy': 3_300_000,
                'sell': 3_350_000,
            },
            'سکه تمام': {
                'buy': 15_000_000,
                'sell': 15_200_000,
            },
        }
