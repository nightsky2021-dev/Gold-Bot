# 🏆 سیستم معاملات طلای آنلاین - Gold Shop

یک سیستم جامع و حرفه‌ای برای مدیریت معاملات طلا از طریق ربات تلگرام، ساخته شده با Django و python-telegram-bot.

## 📋 ویژگی‌ها

### برای کاربران:
- ✅ ثبت‌نام و احراز هویت با شماره تلگرام
- 💰 مشاهده قیمت‌های لحظه‌ای طلا
- 📈 ثبت سفارش خرید طلا (با دو روش: بر اساس مبلغ یا وزن)
- 📉 ثبت سفارش فروش طلا به سیستم
- 📊 مشاهده پورتفولیو (موجودی ریالی و طلا)
- 📜 مشاهده تاریخچه سفارشات

### برای مدیران:
- 🔐 پنل مدیریت قدرتمند Django
- ✅ تأیید/رد کاربران جدید
- 💼 مدیریت محصولات و قیمت‌ها
- 📦 پردازش و تأیید سفارشات
- 📊 گزارش‌گیری کامل

## 🏗️ معماری پروژه

```
gold_shop/
├── gold_shop/          # تنظیمات اصلی پروژه
│   ├── settings.py     # پیکربندی با django-environ
│   └── urls.py
├── core/               # اپلیکیشن هسته (مشترک)
├── users/              # مدیریت کاربران و پروفایل‌ها
│   ├── models.py       # مدل Profile با signals
│   ├── admin.py        # پنل ادمین کاربران
│   └── signals.py
├── trading/            # مدیریت معاملات
│   ├── models.py       # Product, Order
│   ├── services.py     # لایه سرویس (منطق تجاری)
│   ├── admin.py        # پنل ادمین معاملات
│   └── management/
│       └── commands/
│           └── update_prices.py
└── bot/                # ربات تلگرام
    ├── constants.py    # ثوابت و حالت‌های مکالمه
    └── management/
        └── commands/
            └── runbot.py  # Entry point ربات
```

## 🚀 نصب و راه‌اندازی

