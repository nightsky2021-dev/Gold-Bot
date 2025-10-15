# 📋 خلاصه پروژه Gold Shop

## نمای کلی (Overview)

پروژه **Gold Shop** یک سیستم کامل و حرفه‌ای برای مدیریت معاملات طلای آنلاین از طریق ربات تلگرام است که با معماری تمیز، ماژولار و مقیاس‌پذیر طراحی شده است.

---

## 🎯 اهداف پروژه

✅ ساخت یک زیرساخت قدرتمند، امن و قابل توسعه  
✅ پیاده‌سازی بهترین شیوه‌های برنامه‌نویسی (Best Practices)  
✅ جداسازی مسئولیت‌ها (Separation of Concerns)  
✅ کد تمیز (Clean Code) با Type Hinting کامل  
✅ استفاده از معماری لایه‌ای (Layered Architecture)  

---

## 🏗️ معماری سیستم

### ساختار پروژه

```
gold_shop/
├── 📦 Core Layer (هسته سیستم)
│   └── gold_shop/          # تنظیمات Django
│       ├── settings.py     # پیکربندی با django-environ
│       ├── urls.py
│       └── wsgi.py/asgi.py
│
├── 📦 Domain Layer (لایه دامنه)
│   ├── users/              # مدیریت کاربران
│   │   ├── models.py       # User Profile Model
│   │   ├── signals.py      # Auto Profile Creation
│   │   └── admin.py        # Admin Interface
│   │
│   └── trading/            # مدیریت معاملات
│       ├── models.py       # Product, Order Models
│       ├── services.py     # Business Logic Layer
│       ├── admin.py        # Admin Interface
│       └── management/
│           └── commands/
│               └── update_prices.py
│
├── 📦 Presentation Layer (لایه نمایش)
│   └── bot/                # Telegram Bot Interface
│       ├── constants.py    # States & Messages
│       └── management/
│           └── commands/
│               └── runbot.py  # Bot Entry Point
│
└── 📦 Infrastructure
    ├── requirements.txt
    ├── .env.example
    ├── Dockerfile
    ├── docker-compose.yml
    └── setup_sample_data.py
```

### لایه‌بندی معماری

```
┌─────────────────────────────────────────┐
│     Presentation Layer (Bot)            │
│  - Telegram Bot Handlers                │
│  - Conversation Flows                   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     Service Layer (Business Logic)      │
│  - ProductService                       │
│  - OrderService                         │
│  - BalanceService                       │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│     Data Layer (Models)                 │
│  - Profile, Product, Order              │
│  - Database Operations                  │
└─────────────────────────────────────────┘
```

---

## 📊 مدل‌های داده (Data Models)

### 1. Profile (users/models.py)
```python
class Profile:
    - user: OneToOneField(User)
    - telegram_id: CharField (unique, indexed)
    - phone_number: CharField (unique)
    - is_approved: BooleanField
    - rial_balance: DecimalField
    - gold_balance_grams: DecimalField
    - created_at, updated_at
```

**ویژگی‌ها:**
- ✅ اتصال خودکار به User با Signals
- ✅ Validators برای موجودی‌ها
- ✅ Helper methods (can_trade, has_sufficient_balance)
- ✅ Indexes برای بهینه‌سازی Query ها

### 2. Product (trading/models.py)
```python
class Product:
    - name: CharField (unique)
    - slug: SlugField (auto-generated)
    - buy_price: DecimalField (قیمت خرید ما از مشتری)
    - sell_price: DecimalField (قیمت فروش ما به مشتری)
    - is_active: BooleanField
    - updated_at, created_at
```

**ویژگی‌ها:**
- ✅ Auto-generate slug از نام فارسی
- ✅ Helper methods (get_price_spread)
- ✅ Support برای قیمت‌گذاری پویا

### 3. Order (trading/models.py)
```python
class Order:
    - profile: ForeignKey(Profile)
    - product: ForeignKey(Product)
    - order_type: CharField (BUY/SELL)
    - quantity_grams: DecimalField
    - price_per_gram: DecimalField
    - total_amount: DecimalField
    - status: CharField (PENDING/COMPLETED/CANCELLED)
    - created_at, updated_at, completed_at
```

**ویژگی‌ها:**
- ✅ TextChoices برای order_type و status
- ✅ PROTECT constraint برای data integrity
- ✅ Helper methods (is_pending, can_be_cancelled)
- ✅ Composite indexes برای performance

