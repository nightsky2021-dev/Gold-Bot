"""
Constants and configuration for Telegram bot
"""

# ==================== Conversation States ====================
# حالت‌های مختلف در ConversationHandler برای خرید و فروش

# Registration states
(WAITING_FOR_PHONE,) = range(1)

# Buy flow states
(
    SELECTING_PRODUCT_BUY,
    SELECTING_METHOD_BUY,
    ENTERING_AMOUNT_BUY,
    CONFIRMING_BUY,
) = range(100, 104)

# Sell flow states
(
    SELECTING_PRODUCT_SELL,
    SELECTING_METHOD_SELL,
    ENTERING_AMOUNT_SELL,
    CONFIRMING_SELL,
) = range(200, 204)


# ==================== Callback Data Patterns ====================
# الگوهای callback_data برای دکمه‌های شیشه‌ای

# Product selection
CALLBACK_PRODUCT_BUY = "buy_product_{}"
CALLBACK_PRODUCT_SELL = "sell_product_{}"

# Method selection
CALLBACK_METHOD_RIAL = "method_rial"
CALLBACK_METHOD_GRAM = "method_gram"

# Confirmation
CALLBACK_CONFIRM_YES = "confirm_yes"
CALLBACK_CONFIRM_NO = "confirm_no"
CALLBACK_CANCEL = "cancel"


# ==================== Menu Options ====================
# گزینه‌های منوی اصلی

MENU_PRICES = "📈 قیمت لحظه‌ای"
MENU_BUY = "💰 خرید طلا"
MENU_SELL = "🛒 فروش طلا"
MENU_PORTFOLIO = "📊 پورتفولیو من"
MENU_HISTORY = "📜 تاریخچه سفارشات"


# ==================== Messages ====================
# پیام‌های استاندارد ربات

MSG_WELCOME_NEW = """
سلام! 👋

به ربات معاملات طلای آنلاین خوش آمدید.

برای شروع، لطفاً روی دکمه زیر کلیک کنید تا شماره تماس خود را با ما به اشتراک بگذارید.
این اطلاعات برای احراز هویت شما لازم است.
"""

MSG_REGISTRATION_PENDING = """
✅ ثبت‌نام شما با موفقیت انجام شد!

حساب شما در انتظار تایید مدیر است.
لطفاً صبور باشید، ادمین در اسرع وقت حساب شما را بررسی خواهد کرد.

شما از طریق همین ربات از وضعیت حساب خود مطلع خواهید شد.
"""

MSG_NOT_APPROVED = """
⏳ حساب شما هنوز تایید نشده است.

لطفاً صبور باشید. پس از تایید حساب توسط مدیر، می‌توانید از تمامی امکانات استفاده کنید.

در صورت نیاز به پشتیبانی، با ادمین تماس بگیرید.
"""

MSG_WELCOME_APPROVED = """
✨ خوش آمدید!

حساب شما فعال است و می‌توانید از تمامی امکانات استفاده کنید.

از منوی زیر گزینه مورد نظر خود را انتخاب کنید:
"""

MSG_INVALID_INPUT = """
❌ ورودی نامعتبر است.

لطفاً یک عدد معتبر وارد کنید.
"""

MSG_INSUFFICIENT_BALANCE = """
❌ موجودی شما کافی نیست.

لطفاً ابتدا موجودی خود را شارژ کنید یا مقدار کمتری را وارد نمایید.
"""

MSG_ORDER_SUCCESS = """
✅ سفارش شما با موفقیت ثبت شد!

شماره سفارش: `{order_id}`

سفارش شما در انتظار بررسی و تایید مدیر است.
پس از تایید، موجودی شما به‌روزرسانی خواهد شد.

از صبر و شکیبایی شما سپاسگزاریم.
"""

MSG_CANCELLED = """
❌ عملیات لغو شد.

برای شروع مجدد، از منوی اصلی استفاده کنید.
"""

MSG_ERROR = """
❌ خطایی رخ داد!

لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.

جزئیات خطا: {}
"""


# ==================== Button Labels ====================
# برچسب‌های دکمه‌ها

BTN_SHARE_CONTACT = "📱 اشتراک‌گذاری شماره تماس"
BTN_RIAL = "💵 بر اساس مبلغ (ریال)"
BTN_GRAM = "⚖️ بر اساس وزن (گرم)"
BTN_CONFIRM = "✅ تایید نهایی"
BTN_CANCEL = "❌ لغو"
BTN_BACK = "🔙 بازگشت"


# ==================== Validation ====================
# محدودیت‌ها و اعتبارسنجی

MIN_ORDER_RIAL = 100000  # حداقل مبلغ سفارش: 100,000 ریال
MIN_ORDER_GRAM = 0.01    # حداقل وزن سفارش: 0.01 گرم
MAX_ORDER_RIAL = 1000000000  # حداکثر مبلغ سفارش: 1 میلیارد ریال
MAX_ORDER_GRAM = 10000   # حداکثر وزن سفارش: 10 کیلوگرم
