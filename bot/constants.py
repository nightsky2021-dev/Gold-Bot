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

# States for deposit workflow
DEPOSIT_SELECT_CURRENCY: Final[int] = 10
DEPOSIT_ENTER_AMOUNT: Final[int] = 11
DEPOSIT_SELECT_BANK: Final[int] = 12
DEPOSIT_UPLOAD_RECEIPT: Final[int] = 13
DEPOSIT_CONFIRM: Final[int] = 14

# States for withdrawal workflow
WITHDRAW_SELECT_CURRENCY: Final[int] = 20
WITHDRAW_ENTER_AMOUNT: Final[int] = 21
WITHDRAW_SELECT_BANK: Final[int] = 22
WITHDRAW_CONFIRM: Final[int] = 23

# States for bank account management
ACCOUNT_ADD_BANK: Final[int] = 30
ACCOUNT_ADD_HOLDER_NAME: Final[int] = 31
ACCOUNT_ADD_NUMBER: Final[int] = 32
ACCOUNT_ADD_TYPE: Final[int] = 33
ACCOUNT_ADD_CONFIRM: Final[int] = 34

# ==================== Callback Data Prefixes ====================
PRODUCT_PREFIX: Final[str] = "product_"
METHOD_PREFIX: Final[str] = "method_"
CONFIRM_PREFIX: Final[str] = "confirm_"
CANCEL_PREFIX: Final[str] = "cancel_"
CURRENCY_PREFIX: Final[str] = "currency_"
BANK_PREFIX: Final[str] = "bank_"
TRANSACTION_PREFIX: Final[str] = "transaction_"
FILTER_PREFIX: Final[str] = "filter_"
SETTINGS_PREFIX: Final[str] = "settings_"
PAGE_PREFIX: Final[str] = "page_"

# ==================== Calculation Methods ====================
METHOD_GRAMS: Final[str] = "grams"
METHOD_RIAL: Final[str] = "rial"

# ==================== Main Menu Buttons ====================
MENU_PRICE: Final[str] = "📈 قیمت‌ها و معامله"
MENU_WALLET: Final[str] = "💼 کیف پول"
MENU_HISTORY: Final[str] = "📋 تاریخچه"
MENU_SETTINGS: Final[str] = "⚙️ تنظیمات"
MENU_CANCEL: Final[str] = "❌ لغو"

# Legacy buttons (for backward compatibility)
MENU_BUY: Final[str] = "💰 خرید طلا"
MENU_SELL: Final[str] = "🛒 فروش طلا"
MENU_PORTFOLIO: Final[str] = "📊 کیف پول من"

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

# ==================== Wallet Messages ====================
WALLET_DISPLAY_HEADER: Final[str] = (
    "💼 *کیف پول شما:*\n\n"
)

NO_TRANSACTIONS: Final[str] = (
    "📊 شما هنوز تراکنشی ندارید.\n\n"
    "از دکمه‌های زیر برای واریز یا برداشت استفاده کنید."
)

TRANSACTION_HISTORY_HEADER: Final[str] = (
    "📊 *تراکنش‌های شما:*\n\n"
)

# ==================== Deposit Messages ====================
PROMPT_SELECT_DEPOSIT_CURRENCY: Final[str] = (
    "لطفاً ارز مورد نظر برای واریز را انتخاب کنید:"
)

PROMPT_ENTER_DEPOSIT_AMOUNT: Final[str] = (
    "💰 لطفاً مبلغ واریزی را وارد کنید:\n\n"
    "مثال: 1000000"
)

PROMPT_SELECT_DEPOSIT_BANK: Final[str] = (
    "لطفاً حساب بانکی مقصد را انتخاب کنید:"
)

PROMPT_UPLOAD_RECEIPT: Final[str] = (
    "📸 لطفاً تصویر رسید واریز را ارسال کنید:\n\n"
    "⚠️ توجه: تصویر باید واضح و خوانا باشد."
)

DEPOSIT_SUCCESS: Final[str] = (
    "✅ *درخواست واریز شما با موفقیت ثبت شد!*\n\n"
    "شماره تراکنش: #{transaction_id}\n"
    "مبلغ: {amount:,} {currency}\n\n"
    "درخواست شما در صف بررسی قرار گرفت.\n"
    "پس از تأیید مدیر، موجودی شما به‌روزرسانی خواهد شد."
)

