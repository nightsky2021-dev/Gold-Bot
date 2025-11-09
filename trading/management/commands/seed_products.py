"""
Management command to seed initial products in the database.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from trading.models import Product


class Command(BaseCommand):
    help = 'ایجاد محصولات اولیه در دیتابیس'

    def handle(self, *args, **options):
        """Create initial products if they don't exist."""
        
        products_data = [
            # Currencies (all with weight=1 as they're per-unit basis)
            {
                'product_code': Product.PRODUCT_CODE_DOLLAR_USA,
                'name': 'دلار آمریکا',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),  # Will be auto-calculated as 1%
                'sell_margin': Decimal('0'),  # Will be auto-calculated as 1%
                'buy_price': Decimal('700000'),  # Default placeholder
                'sell_price': Decimal('700000'),  # Default placeholder
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_EURO,
                'name': 'یورو',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),
                'sell_margin': Decimal('0'),
                'buy_price': Decimal('750000'),
                'sell_price': Decimal('750000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_LIRA_TURKEY,
                'name': 'لیر ترکیه',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),
                'sell_margin': Decimal('0'),
                'buy_price': Decimal('20000'),
                'sell_price': Decimal('20000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_YUAN_CHINA,
                'name': 'یوان چین',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),
                'sell_margin': Decimal('0'),
                'buy_price': Decimal('95000'),
                'sell_price': Decimal('95000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_POUND_UK,
                'name': 'پوند انگلیس',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),
                'sell_margin': Decimal('0'),
                'buy_price': Decimal('880000'),
                'sell_price': Decimal('880000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_DIRHAM_UAE,
                'name': 'درهم امارات',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('0'),
                'sell_margin': Decimal('0'),
                'buy_price': Decimal('190000'),
                'sell_price': Decimal('190000'),
                'is_active': True,
            },
            
            # Gold (per gram)
            {
                'product_code': Product.PRODUCT_CODE_GOLD_ABSHODEH,
                'name': 'طلای آبشده',
                'weight_grams': Decimal('1'),
                'buy_margin': Decimal('300000'),
                'sell_margin': Decimal('300000'),
                'buy_price': Decimal('5000000'),
                'sell_price': Decimal('5600000'),
                'is_active': True,
            },
            
            # Coins (with specific weights)
            {
                'product_code': Product.PRODUCT_CODE_COIN_FULL,
                'name': 'سکه تمام غیربانکی',
                'weight_grams': Decimal('8.133'),  # Weight of a full coin in grams
                'buy_margin': Decimal('4500000'),
                'sell_margin': Decimal('4500000'),
                'buy_price': Decimal('40000000'),
                'sell_price': Decimal('49000000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_COIN_HALF,
                'name': 'نیم سکه غیربانکی',
                'weight_grams': Decimal('4.0665'),  # Half of full coin weight
                'buy_margin': Decimal('2250000'),
                'sell_margin': Decimal('2250000'),
                'buy_price': Decimal('20000000'),
                'sell_price': Decimal('24500000'),
                'is_active': True,
            },
            {
                'product_code': Product.PRODUCT_CODE_COIN_QUARTER,
                'name': 'ربع سکه غیربانکی',
                'weight_grams': Decimal('2.03325'),  # Quarter of full coin weight
                'buy_margin': Decimal('1125000'),
                'sell_margin': Decimal('1125000'),
                'buy_price': Decimal('10000000'),
                'sell_price': Decimal('12250000'),
                'is_active': True,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for data in products_data:
            product_code = data['product_code']
            
            # Check if product already exists
            product, created = Product.objects.get_or_create(
                product_code=product_code,
                defaults=data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ محصول "{product.name}" ایجاد شد.')
                )
                created_count += 1
            else:
                # Update existing product with new data
                for key, value in data.items():
                    if key != 'product_code':  # Don't update the product_code
                        setattr(product, key, value)
                product.save()
                
                self.stdout.write(
                    self.style.WARNING(f'⚠️  محصول "{product.name}" از قبل موجود بود و به‌روزرسانی شد.')
                )
                updated_count += 1
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('━' * 60))
        self.stdout.write(self.style.SUCCESS(f'✅ عملیات تکمیل شد!'))
        self.stdout.write(self.style.SUCCESS(f'   • تعداد محصولات ایجاد شده: {created_count}'))
        self.stdout.write(self.style.SUCCESS(f'   • تعداد محصولات به‌روزرسانی شده: {updated_count}'))
        self.stdout.write(self.style.SUCCESS(f'   • مجموع: {created_count + updated_count}'))
        self.stdout.write(self.style.SUCCESS('━' * 60))
        self.stdout.write('')
        
        # Suggest next steps
        self.stdout.write(self.style.WARNING('📋 مراحل بعدی:'))
        self.stdout.write('   1. برای به‌روزرسانی قیمت‌ها از API:')
        self.stdout.write(self.style.WARNING('      python manage.py update_prices'))
        self.stdout.write('')
        self.stdout.write('   2. برای مشاهده محصولات در پنل ادمین:')
        self.stdout.write(self.style.WARNING('      http://localhost:8000/admin/trading/product/'))
        self.stdout.write('')
        self.stdout.write('   3. اکنون می‌توانید ربات را اجرا کنید:')
        self.stdout.write(self.style.WARNING('      python manage.py runbot'))
        self.stdout.write('')

