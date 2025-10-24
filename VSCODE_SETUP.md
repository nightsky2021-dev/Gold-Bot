# راهنمای رفع خطاهای Import در VS Code

این راهنما برای رفع خطاهای `Import "..." could not be resolved` در VS Code است.

## ✅ راه‌حل‌های اعمال شده

دو فایل تنظیماتی ایجاد شده‌اند:

1. **`pyrightconfig.json`** - تنظیمات Pyright/Pylance
2. **`.vscode/settings.json`** - تنظیمات VS Code

این فایل‌ها باید مشکل را حل کنند. اگر هنوز warning ها را می‌بینید، مراحل زیر را دنبال کنید:

---

## 🔧 مرحله 1: بررسی نصب پکیج‌ها

ابتدا مطمئن شوید که تمام پکیج‌ها نصب شده‌اند:

```bash
# در ترمینال VS Code یا PowerShell:
cd C:\Gold_bot
pip install -r requirements.txt
```

---

## 🔧 مرحله 2: انتخاب Python Interpreter

1. در VS Code، `Ctrl + Shift + P` را بزنید
2. تایپ کنید: `Python: Select Interpreter`
3. گزینه‌ای که `./venv/Scripts/python.exe` دارد را انتخاب کنید

اگر این گزینه را نمی‌بینید:

### آیا Virtual Environment دارید؟

```bash
# بررسی کنید که پوشه venv وجود دارد:
dir venv
```

اگر پوشه `venv` وجود ندارد، ایجاد کنید:

```bash
# ایجاد virtual environment
python -m venv venv

# فعال‌سازی (Windows PowerShell):
.\venv\Scripts\Activate.ps1

# فعال‌سازی (Windows CMD):
.\venv\Scripts\activate.bat

# نصب پکیج‌ها
pip install -r requirements.txt
```

---

## 🔧 مرحله 3: Reload VS Code

پس از انتخاب interpreter:

1. `Ctrl + Shift + P` را بزنید
2. تایپ کنید: `Developer: Reload Window`

یا:

- VS Code را ببندید و دوباره باز کنید

---

## 🔧 مرحله 4: بررسی Python Path

اگر هنوز مشکل دارید، مسیر Python را بررسی کنید:

```bash
# در ترمینال VS Code:
where python
```

باید چیزی شبیه به این ببینید:
```
C:\Gold_bot\venv\Scripts\python.exe
```

اگر مسیر دیگری نشان می‌دهد، باید interpreter را دوباره انتخاب کنید.

---

## 🔧 مرحله 5: حذف کش Python

گاهی کش Python باعث مشکل می‌شود:

```bash
# حذف فولدرهای __pycache__
Get-ChildItem -Path . -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force

# یا به صورت دستی:
# پوشه‌های __pycache__ را پیدا و حذف کنید
```

سپس VS Code را reload کنید.

---

## 🔧 مرحله 6: نصب مجدد Extension های Python

اگر هیچ کدام کار نکرد:

1. به بخش Extensions بروید (`Ctrl + Shift + X`)
2. Python extension را پیدا کنید
3. روی آن کلیک راست کنید و `Uninstall` را بزنید
4. VS Code را restart کنید
5. Python extension را دوباره نصب کنید
6. Pylance را نیز بررسی کنید (باید نصب باشد)

---

## 📝 بررسی نهایی

پس از اعمال تغییرات، بررسی کنید:

✅ فایل `pyrightconfig.json` در root پروژه وجود دارد
✅ فایل `.vscode/settings.json` وجود دارد
✅ Virtual environment فعال است
✅ Interpreter صحیح در VS Code انتخاب شده
✅ تمام پکیج‌ها نصب شده‌اند

---

## 🚨 توجه

این warning ها **مشکل واقعی نیستند**. کد شما به درستی کار می‌کند. فقط IDE نمی‌تواند پکیج‌ها را پیدا کند.

اگر برنامه به درستی اجرا می‌شود (با `python manage.py runbot`)، می‌توانید warning ها را نادیده بگیرید.

---

## 💡 نکته برای آینده

هر بار که VS Code را باز می‌کنید، مطمئن شوید:
1. Interpreter صحیح انتخاب شده است (نوار پایین VS Code را چک کنید)
2. Virtual environment فعال است (در ترمینال `(venv)` را می‌بینید)

---

## ✅ تست نهایی

برای اطمینان از کارکرد صحیح:

```bash
# فعال‌سازی venv
.\venv\Scripts\Activate.ps1

# اجرای ربات
python manage.py runbot
```

اگر ربات بدون خطا اجرا شد، همه چیز درست است! 🎉

