"""
Constants for the Telegram bot.

Defines conversation states, keyboard layouts, callback patterns, and message templates.
"""

from typing import Final

# ==================== Conversation States ====================
# States for the buy/sell conversation flow
SELECTING_PRODUCT: Final[int] = 0
SELECTING_METHOD: Final[int] = 1
ENTERING_AMOUNT: Final[int] = 2
CONFIRMING_BUY: Final[int] = 3
CONFIRMING_SELL: Final[int] = 4

# States for Account Management
VIEWING_PROFILE: Final[int] = 10
MANAGING_BANK_ACCOUNTS: Final[int] = 11
ADDING_BANK_ACCOUNT: Final[int] = 12
ENTERING_BANK_NAME: Final[int] = 13
ENTERING_ACCOUNT_NUMBER: Final[int] = 14
ENTERING_ACCOUNT_HOLDER: Final[int] = 15

# States for Wallet - Deposit
SELECTING_DEPOSIT_CURRENCY: Final[int] = 20
ENTERING_DEPOSIT_AMOUNT: Final[int] = 21
SELECTING_DEPOSIT_BANK: Final[int] = 22
UPLOADING_RECEIPT: Final[int] = 23
CONFIRMING_DEPOSIT: Final[int] = 24

# States for Wallet - Withdraw
SELECTING_WITHDRAW_CURRENCY: Final[int] = 30
ENTERING_WITHDRAW_AMOUNT: Final[int] = 31
SELECTING_WITHDRAW_BANK: Final[int] = 32
CONFIRMING_WITHDRAW: Final[int] = 33

# States for Wallet - Transfer
SELECTING_TRANSFER_CURRENCY: Final[int] = 40
ENTERING_RECEIVER_PHONE: Final[int] = 41
ENTERING_TRANSFER_AMOUNT: Final[int] = 42
ENTERING_TRANSFER_DESCRIPTION: Final[int] = 43
CONFIRMING_TRANSFER: Final[int] = 44

# ==================== Callback Data Prefixes ====================
PRODUCT_PREFIX: Final[str] = "product_"
METHOD_PREFIX: Final[str] = "method_"
CONFIRM_PREFIX: Final[str] = "confirm_"
CANCEL_PREFIX: Final[str] = "cancel_"

# ==================== Calculation Methods ====================
METHOD_GRAMS: Final[str] = "grams"
METHOD_RIAL: Final[str] = "rial"

# ==================== Main Menu Buttons ====================
MENU_PRICE: Final[str] = "📈 قیمت لحظه‌ای"
MENU_BUY: Final[str] = "💰 خرید طلا"
MENU_SELL: Final[str] = "🛒 فروش طلا"
MENU_PORTFOLIO: Final[str] = "📊 کیف پول من"
MENU_HISTORY: Final[str] = "📜 تاریخچه سفارشات"
MENU_ACCOUNT: Final[str] = "👤 حساب کاربری"
MENU_WALLET: Final[str] = "💼 کیف پول"
MENU_CANCEL: Final[str] = "❌ لغو"

# ==================== Validation Limits ====================
# Minimum order amounts to prevent dust transactions
MIN_ORDER_GRAMS: Final[Decimal] = Decimal('0.01')  # Minimum 0.01 grams
MIN_ORDER_RIAL: Final[Decimal] = Decimal('10000')  # Minimum 10,000 Rials

# Maximum order amounts for safety
MAX_ORDER_GRAMS: Final[Decimal] = Decimal('1000.0')  # Maximum 1kg per order
MAX_ORDER_RIAL: Final[Decimal] = Decimal('10000000000')  # Maximum 10 billion Rials

# ==================== Welcome Messages ====================
WELCOME_NEW_USER: Final[str] = (
    "👋 *سلام و خوش آمدید به ربات معاملات طلا!*\n\n"
    "برای شروع، لطفاً روی دکمه زیر کلیک کنید "
    "تا شماره تماس خود را با ما به اشتراک بگذارید.\n\n"
    "این اطلاعات برای احراز هویت و امنیت حساب شما ضروری است."
)

WELCOME_PENDING_USER: Final[str] = (
    "⏳ *حساب شما در انتظار تأیید است.*\n\n"
    "کارشناسان ما در حال بررسی اطلاعات شما هستند.\n"
    "لطفاً صبور باشید. به محض تأیید، شما را مطلع خواهیم کرد.\n\n"
    "برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
)

