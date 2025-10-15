#!/bin/bash

# Script راه‌اندازی اولیه پروژه Gold Shop

set -e

echo "🚀 شروع راه‌اندازی سامانه معاملات طلا..."

# بررسی Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 نصب نیست. لطفا ابتدا Python 3.9+ را نصب کنید."
    exit 1
fi

echo "✅ Python یافت شد: $(python3 --version)"

# ساخت محیط مجازی
if [ ! -d "venv" ]; then
    echo "📦 ساخت محیط مجازی..."
    python3 -m venv venv
else
    echo "✅ محیط مجازی موجود است"
fi

# فعال‌سازی محیط مجازی
echo "🔧 فعال‌سازی محیط مجازی..."
source venv/bin/activate

# نصب پکیج‌ها
echo "📥 نصب پکیج‌های مورد نیاز..."
pip install --upgrade pip
pip install -r requirements.txt

# تنظیم فایل .env
if [ ! -f ".env" ]; then
    echo "📝 ساخت فایل .env..."
    cp .env.example .env
    echo "⚠️  لطفا فایل .env را ویرایش کنید و TELEGRAM_BOT_TOKEN را تنظیم کنید."
else
    echo "✅ فایل .env موجود است"
fi

# اجرای migrations
echo "🗄️  اجرای migrations..."
python manage.py makemigrations
python manage.py migrate

# بررسی superuser
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 ایجاد کاربر ادمین"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python manage.py createsuperuser

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ راه‌اندازی با موفقیت انجام شد!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 مراحل بعدی:"
echo "1. فایل .env را ویرایش کنید و TELEGRAM_BOT_TOKEN را تنظیم کنید"
echo "2. سرور Django را اجرا کنید: python manage.py runserver"
echo "3. وارد پنل ادمین شوید: http://localhost:8000/admin/"
echo "4. محصولات (انواع طلا) را اضافه کنید"
echo "5. ربات را اجرا کنید: python manage.py runbot"
echo ""
echo "📚 برای راهنمای کامل، فایل SETUP_GUIDE.md را مطالعه کنید."
echo ""