# ==================== Withdrawal Messages ====================
PROMPT_SELECT_WITHDRAW_CURRENCY: Final[str] = (
    "لطفاً ارز مورد نظر برای برداشت را انتخاب کنید:"
)

PROMPT_ENTER_WITHDRAW_AMOUNT: Final[str] = (
    "💰 لطفاً مبلغ برداشت را وارد کنید:\n\n"
    "موجودی قابل برداشت: {available} {currency}\n\n"
    "مثال: 1000000"
)

PROMPT_SELECT_WITHDRAW_BANK: Final[str] = (
    "لطفاً حساب بانکی مقصد را انتخاب کنید:\n\n"
    "⚠️ فقط حساب‌های تأیید شده نمایش داده می‌شوند."
)

WITHDRAW_PREVIEW: Final[str] = (
    "💵 *پیش‌فاکتور برداشت*\n\n"
    "ارز: {currency}\n"
    "مبلغ: {amount:,}\n"
    "حساب بانکی: {bank_name}\n"
    "شماره حساب: {account_number}\n\n"
    "آیا از ثبت درخواست برداشت مطمئن هستید؟"
)

WITHDRAW_SUCCESS: Final[str] = (
    "✅ *درخواست برداشت شما با موفقیت ثبت شد!*\n\n"
    "شماره درخواست: #{request_id}\n"
    "مبلغ: {amount:,} {currency}\n\n"
    "موجودی مورد نظر مسدود شد.\n"
    "پس از تأیید مدیر، واریز به حساب شما انجام خواهد شد."
)

ERROR_NO_VERIFIED_BANKS: Final[str] = (
    "❌ شما هیچ حساب بانکی تأیید شده ندارید.\n\n"
    "لطفاً ابتدا از منوی تنظیمات، حساب بانکی خود را اضافه کنید."
)

ERROR_INSUFFICIENT_BALANCE: Final[str] = (
    "❌ موجودی شما کافی نیست.\n\n"
    "موجودی فعلی: {current:,} {currency}\n"
    "مورد نیاز: {required:,} {currency}"
)

# ==================== Bank Account Messages ====================
NO_BANK_ACCOUNTS: Final[str] = (
    "🏦 شما هنوز حساب بانکی ثبت نکرده‌اید.\n\n"
    "برای واریز و برداشت، لطفاً حساب بانکی خود را اضافه کنید."
)

BANK_ACCOUNTS_LIST_HEADER: Final[str] = (
    "🏦 *حساب‌های بانکی شما:*\n\n"
)

PROMPT_SELECT_BANK_NAME: Final[str] = (
    "لطفاً نام بانک خود را انتخاب کنید:"
)

PROMPT_ENTER_ACCOUNT_HOLDER: Final[str] = (
    "لطفاً نام صاحب حساب را وارد کنید:\n\n"
    "مثال: علی احمدی"
)

PROMPT_ENTER_ACCOUNT_NUMBER: Final[str] = (
    "لطفاً شماره حساب (16 رقمی) را وارد کنید:\n\n"
    "مثال: 1234567890123456"
)

ERROR_INVALID_ACCOUNT_NUMBER: Final[str] = (
    "❌ شماره حساب نامعتبر است.\n\n"
    "شماره حساب باید دقیقاً 16 رقم باشد."
)

BANK_ACCOUNT_ADD_SUCCESS: Final[str] = (
    "✅ *حساب بانکی شما با موفقیت ثبت شد!*\n\n"
    "بانک: {bank_name}\n"
    "صاحب حساب: {holder_name}\n"
    "شماره حساب: {account_number}\n\n"
    "⏳ حساب شما در صف تأیید قرار گرفت.\n"
    "پس از تأیید مدیر، می‌توانید از آن استفاده کنید."
)

BANK_ACCOUNT_REMOVE_CONFIRM: Final[str] = (
    "⚠️ آیا از حذف این حساب بانکی مطمئن هستید؟\n\n"
    "بانک: {bank_name}\n"
    "شماره حساب: {account_number}"
)

BANK_ACCOUNT_REMOVE_SUCCESS: Final[str] = (
    "✅ حساب بانکی با موفقیت حذف شد."
)

ERROR_CANNOT_REMOVE_ACCOUNT: Final[str] = (
    "❌ امکان حذف این حساب وجود ندارد.\n\n"
    "دلیل: این حساب دارای تراکنش‌های در انتظار است."
)

