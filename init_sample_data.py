"""
Script to initialize sample data for testing
Run: python init_sample_data.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from decimal import Decimal
from django.contrib.auth.models import User
from users.models import Profile
from trading.models import Product


def create_sample_products():
    """
    ایجاد محصولات نمونه
    """
    products_data = [
        {
            'name': 'طلای 18 عیار',
            'slug': 'tala-18-ayar',
            'buy_price': Decimal('3850000'),
            'sell_price': Decimal('3950000'),
        },
        {
            'name': 'طلای 24 عیار',
            'slug': 'tala-24-ayar',
            'buy_price': Decimal('5100000'),
            'sell_price': Decimal('5250000'),
        },
        {
            'name': 'سکه بهار آزادی',
            'slug': 'sekeh-bahar-azadi',
            'buy_price': Decimal('47500000'),
            'sell_price': Decimal('48500000'),
        },
        {
            'name': 'نیم سکه',
            'slug': 'nim-sekeh',
            'buy_price': Decimal('24000000'),
            'sell_price': Decimal('24500000'),
        },
        {
            'name': 'ربع سکه',
            'slug': 'rob-sekeh',
            'buy_price': Decimal('12500000'),
            'sell_price': Decimal('13000000'),
        },
    ]
    
    created_count = 0
    for data in products_data:
        product, created = Product.objects.get_or_create(
            slug=data['slug'],
            defaults=data
        )
        if created:
            print(f"✓ محصول ایجاد شد: {product.name}")
            created_count += 1
        else:
            print(f"  محصول از قبل وجود دارد: {product.name}")
    
    return created_count


def create_test_user():
    """
    ایجاد کاربر تست (برای آزمایش ربات)
    """
    # ایجاد یک کاربر تست با موجودی
    username = 'test_user'
    
    user, user_created = User.objects.get_or_create(
        username=username,
        defaults={
            'first_name': 'کاربر',
            'last_name': 'تست',
        }
    )
    
    if user_created:
        user.set_password('testpass123')
        user.save()
    
    # ایجاد پروفایل با موجودی اولیه
    profile, profile_created = Profile.objects.get_or_create(
        user=user,
        defaults={
            'telegram_id': '123456789',
            'telegram_username': 'test_user',
            'phone_number': '09123456789',
            'is_approved': True,
            'rial_balance': Decimal('100000000'),  # 100 میلیون ریال
            'gold_balance_grams': Decimal('10.0000'),  # 10 گرم طلا
        }
    )
    
    if profile_created:
        print(f"\n✓ کاربر تست ایجاد شد:")
        print(f"  Username: {username}")
        print(f"  Password: testpass123")
        print(f"  Telegram ID: {profile.telegram_id}")
        print(f"  موجودی ریالی: {profile.get_formatted_rial_balance()} ریال")
        print(f"  موجودی طلا: {profile.get_formatted_gold_balance()} گرم")
    else:
        print(f"\n  کاربر تست از قبل وجود دارد: {username}")
    
    return profile_created


def main():
    """
    اجرای اصلی اسکریپت
    """
    print("=" * 60)
    print("ایجاد داده‌های نمونه برای سیستم معاملات طلا")
    print("=" * 60)
    print()
    
    # ایجاد محصولات
    print("📦 ایجاد محصولات...")
    products_count = create_sample_products()
    print(f"\n✅ {products_count} محصول جدید ایجاد شد.\n")
    
    # ایجاد کاربر تست
    print("👤 ایجاد کاربر تست...")
    create_test_user()
    
    print("\n" + "=" * 60)
    print("✅ اتمام عملیات! داده‌های نمونه با موفقیت ایجاد شدند.")
    print("=" * 60)
    print()
    print("مراحل بعدی:")
    print("1. python manage.py createsuperuser  (برای ایجاد ادمین)")
    print("2. python manage.py runserver         (اجرای سرور Django)")
    print("3. python manage.py runbot            (اجرای ربات تلگرام)")
    print()


if __name__ == '__main__':
    main()
