# راهنمای راه‌اندازی سیستم قیمت‌گذاری خودکار

این راهنما مراحل راه‌اندازی سیستم قیمت‌گذاری خودکار با استفاده از API Navasan را شرح می‌دهد.

## 📋 فهرست مطالب

1. [نصب کتابخانه‌های مورد نیاز](#نصب-کتابخانه‌ها)
2. [تنظیمات API](#تنظیمات-api)
3. [ایجاد migrations](#ایجاد-migrations)
4. [ایجاد محصولات پایه](#ایجاد-محصولات)
5. [به‌روزرسانی قیمت‌ها](#به‌روزرسانی-قیمت‌ها)
6. [نمایش قیمت‌ها در ربات](#نمایش-در-ربات)

---

## 1. نصب کتابخانه‌های مورد نیاز {#نصب-کتابخانه‌ها}

```bash
pip install -r requirements.txt
```

کتابخانه `requests` به requirements.txt اضافه شده است.

---

## 2. تنظیمات API {#تنظیمات-api}

### فایل `.env`

API Key را در فایل `.env` تنظیم کنید:

```env
NAVASAN_API_KEY=freeTET7c1g57cU7kPnjQa4KAMP7BWaS
```

اگر فایل `.env` ندارید، از `.env.example` کپی بگیرید:

```bash
cp .env.example .env
```

### تغییر API Provider (اختیاری)

اگر در آینده می‌خواهید API دیگری استفاده کنید:

1. یک کلاس جدید از `PriceProvider` در `trading/price_providers.py` بسازید
2. متد `get_active_provider()` را به‌روز کنید

مثال:

```python
class MyCustomProvider(PriceProvider):
    def get_gold_price(self) -> Optional[Decimal]:
        # پیاده‌سازی شما
        pass
    # ...

def get_active_provider() -> PriceProvider:
    # برای استفاده از provider جدید:
    return MyCustomProvider()
```

---

## 3. ایجاد Migrations {#ایجاد-migrations}

فیلد `product_code` به مدل `Product` اضافه شده است. باید migration بسازید:

```bash
python manage.py makemigrations trading
python manage.py migrate
```

---

## 4. ایجاد محصولات پایه {#ایجاد-محصولات}

برای ایجاد محصولات پایه (طلای آبشده، سکه تمام، دلار):

```bash
python setup_products.py
```

این اسکریپت:
- ✅ محصولات پایه را ایجاد می‌کند
- ✅ قیمت‌ها را از API دریافت و به‌روز می‌کند
- ✅ قیمت‌های فعلی را نمایش می‌دهد

### ایجاد دستی محصولات (از طریق Django Admin)

اگر ترجیح می‌دهید دستی محصولات را بسازید:

1. وارد پنل ادمین شوید: `http://127.0.0.1:8000/admin`
2. به بخش "محصولات" بروید
3. سه محصول زیر را ایجاد کنید:

| کد محصول | نام | قیمت اولیه |
|----------|-----|------------|
| `GOLD_ABSHODEH` | طلای آبشده (هر گرم) | 0 |
| `COIN_FULL` | سکه تمام غیربانکی | 0 |
| `DOLLAR` | دلار آمریکا | 0 |

---

## 5. به‌روزرسانی قیمت‌ها {#به‌روزرسانی-قیمت‌ها}

### به‌روزرسانی دستی

```bash
# به‌روزرسانی ساده
python manage.py update_prices

# با نمایش جزئیات
python manage.py update_prices --show-details
```

### به‌روزرسانی خودکار (Cron Job)

برای به‌روزرسانی خودکار هر 5 دقیقه:

#### در Linux/Mac:

```bash
# ویرایش crontab
crontab -e

# اضافه کردن این خط:
*/5 * * * * cd /path/to/Gold_bot && /path/to/venv/bin/python manage.py update_prices
```

#### در Windows (Task Scheduler):

1. Task Scheduler را باز کنید
2. یک Task جدید ایجاد کنید:
   - **Trigger**: هر 5 دقیقه
   - **Action**: اجرای `python manage.py update_prices`
   - **Working Directory**: مسیر پروژه

---

## 6. نمایش قیمت‌ها در ربات {#نمایش-در-ربات}

قیمت‌ها به صورت زیر در ربات نمایش داده می‌شوند:

```
📈 قیمت‌های لحظه‌ای

🪙 طلای آبشده (هر گرم)
   💰 قیمت خرید از شما: X,XXX,XXX ریال
   💵 قیمت فروش به شما: X,XXX,XXX ریال

🥇 سکه تمام غیربانکی
   💰 قیمت خرید از شما: XX,XXX,XXX ریال
   💵 قیمت فروش به شما: XX,XXX,XXX ریال

💵 دلار آمریکا
   💰 قیمت خرید از شما: XXX,XXX ریال
   💵 قیمت فروش به شما: XXX,XXX ریال
```

---

## 📐 فرمول‌های قیمت‌گذاری

سیستم از فرمول‌های زیر استفاده می‌کند:

### طلای آبشده (هر گرم)
- **قیمت خرید**: `قیمت API - 300,000 ریال`
- **قیمت فروش**: `قیمت API + 300,000 ریال`

### سکه تمام غیربانکی
- **قیمت پایه**: `قیمت طلا × 9.573`
- **قیمت خرید**: `قیمت پایه - 4,500,000 ریال`
- **قیمت فروش**: `قیمت پایه + 4,500,000 ریال`

### دلار آمریکا
- **قیمت خرید**: `قیمت خرید API - 10,000 ریال`
- **قیمت فروش**: `قیمت فروش API + 10,000 ریال`

---

## 🔧 عیب‌یابی

### خطا: "no such table: trading_product"

```bash
python manage.py migrate
```

### خطا: "Product matching query does not exist"

```bash
python setup_products.py
```

### قیمت‌ها صفر هستند

```bash
python manage.py update_prices
```

### خطا در دریافت از API

1. بررسی اتصال به اینترنت
2. بررسی صحت API Key در `.env`
3. بررسی لاگ‌ها:
   ```bash
   # در کنسول ربات یا Django server
   ```

---

## 📚 ماژول‌های کلیدی

### `trading/price_providers.py`
ارائه‌دهندگان API (قابل تعویض)

### `trading/price_calculator.py`
محاسبه‌گر قیمت‌های نهایی با فرمول‌ها

### `trading/services.py`
لایه سرویس برای به‌روزرسانی قیمت‌ها

### `trading/management/commands/update_prices.py`
دستور Management برای به‌روزرسانی

---

## ✅ چک‌لیست راه‌اندازی

- [ ] نصب requirements
- [ ] تنظیم API Key در `.env`
- [ ] اجرای migrations
- [ ] اجرای `python setup_products.py`
- [ ] تست به‌روزرسانی: `python manage.py update_prices`
- [ ] تست ربات: ارسال `/start` و انتخاب "قیمت‌های لحظه‌ای"
- [ ] تنظیم Cron Job (اختیاری)

---

## 🆘 پشتیبانی

در صورت مشکل:
1. لاگ‌های Django را بررسی کنید
2. اطمینان حاصل کنید که API در دسترس است
3. محصولات را در پنل ادمین بررسی کنید

موفق باشید! 🚀

