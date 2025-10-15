#!/bin/bash

# راه‌اندازی سریع پروژه Gold Shop
echo "=========================================="
echo "راه‌اندازی پروژه سیستم معاملات طلا"
echo "=========================================="
echo ""

# بررسی وجود Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 یافت نشد. لطفاً ابتدا Python نصب کنید."
    exit 1
fi

echo "✓ Python یافت شد: $(python3 --version)"
echo ""

# نصب وابستگی‌ها
echo "📦 نصب وابستگی‌ها..."
pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "❌ خطا در نصب وابستگی‌ها"
    exit 1
fi

echo "✓ وابستگی‌ها نصب شدند"
echo ""

# بررسی فایل .env
if [ ! -f .env ]; then
    echo "📄 ایجاد فایل .env از روی .env.example..."
    cp .env.example .env
    echo "⚠️  لطفاً فایل .env را ویرایش کنید و TELEGRAM_BOT_TOKEN را وارد کنید."
    echo ""
fi

# اجرای مایگریشن‌ها
echo "🗄️  اجرای مایگریشن‌های دیتابیس..."
python3 manage.py makemigrations
python3 manage.py migrate

if [ $? -ne 0 ]; then
    echo "❌ خطا در اجرای مایگریشن‌ها"
    exit 1
fi

echo "✓ مایگریشن‌ها اجرا شدند"
echo ""

# ایجاد داده‌های نمونه
echo "📊 ایجاد داده‌های نمونه..."
python3 init_sample_data.py

echo ""
echo "=========================================="
echo "✅ راه‌اندازی با موفقیت انجام شد!"
echo "=========================================="
echo ""
echo "مراحل بعدی:"
echo "1. ویرایش فایل .env و تنظیم TELEGRAM_BOT_TOKEN"
echo "2. ایجاد سوپریوزر: python3 manage.py createsuperuser"
echo "3. اجرای سرور: python3 manage.py runserver"
echo "4. اجرای ربات: python3 manage.py runbot"
echo ""