# ==================== Settings Messages ====================
SETTINGS_MENU: Final[str] = (
    "⚙️ *تنظیمات*\n\n"
    "لطفاً گزینه مورد نظر را انتخاب کنید:"
)

PROFILE_DISPLAY: Final[str] = (
    "👤 *پروفایل من*\n\n"
    "نام: {full_name}\n"
    "شماره تماس: {phone_number}\n"
    "نام کاربری تلگرام: @{telegram_username}\n"
    "تاریخ عضویت: {created_at}\n"
    "وضعیت حساب: {status}\n"
)

STATISTICS_DISPLAY: Final[str] = (
    "📊 *آمار من*\n\n"
    "تعداد سفارشات: {total_orders}\n"
    "  • تکمیل شده: {completed_orders}\n"
    "  • در انتظار: {pending_orders}\n"
    "  • لغو شده: {cancelled_orders}\n\n"
    "حجم معاملات: {trade_volume:,} ریال\n"
    "محصول محبوب: {favorite_product}\n"
    "عضویت از: {member_since}"
)

# ==================== Button Texts ====================
BTN_SHARE_CONTACT: Final[str] = "📱 ارسال شماره تماس"
BTN_METHOD_GRAMS: Final[str] = "⚖️ بر اساس مقدار (گرم)"
BTN_METHOD_RIAL: Final[str] = "💰 بر اساس مبلغ (ریال)"
BTN_CONFIRM: Final[str] = "✅ تایید نهایی"
BTN_CANCEL: Final[str] = "❌ لغو"
BTN_BACK_TO_MENU: Final[str] = "🔙 بازگشت به منوی اصلی"

# Wallet action buttons
BTN_DEPOSIT: Final[str] = "📥 واریز"
BTN_WITHDRAW: Final[str] = "📤 برداشت"
BTN_TRANSACTIONS: Final[str] = "📊 تراکنش‌ها"

# Settings submenu buttons
BTN_PROFILE: Final[str] = "👤 پروفایل من"
BTN_BANK_ACCOUNTS: Final[str] = "🏦 حساب‌های بانکی"
BTN_STATISTICS: Final[str] = "📊 آمار من"

# Bank account buttons
BTN_ADD_ACCOUNT: Final[str] = "➕ افزودن حساب"
BTN_REMOVE_ACCOUNT: Final[str] = "🗑️ حذف حساب"

# Transaction filter buttons
BTN_FILTER_ALL: Final[str] = "همه"
BTN_FILTER_PENDING: Final[str] = "در انتظار"
BTN_FILTER_COMPLETED: Final[str] = "تکمیل شده"
BTN_FILTER_CANCELLED: Final[str] = "لغو شده"

# ==================== Currency Types ====================
CURRENCY_RIAL: Final[str] = "rial"
CURRENCY_GOLD: Final[str] = "gold"
CURRENCY_COIN: Final[str] = "coin"
CURRENCY_DOLLAR: Final[str] = "dollar"

# ==================== Iranian Banks ====================
IRANIAN_BANKS: Final[list] = [
    "ملی",
    "ملت",
    "سپه",
    "تجارت",
    "صادرات",
    "رفاه",
    "مسکن",
    "پست بانک",
    "کشاورزی",
    "صنعت و معدن",
    "پاسارگاد",
    "سامان",
    "سینا",
    "پارسیان",
    "کارآفرین",
    "اقتصاد نوین",
    "دی",
    "شهر",
    "آینده",
    "انصار",
    "حکمت ایرانیان",
    "گردشگری",
    "توسعه تعاون",
    "رسالت",
    "قوامین",
    "سایر"
]

# ==================== Transaction Types ====================
TRANSACTION_DEPOSIT: Final[str] = "deposit"
TRANSACTION_WITHDRAW: Final[str] = "withdraw"
TRANSACTION_BUY: Final[str] = "buy"
TRANSACTION_SELL: Final[str] = "sell"
TRANSACTION_ADJUSTMENT: Final[str] = "adjustment"

# ==================== Transaction Status ====================
STATUS_PENDING: Final[str] = "pending"
STATUS_COMPLETED: Final[str] = "completed"
STATUS_CANCELLED: Final[str] = "cancelled"
STATUS_REJECTED: Final[str] = "rejected"

# Import Decimal for validation constants
from decimal import Decimal
