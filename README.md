# 🏆 سامانه معاملات طلای آنلاین - Gold Shop Trading System

یک سیستم پیشرفته و کامل برای معاملات طلا در ایران با ربات تلگرام، ساخته شده با Django و Python Telegram Bot.

## 📋 فهرست مطالب

- [ویژگی‌های کلیدی](#ویژگی‌های-کلیدی)
- [معماری پروژه](#معماری-پروژه)
- [پیش‌نیازها](#پیش‌نیازها)
- [نصب و راه‌اندازی](#نصب-و-راه‌اندازی)
- [استفاده](#استفاده)
- [مستندات API](#مستندات-api)
- [مدیریت قیمت‌ها](#مدیریت-قیمت‌ها)
- [Deployment](#deployment)

## 🌟 ویژگی‌های کلیدی

### ✨ قابلیت‌های کاربر
- ✅ ثبت‌نام و احراز هویت از طریق تلگرام
- 💰 خرید و فروش طلا با قیمت‌های لحظه‌ای
- 📊 مشاهده پورتفولیوی شخصی (موجودی ریال و طلا)
- 📜 تاریخچه سفارشات
- 📈 مشاهده قیمت‌های لحظه‌ای انواع طلا
- 🔄 سیستم تایید سفارشات توسط ادمین

### 🛠️ قابلیت‌های مدیریتی
- 👥 مدیریت کاربران و تایید حساب‌ها
- 📦 مدیریت محصولات (انواع طلا)
- 💵 تنظیم قیمت‌های خرید و فروش
- 📋 مدیریت سفارشات و تغییر وضعیت
- 📊 پنل ادمین Django با UI فارسی

### 🔧 ویژگی‌های تکنیکال
- 🏗️ معماری Clean Architecture با لایه‌های جدا
- 🔐 امنیت بالا با احراز هویت چند مرحله‌ای
- 💾 استفاده از SQLite (پیش‌فرض) با امکان تغییر به PostgreSQL
- ⚡ عملیات Atomic برای تراکنش‌های مالی
- 📝 Type Hinting کامل
- 🧪 قابلیت تست‌پذیری بالا
- 🔄 به‌روزرسانی خودکار قیمت‌ها با Cron Job

## 🏛️ معماری پروژه

```
gold_shop/
├── gold_shop/              # تنظیمات اصلی پروژه
│   ├── settings.py         # تنظیمات با django-environ
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── users/                  # مدیریت کاربران
│   ├── models.py          # مدل Profile
│   ├── admin.py           # پنل ادمین
│   ├── services.py        # منطق تجاری
│   └── signals.py         # سیگنال‌های Django
├── trading/                # مدیریت معاملات
│   ├── models.py          # مدل‌های Product و Order
│   ├── admin.py           # پنل ادمین
│   ├── services.py        # منطق معاملات
│   └── management/
│       └── commands/
│           └── update_prices.py
├── bot/                    # ربات تلگرام
│   ├── constants.py       # ثوابت
│   ├── keyboards.py       # کیبوردها
│   ├── utils.py           # توابع کمکی
│   └── management/
│       └── commands/
│           └── runbot.py  # Command اجرای ربات
├── requirements.txt
├── .env.example
└── README.md
```

### تفکیک مسئولیت‌ها (Separation of Concerns)

- **users**: مدیریت کاربران، پروفایل‌ها و احراز هویت
- **trading**: منطق معاملات، محصولات و سفارشات
- **bot**: لایه نمایش (Presentation Layer) - ربات تلگرام
- **services.py**: لایه سرویس برای منطق تجاری

## 📦 پیش‌نیازها

- Python 3.9 یا بالاتر
- SQLite (پیش‌فرض - نیازی به نصب نیست)
- PostgreSQL 12 یا بالاتر (اختیاری)
- یک Bot Token از [@BotFather](https://t.me/BotFather) در تلگرام

## 🚀 نصب و راه‌اندازی

### 1. کلون کردن پروژه

```bash
git clone <repository-url>
cd gold_shop
```

### 2. ساخت محیط مجازی

```bash
python -m venv venv

# فعال‌سازی در Linux/Mac:
source venv/bin/activate

# فعال‌سازی در Windows:
venv\Scripts\activate
```

### 3. نصب پکیج‌ها

```bash
pip install -r requirements.txt
```

### 4. تنظیم متغیرهای محیطی

```bash
# کپی کردن فایل نمونه
cp .env.example .env

# ویرایش فایل .env و تنظیم مقادیر
nano .env
```

مقادیر ضروری در `.env`:

```env
SECRET_KEY=your-secure-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (برای PostgreSQL)
DATABASE_URL=postgres://user:password@localhost:5432/gold_shop

# یا برای SQLite (development)
# DATABASE_URL=sqlite:///db.sqlite3

TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

LANGUAGE_CODE=fa-ir
TIME_ZONE=Asia/Tehran
```

### 5. اجرای Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. ایجاد کاربر ادمین

```bash
python manage.py createsuperuser
```

### 7. ایجاد محصولات نمونه (اختیاری)

وارد پنل ادمین شوید (`http://localhost:8000/admin/`) و محصولات را اضافه کنید:

- طلای 18 عیار
- طلای 24 عیار
- سکه تمام بهار آزادی
- نیم سکه

## 💻 استفاده

### اجرای ربات تلگرام

```bash
python manage.py runbot
```

### اجرای سرور Django (در ترمینال جداگانه)

```bash
python manage.py runserver
```

### دسترسی به پنل ادمین

مرورگر خود را باز کنید و به آدرس زیر بروید:

```
http://localhost:8000/admin/
```

## 🤖 دستورات ربات تلگرام

### برای کاربران

- `/start` - شروع و ثبت‌نام / ورود
- `📈 قیمت لحظه‌ای` - مشاهده قیمت‌های فعلی
- `💰 خرید طلا` - شروع فرآیند خرید
- `🛒 فروش طلا` - شروع فرآیند فروش
- `📊 پورتفولیو من` - مشاهده موجودی
- `📜 تاریخچه سفارشات` - مشاهده سفارشات قبلی

### جریان خرید/فروش

1. کاربر گزینه خرید/فروش را انتخاب می‌کند
2. محصول مورد نظر را انتخاب می‌کند
3. روش محاسبه (گرم یا ریال) را انتخاب می‌کند
4. مقدار را وارد می‌کند
5. پیش‌فاکتور نمایش داده می‌شود
6. تایید نهایی
7. سفارش ثبت می‌شود و در انتظار تایید ادمین قرار می‌گیرد

## 🔄 مدیریت قیمت‌ها

### به‌روزرسانی دستی قیمت‌ها

از طریق پنل ادمین Django قیمت‌ها را به‌روزرسانی کنید.

### به‌روزرسانی خودکار قیمت‌ها

```bash
# اجرای دستی
python manage.py update_prices

# آزمایش بدون ذخیره (Dry Run)
python manage.py update_prices --dry-run
```

### راه‌اندازی Cron Job

برای به‌روزرسانی خودکار هر ساعت:

```bash
# ویرایش crontab
crontab -e

# افزودن خط زیر
0 * * * * cd /path/to/gold_shop && /path/to/venv/bin/python manage.py update_prices >> /var/log/gold_shop_prices.log 2>&1
```

## 🔐 امنیت

### بهترین شیوه‌های امنیتی پیاده‌سازی شده:

1. ✅ احراز هویت دو مرحله‌ای (تلگرام + تایید ادمین)
2. ✅ استفاده از متغیرهای محیطی برای اطلاعات حساس
3. ✅ Validators برای تمام ورودی‌های کاربر
4. ✅ تراکنش‌های Atomic برای عملیات مالی
5. ✅ محافظت CSRF در Django
6. ✅ SQL Injection Prevention با ORM
7. ✅ Rate Limiting (پیشنهاد می‌شود در production)

### نکات امنیتی برای Production:

```python
# در settings.py:
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 📊 مدیریت دیتابیس

### Backup گرفتن

```bash
# PostgreSQL
pg_dump gold_shop > backup.sql

# SQLite
cp db.sqlite3 backup_$(date +%Y%m%d).sqlite3
```

### Restore کردن

```bash
# PostgreSQL
psql gold_shop < backup.sql

# SQLite
cp backup.sqlite3 db.sqlite3
```

## 🚢 Deployment

### آماده‌سازی برای Production

1. تنظیم `DEBUG=False` در `.env`
2. تنظیم `ALLOWED_HOSTS` با دامنه واقعی
3. استفاده از PostgreSQL به جای SQLite
4. راه‌اندازی HTTPS
5. جمع‌آوری فایل‌های استاتیک:

```bash
python manage.py collectstatic --noinput
```

6. استفاده از Gunicorn یا uWSGI برای WSGI Server:

```bash
pip install gunicorn
gunicorn gold_shop.wsgi:application --bind 0.0.0.0:8000
```

7. راه‌اندازی Nginx به عنوان Reverse Proxy
8. استفاده از Supervisor یا systemd برای مدیریت process ها

### مثال Service برای systemd

```ini
# /etc/systemd/system/goldshop-bot.service
[Unit]
Description=Gold Shop Telegram Bot
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/gold_shop
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python manage.py runbot
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable goldshop-bot
sudo systemctl start goldshop-bot
```

## 🧪 تست

```bash
# اجرای تست‌ها
python manage.py test

# با coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 لاگ‌ها

لاگ‌ها در فایل‌های زیر ذخیره می‌شوند:

- ربات تلگرام: کنسول یا فایل لاگ مشخص شده
- Django: در `DEBUG=True` در کنسول، در production باید به فایل یا سرویس لاگ‌گیری فرستاده شود

## 🤝 مشارکت

برای مشارکت در پروژه:

1. Fork کنید
2. یک Branch جدید بسازید (`git checkout -b feature/amazing-feature`)
3. تغییرات را Commit کنید (`git commit -m 'Add some amazing feature'`)
4. Push به Branch کنید (`git push origin feature/amazing-feature`)
5. یک Pull Request باز کنید

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## 👨‍💻 نویسنده

ساخته شده با ❤️ برای جامعه توسعه‌دهندگان ایرانی

## 🙏 تشکر

- Django Framework
- Python Telegram Bot
- جامعه Open Source

---

**نکته**: این یک سیستم آموزشی/نمونه است. برای استفاده در محیط واقعی حتما:
- از یک API معتبر برای قیمت‌های طلا استفاده کنید
- سیستم پرداخت امن پیاده‌سازی کنید
- با یک وکیل مشورت کنید برای مسائل قانونی معاملات
- امنیت را در اولویت قرار دهید
