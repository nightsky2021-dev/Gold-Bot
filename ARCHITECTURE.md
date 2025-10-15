# 🏛️ معماری سیستم - System Architecture

## نمای کلی (Overview)

این پروژه از معماری **Clean Architecture** با تفکیک واضح مسئولیت‌ها (Separation of Concerns) استفاده می‌کند.

## لایه‌های معماری

```
┌─────────────────────────────────────────────────────────┐
│                   Presentation Layer                     │
│                  (Telegram Bot - bot/)                   │
│              • Handlers & Conversation Flows             │
│              • Keyboards & User Interface                │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                    Service Layer                         │
│           (Business Logic - services.py files)           │
│     • UserService • TradingService                       │
│     • Transaction Management • Validations               │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                     Data Layer                           │
│              (Models & Database - models.py)             │
│     • Profile • Product • Order                          │
│     • ORM Queries • Database Operations                  │
└─────────────────────────────────────────────────────────┘
```

## ساختار اپلیکیشن‌ها

### 1. `gold_shop/` - پروژه اصلی

**مسئولیت**: تنظیمات مرکزی و پیکربندی

```python
gold_shop/
├── settings.py      # تنظیمات Django با django-environ
├── urls.py          # URL routing اصلی
├── wsgi.py          # WSGI application
└── asgi.py          # ASGI application
```

**قابلیت‌های کلیدی**:
- مدیریت متغیرهای محیطی با `django-environ`
- تنظیمات دیتابیس (PostgreSQL/SQLite)
- تنظیمات امنیتی
- پیکربندی timezone و زبان فارسی

### 2. `users/` - مدیریت کاربران

**مسئولیت**: احراز هویت، پروفایل‌ها و موجودی‌ها

```python
users/
├── models.py        # Profile Model
├── services.py      # UserService
├── admin.py         # Admin Panel Configuration
├── signals.py       # Django Signals
└── apps.py          # App Configuration
```

#### مدل‌ها:
- **Profile**: پروفایل کاربر با ارتباط OneToOne به User
  - `telegram_id`: شناسه یکتا تلگرام
  - `phone_number`: شماره تماس
  - `is_approved`: وضعیت تایید توسط ادمین
  - `rial_balance`: موجودی ریالی
  - `gold_balance_grams`: موجودی طلا (گرم)

#### سرویس‌ها:
- `UserService.create_user_from_telegram()`: ثبت‌نام کاربر جدید
- `UserService.check_user_approval_status()`: بررسی وضعیت تایید

### 3. `trading/` - مدیریت معاملات

**مسئولیت**: محصولات، قیمت‌ها و سفارشات

```python
trading/
├── models.py              # Product & Order Models
├── services.py            # TradingService
├── admin.py               # Admin Panel
└── management/
    └── commands/
        └── update_prices.py  # Price Update Command
```

#### مدل‌ها:

**Product** (محصول):
- `name`: نام محصول (مثلا: طلای 18 عیار)
- `slug`: اسلاگ برای URL
- `buy_price`: قیمت خرید ما از مشتری
- `sell_price`: قیمت فروش ما به مشتری
- `is_active`: وضعیت فعال بودن

**Order** (سفارش):
- `profile`: کاربر سفارش‌دهنده
- `product`: محصول
- `order_type`: نوع (BUY/SELL)
- `quantity_grams`: مقدار به گرم
- `price_per_gram`: قیمت لحظه ثبت
- `total_amount`: مبلغ کل
- `status`: وضعیت (PENDING/COMPLETED/CANCELLED)

#### سرویس‌ها:
- `TradingService.get_active_products()`: دریافت محصولات فعال
- `TradingService.calculate_buy_details()`: محاسبه جزئیات خرید
- `TradingService.calculate_sell_details()`: محاسبه جزئیات فروش
- `TradingService.create_buy_order()`: ثبت سفارش خرید
- `TradingService.create_sell_order()`: ثبت سفارش فروش
- `TradingService.get_user_recent_orders()`: دریافت سفارشات اخیر

### 4. `bot/` - ربات تلگرام

**مسئولیت**: رابط کاربری و تعامل با کاربر

```python
bot/
├── constants.py           # ثوابت و States
├── keyboards.py          # کیبوردها (Reply & Inline)
├── utils.py              # توابع کمکی
└── management/
    └── commands/
        └── runbot.py     # ربات اصلی
```

#### جریان‌های کاری (Conversation Flows):

**جریان ثبت‌نام**:
```
/start → درخواست شماره تماس → ثبت در دیتابیس → انتظار تایید ادمین
```

**جریان خرید**:
```
انتخاب خرید → انتخاب محصول → انتخاب روش (گرم/ریال) 
→ وارد کردن مقدار → نمایش پیش‌فاکتور → تایید → ثبت سفارش
```

**جریان فروش**:
```
انتخاب فروش → بررسی موجودی → انتخاب محصول → انتخاب روش 
→ وارد کردن مقدار → بررسی کفایت موجودی → تایید → ثبت سفارش
```