WELCOME_APPROVED_USER: Final[str] = (
    "✅ *خوش آمدید {name}!*\n\n"
    "حساب شما فعال است و می‌توانید از خدمات ما استفاده کنید.\n"
    "از منوی زیر گزینه مورد نظر را انتخاب کنید:"
)

REGISTRATION_SUCCESS: Final[str] = (
    "✅ *ثبت‌نام شما با موفقیت انجام شد!*\n\n"
    "📋 اطلاعات شما:\n"
    "📱 شماره تماس: {phone}\n\n"
    "⏳ لطفاً منتظر تایید مدیر باشید.\n"
    "کارشناسان ما در اسرع وقت حساب شما را بررسی خواهند کرد.\n\n"
    "پس از تایید، می‌توانید شروع به معامله کنید."
)

# ==================== Error Messages ====================
ERROR_NOT_APPROVED: Final[str] = (
    "⚠️ حساب شما هنوز تأیید نشده است.\n"
    "لطفاً منتظر تایید مدیر باشید."
)

ERROR_INVALID_AMOUNT: Final[str] = (
    "❌ مقدار وارد شده نامعتبر است.\n"
    "لطفاً یک عدد معتبر وارد کنید."
)

ERROR_INSUFFICIENT_BALANCE_RIAL: Final[str] = (
    "❌ موجودی ریالی شما کافی نیست.\n\n"
    "موجودی فعلی: {current} ریال\n"
    "مورد نیاز: {required} ریال"
)

ERROR_INSUFFICIENT_BALANCE_GOLD: Final[str] = (
    "❌ موجودی طلای شما کافی نیست.\n\n"
    "موجودی فعلی: {current} گرم\n"
    "مورد نیاز: {required} گرم"
)

ERROR_GENERAL: Final[str] = (
    "❌ متأسفانه خطایی رخ داد.\n"
    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
)

ERROR_NO_PRODUCTS: Final[str] = (
    "❌ متأسفانه در حال حاضر محصولی برای معامله موجود نیست.\n"
    "لطفاً بعداً تلاش کنید."
)

ERROR_AMOUNT_TOO_SMALL: Final[str] = (
    "❌ مقدار سفارش خیلی کم است.\n\n"
    "حداقل مقدار: {min_amount}"
)

ERROR_AMOUNT_TOO_LARGE: Final[str] = (
    "❌ مقدار سفارش خیلی زیاد است.\n\n"
    "حداکثر مقدار: {max_amount}"
)

# ==================== Order Messages ====================
ORDER_SUCCESS: Final[str] = (
    "✅ *سفارش شما با موفقیت ثبت شد!*\n\n"
    "شماره سفارش: #{order_id}\n\n"
    "سفارش شما در صف بررسی قرار گرفت.\n"
    "پس از تأیید مدیر، به شما اطلاع داده خواهد شد.\n\n"
    "می‌توانید وضعیت سفارش را از منوی \"تاریخچه سفارشات\" مشاهده کنید."
)

ORDER_CANCELLED: Final[str] = (
    "❌ سفارش لغو شد.\n"
    "شما به منوی اصلی بازگشتید."
)

# ==================== Prompts ====================
PROMPT_SELECT_PRODUCT: Final[str] = (
    "لطفاً محصول مورد نظر خود را انتخاب کنید:"
)

PROMPT_SELECT_METHOD: Final[str] = (
    "روش محاسبه را انتخاب کنید:\n\n"
    "• *بر اساس مبلغ (ریال):* مبلغی که می‌خواهید خرج کنید را وارد کنید.\n"
    "• *بر اساس مقدار (گرم):* مقدار طلایی که می‌خواهید بخرید را وارد کنید."
)

PROMPT_ENTER_AMOUNT_GRAMS: Final[str] = (
    "⚖️ لطفاً مقدار طلا را به *گرم* وارد کنید:\n\n"
    "مثال: 2.5 یا 10"
)

PROMPT_ENTER_AMOUNT_RIAL: Final[str] = (
    "💰 لطفاً مبلغ مورد نظر را به *ریال* وارد کنید:\n\n"
    "مثال: 1000000 یا 5000000"
)

