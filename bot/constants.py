"""
ثوابت و حالت‌های مورد استفاده در ربات تلگرام
"""

# حالت‌های ConversationHandler
(
    SELECTING_PRODUCT,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_BUY,
    CONFIRMING_SELL,
) = range(5)

# متن‌های منو
MENU_PRICES = "📈 قیمت لحظه‌ای"
MENU_BUY = "💰 خرید طلا"
MENU_SELL = "🛒 فروش طلا"
MENU_PORTFOLIO = "📊 پورتفولیو من"
MENU_HISTORY = "📜 تاریخچه سفارشات"
MENU_CANCEL = "❌ لغو"

# Callback Data Patterns
CALLBACK_PRODUCT_PREFIX = "product_"
CALLBACK_METHOD_GRAM = "method_gram"
CALLBACK_METHOD_RIAL = "method_rial"
CALLBACK_CONFIRM_YES = "confirm_yes"
CALLBACK_CONFIRM_NO = "confirm_no"
CALLBACK_BUY_PREFIX = "buy_"
CALLBACK_SELL_PREFIX = "sell_"