---

## 🎨 ویژگی‌های کلیدی

### 1. ربات تلگرام (Telegram Bot)

**فرآیند ثبت‌نام:**
```
کاربر → /start
    ↓
آیا Profile دارد?
    │
    ├─ خیر → درخواست شماره تماس
    │           ↓
    │         ثبت User + Profile
    │           ↓
    │         انتظار برای تأیید مدیر
    │
    └─ بله → آیا تأیید شده?
                │
                ├─ خیر → پیام انتظار
                └─ بله → نمایش منوی اصلی
```

**ConversationHandler برای خرید:**
```
SELECTING_PRODUCT → SELECTING_METHOD → ENTERING_AMOUNT → CONFIRMING_BUY
```

### 2. لایه سرویس (Service Layer)

**ProductService:**
- `get_active_products()`: لیست محصولات فعال
- `get_product_by_id(id)`: دریافت محصول با ID
- `format_product_prices(product)`: فرمت قیمت‌ها برای نمایش

**OrderService:**
- `calculate_order_details()`: محاسبه جزئیات سفارش
- `create_order()`: ایجاد سفارش با transaction atomic
- `get_user_orders()`: دریافت سفارشات کاربر
- `format_order_for_display()`: فرمت سفارش برای تلگرام

**BalanceService:**
- `format_portfolio()`: نمایش پورتفولیو
- `update_balance()`: به‌روزرسانی موجودی با atomic transaction

### 3. پنل مدیریت (Admin Panel)

**ProfileAdmin:**
- ✅ نمایش اطلاعات کامل کاربر
- ✅ فیلتر بر اساس is_approved
- ✅ Bulk actions: تأیید/رد کاربران
- ✅ نمایش آمار سفارشات

**ProductAdmin:**
- ✅ ویرایش inline قیمت‌ها
- ✅ نمایش اختلاف قیمت (spread)
- ✅ فعال/غیرفعال کردن محصولات

**OrderAdmin:**
- ✅ فیلتر پیشرفته (status, type, product, date)
- ✅ Autocomplete برای profile و product
- ✅ Bulk action: تکمیل سفارشات (با atomic transaction)
- ✅ نمایش رنگی status ها

---

## 🔐 امنیت و Best Practices

### 1. امنیت
- ✅ **Atomic Transactions**: همه عملیات مالی atomic هستند
- ✅ **Input Validation**: اعتبارسنجی در model, service و view
- ✅ **Protection**: استفاده از PROTECT در ForeignKey ها
- ✅ **Environment Variables**: django-environ برای مدیریت امن
- ✅ **Logging**: ثبت همه رویدادهای مهم

### 2. کد تمیز
- ✅ **Type Hinting**: همه توابع type-annotated
- ✅ **Docstrings**: مستندسازی کامل
- ✅ **DRY Principle**: عدم تکرار کد
- ✅ **Single Responsibility**: هر کلاس/تابع یک مسئولیت
- ✅ **Service Layer**: جداسازی منطق تجاری

### 3. Performance
- ✅ **Database Indexes**: indexes بر روی فیلدهای پرکاربرد
- ✅ **Select Related**: بهینه‌سازی queries
- ✅ **Pagination**: محدودیت در تعداد نتایج
- ✅ **Caching Ready**: آماده برای cache layer

---

## 🚀 قابلیت‌های پیاده‌سازی شده

### کاربران (Users)
- [x] ثبت‌نام با شماره تلگرام
- [x] سیستم تأیید توسط مدیر
- [x] مدیریت موجودی ریالی و طلا
- [x] پنل ادمین کامل

### محصولات (Products)
- [x] مدیریت انواع محصولات طلا
- [x] قیمت‌گذاری دو طرفه (خرید/فروش)
- [x] فعال/غیرفعال کردن
- [x] Auto slug generation

### سفارشات (Orders)
- [x] ثبت سفارش خرید (2 روش: مبلغ/وزن)
- [x] ثبت سفارش فروش (2 روش: مبلغ/وزن)
- [x] پیش‌فاکتور و تأیید
- [x] پردازش توسط ادمین
- [x] به‌روزرسانی خودکار موجودی‌ها

### ربات تلگرام (Bot)
- [x] ConversationHandler پیشرفته
- [x] منوی کاربرپسند
- [x] پیام‌های فارسی با emoji
- [x] خطاهای واضح و راهنما
- [x] دکمه‌های inline و keyboard

