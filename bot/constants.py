"""
Constants for the Telegram bot.

Defines conversation states, keyboard layouts, callback patterns, and message templates.
"""

from typing import Final
from decimal import Decimal

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

# States for profile update
PROFILE_UPDATE_CHOICE: Final[int] = 40
PROFILE_UPDATE_NAME: Final[int] = 41
PROFILE_UPDATE_NATIONAL_CODE: Final[int] = 42
PROFILE_UPDATE_CONFIRM: Final[int] = 43

# States for registration (profile completion)
REG_COLLECT_CONTACT: Final[int] = 50
REG_COLLECT_NAME: Final[int] = 51
REG_COLLECT_NATIONAL_CODE: Final[int] = 52
REG_CONFIRM_PROFILE: Final[int] = 53

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

# ==================== Specific Callback Data ====================
# Price menu callbacks
CALLBACK_PRICE_GOLD: Final[str] = "price_gold"
CALLBACK_PRICE_COIN: Final[str] = "price_coin"
CALLBACK_PRICE_DOLLAR: Final[str] = "price_dollar"
CALLBACK_PRICE_ALL: Final[str] = "price_all"
CALLBACK_PRICE_REFRESH: Final[str] = "price_refresh_"

# Navigation callbacks
CALLBACK_BACK_TO_PRICES_MENU: Final[str] = "back_to_prices_menu"
CALLBACK_BACK_TO_MAIN: Final[str] = "back_to_main"

# Trade callbacks
CALLBACK_TRADE_PRODUCT_PREFIX: Final[str] = "trade_"
CALLBACK_ACTION_BUY: Final[str] = "buy"
CALLBACK_ACTION_SELL: Final[str] = "sell"

# Method callbacks
CALLBACK_METHOD_GRAM: Final[str] = "method_gram"
CALLBACK_METHOD_RIAL: Final[str] = "method_rial"
CALLBACK_METHOD_COUNT: Final[str] = "method_count"

# Confirmation callbacks
CALLBACK_CONFIRM_YES: Final[str] = "confirm_yes"
CALLBACK_CONFIRM_NO: Final[str] = "confirm_no"

# ==================== Product Codes ====================
# Legacy constants for backward compatibility
PRODUCT_GOLD: Final[str] = "gold_abshodeh"
PRODUCT_COIN: Final[str] = "coin_full"
PRODUCT_DOLLAR: Final[str] = "dollar_usa"

# All currency product codes (use count-based calculation)
CURRENCY_PRODUCTS: Final[list] = [
    'dollar_usa',
    'euro',
    'lira_turkey',
    'yuan_china',
    'pound_uk',
    'dirham_uae',
]

# All coin product codes (use count-based calculation)
COIN_PRODUCTS: Final[list] = [
    'coin_full',
    'coin_half',
    'coin_quarter',
]

# Gold products (use weight-based calculation)
GOLD_PRODUCTS: Final[list] = [
    'gold_abshodeh',
]

# ==================== Calculation Methods ====================
METHOD_GRAMS: Final[str] = "grams"
METHOD_RIAL: Final[str] = "rial"
METHOD_COUNT: Final[str] = "count"  # For coin and dollar

# ==================== Main Menu Buttons ====================
MENU_PRICE: Final[str] = "📈 قیمت‌ها و معامله"
MENU_PRICES: Final[str] = "📈 قیمت‌ها و معامله"  # Alias for MENU_PRICE
MENU_WALLET: Final[str] = "💼 کیف پول"
MENU_HISTORY: Final[str] = "📋 تاریخچه معاملات"
MENU_SETTINGS: Final[str] = "⚙️ تنظیمات"
MENU_CANCEL: Final[str] = "❌ لغو"
MENU_ACCOUNT: Final[str] = "👤 حساب من"
MENU_PORTAL: Final[str] = "🌐 پورتال وب"

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
    "پس از تأیید حساب، می‌توانید به صورت آنی معامله انجام دهید.\n\n"
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
    "پس از تایید، می‌توانید به صورت آنی معامله انجام دهید."
)

# ==================== Error Messages ====================
ERROR_NOT_APPROVED: Final[str] = (
    "⚠️ حساب شما هنوز تأیید نشده است.\n"
    "لطفاً منتظر تایید مدیر باشید."
)

