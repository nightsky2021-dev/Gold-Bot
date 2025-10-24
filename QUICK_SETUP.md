# 🚀 راه‌اندازی سریع سیستم قیمت‌گذاری

## مراحل به ترتیب:

### 1️⃣ ایجاد و اعمال Migrations

```bash
# در PowerShell یا CMD در پوشه C:\Gold_bot:

# ایجاد migration برای تغییرات جدید
python manage.py makemigrations

# اعمال migrations به دیتابیس
python manage.py migrate
```

---

### 2️⃣ ایجاد محصولات پایه

```bash
# اجرای اسکریپت setup
python setup_products.py
```

این اسکریپت:
- ✅ 3 محصول (طلا، سکه، دلار) ایجاد می‌کند
- ✅ قیمت‌ها را از API دریافت می‌کند
- ✅ قیمت‌ها را در دیتابیس ذخیره می‌کند

---

### 3️⃣ تأیید حساب کاربری (اگر هنوز تأیید نشده)

```bash
# باز کردن Django shell
python manage.py shell
```

سپس:

```python
from users.models import Profile

# پیدا کردن کاربر با شماره تلفن یا telegram_id
profile = Profile.objects.all().first()  # یا .get(phone_number="09...")

# نمایش اطلاعات
print(f"کاربر: {profile.user.get_full_name()}")
print(f"تأیید شده: {profile.is_approved}")

# تأیید کاربر
profile.is_approved = True
profile.save()

print("✅ کاربر تأیید شد!")

# خروج
exit()
```

یا از پنل ادمین:

```bash
# اگر ادمین ندارید، ایجاد کنید:
python manage.py createsuperuser

# سپس سرور را اجرا کنید:
python manage.py runserver

# وارد شوید: http://127.0.0.1:8000/admin
# به بخش "Profiles" بروید و کاربر را تأیید کنید (is_approved = ✓)
```

---

### 4️⃣ اجرای ربات

```bash
python manage.py runbot
```

---

### 5️⃣ تست در تلگرام

1. در تلگرام، به ربات پیام بدهید: `/start`
2. اگر تأیید شده‌اید، منوی اصلی نمایش داده می‌شود
3. گزینه "📈 قیمت‌های لحظه‌ای" را انتخاب کنید
4. باید قیمت‌های طلا، سکه و دلار نمایش داده شود

---

## ❓ عیب‌یابی

### مشکل: "هیچ محصولی فعال نیست"

```bash
# بررسی محصولات
python manage.py shell
```

```python
from trading.models import Product

# نمایش تمام محصولات
products = Product.objects.all()
print(f"تعداد محصولات: {products.count()}")

for p in products:
    print(f"- {p.name} (کد: {p.product_code}, فعال: {p.is_active})")
    print(f"  خرید: {p.buy_price:,} | فروش: {p.sell_price:,}")

exit()
```

اگر تعداد 0 است، دوباره `setup_products.py` را اجرا کنید.

---

### مشکل: قیمت‌ها صفر هستند

```bash
# به‌روزرسانی دستی قیمت‌ها
python manage.py update_prices --show-details
```

اگر خطا داد:
- اتصال اینترنت را بررسی کنید
- API Key را در `.env` چک کنید

---

### مشکل: "شما مجاز نیستید"

کاربر باید تأیید شود (`is_approved = True`). مرحله 3 را اجرا کنید.

---

## ✅ چک‌لیست نهایی

- [ ] `python manage.py migrate` اجرا شد
- [ ] `python setup_products.py` اجرا شد و موفق بود
- [ ] 3 محصول در دیتابیس وجود دارد
- [ ] قیمت‌ها غیرصفر هستند
- [ ] کاربر تأیید شده است (`is_approved = True`)
- [ ] ربات در حال اجرا است (`python manage.py runbot`)
- [ ] در تلگرام تست شد و قیمت‌ها نمایش داده شد

---

## 📞 دستورات مفید

```bash
# نمایش محصولات
python manage.py shell -c "from trading.models import Product; [print(f'{p.name}: {p.buy_price:,} / {p.sell_price:,}') for p in Product.objects.all()]"

# نمایش کاربران
python manage.py shell -c "from users.models import Profile; [print(f'{p.user.get_full_name()}: approved={p.is_approved}') for p in Profile.objects.all()]"

# به‌روزرسانی قیمت‌ها
python manage.py update_prices

# اجرای ربات
python manage.py runbot
```

موفق باشید! 🎉

