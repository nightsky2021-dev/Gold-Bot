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

# Import Decimal for validation constants
from decimal import Decimal

# ==================== Account & Wallet Management States ====================
# Account Management States
VIEWING_PROFILE: Final[str] = "viewing_profile"
MANAGING_BANK_ACCOUNTS: Final[str] = "managing_bank_accounts"
ADDING_BANK_ACCOUNT: Final[str] = "adding_bank_account"
ENTERING_BANK_NAME: Final[str] = "entering_bank_name"
ENTERING_ACCOUNT_NUMBER: Final[str] = "entering_account_number"
ENTERING_ACCOUNT_HOLDER: Final[str] = "entering_account_holder"
ENTERING_ACCOUNT_TYPE: Final[str] = "entering_account_type"

# Deposit States
SELECTING_DEPOSIT_CURRENCY: Final[str] = "selecting_deposit_currency"
ENTERING_DEPOSIT_AMOUNT: Final[str] = "entering_deposit_amount"
SELECTING_DEPOSIT_BANK: Final[str] = "selecting_deposit_bank"
UPLOADING_RECEIPT: Final[str] = "uploading_receipt"
CONFIRMING_DEPOSIT: Final[str] = "confirming_deposit"

# Withdraw States
SELECTING_WITHDRAW_CURRENCY: Final[str] = "selecting_withdraw_currency"
ENTERING_WITHDRAW_AMOUNT: Final[str] = "entering_withdraw_amount"
SELECTING_WITHDRAW_BANK: Final[str] = "selecting_withdraw_bank"
CONFIRMING_WITHDRAW: Final[str] = "confirming_withdraw"

# ==================== Callback Data for Account & Wallet ====================
CALLBACK_ACCOUNT_PROFILE: Final[str] = "account_profile"
CALLBACK_ACCOUNT_BANKCARDS: Final[str] = "account_bankcards"
CALLBACK_ACCOUNT_BALANCES: Final[str] = "account_balances"
CALLBACK_ACCOUNT_TRANSACTIONS: Final[str] = "account_transactions"

CALLBACK_WALLET_DEPOSIT: Final[str] = "wallet_deposit"
CALLBACK_WALLET_WITHDRAW: Final[str] = "wallet_withdraw"
CALLBACK_WALLET_BALANCES: Final[str] = "wallet_balances"
CALLBACK_WALLET_TRANSACTIONS: Final[str] = "wallet_transactions"

CALLBACK_CURRENCY_RIAL: Final[str] = "currency_rial"
CALLBACK_CURRENCY_GOLD: Final[str] = "currency_gold"
CALLBACK_CURRENCY_COIN: Final[str] = "currency_coin"
CALLBACK_CURRENCY_DOLLAR: Final[str] = "currency_dollar"

CALLBACK_SELECT_BANK_PREFIX: Final[str] = "select_bank_"
CALLBACK_ADD_BANK_ACCOUNT: Final[str] = "add_bank_account"
CALLBACK_REMOVE_BANK_PREFIX: Final[str] = "remove_bank_"

# Generic callback data
CALLBACK_BACK_TO_MAIN: Final[str] = "back_to_main"
CALLBACK_CONFIRM_YES: Final[str] = "confirm_yes"
CALLBACK_CONFIRM_NO: Final[str] = "confirm_no"

# ==================== Menu Buttons ====================
MENU_ACCOUNT: Final[str] = "👤 حساب کاربری"
MENU_WALLET: Final[str] = "💼 کیف پول"
MENU_PRICES: Final[str] = "📈 قیمت‌ها"

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