ERROR_INVALID_AMOUNT: Final[str] = (
    "❌ *مقدار وارد شده نامعتبر است!*\n\n"
    "لطفاً فقط عدد وارد کنید (بدون حروف یا علامت).\n\n"
    "💡 مثال‌های صحیح:\n"
    "   • 2.5\n"
    "   • 1000000\n"
    "   • 10\n\n"
    "🔄 دوباره تلاش کنید..."
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
    "✅ *معامله شما با موفقیت انجام شد!*\n\n"
    "شماره سفارش: #{order_id}\n\n"
    "✨ معامله به صورت آنی اجرا شد\n"
    "موجودی شما به‌روزرسانی گردید.\n\n"
    "می‌توانید تاریخچه معاملات خود را مشاهده کنید."
)

ORDER_CANCELLED: Final[str] = (
    "❌ *عملیات لغو شد*\n\n"
    "سفارش شما ثبت نشد.\n"
    "می‌توانید از منوی اصلی مجدداً اقدام کنید."
)

# ==================== Prompts ====================
PROMPT_SELECT_PRODUCT: Final[str] = (
    "🛍️ *انتخاب محصول*\n\n"
    "لطفاً محصول مورد نظر خود را از لیست زیر انتخاب کنید:"
)

PROMPT_SELECT_METHOD: Final[str] = (
    "📊 *انتخاب روش محاسبه*\n\n"
    "لطفاً روش محاسبه مورد نظر خود را انتخاب کنید:\n\n"
    "🔹 *محاسبه بر اساس گرم:*\n"
    "   مقدار دقیق طلا را مشخص می‌کنید\n\n"
    "🔹 *محاسبه بر اساس ریال:*\n"
    "   مبلغی که می‌خواهید خرج کنید را مشخص می‌کنید"
)

PROMPT_SELECT_METHOD_COUNT: Final[str] = (
    "📊 *انتخاب روش محاسبه*\n\n"
    "لطفاً روش محاسبه مورد نظر خود را انتخاب کنید:\n\n"
    "🔹 *محاسبه بر اساس تعداد:*\n"
    "   تعداد دقیق را مشخص می‌کنید\n\n"
    "🔹 *محاسبه بر اساس ریال:*\n"
    "   مبلغی که می‌خواهید خرج کنید را مشخص می‌کنید"
)

