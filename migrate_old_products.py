#!/usr/bin/env python
"""
اسکریپت مهاجرت محصولات قدیمی

این اسکریپت محصولات موجود بدون product_code را شناسایی و به‌روز می‌کند.
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from trading.models import Product


def migrate_old_products():
    """مهاجرت محصولات قدیمی بدون product_code"""
    
    print("🔍 جستجوی محصولات بدون کد...")
    
    products_without_code = Product.objects.filter(product_code__isnull=True)
    
    if not products_without_code.exists():
        print("✅ همه محصولات دارای کد هستند!")
        return
    
    print(f"📦 {products_without_code.count()} محصول بدون کد یافت شد.\n")
    
    # نقشه برای تشخیص خودکار بر اساس نام
    name_mapping = {
        'طلا': Product.PRODUCT_CODE_GOLD,
        'آبشده': Product.PRODUCT_CODE_GOLD,
        'gold': Product.PRODUCT_CODE_GOLD,
        'سکه': Product.PRODUCT_CODE_COIN,
        'coin': Product.PRODUCT_CODE_COIN,
        'دلار': Product.PRODUCT_CODE_DOLLAR,
        'dollar': Product.PRODUCT_CODE_DOLLAR,
        'usd': Product.PRODUCT_CODE_DOLLAR,
    }
    
    updated = 0
    manual_review = []
    
    for product in products_without_code:
        # تلاش برای تشخیص خودکار
        detected_code = None
        product_name_lower = product.name.lower()
        
        for keyword, code in name_mapping.items():
            if keyword in product_name_lower:
                detected_code = code
                break
        
        if detected_code:
            # بررسی اینکه این کد قبلاً استفاده نشده
            if not Product.objects.filter(product_code=detected_code).exists():
                product.product_code = detected_code
                product.save()
                print(f"✅ '{product.name}' → کد: {detected_code}")
                updated += 1
            else:
                manual_review.append(product)
                print(f"⚠️  '{product.name}' → کد {detected_code} قبلاً استفاده شده")
        else:
            manual_review.append(product)
            print(f"❓ '{product.name}' → نیاز به بررسی دستی")
    
    print(f"\n📊 خلاصه:")
    print(f"  ✅ {updated} محصول به‌روز شد")
    print(f"  ⚠️  {len(manual_review)} محصول نیاز به بررسی دستی دارد")
    
    if manual_review:
        print("\n📝 محصولات نیازمند بررسی دستی:")
        for product in manual_review:
            print(f"  - ID: {product.id} | نام: {product.name}")
        
        print("\nبرای تنظیم دستی:")
        print("1. وارد پنل ادمین شوید")
        print("2. یا از Django shell استفاده کنید:")
        print("\n   python manage.py shell")
        print("   >>> from trading.models import Product")
        print("   >>> p = Product.objects.get(id=X)")
        print("   >>> p.product_code = 'GOLD_ABSHODEH'  # یا COIN_FULL یا DOLLAR")
        print("   >>> p.save()")


if __name__ == '__main__':
    print("🔄 شروع مهاجرت محصولات قدیمی...\n")
    migrate_old_products()
    print("\n✅ مهاجرت کامل شد!")

