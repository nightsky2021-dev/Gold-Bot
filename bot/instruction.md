
# 📋 دستورالعمل پیاده‌سازی سیستم کیف پول و حساب کاربری

## 🎯 هدف کلی
توسعه یک سیستم کامل مدیریت کیف پول و حساب کاربری که امکان مدیریت موجودی‌های چندگانه (ریال، طلا، سکه، دلار)، واریز/برداشت از طریق حساب‌های بانکی ثبت‌شده، و مدیریت تراکنش‌ها را فراهم کند.

---

## 📊 وضعیت فعلی پروژه

### ✅ موارد موجود:
- مدل `Profile` با موجودی ریالی (`rial_balance`) و موجودی طلا (`gold_balance_grams`)
- مدل `Order` برای ثبت سفارشات خرید/فروش
- سیستم احراز هویت با Telegram ID
- تایید دو مرحله‌ای (ثبت‌نام + تایید ادمین)
- سرویس‌های `UserService` و `TradingService`

### ❌ موارد نیازمند توسعه:
- مدیریت کارت‌ها و حساب‌های بانکی کاربران
- سیستم کیف پول چندارزی کامل
- سیستم واریز و برداشت وجه
- مدل تراکنش‌های مالی
- موجودی سکه و دلار جداگانه در Profile

---

## 🗂️ مدل‌های دیتابیس مورد نیاز

### 1️⃣ مدل `BankAccount` (حساب‌های بانکی)

**مسیر پیشنهادی**: `users/models.py`

**فیلدهای مورد نیاز**:
```
- id (Primary Key)
- profile (ForeignKey به Profile)
- account_holder_name (نام صاحب حساب - باید با نام کاربر مطابقت داشته باشد)
- bank_name (نام بانک - انتخابی از لیست بانک‌های ایران)
- account_number (شماره حساب - IBAN و شماره کارت 16 رقمی)
- account_type (نوع حساب: CARD, IBAN)
- is_verified (تایید شده توسط ادمین)
- is_active (فعال برای واریز/برداشت)
- created_at
- updated_at
```

**نکات مهم**:
- یک کاربر می‌تواند چندین حساب بانکی داشته باشد
- فقط حساب‌های تایید شده (`is_verified=True`) قابل استفاده برای واریز/برداشت هستند
- نام صاحب حساب باید با `profile.user.first_name` و `profile.user.last_name` مطابقت داشته باشد
- Validation برای شماره کارت 16 رقمی و شماره شبا (IBAN) ایران

### 2️⃣ مدل `Wallet` (کیف پول - اختیاری)

**توضیح**: از آنجا که موجودی‌ها در `Profile` ذخیره می‌شوند، نیازی به مدل جداگانه Wallet نیست. اما باید `Profile` را توسعه دهید.

**تغییرات در مدل `Profile`**:
```
# فیلدهای موجود:
- rial_balance (موجودی ریالی)
- gold_balance_grams (موجودی طلا به گرم)

# فیلدهای جدید مورد نیاز:
- coin_balance (موجودی سکه تمام - Decimal)
- dollar_balance (موجودی دلار - Decimal)
- frozen_rial_balance (موجودی ریالی مسدود شده - برای تراکنش‌های در حال انجام)
- frozen_gold_balance (موجودی طلای مسدود شده)
- frozen_coin_balance (موجودی سکه مسدود شده)
- frozen_dollar_balance (موجودی دلار مسدود شده)
```

**دلیل Frozen Balance**:
- هنگام ثبت درخواست برداشت، موجودی مسدود می‌شود
- تا زمان تایید ادمین، موجودی از `balance` به `frozen_balance` منتقل می‌شود
- در صورت تایید، از `frozen_balance` کسر می‌شود
- در صورت لغو، به `balance` برمی‌گردد

### 3️⃣ مدل `Transaction` (تراکنش‌های مالی)

**مسیر پیشنهادی**: `trading/models.py` یا ایجاد اپ جدید `wallet/`