PROMPT_ENTER_AMOUNT_GRAMS: Final[str] = (
    "⚖️ *ورود مقدار به گرم*\n\n"
    "لطفاً مقدار طلا را به *گرم* تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 2.5 (دو گرم و نیم)\n"
    "   • 10 (ده گرم)\n"
    "   • 0.5 (نیم گرم)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

PROMPT_ENTER_AMOUNT_RIAL: Final[str] = (
    "💰 *ورود مبلغ به ریال*\n\n"
    "لطفاً مبلغ مورد نظر را به *ریال* تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 1000000 (یک میلیون)\n"
    "   • 5000000 (پنج میلیون)\n"
    "   • 10000000 (ده میلیون)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

PROMPT_ENTER_AMOUNT_SELL_GRAMS: Final[str] = (
    "⚖️ *ورود مقدار برای فروش*\n\n"
    "💼 موجودی فعلی شما: *{balance} گرم*\n\n"
    "لطفاً مقدار طلایی که می‌خواهید بفروشید را به *گرم* تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 2.5 (دو گرم و نیم)\n"
    "   • 10 (ده گرم)\n"
    "   • 0.5 (نیم گرم)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

PROMPT_ENTER_AMOUNT_SELL_RIAL: Final[str] = (
    "💰 *ورود مبلغ دریافتی*\n\n"
    "💼 موجودی فعلی شما: *{balance} گرم*\n\n"
    "لطفاً مبلغی که می‌خواهید از فروش طلا دریافت کنید را به *ریال* تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 1000000 (یک میلیون)\n"
    "   • 5000000 (پنج میلیون)\n"
    "   • 10000000 (ده میلیون)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

PROMPT_ENTER_AMOUNT_COUNT: Final[str] = (
    "🔢 *ورود تعداد*\n\n"
    "لطفاً تعداد مورد نظر را تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 1 (یک عدد)\n"
    "   • 5 (پنج عدد)\n"
    "   • 10 (ده عدد)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

PROMPT_ENTER_AMOUNT_SELL_COUNT: Final[str] = (
    "🔢 *ورود تعداد برای فروش*\n\n"
    "💼 موجودی فعلی شما: *{balance} عدد*\n\n"
    "لطفاً تعداد مورد نظر برای فروش را تایپ کنید:\n\n"
    "💡 مثال‌ها:\n"
    "   • 1 (یک عدد)\n"
    "   • 5 (پنج عدد)\n"
    "   • 10 (ده عدد)\n\n"
    "✍️ عدد مورد نظر را تایپ کنید..."
)

# ==================== History Messages ====================
NO_ORDERS: Final[str] = (
    "📜 شما هنوز معامله‌ای ندارید.\n\n"
    "از منوی اصلی می‌توانید معامله جدید انجام دهید."
)

ORDERS_HISTORY_HEADER: Final[str] = (
    "📜 *تاریخچه معاملات شما:*\n\n"
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
    "کد ملی: {national_code}\n"
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
BTN_METHOD_GRAMS: Final[str] = "⚖️ محاسبه بر اساس گرم"
BTN_METHOD_RIAL: Final[str] = "💰 محاسبه بر اساس ریال"
BTN_METHOD_COUNT: Final[str] = "🔢 محاسبه بر اساس تعداد"
BTN_CONFIRM: Final[str] = "✅ تایید و ثبت نهایی"
BTN_CANCEL: Final[str] = "❌ لغو عملیات"
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

# ==================== Reporting & Export ====================
# Date range presets for filtering
REPORT_LAST_7_DAYS: Final[str] = "last_7_days"
REPORT_LAST_30_DAYS: Final[str] = "last_30_days"
REPORT_THIS_MONTH: Final[str] = "this_month"
REPORT_LAST_MONTH: Final[str] = "last_month"
REPORT_CUSTOM: Final[str] = "custom"

# Report types
REPORT_TYPE_TRANSACTIONS: Final[str] = "transactions"
REPORT_TYPE_ORDERS: Final[str] = "orders"
REPORT_TYPE_SUMMARY: Final[str] = "summary"

# Export formats
EXPORT_FORMAT_CSV: Final[str] = "csv"
EXPORT_FORMAT_PDF: Final[str] = "pdf"

# Report menu buttons
BTN_VIEW_HISTORY: Final[str] = "📊 مشاهده تاریخچه"
BTN_FILTER_HISTORY: Final[str] = "🔍 فیلتر تاریخچه"
BTN_EXPORT_HISTORY: Final[str] = "📥 دریافت گزارش"
BTN_SUMMARY: Final[str] = "📈 خلاصه آمار"

# Date range buttons
BTN_LAST_7_DAYS: Final[str] = "📅 7 روز گذشته"
BTN_LAST_30_DAYS: Final[str] = "📅 30 روز گذشته"
BTN_THIS_MONTH: Final[str] = "📅 این ماه"
BTN_LAST_MONTH: Final[str] = "📅 ماه گذشته"
BTN_CUSTOM_RANGE: Final[str] = "📅 بازه دلخواه"
BTN_ALL_TIME: Final[str] = "📅 کل"

# Transaction type filters
BTN_FILTER_BUY: Final[str] = "خرید"
BTN_FILTER_SELL: Final[str] = "فروش"
BTN_FILTER_DEPOSIT: Final[str] = "واریز"
BTN_FILTER_WITHDRAW: Final[str] = "برداشت"

# Export format buttons
BTN_EXPORT_CSV: Final[str] = "📊 Excel/CSV"
BTN_EXPORT_PDF: Final[str] = "📄 PDF"

# Report messages
MSG_REPORT_GENERATING: Final[str] = (
    "⏳ *در حال تهیه گزارش...*\n\n"
    "لطفاً چند لحظه صبر کنید..."
)

MSG_REPORT_READY: Final[str] = (
    "✅ *گزارش شما آماده است!*\n\n"
    "📊 تعداد رکورد: {count}\n"
    "📅 بازه زمانی: {period}\n\n"
    "فایل در پیام بعدی ارسال می‌شود..."
)

MSG_REPORT_EMPTY: Final[str] = (
    "ℹ️ *هیچ رکوردی یافت نشد*\n\n"
    "در بازه زمانی انتخابی، هیچ تراکنشی ثبت نشده است.\n"
    "لطفاً بازه زمانی دیگری را انتخاب کنید."
)

MSG_REPORT_ERROR: Final[str] = (
    "❌ *خطا در تهیه گزارش*\n\n"
    "متأسفانه در تهیه گزارش مشکلی پیش آمد.\n"
    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
)

MSG_SUMMARY_REPORT: Final[str] = (
    "📊 *خلاصه آمار معاملات شما*\n\n"
    "📅 *بازه زمانی:* {period}\n\n"
    "💰 *خرید:*\n"
    "   • تعداد: {buy_count} معامله\n"
    "   • مقدار کل: {buy_quantity} گرم\n"
    "   • مبلغ کل: {buy_amount:,} ریال\n"
    "   • میانگین قیمت: {buy_avg_price:,} ریال/گرم\n\n"
    "📈 *فروش:*\n"
    "   • تعداد: {sell_count} معامله\n"
    "   • مقدار کل: {sell_quantity} گرم\n"
    "   • مبلغ کل: {sell_amount:,} ریال\n"
    "   • میانگین قیمت: {sell_avg_price:,} ریال/گرم\n\n"
    "📊 *خالص:*\n"
    "   • مقدار: {net_quantity} گرم\n"
    "   • مبلغ: {net_amount:,} ریال\n\n"
    "💼 *موجودی فعلی:*\n"
    "   • ریال: {current_rial:,} ریال\n"
    "   • طلا: {current_gold} گرم\n"
    "   • سکه: {current_coin} عدد\n"
    "   • دلار: {current_dollar} دلار"
)

MSG_FILTER_PROMPT: Final[str] = (
    "🔍 *فیلتر تاریخچه معاملات*\n\n"
    "لطفاً بازه زمانی مورد نظر را انتخاب کنید:\n\n"
    "📅 می‌توانید از پیش‌فرض‌های آماده استفاده کنید\n"
    "یا بازه دلخواه خود را تعیین نمایید."
)

MSG_SELECT_EXPORT_FORMAT: Final[str] = (
    "📥 *انتخاب فرمت گزارش*\n\n"
    "لطفاً فرمت مورد نظر برای دریافت گزارش را انتخاب کنید:\n\n"
    "📊 *Excel/CSV:* مناسب برای ویرایش و تحلیل\n"
    "📄 *PDF:* مناسب برای چاپ و آرشیو\n\n"
    "💡 توجه: گزارش شامل {count} رکورد خواهد بود."
)

MSG_SELECT_REPORT_TYPE: Final[str] = (
    "📊 *انتخاب نوع گزارش*\n\n"
    "لطفاً نوع گزارش مورد نظر را انتخاب کنید:\n\n"
    "🔹 *تراکنش‌ها:* تمام واریز و برداشت‌ها\n"
    "🔹 *سفارشات:* تمام معاملات خرید و فروش\n"
    "🔹 *خلاصه آمار:* آمار کلی بدون جزئیات"
)

MSG_EXPORT_LIMITS: Final[str] = (
    "ℹ️ *محدودیت‌های گزارش:*\n\n"
    "• حداکثر {max_records} رکورد در هر گزارش\n"
    "• حداکثر بازه زمانی: {max_days} روز\n"
    "• فرمت CSV: تا 10,000 رکورد\n"
    "• فرمت PDF: تا 1,000 رکورد\n\n"
    "برای گزارش‌های بزرگتر، لطفاً با پشتیبانی تماس بگیرید."
)

# Callback prefixes for reports
CALLBACK_REPORT_PREFIX: Final[str] = "report_"
CALLBACK_FILTER_PREFIX: Final[str] = "filter_"
CALLBACK_EXPORT_PREFIX: Final[str] = "export_"
CALLBACK_DATE_PREFIX: Final[str] = "date_"

# Specific report callbacks
CALLBACK_REPORT_TRANSACTIONS: Final[str] = "report_transactions"
CALLBACK_REPORT_ORDERS: Final[str] = "report_orders"
CALLBACK_REPORT_SUMMARY: Final[str] = "report_summary"
CALLBACK_EXPORT_CSV: Final[str] = "export_csv"
CALLBACK_EXPORT_PDF: Final[str] = "export_pdf"
CALLBACK_DATE_7D: Final[str] = "date_7d"
CALLBACK_DATE_30D: Final[str] = "date_30d"
CALLBACK_DATE_THIS_MONTH: Final[str] = "date_this_month"
CALLBACK_DATE_LAST_MONTH: Final[str] = "date_last_month"
CALLBACK_DATE_CUSTOM: Final[str] = "date_custom"
CALLBACK_DATE_ALL: Final[str] = "date_all"

# ==================== Portal Callbacks ====================
CALLBACK_PORTAL_REFRESH: Final[str] = "portal_refresh"
