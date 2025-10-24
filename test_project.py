#!/usr/bin/env python
"""
اسکریپت تست سریع برای بررسی صحت نصب و پیکربندی پروژه
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from django.conf import settings
from django.core.management import call_command


def test_imports():
    """تست import کردن ماژول‌ها"""
    print("🔍 تست import ماژول‌ها...")
    
    try:
        from users.models import Profile
        from trading.models import Product, Order
        from users.services import UserService
        from trading.services import TradingService
        print("✅ تمام ماژول‌ها با موفقیت import شدند")
        return True
    except ImportError as e:
        print(f"❌ خطا در import: {e}")
        return False


def test_settings():
    """تست تنظیمات"""
    print("\n🔍 تست تنظیمات...")
    
    checks = [
        ("SECRET_KEY", settings.SECRET_KEY != 'django-insecure-change-this-in-production'),
        ("INSTALLED_APPS", 'users' in settings.INSTALLED_APPS),
        ("INSTALLED_APPS", 'trading' in settings.INSTALLED_APPS),
        ("INSTALLED_APPS", 'bot' in settings.INSTALLED_APPS),
        ("TIME_ZONE", settings.TIME_ZONE == 'Asia/Tehran'),
        ("LANGUAGE_CODE", settings.LANGUAGE_CODE == 'fa-ir'),
    ]
    
    all_pass = True
    for name, check in checks:
        status = "✅" if check else "❌"
        print(f"{status} {name}")
        if not check:
            all_pass = False
    
    return all_pass


def test_migrations():
    """تست migrations"""
    print("\n🔍 بررسی migrations...")
    
    try:
        from django.db.migrations.executor import MigrationExecutor
        from django.db import connection
        
        executor = MigrationExecutor(connection)
        plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
        
        if plan:
            print(f"⚠️  {len(plan)} migration در انتظار اجرا است")
            print("💡 لطفا اجرا کنید: python manage.py migrate")
            return False
        else:
            print("✅ تمام migrations اجرا شده‌اند")
            return True
            
    except Exception as e:
        print(f"⚠️  نمی‌توان وضعیت migrations را بررسی کرد: {e}")
        print("💡 احتمالاً هنوز migrate اجرا نشده است")
        return False


def test_models():
    """تست مدل‌ها"""
    print("\n🔍 تست مدل‌ها...")
    
    try:
        from users.models import Profile
        from trading.models import Product, Order
        
        # بررسی فیلدها
        profile_fields = [f.name for f in Profile._meta.get_fields()]
        product_fields = [f.name for f in Product._meta.get_fields()]
        order_fields = [f.name for f in Order._meta.get_fields()]
        
        required_profile_fields = ['telegram_id', 'phone_number', 'is_approved', 
                                   'rial_balance', 'gold_balance_grams']
        required_product_fields = ['name', 'buy_price', 'sell_price', 'is_active']
        required_order_fields = ['profile', 'product', 'order_type', 'quantity_grams', 
                                'status', 'total_amount']
        
        checks = []
        for field in required_profile_fields:
            checks.append(("Profile." + field, field in profile_fields))
        
        for field in required_product_fields:
            checks.append(("Product." + field, field in product_fields))
        
        for field in required_order_fields:
            checks.append(("Order." + field, field in order_fields))
        
        all_pass = True
        for name, check in checks:
            status = "✅" if check else "❌"
            print(f"{status} {name}")
            if not check:
                all_pass = False
        
        return all_pass
        
    except Exception as e:
        print(f"❌ خطا در تست مدل‌ها: {e}")
        return False


def test_admin():
    """تست ثبت شدن در Admin"""
    print("\n🔍 تست پنل ادمین...")
    
    try:
        from django.contrib import admin
        from users.models import Profile
        from trading.models import Product, Order
        
        checks = [
            ("Profile", Profile in admin.site._registry),
            ("Product", Product in admin.site._registry),
            ("Order", Order in admin.site._registry),
        ]
        
        all_pass = True
        for name, check in checks:
            status = "✅" if check else "❌"
            print(f"{status} {name} در admin ثبت شده")
            if not check:
                all_pass = False
        
        return all_pass
        
    except Exception as e:
        print(f"❌ خطا در تست admin: {e}")
        return False


def test_management_commands():
    """تست management commands"""
    print("\n🔍 تست management commands...")
    
    try:
        from django.core.management import get_commands
        commands = get_commands()
        
        required_commands = ['runbot', 'update_prices']
        checks = []
        
        for cmd in required_commands:
            checks.append((cmd, cmd in commands))
        
        all_pass = True
        for name, check in checks:
            status = "✅" if check else "❌"
            print(f"{status} Command '{name}'")
            if not check:
                all_pass = False
        
        return all_pass
        
    except Exception as e:
        print(f"❌ خطا در تست commands: {e}")
        return False


def main():
    """اجرای تمام تست‌ها"""
    print("=" * 60)
    print("🧪 شروع تست سیستم Gold Shop Trading")
    print("=" * 60)
    
    tests = [
        ("Import ماژول‌ها", test_imports),
        ("تنظیمات", test_settings),
        ("Migrations", test_migrations),
        ("مدل‌ها", test_models),
        ("پنل ادمین", test_admin),
        ("Management Commands", test_management_commands),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ خطای غیرمنتظره در تست {name}: {e}")
            results.append((name, False))
    
    # خلاصه نتایج
    print("\n" + "=" * 60)
    print("📊 خلاصه نتایج:")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ موفق" if result else "❌ ناموفق"
        print(f"{status} - {name}")
    
    print("\n" + "=" * 60)
    print(f"نتیجه نهایی: {passed}/{total} تست موفق")
    
    if passed == total:
        print("🎉 همه تست‌ها موفقیت‌آمیز بود!")
        print("\n💡 مراحل بعدی:")
        print("  1. فایل .env را تنظیم کنید (TELEGRAM_BOT_TOKEN)")
        print("  2. python manage.py makemigrations")
        print("  3. python manage.py migrate")
        print("  4. python manage.py createsuperuser")
        print("  5. python manage.py runserver")
        print("  6. محصولات را در پنل ادمین اضافه کنید")
        print("  7. python manage.py runbot")
        return 0
    else:
        print("⚠️  برخی تست‌ها ناموفق بودند. لطفا مشکلات را برطرف کنید.")
        return 1
    
    print("=" * 60)


if __name__ == '__main__':
    sys.exit(main())