**فیلدهای مورد نیاز**:
```
- id (Primary Key)
- transaction_number (شماره یونیک تراکنش - مثل: TXN-20241024-001)
- profile (ForeignKey به Profile - کاربر اصلی)
- transaction_type (نوع تراکنش: DEPOSIT, WITHDRAW, TRANSFER_SEND, TRANSFER_RECEIVE, BUY, SELL)
- currency_type (نوع ارز: RIAL, GOLD, COIN, DOLLAR)
- amount (مقدار تراکنش)
- balance_before (موجودی قبل از تراکنش)
- balance_after (موجودی بعد از تراکنش)
- status (وضعیت: PENDING, COMPLETED, CANCELLED, FAILED)
- related_bank_account (ForeignKey به BankAccount - اختیاری، برای واریز/برداشت)
- related_order (ForeignKey به Order - اختیاری، برای خرید/فروش)
- admin_note (یادداشت ادمین)
- user_note (یادداشت کاربر)
- created_at
- completed_at (زمان تکمیل)
```

**انواع تراکنش‌ها**:
- `DEPOSIT`: واریز وجه به حساب
- `WITHDRAW`: برداشت وجه از حساب
- `BUY`: خرید محصول (کسر ریال، اضافه طلا/سکه/دلار)
- `SELL`: فروش محصول (کسر طلا/سکه/دلار، اضافه ریال)

### 4️⃣ مدل `WithdrawRequest` (درخواست برداشت)

**مسیر پیشنهادی**: `trading/models.py`

**فیلدهای مورد نیاز**:
```
- id (Primary Key)
- request_number (شماره یونیک درخواست)
- profile (ForeignKey به Profile)
- bank_account (ForeignKey به BankAccount - حساب مقصد)
- currency_type (نوع ارز: RIAL, GOLD, COIN, DOLLAR)
- amount (مقدار درخواستی)
- status (وضعیت: PENDING, APPROVED, REJECTED, COMPLETED)
- related_transaction (ForeignKey به Transaction - OneToOne)
- admin_note (دلیل رد یا توضیحات)
- created_at
- processed_at (زمان پردازش توسط ادمین)
- completed_at (زمان تکمیل)
```


## 🏗️ سرویس‌های مورد نیاز

### 1️⃣ سرویس `BankAccountService`

**مسیر پیشنهادی**: `users/services.py`

**متدهای مورد نیاز**:

```
add_bank_account(profile, account_holder_name, bank_name, account_number, account_type)
    ↳ افزودن حساب بانکی جدید
    ↳ Validation: بررسی تطابق نام با مشخصات کاربر
    ↳ بررسی عدم تکرار شماره حساب
    ↳ وضعیت اولیه: is_verified=False

get_user_bank_accounts(profile, only_verified=False)
    ↳ دریافت لیست حساب‌های بانکی کاربر
    ↳ فیلتر بر اساس تایید شده بودن

verify_bank_account(bank_account_id, admin_user)
    ↳ تایید حساب بانکی توسط ادمین
    ↳ تغییر وضعیت به is_verified=True
    ↳ ارسال نوتیفیکیشن به کاربر

remove_bank_account(bank_account_id, profile)
    ↳ حذف حساب بانکی (soft delete یا hard delete)
    ↳ بررسی عدم وجود تراکنش pending
```

### 2️⃣ سرویس `WalletService`

**مسیر پیشنهادی**: `trading/services.py` یا ایجاد فایل جدید `users/wallet_services.py`

**متدهای مورد نیاز**:

```
get_wallet_balance(profile)
    ↳ دریافت موجودی‌های کامل کاربر
    ↳ Return: Dict شامل {rial, gold, coin, dollar, frozen_rial, frozen_gold, ...}

freeze_balance(profile, currency_type, amount)
    ↳ مسدود کردن موجودی برای تراکنش
    ↳ کسر از balance اصلی و اضافه به frozen_balance
    ↳ استفاده از @transaction.atomic()

unfreeze_balance(profile, currency_type, amount)
    ↳ آزاد کردن موجودی مسدود شده
    ↳ کسر از frozen_balance و اضافه به balance

deduct_balance(profile, currency_type, amount)
    ↳ کسر موجودی (برای تراکنش‌های تکمیل شده)
    ↳ بررسی کفایت موجودی
    ↳ استفاده از @transaction.atomic()

add_balance(profile, currency_type, amount)
    ↳ افزودن موجودی
    ↳ استفاده از @transaction.atomic()

check_sufficient_balance(profile, currency_type, amount)
    ↳ بررسی کفایت موجودی
    ↳ Return: Boolean
```

### 3️⃣ سرویس `TransactionService`

