# 🪙 سیستم معاملات طلای آنلاین با ربات تلگرام

یک سیستم کامل بک‌اند و ربات تلگرامی برای معاملات طلا با معماری تمیز و مقیاس‌پذیر.

## 📋 ویژگی‌ها

- ✅ ثبت‌نام و احراز هویت کاربران از طریق تلگرام
- ✅ سیستم تایید کاربران توسط ادمین
- ✅ مدیریت موجودی ریالی و طلای کاربران
- ✅ ثبت سفارشات خرید و فروش طلا
- ✅ محاسبه خودکار بر اساس ریال یا گرم
- ✅ پنل مدیریت قدرتمند Django
- ✅ ربات تلگرامی با رابط کاربری ساده و کارآمد
- ✅ معماری ماژولار و قابل توسعه
- ✅ استفاده از Type Hinting و Clean Code
- ✅ تراکنش‌های اتمی برای امنیت داده‌ها

## 🏗️ معماری پروژه

```
gold_shop/
├── core/                   # تنظیمات مرکزی پروژه
│   ├── settings.py        # تنظیمات با django-environ
│   ├── urls.py
│   └── wsgi.py
│
├── users/                  # مدیریت کاربران و پروفایل‌ها
│   ├── models.py          # مدل Profile
│   ├── admin.py           # پنل مدیریت کاربران
│   └── services.py        # لایه سرویس کاربران
│
├── trading/                # مدیریت محصولات و سفارشات
│   ├── models.py          # مدل‌های Product و Order
│   ├── admin.py           # پنل مدیریت معاملات
│   └── services.py        # منطق تجاری معاملات
│
├── bot/                    # ربات تلگرام
│   ├── constants.py       # ثوابت و پیام‌های ربات
│   ├── management/
│   │   └── commands/
│   │       ├── runbot.py          # اجرای ربات
│   │       └── update_prices.py   # به‌روزرسانی قیمت‌ها
│
├── requirements.txt        # وابستگی‌های پروژه
├── .env                    # متغیرهای محیطی (نباید commit شود)
└── .env.example            # نمونه متغیرهای محیطی
```

## 🚀 راه‌اندازی پروژه

### 1. پیش‌نیازها

