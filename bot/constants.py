"""
ثوابت و حالت‌های مورد استفاده در ربات تلگرام
"""

# حالت‌های ConversationHandler
(
    SELECTING_PRODUCT,
    SELECTING_ACTION,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_TRADE,
    ENTERING_FIRST_NAME,
    ENTERING_LAST_NAME,
    ENTERING_NATIONAL_CODE,
) = range(8)

# متن‌های منو اصلی
MENU_PRICES = "💰 قیمت و معامله"
MENU_TRADE = "💎 معامله"
MENU_PORTFOLIO = "👛 کیف پول"
MENU_HISTORY = "📋 تاریخچه"
MENU_REFRESH = "🔄 به‌روزرسانی قیمت‌ها"
MENU_CANCEL = "❌ بازگشت"

# Callback Data Patterns - قیمت‌ها
CALLBACK_PRICE_GOLD = "price_gold"
CALLBACK_PRICE_COIN = "price_coin"
CALLBACK_PRICE_DOLLAR = "price_dollar"
CALLBACK_PRICE_ALL = "price_all"
CALLBACK_PRICE_REFRESH = "price_refresh_"  # + product_code
CALLBACK_BACK_TO_MAIN = "back_main"

# Callback Data Patterns - معامله
CALLBACK_TRADE_PRODUCT_PREFIX = "trade_"
CALLBACK_ACTION_BUY = "action_buy"
CALLBACK_ACTION_SELL = "action_sell"
CALLBACK_METHOD_GRAM = "method_gram"
CALLBACK_METHOD_RIAL = "method_rial"
CALLBACK_CONFIRM_YES = "confirm_yes"
CALLBACK_CONFIRM_NO = "confirm_no"

# Product Codes (for callbacks)
PRODUCT_GOLD = "gold"
PRODUCT_COIN = "coin"
PRODUCT_DOLLAR = "dollar"