**مسیر پیشنهادی**: `trading/services.py` یا فایل جدید

**متدهای مورد نیاز**:

```
create_transaction(profile, transaction_type, currency_type, amount, **kwargs)
    ↳ ایجاد تراکنش جدید
    ↳ تولید transaction_number یونیک
    ↳ ثبت balance_before و balance_after
    ↳ Return: Transaction instance

get_user_transactions(profile, currency_type=None, limit=20, status=None)
    ↳ دریافت تاریخچه تراکنش‌های کاربر
    ↳ فیلتر بر اساس نوع ارز و وضعیت
    ↳ مرتب‌سازی بر اساس تاریخ (جدیدترین اول)

complete_transaction(transaction_id, admin_user=None)
    ↳ تکمیل تراکنش
    ↳ تغییر وضعیت به COMPLETED
    ↳ ثبت زمان completed_at

cancel_transaction(transaction_id, reason, admin_user=None)
    ↳ لغو تراکنش
    ↳ بازگشت موجودی frozen (در صورت نیاز)
    ↳ ثبت دلیل لغو
```

### 4️⃣ سرویس `DepositService`

**مسیر پیشنهادی**: `trading/services.py`

**متدهای مورد نیاز**:

```
create_deposit_request(profile, currency_type, amount, bank_account_id, receipt_image=None)
    ↳ ایجاد درخواست واریز
    ↳ بررسی تایید شده بودن حساب بانکی
    ↳ ایجاد Transaction با status=PENDING
    ↳ ذخیره تصویر رسید (اختیاری)
    ↳ ارسال نوتیفیکیشن به ادمین

approve_deposit(transaction_id, admin_user)
    ↳ تایید واریز توسط ادمین
    ↳ افزودن موجودی به حساب کاربر
    ↳ تکمیل تراکنش
    ↳ ارسال نوتیفیکیشن به کاربر
    ↳ استفاده از @transaction.atomic()

reject_deposit(transaction_id, reason, admin_user)
    ↳ رد واریز
    ↳ تغییر وضعیت به CANCELLED
    ↳ ارسال نوتیفیکیشن به کاربر با دلیل
```

### 5️⃣ سرویس `WithdrawService`

**مسیر پیشنهادی**: `trading/services.py`

**متدهای مورد نیاز**:

```
create_withdraw_request(profile, currency_type, amount, bank_account_id)
    ↳ ایجاد درخواست برداشت
    ↳ بررسی کفایت موجودی
    ↳ بررسی تایید شده بودن حساب بانکی مقصد
    ↳ مسدود کردن موجودی (freeze_balance)
    ↳ ایجاد WithdrawRequest و Transaction
    ↳ ارسال نوتیفیکیشن به ادمین
    ↳ استفاده از @transaction.atomic()

approve_withdraw(withdraw_request_id, admin_user)
    ↳ تایید برداشت
    ↳ کسر از frozen_balance
    ↳ تکمیل تراکنش
    ↳ ارسال نوتیفیکیشن به کاربر
    ↳ استفاده از @transaction.atomic()

reject_withdraw(withdraw_request_id, reason, admin_user)
    ↳ رد برداشت
    ↳ آزاد کردن موجودی مسدود شده (unfreeze)
    ↳ لغو تراکنش
    ↳ ارسال نوتیفیکیشن به کاربر با دلیل
    ↳ استفاده از @transaction.atomic()
```


## 🤖 تغییرات در ربات تلگرام

### کیبوردهای جدید مورد نیاز

**1. منوی حساب کاربری** (`bot/keyboards.py`):
```python
def get_account_menu_keyboard():
    """کیبورد منوی حساب کاربری"""
    keyboard = [
        [InlineKeyboardButton("👤 مشخصات من", callback_data="account_profile")],
        [InlineKeyboardButton("💳 کارت‌های بانکی", callback_data="account_bankcards")],
        [InlineKeyboardButton("💰 موجودی‌ها", callback_data="account_balances")],
        [InlineKeyboardButton("📊 تراکنش‌ها", callback_data="account_transactions")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_MAIN)],
    ]
```