- Python 3.10 یا بالاتر
- PostgreSQL (اختیاری، برای پروداکشن)
- یک ربات تلگرام (از [@BotFather](https://t.me/botfather) دریافت کنید)

### 2. نصب

```bash
# کلون پروژه
git clone <repository-url>
cd gold_shop

# ایجاد محیط مجازی
python -m venv venv
source venv/bin/activate  # در ویندوز: venv\Scripts\activate

# نصب وابستگی‌ها
pip install -r requirements.txt

# کپی فایل محیطی
cp .env.example .env
```

### 3. تنظیمات

فایل `.env` را ویرایش کرده و مقادیر زیر را تنظیم کنید:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather

# برای استفاده از PostgreSQL:
DATABASE_URL=postgres://user:password@localhost:5432/dbname
```

### 4. مهاجرت دیتابیس و ایجاد سوپریوزر

```bash
# اجرای مهاجرت‌ها
python manage.py makemigrations
python manage.py migrate

# ایجاد سوپریوزر
python manage.py createsuperuser
```

### 5. ایجاد محصولات نمونه

پس از ورود به پنل ادمین (`http://localhost:8000/admin/`), محصولات طلا را اضافه کنید:

- طلای 18 عیار (slug: tala-18-ayar)
- طلای 24 عیار (slug: tala-24-ayar)
- سکه بهار آزادی (slug: sekeh-bahar-azadi)

### 6. اجرای پروژه

```bash
# اجرای سرور Django
python manage.py runserver

# در ترمینال دیگر، اجرای ربات تلگرام
python manage.py runbot
```

## 🤖 استفاده از ربات تلگرام

### جریان کار کاربر:

1. **ثبت‌نام**: `/start` → اشتراک‌گذاری شماره تماس
2. **انتظار تایید**: ادمین باید کاربر را در پنل مدیریت تایید کند
3. **منوی اصلی** (پس از تایید):
   - 📈 قیمت لحظه‌ای
   - 💰 خرید طلا
   - 🛒 فروش طلا
   - 📊 پورتفولیو من
   - 📜 تاریخچه سفارشات

### جریان خرید/فروش:

1. انتخاب محصول
2. انتخاب روش محاسبه (ریال یا گرم)
3. وارد کردن مقدار
4. تایید پیش‌فاکتور
5. ثبت سفارش (منتظر تایید ادمین)

## 👨‍💼 پنل مدیریت

### تایید کاربران:
1. به `Users → Profiles` بروید
2. کاربر را انتخاب کنید
3. گزینه "تأیید شده" را فعال کنید

### مدیریت سفارشات:
1. به `Trading → Orders` بروید
2. سفارشات در انتظار را مشاهده کنید
3. استفاده از Action "تایید و پردازش سفارشات انتخاب شده"
   - این عملیات به صورت خودکار موجودی کاربر را به‌روزرسانی می‌کند

### به‌روزرسانی قیمت‌ها:
```bash
# دستی
python manage.py update_prices

# برای تست (بدون ذخیره تغییرات)
python manage.py update_prices --dry-run
```

### تنظیم Cron Job برای به‌روزرسانی خودکار:
```bash
# ویرایش crontab
crontab -e

# اضافه کردن: هر 30 دقیقه یکبار
*/30 * * * * cd /path/to/project && /path/to/venv/bin/python manage.py update_prices >> /var/log/gold_shop_prices.log 2>&1
```

## 🔒 امنیت

- ✅ استفاده از `transaction.atomic()` برای عملیات‌های حساس
- ✅ اعتبارسنجی ورودی‌های کاربر
- ✅ محافظت در برابر موجودی منفی
- ✅ استفاده از `select_for_update()` برای جلوگیری از race conditions
- ✅ جداسازی کامل منطق تجاری در لایه سرویس

## 📊 مدل‌های پایگاه داده

### Profile (users app)
- کاربر (OneToOne به User)
- شناسه و نام کاربری تلگرام
- شماره تماس
- وضعیت تایید
- موجودی ریالی و طلا

### Product (trading app)
- نام و slug محصول
- قیمت خرید و فروش
- وضعیت فعال/غیرفعال

### Order (trading app)
- پروفایل کاربر و محصول
- نوع سفارش (خرید/فروش)
- مقدار و قیمت
- وضعیت (در انتظار/تکمیل شده/لغو شده)

## 🛠️ توسعه و سفارشی‌سازی

### افزودن API واقعی برای قیمت‌ها:
فایل `bot/management/commands/update_prices.py` را ویرایش کنید:

```python
def fetch_prices_from_api(self):
    import requests
    response = requests.get('https://your-api.com/prices')
    data = response.json()
    return self.parse_api_response(data)
```

### افزودن قابلیت‌های جدید به ربات:
1. ثوابت را در `bot/constants.py` تعریف کنید
2. هندلرها را در `bot/management/commands/runbot.py` اضافه کنید
3. منطق تجاری را در `services.py` مربوطه پیاده‌سازی کنید

## 🧪 تست

```bash
# اجرای تست‌ها
python manage.py test

# بررسی کد با flake8 (نصب: pip install flake8)
flake8 .

# بررسی Type hints (نصب: pip install mypy)
mypy .
```

## 📝 TODO و پیشنهادات

- [ ] افزودن تست‌های واحد (Unit Tests)
- [ ] پیاده‌سازی API RESTful با Django REST Framework
- [ ] افزودن سیستم نوتیفیکیشن (اطلاع‌رسانی تایید سفارش)
- [ ] افزودن لاگ‌های دقیق‌تر
- [ ] پیاده‌سازی کش با Redis
- [ ] افزودن گزارشات و آمار برای ادمین
- [ ] پشتیبانی از چند ارز
- [ ] افزودن محدودیت نرخ (Rate Limiting)

## 🤝 مشارکت

برای مشارکت در پروژه:
1. Fork کنید
2. برنچ جدید بسازید (`git checkout -b feature/AmazingFeature`)
3. تغییرات را commit کنید (`git commit -m 'Add some AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request ایجاد کنید

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## 💬 پشتیبانی

برای سوالات و پشتیبانی، یک Issue در GitHub ایجاد کنید.

---

**ساخته شده با ❤️ برای جامعه توسعه‌دهندگان ایرانی**