### پیش‌نیازها:
- Python 3.10 یا بالاتر
- PostgreSQL (اختیاری، SQLite برای توسعه کافی است)
- یک ربات تلگرام (از [@BotFather](https://t.me/botfather) دریافت کنید)

### مراحل نصب:

#### 1. کلون کردن پروژه
```bash
git clone <repository-url>
cd gold_shop
```

#### 2. ایجاد محیط مجازی
```bash
python -m venv venv

# در لینوکس/مک:
source venv/bin/activate

# در ویندوز:
venv\Scripts\activate
```

#### 3. نصب پکیج‌ها
```bash
pip install -r requirements.txt
```

#### 4. پیکربندی متغیرهای محیطی
```bash
# کپی کردن فایل نمونه
cp .env.example .env

# ویرایش .env و تنظیم مقادیر
nano .env
```

محتوای `.env`:
```env
SECRET_KEY=your-very-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Telegram Bot Token from @BotFather
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

TIME_ZONE=Asia/Tehran
```

#### 5. اجرای Migration ها
```bash
python manage.py makemigrations
python manage.py migrate
```

#### 6. ایجاد سوپریوزر
```bash
python manage.py createsuperuser
```

#### 7. ایجاد محصولات اولیه (اختیاری)
```bash
python manage.py shell
```

در shell پایتون:
```python
from trading.models import Product

Product.objects.create(
    name="سکه بهار آزادی",
    buy_price=65000000,
    sell_price=68000000,
    is_active=True
)

Product.objects.create(
    name="طلای 18 عیار",
    buy_price=2500000,
    sell_price=2600000,
    is_active=True
)

exit()
```

#### 8. اجرای سرور Django (برای پنل ادمین)
```bash
python manage.py runserver
```

پنل ادمین در: http://localhost:8000/admin

#### 9. اجرای ربات تلگرام
```bash
python manage.py runbot
```

## 📱 استفاده از ربات

### برای کاربران:

1. **شروع (/start)**
   - کاربر جدید: درخواست شماره تماس
   - ثبت‌نام و انتظار برای تأیید مدیر
   - پس از تأیید: دسترسی به منوی اصلی

2. **منوی اصلی**
   - 📈 قیمت لحظه‌ای
   - 💰 خرید طلا
   - 🛒 فروش طلا
   - 📊 پورتفولیو من
   - 📜 تاریخچه سفارشات

3. **فرآیند خرید/فروش**
   - انتخاب محصول
   - انتخاب روش محاسبه (مبلغ یا وزن)
   - وارد کردن مقدار
   - تأیید پیش‌فاکتور
   - ثبت سفارش

### برای مدیران:

1. ورود به پنل ادمین: http://localhost:8000/admin

2. **تأیید کاربران**
   - رفتن به بخش "پروفایل‌ها"
   - انتخاب کاربران در انتظار
   - استفاده از bulk action "تأیید کاربران"

3. **مدیریت محصولات**
   - افزودن محصول جدید
   - به‌روزرسانی قیمت‌ها
   - فعال/غیرفعال کردن محصولات

4. **پردازش سفارشات**
   - مشاهده سفارشات در حالت PENDING
   - بررسی جزئیات
   - استفاده از bulk action "تکمیل سفارشات"
   - موجودی‌های کاربر به صورت خودکار به‌روزرسانی می‌شود

## 🔄 به‌روزرسانی قیمت‌ها

### روش دستی:
```bash
python manage.py update_prices --dry-run  # نمایش تغییرات بدون ذخیره
python manage.py update_prices            # اعمال تغییرات
```

### زمان‌بندی خودکار (Cron Job):
```bash
# ویرایش crontab
crontab -e

# افزودن این خط برای به‌روزرسانی هر ساعت
0 * * * * cd /path/to/gold_shop && /path/to/venv/bin/python manage.py update_prices
```

## 🔧 تنظیمات پیشرفته

### استفاده از PostgreSQL (توصیه شده برای Production):

1. نصب PostgreSQL و ایجاد دیتابیس:
```bash
sudo -u postgres psql
CREATE DATABASE gold_shop;
CREATE USER gold_shop_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE gold_shop TO gold_shop_user;
\q
```

2. تغییر DATABASE_URL در `.env`:
```env
DATABASE_URL=postgres://gold_shop_user:your-password@localhost:5432/gold_shop
```

### Logging:

لاگ‌ها در `logs/gold_shop.log` ذخیره می‌شوند. برای تنظیمات بیشتر، `settings.py` را ویرایش کنید.

## 🛡️ امنیت

- ✅ همه تراکنش‌های مالی atomic هستند
- ✅ اعتبارسنجی کامل ورودی‌ها
- ✅ احراز هویت با شماره تلگرام
- ✅ تأیید دو مرحله‌ای توسط مدیر
- ⚠️ در Production حتماً DEBUG=False قرار دهید
- ⚠️ SECRET_KEY را تغییر دهید
- ⚠️ از HTTPS استفاده کنید

## 📊 بهترین شیوه‌ها (Best Practices)

1. **Separation of Concerns**: منطق تجاری در services.py
2. **Type Hinting**: تمام توابع type-annotated هستند
3. **Atomic Transactions**: عملیات مالی داخل transaction.atomic
4. **Validation**: اعتبارسنجی در سه لایه (مدل، سرویس، view)
5. **Logging**: ثبت همه رویدادهای مهم
6. **Clean Code**: کد خوانا و قابل نگهداری

## 🧪 تست

```bash
# اجرای تست‌ها
python manage.py test

# بررسی coverage
coverage run --source='.' manage.py test
coverage report
```

## 📝 توسعه‌های آتی

- [ ] یکپارچه‌سازی با API واقعی قیمت طلا (Tgju.org)
- [ ] سیستم اعلان‌های Webhook
- [ ] پشتیبانی از پرداخت آنلاین
- [ ] گزارش‌های پیشرفته و نمودارها
- [ ] API RESTful برای اپلیکیشن موبایل
- [ ] سیستم پشتیبانی چت

## 🤝 مشارکت

برای مشارکت در پروژه:
1. Fork کنید
2. یک branch جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. یک Pull Request باز کنید

## 📄 مجوز

این پروژه تحت مجوز MIT منتشر شده است.

## 📞 پشتیبانی

برای سوالات و مشکلات، یک Issue در GitHub باز کنید.

---

**توجه**: این پروژه یک نمونه آموزشی و پایه‌ای است. برای استفاده در محیط تولید (Production)، حتماً موارد امنیتی و قانونی را بررسی کنید.