**2. منوی کیف پول**:
```python
def get_wallet_menu_keyboard():
    """کیبورد منوی کیف پول"""
    keyboard = [
        [InlineKeyboardButton("➕ واریز وجه", callback_data="wallet_deposit")],
        [InlineKeyboardButton("➖ برداشت وجه", callback_data="wallet_withdraw")],
        [InlineKeyboardButton("💰 موجودی‌ها", callback_data="wallet_balances")],
        [InlineKeyboardButton("📜 تراکنش‌ها", callback_data="wallet_transactions")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_MAIN)],
    ]
```

**3. کیبورد انتخاب نوع ارز**:
```python
def get_currency_selection_keyboard(action_type):
    """کیبورد انتخاب نوع ارز"""
    keyboard = [
        [InlineKeyboardButton("💵 ریال", callback_data=f"{action_type}_RIAL")],
        [InlineKeyboardButton("🪙 طلا", callback_data=f"{action_type}_GOLD")],
        [InlineKeyboardButton("🥇 سکه", callback_data=f"{action_type}_COIN")],
        [InlineKeyboardButton("💵 دلار", callback_data=f"{action_type}_DOLLAR")],
        [InlineKeyboardButton("🔙 انصراف", callback_data=CALLBACK_CONFIRM_NO)],
    ]
```

**4. کیبورد لیست حساب‌های بانکی**:
```python
def get_bank_accounts_keyboard(bank_accounts, action_prefix="select_bank"):
    """کیبورد لیست حساب‌های بانکی کاربر"""
    keyboard = []
    for account in bank_accounts:
        card_display = account.account_number[-4:]  # 4 رقم آخر
        keyboard.append([
            InlineKeyboardButton(
                f"💳 {account.bank_name} - ****{card_display}",
                callback_data=f"{action_prefix}_{account.id}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton("➕ افزودن حساب جدید", callback_data="add_bank_account")
    ])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_MAIN)])
```

### Conversation Handlers جدید

**1. Account Management Handler** (`bot/management/commands/runbot.py`):
- State: `VIEWING_PROFILE`, `MANAGING_BANK_ACCOUNTS`, `ADDING_BANK_ACCOUNT`
- نمایش مشخصات کاربر
- مدیریت کارت‌های بانکی
- افزودن/حذف کارت بانکی

**2. Deposit Handler**:
- States: `SELECTING_DEPOSIT_CURRENCY`, `ENTERING_DEPOSIT_AMOUNT`, `SELECTING_DEPOSIT_BANK`, `UPLOADING_RECEIPT`, `CONFIRMING_DEPOSIT`
- انتخاب نوع ارز
- ورود مقدار
- انتخاب حساب بانکی مبدا
- آپلود تصویر رسید (اختیاری)
- تایید نهایی و ثبت درخواست

**3. Withdraw Handler**:
- States: `SELECTING_WITHDRAW_CURRENCY`, `ENTERING_WITHDRAW_AMOUNT`, `SELECTING_WITHDRAW_BANK`, `CONFIRMING_WITHDRAW`
- انتخاب نوع ارز
- ورود مقدار
- بررسی کفایت موجودی
- انتخاب حساب بانکی مقصد
- تایید نهایی و ثبت درخواست


**5. Transaction History Handler**:
- نمایش تاریخچه تراکنش‌ها
- فیلتر بر اساس نوع ارز
- صفحه‌بندی (Pagination)
- جزئیات هر تراکنش

### دکمه جدید در منوی اصلی

**تغییر در `get_main_menu_keyboard()`**:
```python
def get_main_menu_keyboard():
    keyboard = [
        [MENU_PRICES],
        [MENU_PORTFOLIO, MENU_HISTORY],
        ["👤 حساب کاربری", "💼 کیف پول"],  # دکمه‌های جدید
    ]
```

---

## 🛡️ امنیت و اعتبارسنجی

### Validations ضروری:

1. **کارت بانکی**:
   - بررسی فرمت صحیح شماره کارت (16 رقم)
   - بررسی فرمت صحیح شبا (IR + 24 رقم)
   - تطابق نام صاحب حساب با مشخصات کاربر
   - تایید ادمین قبل از استفاده

2. **تراکنش‌ها**:
   - استفاده از `@transaction.atomic()` در تمام عملیات‌های مالی
   - بررسی کفایت موجودی قبل از هر تراکنش
   - لاگ کردن تمام تراکنش‌ها
   - ثبت `balance_before` و `balance_after` برای Audit Trail

