# 🚀 راهنمای سریع راه‌اندازی

## پیش‌نیازها
- Python 3.10 یا بالاتر
- pip (Python package manager)
- Git
- یک Bot Token از [@BotFather](https://t.me/botfather) در تلگرام

## مراحل راه‌اندازی (5-10 دقیقه)

### مرحله 1: دانلود و نصب وابستگی‌ها

```bash
# 1. کلون پروژه (اگر از Git استفاده می‌کنید)
git clone <repository-url>
cd gold_shop

# 2. ایجاد محیط مجازی
python -m venv venv

# فعال‌سازی محیط مجازی
# در لینوکس/مک:
source venv/bin/activate
# در ویندوز:
venv\Scripts\activate

# 3. نصب پکیج‌ها
pip install -r requirements.txt
```

### مرحله 2: تنظیمات محیطی

```bash
# 1. کپی فایل نمونه
cp .env.example .env

# 2. ویرایش فایل .env
nano .env  # یا از ویرایشگر دلخواه استفاده کنید
```

**مهم**: حداقل این موارد را تنظیم کنید:
```env
SECRET_KEY=یک-کلید-تصادفی-قوی-اینجا-بگذارید
DEBUG=True
TELEGRAM_BOT_TOKEN=توکن-ربات-خود-را-اینجا-بگذارید
```

برای تولید SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### مرحله 3: راه‌اندازی دیتابیس

```bash
# 1. اجرای مایگریشن‌ها
python manage.py migrate

# 2. ایجاد داده‌های نمونه (اختیاری اما توصیه می‌شود)
python setup_sample_data.py

# 3. ایجاد حساب مدیر
python manage.py createsuperuser
```

### مرحله 4: اجرای پروژه

**دو روش داریم:**

#### روش 1: اجرای دستی (برای توسعه)

```bash
# ترمینال 1: Django Admin Panel
python manage.py runserver
# دسترسی: http://localhost:8000/admin

# ترمینال 2: Telegram Bot
python manage.py runbot
```

#### روش 2: استفاده از Docker (توصیه شده برای production)

```bash
docker-compose up -d
```

## ✅ بررسی موفقیت‌آمیز بودن نصب

### 1. بررسی Django Admin
- مرور `http://localhost:8000/admin`
- ورود با حساب superuser
- بررسی بخش‌های: Users, Products, Orders

### 2. بررسی Telegram Bot
- باز کردن ربات در تلگرام
- ارسال `/start`
- باید منوی اصلی نمایش داده شود

### 3. تست معامله
- ثبت‌نام یک کاربر جدید در ربات
- تایید کاربر از پنل ادمین (Users → Profiles → تایید)
- انجام یک معامله تستی

## 🔧 عیب‌یابی رایج

### خطا: `ModuleNotFoundError: No module named 'django'`
```bash
# اطمینان از فعال بودن محیط مجازی
source venv/bin/activate  # لینوکس/مک
venv\Scripts\activate      # ویندوز

# نصب مجدد وابستگی‌ها
pip install -r requirements.txt
```

### خطا: `TELEGRAM_BOT_TOKEN is not set`
```bash
# بررسی فایل .env
cat .env | grep TELEGRAM_BOT_TOKEN

# اطمینان از وجود توکن
# اگر خالی است، توکن را از @BotFather دریافت و تنظیم کنید
```

### خطا: `relation "trading_product" already exists`
```bash
# حذف دیتابیس و ایجاد مجدد
rm db.sqlite3
python manage.py migrate
python setup_sample_data.py
```

### Bot پاسخ نمی‌دهد
```bash
# بررسی لاگ‌ها
tail -f logs/gold_shop.log

# اطمینان از صحت توکن
# رفتن به @BotFather و بررسی توکن ربات
```

## 📚 مستندات بیشتر

- **راهنمای کامل**: [README.md](README.md)
- **راهنمای استقرار**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **شروع سریع**: [QUICKSTART.md](QUICKSTART.md)
- **خلاصه پروژه**: [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)

## 🎯 مراحل بعدی

بعد از راه‌اندازی موفق:

1. **تنظیم قیمت‌ها**: به پنل ادمین بروید و قیمت‌های واقعی را تنظیم کنید
2. **به‌روزرسانی خودکار**: یک Cron Job برای `update_prices` تنظیم کنید
3. **پشتیبان‌گیری**: یک برنامه پشتیبان‌گیری منظم از دیتابیس تنظیم کنید
4. **مانیتورینگ**: لاگ‌ها را بررسی کنید و یک سیستم مانیتورینگ راه‌اندازی کنید
5. **امنیت**: در production حتماً `DEBUG=False` و از HTTPS استفاده کنید

## 💬 پشتیبانی

اگر مشکلی با راه‌اندازی داشتید:
1. ابتدا بخش عیب‌یابی بالا را بررسی کنید
2. لاگ‌ها را چک کنید: `logs/gold_shop.log`
3. یک Issue در GitHub باز کنید
4. مستندات کامل را مطالعه کنید

---

**نکته**: این راهنما برای محیط توسعه (Development) است. برای استقرار Production به [DEPLOYMENT.md](DEPLOYMENT.md) مراجعه کنید.