### مدیریت (Management)
- [x] Command برای اجرای ربات
- [x] Command برای به‌روزرسانی قیمت‌ها
- [x] اسکریپت setup داده نمونه
- [x] پنل ادمین حرفه‌ای

---

## 📚 فایل‌های مستندات

| فایل | توضیحات |
|------|---------|
| `README.md` | مستندات کامل پروژه |
| `QUICKSTART.md` | راهنمای شروع سریع (5 دقیقه) |
| `DEPLOYMENT.md` | راهنمای استقرار Production |
| `PROJECT_SUMMARY.md` | این فایل - خلاصه پروژه |
| `.env.example` | نمونه تنظیمات محیطی |

---

## 🐳 Docker Support

پروژه شامل:
- ✅ `Dockerfile`: Multi-stage optimized image
- ✅ `docker-compose.yml`: Stack کامل (db, web, bot, price_updater)
- ✅ `.dockerignore`: بهینه‌سازی build
- ✅ Health checks
- ✅ Volume management

---

## 🔄 CI/CD Ready

پروژه آماده برای:
- ✅ GitHub Actions
- ✅ GitLab CI
- ✅ Jenkins
- ✅ Docker Hub
- ✅ Kubernetes

---

## 📊 آمار پروژه

```
📁 تعداد اپلیکیشن‌ها:    4 (core, users, trading, bot)
📄 تعداد مدل‌ها:         3 (Profile, Product, Order)
🔧 تعداد سرویس‌ها:       3 (Product, Order, Balance)
🤖 تعداد Bot Handlers:  10+ (start, buy, sell, portfolio, etc.)
📋 تعداد Admin Classes:  3 (Profile, Product, Order)
⚙️  Management Commands:  2 (runbot, update_prices)
📝 خطوط کد:             ~2500+ (بدون کامنت)
```

---

## 🎓 تکنولوژی‌های استفاده شده

### Backend
- **Django 4.2+**: Framework اصلی
- **Python 3.10+**: زبان برنامه‌نویسی
- **PostgreSQL**: Database (SQLite for dev)
- **django-environ**: مدیریت environment

### Telegram
- **python-telegram-bot 21+**: async/await support
- **ConversationHandler**: مدیریت جریان گفتگو

### DevOps
- **Docker**: Containerization
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Reverse proxy
- **Gunicorn**: WSGI server
- **Systemd**: Service management

---

## 🔮 توسعه‌های پیشنهادی آینده

### Phase 2
- [ ] یکپارچه‌سازی با API واقعی Tgju.org
- [ ] سیستم اعلان‌ها (Notifications)
- [ ] گزارش‌گیری پیشرفته
- [ ] Export به Excel/PDF

### Phase 3
- [ ] پرداخت آنلاین (درگاه بانکی)
- [ ] سیستم چت پشتیبانی
- [ ] اپلیکیشن موبایل (REST API)
- [ ] نمودارها و Analytics

### Phase 4
- [ ] Machine Learning برای پیش‌بینی قیمت
- [ ] سیستم referral
- [ ] Multi-language support
- [ ] White-label solution

---

## 👥 مناسب برای

✅ **تیم‌های توسعه**: معماری تمیز و قابل توسعه  
✅ **کسب‌وکارهای طلا**: راه‌حل آماده برای شروع  
✅ **دانشجویان**: یادگیری Django و Bot Development  
✅ **Freelancers**: پروژه قابل سفارشی‌سازی  

---

## 📞 پشتیبانی و مشارکت

- 🐛 **Bug Reports**: GitHub Issues
- 💡 **Feature Requests**: GitHub Discussions
- 🤝 **Contributions**: Pull Requests Welcome
- 📧 **Email**: [به README.md مراجعه کنید]

---

## 📄 لایسنس

این پروژه تحت لایسنس MIT منتشر شده است - برای جزئیات به فایل LICENSE مراجعه کنید.

---

## 🙏 تشکر

این پروژه با ❤️ و ☕ توسعه داده شده است.

از همه کسانی که در ساخت کتابخانه‌ها و ابزارهای استفاده شده مشارکت داشته‌اند، سپاسگزاریم.

---

**تاریخ ایجاد**: 2025-10-15  
**نسخه**: 1.0.0  
**وضعیت**: Production Ready ✅
