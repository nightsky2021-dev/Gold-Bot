# ⚡ شروع سریع - Quick Start

## 🎯 راه‌اندازی در 10 دقیقه

### گام 1: کلون و نصب (2 دقیقه)

```bash
# اجرای اسکریپت خودکار
bash setup.sh
```

**یا به صورت دستی**:

```bash
# ساخت محیط مجازی
python3 -m venv venv
source venv/bin/activate

# نصب پکیج‌ها
pip install -r requirements.txt
```

### گام 2: تنظیم محیط (1 دقیقه)

```bash
# کپی فایل .env
cp .env.example .env

# ویرایش و تنظیم توکن
nano .env
```

**مهم**: حداقل `TELEGRAM_BOT_TOKEN` را تنظیم کنید:
- به [@BotFather](https://t.me/BotFather) پیام `/newbot` بدهید
- توکن دریافتی را در `.env` قرار دهید

### گام 3: راه‌اندازی دیتابیس (2 دقیقه)

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### گام 4: ایجاد محصولات (3 دقیقه)

```bash
# اجرای سرور
python manage.py runserver
```

در مرورگر به `http://localhost:8000/admin/` بروید و محصولات زیر را اضافه کنید:

| نام | قیمت خرید | قیمت فروش |
|-----|-----------|-----------|
| طلای 18 عیار | 2500000 | 2550000 |
| طلای 24 عیار | 3300000 | 3350000 |

### گام 5: اجرای ربات (1 دقیقه)

```bash
# در ترمینال جدید
python manage.py runbot
```

### گام 6: تست (1 دقیقه)

1. در تلگرام به ربات خود پیام `/start` بدهید
2. شماره تماس را ارسال کنید
3. در پنل ادمین کاربر را تایید کنید (`is_approved = True`)
4. دوباره `/start` بزنید
5. از منو "قیمت لحظه‌ای" را انتخاب کنید

🎉 **تبریک! سیستم شما آماده است.**

---

## 🐳 استفاده از Docker (آلترناتیو)

اگر Docker دارید:

```bash
# ساخت و اجرای کانتینرها
docker-compose up -d

# ایجاد migrations
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate

# ساخت superuser
docker-compose exec web python manage.py createsuperuser
```

پنل ادمین: `http://localhost:8000/admin/`

---

## 📝 چک‌لیست تست

- [ ] ربات پاسخ می‌دهد به `/start`
- [ ] ثبت‌نام با شماره تماس کار می‌کند
- [ ] تایید کاربر در پنل ادمین کار می‌کند
- [ ] منوی اصلی نمایش داده می‌شود
- [ ] قیمت‌های لحظه‌ای نمایش داده می‌شود
- [ ] خرید طلا کار می‌کند (بعد از افزایش موجودی ریالی)
- [ ] پورتفولیو صحیح نمایش داده می‌شود

---

## 🔧 تنظیمات اختیاری

### استفاده از PostgreSQL

```bash
# نصب PostgreSQL
sudo apt install postgresql

# ساخت دیتابیس
sudo -u postgres createdb gold_shop

# تنظیم در .env
DATABASE_URL=postgres://postgres:password@localhost:5432/gold_shop
```

### راه‌اندازی Cron برای قیمت‌ها

```bash
crontab -e

# هر ساعت
0 * * * * cd /path/to/gold_shop && /path/to/venv/bin/python manage.py update_prices
```

---

## ❓ مشکل رایج

### "Bot doesn't respond"
- بررسی کنید ربات در حال اجرا است
- توکن را چک کنید
- لاگ‌ها را بررسی کنید

### "Permission denied"
```bash
chmod +x setup.sh
chmod +x test_project.py
```

### "Module not found"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

## 📚 مستندات بیشتر

- [README.md](README.md) - مستندات کامل
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - راهنمای تفصیلی
- [ARCHITECTURE.md](ARCHITECTURE.md) - معماری سیستم

---

**موفق باشید!** 🚀

