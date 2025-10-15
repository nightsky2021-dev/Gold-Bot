"""
Constants for the Telegram bot.

Defines conversation states, keyboard layouts, and message templates.
"""

from typing import Final

# Conversation States
SELECTING_PRODUCT: Final[int] = 0
SELECTING_METHOD: Final[int] = 1
ENTERING_AMOUNT: Final[int] = 2
CONFIRMING_BUY: Final[int] = 3
CONFIRMING_SELL: Final[int] = 4

# Callback Data Prefixes
PRODUCT_PREFIX: Final[str] = "product_"
METHOD_PREFIX: Final[str] = "method_"
CONFIRM_PREFIX: Final[str] = "confirm_"
CANCEL_PREFIX: Final[str] = "cancel_"

# Calculation Methods
METHOD_GRAMS: Final[str] = "grams"
METHOD_RIAL: Final[str] = "rial"

# Main Menu Buttons
MENU_PRICE: Final[str] = "📈 قیمت لحظه‌ای"
MENU_BUY: Final[str] = "💰 خرید طلا"
MENU_SELL: Final[str] = "🛒 فروش طلا"
MENU_PORTFOLIO: Final[str] = "📊 پورتفولیو من"
MENU_HISTORY: Final[str] = "📜 تاریخچه سفارشات"
MENU_CANCEL: Final[str] = "❌ لغو"

# Welcome Messages
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

# Error Messages
ERROR_NOT_APPROVED: Final[str] = (
    "⚠️ حساب شما هنوز تأیید نشده است.\n"
    "لطفاً منتظر تایید مدیر باشید."
)

ERROR_INVALID_AMOUNT: Final[str] = (
    "❌ مقدار وارد شده نامعتبر است.\n"
    "لطفاً یک عدد معتبر وارد کنید."
)

ERROR_GENERAL: Final[str] = (
    "❌ متأسفانه خطایی رخ داد.\n"
    "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
)

ERROR_NO_PRODUCTS: Final[str] = (
    "❌ متأسفانه در حال حاضر محصولی برای معامله موجود نیست.\n"
    "لطفاً بعداً تلاش کنید."
)

# Order Messages
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

# Prompts
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

# History Messages
NO_ORDERS: Final[str] = (
    "📜 شما هنوز سفارشی ثبت نکرده‌اید.\n\n"
    "از منوی اصلی می‌توانید سفارش جدید ثبت کنید."
)

ORDERS_HISTORY_HEADER: Final[str] = (
    "📜 *آخرین سفارشات شما:*\n\n"
)

# Button Texts
BTN_SHARE_CONTACT: Final[str] = "📱 ارسال شماره تماس"
BTN_METHOD_GRAMS: Final[str] = "⚖️ بر اساس مقدار (گرم)"
BTN_METHOD_RIAL: Final[str] = "💰 بر اساس مبلغ (ریال)"
BTN_CONFIRM: Final[str] = "✅ تایید نهایی"
BTN_CANCEL: Final[str] = "❌ لغو"
BTN_BACK_TO_MENU: Final[str] = "🔙 بازگشت به منوی اصلی"