PROMPT_ENTER_AMOUNT_SELL_GRAMS: Final[str] = (
    "⚖️ لطفاً مقدار طلایی که می‌خواهید بفروشید را به *گرم* وارد کنید:\n\n"
    "موجودی فعلی شما: {balance} گرم\n\n"
    "مثال: 2.5 یا 10"
)

PROMPT_ENTER_AMOUNT_SELL_RIAL: Final[str] = (
    "💰 لطفاً مبلغی که می‌خواهید از فروش طلا دریافت کنید را به *ریال* وارد کنید:\n\n"
    "موجودی فعلی شما: {balance} گرم\n\n"
    "مثال: 1000000 یا 5000000"
)

# ==================== History Messages ====================
NO_ORDERS: Final[str] = (
    "📜 شما هنوز سفارشی ثبت نکرده‌اید.\n\n"
    "از منوی اصلی می‌توانید سفارش جدید ثبت کنید."
)

ORDERS_HISTORY_HEADER: Final[str] = (
    "📜 *آخرین سفارشات شما:*\n\n"
)

# ==================== Button Texts ====================
BTN_SHARE_CONTACT: Final[str] = "📱 ارسال شماره تماس"
BTN_METHOD_GRAMS: Final[str] = "⚖️ بر اساس مقدار (گرم)"
BTN_METHOD_RIAL: Final[str] = "💰 بر اساس مبلغ (ریال)"
BTN_CONFIRM: Final[str] = "✅ تایید نهایی"
BTN_CANCEL: Final[str] = "❌ لغو"
BTN_BACK_TO_MENU: Final[str] = "🔙 بازگشت به منوی اصلی"

# ==================== Callback Data for Account & Wallet ====================
CALLBACK_ACCOUNT_PROFILE: Final[str] = "account_profile"
CALLBACK_ACCOUNT_BANKCARDS: Final[str] = "account_bankcards"
CALLBACK_ACCOUNT_BALANCES: Final[str] = "account_balances"
CALLBACK_ACCOUNT_TRANSACTIONS: Final[str] = "account_transactions"

CALLBACK_WALLET_DEPOSIT: Final[str] = "wallet_deposit"
CALLBACK_WALLET_WITHDRAW: Final[str] = "wallet_withdraw"
CALLBACK_WALLET_TRANSFER: Final[str] = "wallet_transfer"
CALLBACK_WALLET_BALANCES: Final[str] = "wallet_balances"
CALLBACK_WALLET_TRANSACTIONS: Final[str] = "wallet_transactions"

# Currency selection callbacks
CALLBACK_CURRENCY_RIAL: Final[str] = "currency_rial"
CALLBACK_CURRENCY_GOLD: Final[str] = "currency_gold"
CALLBACK_CURRENCY_COIN: Final[str] = "currency_coin"
CALLBACK_CURRENCY_DOLLAR: Final[str] = "currency_dollar"

# Bank account callbacks
CALLBACK_SELECT_BANK_PREFIX: Final[str] = "select_bank_"
CALLBACK_ADD_BANK_ACCOUNT: Final[str] = "add_bank_account"
CALLBACK_REMOVE_BANK_PREFIX: Final[str] = "remove_bank_"

# Back navigation
CALLBACK_BACK_TO_MAIN: Final[str] = "back_to_main"
CALLBACK_BACK_TO_WALLET: Final[str] = "back_to_wallet"
CALLBACK_BACK_TO_ACCOUNT: Final[str] = "back_to_account"

# Confirm callbacks
CALLBACK_CONFIRM_YES: Final[str] = "confirm_yes"
CALLBACK_CONFIRM_NO: Final[str] = "confirm_no"

# ==================== Currency Types ====================
CURRENCY_TYPES: Final[dict] = {
    'RIAL': 'ریال',
    'GOLD': 'طلا',
    'COIN': 'سکه',
    'DOLLAR': 'دلار',
}

# ==================== Iranian Banks ====================
IRANIAN_BANKS: Final[list] = [
    'ملی ایران', 'ملت', 'تجارت', 'صادرات', 'سپه',
    'رفاه', 'پاسارگاد', 'پارسیان', 'اقتصاد نوین', 'سامان',
    'سینا', 'کارآفرین', 'آینده', 'شهر', 'دی',
    'صنعت و معدن', 'توسعه تعاون', 'قوامین', 'مهر اقتصاد', 'حکمت ایرانیان'
]

# ==================== Wallet Messages ====================
MSG_WALLET_MENU: Final[str] = (
    "💼 *منوی کیف پول*\n\n"
    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
)