3. **واریز و برداشت**:
   - محدودیت حداقل و حداکثر مبلغ
   - تایید دو مرحله‌ای (ثبت درخواست + تایید ادمین)
   - تایم‌استمپ دقیق برای هر مرحله


### Rate Limiting:
- محدودیت تعداد درخواست‌های واریز/برداشت در روز
- محدودیت مجموع مبلغ برداشت در روز

---

## 📱 پنل ادمین Django

### صفحات جدید مورد نیاز:

**1. مدیریت حساب‌های بانکی** (`users/admin.py`):
- نمایش لیست حساب‌های بانکی در حال انتظار تایید
- امکان تایید/رد دسته‌جمع
- نمایش اطلاعات کاربر در کنار اطلاعات حساب
- فیلتر بر اساس بانک، وضعیت، تاریخ

**2. مدیریت درخواست‌های واریز** (`trading/admin.py`):
- نمایش درخواست‌های واریز Pending
- نمایش تصویر رسید (در صورت وجود)
- دکمه‌های تایید/رد سریع
- فیلترها: نوع ارز، وضعیت، تاریخ، کاربر

**3. مدیریت درخواست‌های برداشت** (`trading/admin.py`):
- نمایش درخواست‌های برداشت Pending
- نمایش اطلاعات کامل حساب مقصد
- دکمه‌های تایید/رد سریع
- Alert برای درخواست‌های مبالغ بالا

**4. گزارش تراکنش‌ها** (`trading/admin.py`):
- نمایش تمام تراکنش‌ها با فیلترهای پیشرفته
- خلاصه آماری: مجموع واریز، برداشت، انتقال در بازه زمانی
- Export به Excel/CSV
- نمودارهای تحلیلی

### Actions سفارشی:

```python
# در admin.py
@admin.action(description="تایید حساب‌های بانکی انتخاب شده")
def approve_bank_accounts(modeladmin, request, queryset):
    queryset.update(is_verified=True)
    # ارسال نوتیفیکیشن به کاربران

@admin.action(description="تایید درخواست‌های واریز")
def approve_deposits(modeladmin, request, queryset):
    for deposit in queryset:
        DepositService.approve_deposit(deposit.id, request.user)
```

---

## 📊 Dashboard و گزارش‌گیری

### ویجت‌های پیشنهادی برای Admin Dashboard:

1. **آماری کلی امروز**:
   - ت

### ویجت‌های پیشنهادی برای Admin Dashboard:

1. **آماری کلی امروز**:
   - تعداد و مجموع واریزها
   - تعداد و مجموع برداشت‌ها
   - تعداد درخواست‌های در انتظار

2. **درخواست‌های نیازمند بررسی**:
   - حساب‌های بانکی منتظر تایید (با Badge قرمز)
   - درخواست‌های واریز Pending
   - درخواست‌های برداشت Pending
   - لینک مستقیم برای بررسی سریع

3. **موجودی کل سیستم**:
   - مجموع موجودی ریالی تمام کاربران
   - مجموع موجودی طلا
   - مجموع موجودی سکه
   - مجموع موجودی دلار
   - مجموع موجودی‌های مسدود شده

4. **نمودارهای تحلیلی**:
   - نمودار روند واریز/برداشت (۳۰ روز اخیر)
   - نمودار نوع تراکنش‌ها (Pie Chart)
   - نمودار کاربران فعال

---

## 🔔 سیستم نوتیفیکیشن

### نوتیفیکیشن‌های کاربر (از طریق تلگرام):

1. **تایید حساب بانکی**:
   ```
   ✅ حساب بانکی شما تایید شد
   🏦 بانک: [نام بانک]
   💳 شماره کارت: ****[4 رقم آخر]
   
   اکنون می‌توانید از این حساب برای واریز و برداشت استفاده کنید.
   ```

2. **تایید واریز**:
   ```
   ✅ واریز شما تایید شد
   💰 مبلغ: [مقدار] [نوع ارز]
   📊 موجودی جدید: [موجودی]
   🔢 شماره تراکنش: [TXN-NUMBER]
   ```

3. **تایید برداشت**:
   ```
   ✅ برداشت شما انجام شد
   💸 مبلغ: [مقدار] [نوع ارز]
   🏦 به حساب: [بانک] - ****[4 رقم آخر]
   📊 موجودی جدید: [موجودی]
   
   ⏰ مبلغ ظرف 24 ساعت آینده به حساب شما واریز می‌شود.
   ```

