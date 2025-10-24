# 🤝 راهنمای مشارکت - Contributing Guide

از اینکه قصد مشارکت در پروژه را دارید متشکریم! 🙏

## 📋 فهرست

- [نحوه مشارکت](#نحوه-مشارکت)
- [استانداردهای کد](#استانداردهای-کد)
- [فرآیند توسعه](#فرآیند-توسعه)
- [راهنمای Commit](#راهنمای-commit)
- [تست‌ها](#تست‌ها)

## 🚀 نحوه مشارکت

### 1. Fork و Clone

```bash
# Fork کردن پروژه در GitHub
# سپس:
git clone https://github.com/YOUR_USERNAME/gold_shop.git
cd gold_shop
```

### 2. ساخت Branch جدید

```bash
git checkout -b feature/amazing-feature
```

نام‌گذاری Branch:
- `feature/` برای ویژگی جدید
- `fix/` برای رفع باگ
- `docs/` برای مستندات
- `refactor/` برای بازنویسی کد

### 3. نصب محیط توسعه

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # اگر وجود دارد
```

### 4. انجام تغییرات

مطمئن شوید:
- کد تمیز است
- از استانداردهای پروژه پیروی می‌کند
- مستندات به‌روز شده است
- تست‌ها می‌گذرند

### 5. Commit و Push

```bash
git add .
git commit -m "feat: add amazing feature"
git push origin feature/amazing-feature
```

### 6. ایجاد Pull Request

در GitHub یک Pull Request باز کنید با:
- عنوان واضح
- توضیح کامل تغییرات
- لینک به Issue (اگر وجود دارد)
- اسکرین‌شات (اگر لازم است)

## 📝 استانداردهای کد

### Python Style Guide

ما از [PEP 8](https://pep8.org/) پیروی می‌کنیم با تغییرات زیر:

```python
# ✅ خوب
def calculate_total_price(
    quantity: Decimal,
    price_per_unit: Decimal
) -> Decimal:
    """
    محاسبه مبلغ کل
    
    Args:
        quantity: مقدار
        price_per_unit: قیمت واحد
        
    Returns:
        Decimal: مبلغ کل
    """
    return quantity * price_per_unit


# ❌ بد
def calc(q,p):
    return q*p
```

### قوانین:
1. **Type Hinting**: همیشه استفاده شود
2. **Docstrings**: به زبان فارسی برای توابع عمومی
3. **نام‌گذاری**: واضح و توصیفی (فارسی یا انگلیسی)
4. **Import ها**: مرتب‌سازی شده
5. **حداکثر طول خط**: 100 کاراکتر

### Django Specific

```python
# Models
class MyModel(models.Model):
    """توضیح مدل به فارسی"""
    
    class Meta:
        verbose_name = "نام فارسی"
        verbose_name_plural = "نام جمع فارسی"
        ordering = ['-created_at']

# Services
class MyService:
    """سرویس ..."""
    
    @staticmethod
    @transaction.atomic
    def important_operation():
        """عملیات مهم با تراکنش"""
        pass
```

## 🔄 فرآیند توسعه

### قبل از شروع:
1. Issue باز کنید (اگر وجود ندارد)
2. منتظر تایید باشید
3. خودتان را assign کنید

### در حین توسعه:
1. Branch جدید بسازید
2. تغییرات کوچک commit کنید
3. مرتب push کنید
4. با main branch sync باشید

### بعد از اتمام:
1. تست کنید
2. مستندات را update کنید
3. Pull Request باز کنید
4. به بازخوردها پاسخ دهید

## 📝 راهنمای Commit

از [Conventional Commits](https://www.conventionalcommits.org/) استفاده می‌کنیم:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types:
- `feat`: ویژگی جدید
- `fix`: رفع باگ
- `docs`: تغییر در مستندات
- `style`: فرمت‌بندی کد
- `refactor`: بازنویسی بدون تغییر عملکرد
- `test`: افزودن تست
- `chore`: تغییرات build یا tools

### مثال‌ها:

```bash
# ویژگی جدید
git commit -m "feat(bot): add notification for price changes"

# رفع باگ
git commit -m "fix(trading): resolve decimal precision in calculations"

# مستندات
git commit -m "docs: update setup guide with PostgreSQL instructions"

# Refactor
git commit -m "refactor(users): extract validation to separate method"
```

## 🧪 تست‌ها

### اجرای تست‌ها

```bash
# تمام تست‌ها
python manage.py test

# تست یک app
python manage.py test users

# با coverage
coverage run --source='.' manage.py test
coverage report
```

### نوشتن تست

```python
from django.test import TestCase
from users.services import UserService

class UserServiceTest(TestCase):
    """تست سرویس کاربران"""
    
    def test_create_user_from_telegram(self):
        """تست ایجاد کاربر از تلگرام"""
        user, profile, created = UserService.create_user_from_telegram(
            telegram_id="test_123",
            phone_number="09121234567"
        )
        
        self.assertTrue(created)
        self.assertEqual(profile.telegram_id, "test_123")
        self.assertFalse(profile.is_approved)
```

## 🐛 گزارش باگ

### قبل از گزارش:
1. جستجو کنید باگ قبلاً گزارش نشده باشد
2. مطمئن شوید واقعاً باگ است نه سوال

### اطلاعات مورد نیاز:
- **توضیح**: باگ چیست؟
- **مراحل بازتولید**: چطور اتفاق می‌افتد؟
- **رفتار انتظاری**: چه باید اتفاق بیفتد؟
- **رفتار فعلی**: چه اتفاق می‌افتد؟
- **محیط**: 
  - Python version
  - Django version
  - OS
- **لاگ‌ها**: خطاها و traceback
- **اسکرین‌شات**: اگر مفید است

### Template:

```markdown
## توضیح
توضیح کوتاه از باگ

## مراحل بازتولید
1. برو به '...'
2. کلیک کن روی '...'
3. Error می‌بینی

## رفتار انتظاری
باید ... اتفاق بیفتد

## رفتار فعلی
... اتفاق می‌افتد

## محیط
- Python: 3.11
- Django: 4.2
- OS: Ubuntu 22.04

## لاگ‌ها
```
traceback here
```

## اسکرین‌شات
...
```

## 💡 پیشنهاد ویژگی

### قبل از پیشنهاد:
1. بررسی کنید قبلاً پیشنهاد نشده باشد
2. مطمئن شوید با اهداف پروژه همخوانی دارد

### Template:

```markdown
## خلاصه
یک جمله توضیح

## مشکل
چه مشکلی را حل می‌کند؟

## راه‌حل پیشنهادی
چطور باید پیاده‌سازی شود؟

## جایگزین‌ها
راه‌های دیگر چیست؟

## اطلاعات بیشتر
...
```

## 📚 منابع مفید

- [Django Documentation](https://docs.djangoproject.com/)
- [Python Telegram Bot Docs](https://python-telegram-bot.readthedocs.io/)
- [PEP 8](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## ❓ سوالات؟

اگر سوالی دارید:
1. ابتدا [README.md](README.md) را بخوانید
2. در [Issues](../../issues) جستجو کنید
3. سوال جدید بپرسید

## 🙏 تشکر

از مشارکت شما متشکریم! هر کمکی، کوچک یا بزرگ، ارزشمند است. 💚

---

**یادتان باشد**: 
- کد تمیز بنویسید
- مستندات به‌روز کنید
- تست بنویسید
- صبور باشید در review

موفق باشید! 🚀

