#!/usr/bin/env python
"""
اسکریپت راه‌اندازی اولیه محصولات

این اسکریپت محصولات پایه را در دیتابیس ایجاد می‌کند.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from trading.models import Product
from decimal import Decimal


def create_default_products():
    """ایجاد محصولات پیش‌فرض"""
    
    products_data = [
        {
            'product_code': Product.PRODUCT_CODE_GOLD,
            'name': 'طلای آبشده (هر گرم)',
            'slug': 'gold-abshodeh',
            'buy_price': Decimal('0'),
            'sell_price': Decimal('0'),
            'is_active': True,
        },
        {
            'product_code': Product.PRODUCT_CODE_COIN,
            'name': 'سکه تمام غیربانکی',
            'slug': 'coin-full',
            'buy_price': Decimal('0'),
            'sell_price': Decimal('0'),
            'is_active': True,
        },
        {
            'product_code': Product.PRODUCT_CODE_DOLLAR,
            'name': 'دلار آمریکا',
            'slug': 'dollar-usd',
            'buy_price': Decimal('0'),
            'sell_price': Decimal('0'),
            'is_active': True,
        },
    ]
    
    created_count = 0
    updated_count = 0
    
    for data in products_data:
        product, created = Product.objects.get_or_create(
            product_code=data['product_code'],
            defaults=data
        )
        
        if created:
            print(f"✅ محصول '{product.name}' ایجاد شد")
            created_count += 1
        else:
            # به‌روزرسانی محصول موجود اگر نیاز باشد
            product.name = data['name']
            product.slug = data['slug']
            product.is_active = data['is_active']
            product.save()
            print(f"ℹ️  محصول '{product.name}' از قبل وجود دارد و به‌روز شد")
            updated_count += 1
    
    print(f"\n📊 خلاصه: {created_count} محصول جدید | {updated_count} محصول موجود")
    
    # به‌روزرسانی قیمت‌ها
    print("\n🔄 به‌روزرسانی قیمت‌ها از API...")
    from trading.services import TradingService
    
    success = TradingService.update_all_prices()
    
    if success:
        print("✅ قیمت‌ها با موفقیت به‌روزرسانی شد!")
        
        # نمایش قیمت‌ها
        print("\n📊 قیمت‌های فعلی:")
        for product in Product.objects.filter(is_active=True):
            print(f"  • {product.name}:")
            print(f"    خرید: {product.buy_price:,} ریال | فروش: {product.sell_price:,} ریال")
    else:
        print("⚠️  خطا در به‌روزرسانی قیمت‌ها. لطفاً بعداً دستور update_prices را اجرا کنید.")


if __name__ == '__main__':
    print("🚀 راه‌اندازی محصولات پایه...\n")
    create_default_products()
    print("\n✅ راه‌اندازی کامل شد!")