4. **رد درخواست**:
   ```
   ❌ درخواست [نوع] شما رد شد
   💰 مبلغ: [مقدار] [نوع ارز]
   📋 دلیل: [دلیل ادمین]
   
   در صورت سوال، با پشتیبانی تماس بگیرید.
   ```

### نوتیفیکیشن‌های ادمین:

1. **درخواست واریز جدید** (تلگرام یا ایمیل):
   ```
   🔔 درخواست واریز جدید
   👤 کاربر: [نام]
   💰 مبلغ: [مقدار] [نوع ارز]
   
   [لینک به پنل ادمین]
   ```

2. **درخواست برداشت جدید**:
   ```
   🔔 درخواست برداشت جدید
   👤 کاربر: [نام]
   💸 مبلغ: [مقدار] [نوع ارز]
   🏦 به حساب: [بانک]
   
   [لینک به پنل ادمین]
   ```

3. **حساب بانکی جدید برای تایید**:
   ```
   🔔 حساب بانکی جدید
   👤 کاربر: [نام]
   🏦 بانک: [نام بانک]
   💳 شماره: [شماره حساب]
   
   [لینک به پنل ادمین]
   ```

---

## 🔄 جریان کاری (Workflow)

### فلوچارت واریز وجه:

```
کاربر: کلیک "واریز وجه"
    ↓
بررسی وجود حساب بانکی تایید شده
    ↓ (دارد)
انتخاب نوع ارز (ریال/طلا/سکه/دلار)
    ↓
ورود مقدار واریز
    ↓
انتخاب حساب بانکی مبدا
    ↓
(اختیاری) آپلود تصویر رسید
    ↓
نمایش خلاصه و تایید نهایی
    ↓
ثبت Transaction با status=PENDING
    ↓
ارسال نوتیفیکیشن به ادمین
    ↓
[منتظر بررسی ادمین]
    ↓
ادمین: بررسی و تایید/رد
    ↓ (تایید)
افزودن به موجودی کاربر
    ↓
تکمیل Transaction (status=COMPLETED)
    ↓
ارسال نوتیفیکیشن به کاربر
```

### فلوچارت برداشت وجه:

```
کاربر: کلیک "برداشت وجه"
    ↓
بررسی وجود حساب بانکی تایید شده
    ↓ (دارد)
انتخاب نوع ارز
    ↓
ورود مقدار برداشت
    ↓
بررسی کفایت موجودی
    ↓ (کافی است)
انتخاب حساب بانکی مقصد
    ↓
نمایش خلاصه و تایید نهایی
    ↓
مسدود کردن موجودی (freeze_balance)
    ↓
ثبت WithdrawRequest و Transaction
    ↓
ارسال نوتیفیکیشن به ادمین
    ↓
[منتظر بررسی ادمین]
    ↓
ادمین: بررسی و تایید/رد
    ↓ (تایید)
کسر از frozen_balance
    ↓
تکمیل Transaction (status=COMPLETED)
    ↓
ارسال نوتیفیکیشن به کاربر
    ↓ (رد)
آزاد کردن موجودی (unfreeze_balance)
    ↓
لغو Transaction (status=CANCELLED)
    ↓
ارسال نوتیفیکیشن به کاربر با دلیل
```

---

## 🎨 UI/UX در ربات تلگرام

### نمایش موجودی‌ها:

```
💼 کیف پول شما:

💵 موجودی ریالی:
├─ آزاد: 5,000,000 ریال
└─ مسدود شده: 500,000 ریال

🪙 موجودی طلا:
├─ آزاد: 12.5 گرم
└─ مسدود شده: 0 گرم

🥇 موجودی سکه:
├─ آزاد: 3 عدد
└─ مسدود شده: 0 عدد

💵 موجودی دلار:
├─ آزاد: 100 دلار
└─ مسدود شده: 0 دلار

⏰ آخرین بروزرسانی: 1403/08/03 - 14:25
```

### نمایش تاریخچه تراکنش:

```
📜 تاریخچه تراکنش‌ها:

┌─────────────────────────
│ 🟢 واریز ریال
│ 💰 مبلغ: +2,000,000 ریال
│ 📅 1403/08/03 - 10:15
│ ✅ تکمیل شده
│ 🔢 TXN-20241024-0012
└─────────────────────────

┌─────────────────────────
│ 🔴 برداشت طلا
│ 💰 مبلغ: -2.5 گرم
│ 📅 1403/08/02 - 16:30
│ ⏳ در حال بررسی
│ 🔢 TXN-20241023-0087
└─────────────────────────

[دکمه: صفحه بعد]
[دکمه: فیلتر بر اساس نوع ارز]
[دکمه: بازگشت]
```

### نمایش جزئیات تراکنش:

```
📋 جزئیات تراکنش

🔢 شماره: TXN-20241024-0012
📊 نوع: واریز ریال
💰 مبلغ: 2,000,000 ریال

📈 موجودی قبل: 3,000,000 ریال
📈 موجودی بعد: 5,000,000 ریال

📅 تاریخ ثبت: 1403/08/03 - 09:45
✅ تاریخ تکمیل: 1403/08/03 - 10:15
⏱ مدت زمان: 30 دقیقه

🏦 از حساب: بانک ملی - ****1234

✅ وضعیت: تکمیل شده

[دکمه: بازگشت به لیست]
```

---

## 📝 Constants جدید مورد نیاز

**در فایل `bot/constants.py`:**

```python
# States برای Account Management
VIEWING_PROFILE = "viewing_profile"
MANAGING_BANK_ACCOUNTS = "managing_bank_accounts"
ADDING_BANK_ACCOUNT = "adding_bank_account"
ENTERING_BANK_NAME = "entering_bank_name"
ENTERING_ACCOUNT_NUMBER = "entering_account_number"
ENTERING_ACCOUNT_HOLDER = "entering_account_holder"

# States برای Wallet Management
SELECTING_DEPOSIT_CURRENCY = "selecting_deposit_currency"
ENTERING_DEPOSIT_AMOUNT = "entering_deposit_amount"
SELECTING_DEPOSIT_BANK = "selecting_deposit_bank"
UPLOADING_RECEIPT = "uploading_receipt"
CONFIRMING_DEPOSIT = "confirming_deposit"

SELECTING_WITHDRAW_CURRENCY = "selecting_withdraw_currency"
ENTERING_WITHDRAW_AMOUNT = "entering_withdraw_amount"
SELECTING_WITHDRAW_BANK = "selecting_withdraw_bank"
CONFIRMING_WITHDRAW = "confirming_withdraw"

# Callback Data Prefixes
CALLBACK_ACCOUNT_PROFILE = "account_profile"
CALLBACK_ACCOUNT_BANKCARDS = "account_bankcards"
CALLBACK_ACCOUNT_BALANCES = "account_balances"
CALLBACK_ACCOUNT_TRANSACTIONS = "account_transactions"

CALLBACK_WALLET_DEPOSIT = "wallet_deposit"
CALLBACK_WALLET_WITHDRAW = "wallet_withdraw"
CALLBACK_WALLET_BALANCES = "wallet_balances"
CALLBACK_WALLET_TRANSACTIONS = "wallet_transactions"

CALLBACK_CURRENCY_RIAL = "currency_rial"
CALLBACK_CURRENCY_GOLD = "currency_gold"
CALLBACK_CURRENCY_COIN = "currency_coin"
CALLBACK_CURRENCY_DOLLAR = "currency_dollar"

CALLBACK_SELECT_BANK_PREFIX = "select_bank_"
CALLBACK_ADD_BANK_ACCOUNT = "add_bank_account"
CALLBACK_REMOVE_BANK_PREFIX = "remove_bank_"

# منوهای اصلی جدید
MENU_ACCOUNT = "👤 حساب کاربری"
MENU_WALLET = "💼 کیف پول"

# انواع ارز
CURRENCY_TYPES = {
    'RIAL': 'ریال',
    'GOLD': 'طلا',
    'COIN': 'سکه',
    'DOLLAR': 'دلار',
}

# لیست بانک‌های ایران
IRANIAN_BANKS = [
    'ملی ایران', 'ملت', 'تجارت', 'صادرات', 'سپه',
    'رفاه', 'پاسارگاد', 'پارسیان', 'اقتصاد نوین', 'سامان',
    'سینا', 'کارآفرین', 'آینده', 'شهر', 'دی',
    'صنعت و معدن', 'توسعه تعاون', 'قوامین', 'مهر اقتصاد', 'حکمت ایرانیان'
]
```