## جریان داده (Data Flow)

### مثال: خرید طلا

```
1. User: کلیک روی "💰 خرید طلا"
   ↓
2. Bot Handler (buy_start):
   - بررسی احراز هویت
   - دریافت محصولات فعال از TradingService
   - نمایش کیبورد محصولات
   ↓
3. User: انتخاب محصول
   ↓
4. Bot Handler (buy_product_selected):
   - ذخیره محصول در context
   - نمایش کیبورد روش محاسبه
   ↓
5. User: انتخاب روش (گرم/ریال)
   ↓
6. Bot Handler (buy_method_selected):
   - ذخیره روش در context
   - درخواست ورود مقدار
   ↓
7. User: وارد کردن مقدار (مثلا: 2.5)
   ↓
8. Bot Handler (buy_amount_entered):
   - Validation ورودی
   - فراخوانی TradingService.calculate_buy_details()
   - نمایش پیش‌فاکتور
   ↓
9. User: تایید نهایی
   ↓
10. Bot Handler (buy_confirmed):
    - فراخوانی TradingService.create_buy_order()
    - ثبت Order با status=PENDING
    - نمایش پیام موفقیت
    ↓
11. Admin: بررسی و تایید سفارش در پنل ادمین
    ↓
12. System: به‌روزرسانی موجودی‌ها با transaction.atomic()
```

## امنیت (Security)

### لایه‌های امنیتی:

1. **احراز هویت**:
   - شناسایی از طریق Telegram ID
   - تایید دو مرحله‌ای (ثبت‌نام + تایید ادمین)
   - بررسی `is_approved` در هر عملیات

2. **اعتبارسنجی ورودی**:
   - استفاده از Django Validators
   - بررسی نوع داده‌ها
   - محدودیت مقادیر (MinValueValidator)

3. **تراکنش‌های ایمن**:
   - استفاده از `@transaction.atomic`
   - Rollback خودکار در صورت خطا
   - جلوگیری از Race Conditions

4. **حفاظت از داده‌ها**:
   - استفاده از متغیرهای محیطی
   - عدم ذخیره اطلاعات حساس در کد
   - Logging امن (بدون لاگ کردن توکن‌ها)

## قابلیت مقیاس‌پذیری (Scalability)

### فعلی:
- تک سرور
- SQLite/PostgreSQL
- Polling mode برای ربات

### پیشنهادات برای مقیاس بزرگ:
1. **دیتابیس**:
   - استفاده از PostgreSQL با Connection Pooling
   - Redis برای Cache
   - Read Replicas

2. **ربات**:
   - استفاده از Webhook به جای Polling
   - Load Balancer برای چند نمونه ربات
   - Message Queue (Celery) برای کارهای سنگین

3. **Application**:
   - Container Orchestration (Kubernetes)
   - Horizontal Scaling
   - CDN برای فایل‌های استاتیک

## نمونه کد استفاده از سرویس‌ها

```python
# مثال 1: ثبت‌نام کاربر جدید
from users.services import UserService

user, profile, created = UserService.create_user_from_telegram(
    telegram_id="123456789",
    phone_number="09123456789",
    telegram_username="user123",
    first_name="علی",
    last_name="محمدی"
)

# مثال 2: ثبت سفارش خرید
from trading.services import TradingService
from decimal import Decimal

# محاسبه جزئیات
quantity_grams, total_amount = TradingService.calculate_buy_details(
    product=product,
    amount_type='gram',
    amount=Decimal('2.5')
)

# ثبت سفارش
order = TradingService.create_buy_order(
    profile=profile,
    product=product,
    quantity_grams=quantity_grams,
    total_amount=total_amount
)
```

## تست‌پذیری (Testability)

معماری لایه‌بندی شده این مزایا را دارد:

1. **Unit Testing**: تست سرویس‌ها به صورت مستقل
2. **Integration Testing**: تست جریان کامل
3. **Mocking**: Mock کردن لایه‌های پایین‌تر
4. **Isolation**: هر لایه مستقل از دیگری

```python
# مثال Unit Test
from django.test import TestCase
from users.services import UserService

class UserServiceTest(TestCase):
    def test_create_user_from_telegram(self):
        user, profile, created = UserService.create_user_from_telegram(
            telegram_id="test_123",
            phone_number="09121234567"
        )
        self.assertTrue(created)
        self.assertEqual(profile.telegram_id, "test_123")
```

## نتیجه‌گیری

این معماری مزایای زیر را دارد:

✅ **قابلیت نگهداری**: کد تمیز و سازمان‌یافته
✅ **مقیاس‌پذیری**: آماده برای رشد
✅ **امنیت**: چندین لایه حفاظتی
✅ **تست‌پذیری**: جدا کردن منطق تجاری
✅ **انعطاف‌پذیری**: تغییر آسان در هر لایه
✅ **خوانایی**: ساختار واضح و مستند