MSG_ACCOUNT_MENU: Final[str] = (
    "👤 *منوی حساب کاربری*\n\n"
    "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:"
)

MSG_SELECT_CURRENCY: Final[str] = (
    "💱 لطفاً نوع ارز را انتخاب کنید:"
)

MSG_ENTER_AMOUNT: Final[str] = (
    "💰 لطفاً مقدار را وارد کنید:\n\n"
    "مثال: 1000000 (برای ریال) یا 2.5 (برای طلا)"
)

MSG_SELECT_BANK_ACCOUNT: Final[str] = (
    "💳 لطفاً حساب بانکی خود را انتخاب کنید:"
)

MSG_NO_BANK_ACCOUNTS: Final[str] = (
    "❌ شما هیچ حساب بانکی تایید شده ندارید.\n\n"
    "لطفاً ابتدا از منوی حساب کاربری، حساب بانکی خود را اضافه کنید."
)

MSG_DEPOSIT_SUCCESS: Final[str] = (
    "✅ درخواست واریز شما ثبت شد!\n\n"
    "شماره تراکنش: {transaction_number}\n\n"
    "درخواست شما در صف بررسی قرار گرفت.\n"
    "پس از تایید مدیر، موجودی به حساب شما اضافه خواهد شد."
)

MSG_WITHDRAW_SUCCESS: Final[str] = (
    "✅ درخواست برداشت شما ثبت شد!\n\n"
    "شماره درخواست: {request_number}\n\n"
    "موجودی شما مسدود شد و در صف بررسی قرار گرفت.\n"
    "پس از تایید مدیر، مبلغ به حساب شما واریز می‌شود."
)

MSG_TRANSFER_SUCCESS: Final[str] = (
    "✅ انتقال وجه با موفقیت انجام شد!\n\n"
    "شماره درخواست: {request_number}\n"
    "به: {receiver_name}\n"
    "مبلغ: {amount} {currency}\n\n"
    "موجودی جدید: {new_balance}"
)

MSG_INSUFFICIENT_BALANCE: Final[str] = (
    "❌ موجودی کافی نیست.\n\n"
    "موجودی فعلی: {balance}\n"
    "مورد نیاز: {required}"
)

MSG_ENTER_RECEIVER_PHONE: Final[str] = (
    "📱 لطفاً شماره تلفن گیرنده را وارد کنید:\n\n"
    "مثال: 09123456789"
)

MSG_RECEIVER_NOT_FOUND: Final[str] = (
    "❌ کاربری با این شماره تلفن یافت نشد.\n\n"
    "لطفاً مطمئن شوید شماره تلفن صحیح است و کاربر در سیستم ثبت‌نام کرده است."
)

MSG_BANK_ACCOUNT_INFO: Final[str] = (
    "💳 اطلاعات حساب بانکی:\n\n"
    "🏦 بانک: {bank_name}\n"
    "👤 صاحب حساب: {holder_name}\n"
    "🔢 شماره: {account_number}\n"
    "✅ وضعیت: {status}\n"
    "📅 تاریخ ثبت: {created_at}"
)

MSG_ADD_BANK_ACCOUNT_START: Final[str] = (
    "💳 *افزودن حساب بانکی جدید*\n\n"
    "لطفاً نام بانک خود را وارد کنید:\n\n"
    "مثال: ملی ایران، ملت، سامان"
)

MSG_ENTER_ACCOUNT_NUMBER: Final[str] = (
    "🔢 لطفاً شماره کارت یا شبا خود را وارد کنید:\n\n"
    "مثال:\n"
    "• شماره کارت: 6037997512345678\n"
    "• شماره شبا: IR123456789012345678901234"
)

MSG_ENTER_ACCOUNT_HOLDER: Final[str] = (
    "👤 لطفاً نام و نام خانوادگی صاحب حساب را وارد کنید:\n\n"
    "مثال: علی احمدی"
)

MSG_BANK_ACCOUNT_ADDED: Final[str] = (
    "✅ حساب بانکی با موفقیت اضافه شد!\n\n"
    "درخواست شما در صف بررسی قرار گرفت.\n"
    "پس از تایید مدیر، می‌توانید از این حساب برای واریز و برداشت استفاده کنید."
)

# Import Decimal for validation constants
from decimal import Decimal