---

## 🧪 تست‌های مورد نیاز

### Unit Tests:

**1. تست سرویس BankAccount:**
```python
# tests/test_bank_account_service.py
def test_add_bank_account_success()
def test_add_bank_account_duplicate()
def test_add_bank_account_invalid_name()
def test_verify_bank_account()
def test_remove_bank_account_with_pending_transaction()
```

**2. تست سرویس Wallet:**
```python
# tests/test_wallet_service.py
def test_freeze_balance_success()
def test_freeze_balance_insufficient()
def test_unfreeze_balance()
def test_deduct_balance()
def test_add_balance()
def test_check_sufficient_balance()
```

**3. تست سرویس Transaction:**
```python
# tests/test_transaction_service.py
def test_create_transaction()
def test_complete_transaction()
def test_cancel_transaction()
def test_get_user_transactions_filtered()
```

**4. تست سرویس Deposit:**
```python
# tests/test_deposit_service.py
def test_create_deposit_request()
def test_approve_deposit()
def test_reject_deposit()
def test_deposit_with_unverified_bank()
```

**5. تست سرویس Withdraw:**
```python
# tests/test_withdraw_service.py
def test_create_withdraw_request()
def test_approve_withdraw()
def test_reject_withdraw()
def test_withdraw_insufficient_balance()
def test_freeze_unfreeze_on_reject()
```


### Integration Tests:

```python
# tests/test_wallet_integration.py
def test_complete_deposit_workflow()
def test_complete_withdraw_workflow()
def test_concurrent_transactions()
def test_balance_consistency()
```

---

## ⚠️ نکات مهم و توصیه‌ها

### 1. امنیت:
- ✅ همیشه از `@transaction.atomic()` استفاده کنید
- ✅ تمام ورودی‌های کاربر را Validate کنید
- ✅ از Decimal برای مقادیر مالی استفاده کنید (نه Float)
- ✅ تمام تراکنش‌ها را لاگ کنید
- ✅ دسترسی به Admin Panel را محدود کنید

### 2. عملکرد:
- ✅ از Select Related و Prefetch Related استفاده کنید
- ✅ Index مناسب برای فیلدهای جستجو
- ✅ Pagination برای لیست‌های طولانی
- ✅ Cache برای قیمت‌ها و داده‌های ثابت

### 3. تجربه کاربری:
- ✅ پیام‌های خطا واضح و فارسی
- ✅ Loading indicators برای عملیات‌های طولانی
- ✅ تاییدیه قبل از عملیات‌های حساس
- ✅ نمایش پیشرفت در Conversation Handlers

### 4. مقیاس‌پذیری:
- ✅ استفاده از Celery برای کارهای سنگین (اختیاری)
- ✅ Redis برای Queue مدیریت نوتیفیکیشن‌ها (اختیاری)
- ✅ استفاده از PostgreSQL به جای SQLite در Production
- ✅ Backup منظم دیتابیس

### 5. Monitoring:
- ✅ Logging مناسب برای تمام تراکنش‌ها
- ✅ Alert برای تراکنش‌های مشکوک
- ✅ گزارش‌گیری روزانه برای ادمین
- ✅ پیگیری خطاها با Sentry (اختیاری)

---

## 🎓 خلاصه و نتیجه‌گیری

این دستورالعمل یک راهکار کامل و حرفه‌ای برای پیاده‌سازی سیستم کیف پول و مدیریت حساب کاربری در ربات تلگرام طلافروشی شما ارائه می‌دهد.

### ویژگی‌های کلیدی:
✅ مدیریت چندین نوع دارایی (ریال، طلا، سکه، دلار)
✅ سیستم کارت‌های بانکی با تایید ادمین
✅ واریز و برداشت وجه با Workflow کامل
✅ تاریخچه کامل تراکنش‌ها
✅ موجودی‌های مسدود شده (Frozen) برای امنیت
✅ پنل ادمین قدرتمند
✅ سیستم نوتیفیکیشن دوطرفه
✅ امنیت بالا با Atomic Transactions
✅ مستندسازی کامل

این سیستم با رعایت بهترین شیوه‌های برنامه‌نویسی، امنیت بالا، و قابلیت مقیاس‌پذیری طراحی شده است.
