# 📚 راهنمای راه‌اندازی سریع - Quick Setup Guide

این راهنما شما را گام به گام در راه‌اندازی سیستم همراهی می‌کند.

## ⚡ راه‌اندازی سریع (5 دقیقه)

### گام 1: نصب پکیج‌ها

```bash
# ساخت محیط مجازی
python3 -m venv venv
source venv/bin/activate  # در Windows: venv\Scripts\activate

# نصب requirements
pip install -r requirements.txt
```

### گام 2: تنظیم محیط

```bash
# کپی فایل .env
cp .env.example .env

# ویرایش .env و تنظیم توکن ربات
# حداقل باید TELEGRAM_BOT_TOKEN را تنظیم کنید
```

### گام 3: راه‌اندازی دیتابیس

```bash
# اجرای migrations
python manage.py migrate

# ساخت کاربر ادمین
python manage.py createsuperuser
```

### گام 4: ایجاد محصولات اولیه

```bash
# اجرای سرور Django
python manage.py runserver
```

وارد پنل ادمین شوید: `http://localhost:8000/admin/`

محصولات را اضافه کنید:

| نام محصول | قیمت خرید | قیمت فروش | فعال |
|-----------|-----------|-----------|------|
| طلای 18 عیار | 2500000 | 2550000 | ✅ |
| طلای 24 عیار | 3300000 | 3350000 | ✅ |
| سکه تمام | 15000000 | 15200000 | ✅ |

### گام 5: اجرای ربات

در یک ترمینال جدید:

```bash
python manage.py runbot
```

🎉 **تمام!** ربات شما آماده است.

## 🔧 تنظیمات پیشرفته

### استفاده از PostgreSQL

```bash
# نصب PostgreSQL
sudo apt install postgresql postgresql-contrib

# ساخت دیتابیس
sudo -u postgres psql
CREATE DATABASE gold_shop;
CREATE USER gold_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE gold_shop TO gold_user;
\q

# تنظیم در .env
DATABASE_URL=postgres://gold_user:secure_password@localhost:5432/gold_shop
```

### راه‌اندازی Cron Job برای به‌روزرسانی قیمت‌ها

```bash
# باز کردن crontab
crontab -e

# اضافه کردن job (هر ساعت)
0 * * * * cd /path/to/gold_shop && /path/to/venv/bin/python manage.py update_prices >> /var/log/gold_prices.log 2>&1
```

## 🧪 تست کردن سیستم

### 1. تست ربات در تلگرام

1. به ربات خود در تلگرام پیام `/start` بدهید
2. شماره تماس خود را ارسال کنید
3. در پنل ادمین، کاربر جدید را تایید کنید (`is_approved = True`)
4. دوباره `/start` بزنید - باید منوی اصلی را ببینید

### 2. تست خرید طلا

1. از منو "💰 خرید طلا" را انتخاب کنید
2. یک محصول را انتخاب کنید
3. روش محاسبه را انتخاب کنید
4. مقدار را وارد کنید (مثلا: 1.5)
5. تایید کنید

**نکته**: برای اینکه خرید موفق باشد، ابتدا باید موجودی ریالی کاربر را در پنل ادمین افزایش دهید.

### 3. افزایش موجودی تستی

در پنل ادمین:
- بخش Users > Profiles
- پروفایل کاربر را باز کنید
- `Rial balance` را روی 10000000 (ده میلیون) تنظیم کنید
- ذخیره کنید

حالا می‌توانید خرید تست کنید.

## 📋 Checklist راه‌اندازی

- [ ] Python 3.9+ نصب شده
- [ ] محیط مجازی ساخته شده
- [ ] پکیج‌ها نصب شده
- [ ] فایل .env تنظیم شده
- [ ] توکن ربات از BotFather دریافت شده
- [ ] Migrations اجرا شده
- [ ] کاربر ادمین ساخته شده
- [ ] محصولات اولیه اضافه شده
- [ ] ربات اجرا شده و پاسخ می‌دهد
- [ ] تست کامل انجام شده

## 🐛 رفع مشکلات رایج

### مشکل: ربات پاسخ نمی‌دهد

**راه‌حل**:
1. بررسی کنید ربات (`python manage.py runbot`) در حال اجرا است
2. توکن را در `.env` چک کنید
3. لاگ‌ها را بررسی کنید

### مشکل: خطای Database

**راه‌حل**:
```bash
# پاک کردن migrations و دوباره اجرا
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc" -delete
python manage.py makemigrations
python manage.py migrate
```

### مشکل: "No module named '...'"

**راه‌حل**:
```bash
# مطمئن شوید محیط مجازی فعال است
source venv/bin/activate

# نصب مجدد requirements
pip install -r requirements.txt
```

### مشکل: کاربر تایید شده اما منو نمی‌بینید

**راه‌حل**:
دوباره دستور `/start` را در ربات بزنید.

## 📞 پشتیبانی

اگر مشکلی داشتید:

1. ابتدا لاگ‌ها را بررسی کنید
2. Documentation را مطالعه کنید
3. Issue باز کنید در GitHub (اگر وجود دارد)

---

**موفق باشید!** 🚀
