"""
کیبوردهای مورد استفاده در ربات تلگرام
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from .constants import (
    MENU_PRICES, MENU_HISTORY, MENU_CANCEL, MENU_WALLET, MENU_ACCOUNT,
    CALLBACK_PRICE_GOLD, CALLBACK_PRICE_COIN, CALLBACK_PRICE_DOLLAR, CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH, CALLBACK_BACK_TO_PRICES_MENU,
    CALLBACK_TRADE_PRODUCT_PREFIX, CALLBACK_ACTION_BUY, CALLBACK_ACTION_SELL,
    CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL, CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO,
    CALLBACK_BACK_TO_MAIN, PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد منوی اصلی بهینه شده"""
    keyboard = [
        [MENU_PRICES],
        [MENU_WALLET, MENU_ACCOUNT],
        [MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد درخواست شماره تماس"""
    keyboard = [
        [KeyboardButton("📱 ارسال شماره تماس", request_contact=True)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_prices_menu_keyboard(products=None) -> InlineKeyboardMarkup:
    """کیبورد منوی قیمت‌ها با دکمه‌های اینلاین بهینه شده
    
    Args:
        products: لیست محصولات از دیتابیس (اگر None باشد، از دکمه‌های قدیمی استفاده می‌شود)
    """
    keyboard = []
    
    if products:
        # ایجاد دکمه برای هر محصول به صورت داینامیک
        # هر ردیف 2 دکمه
        row = []
        for i, product in enumerate(products):
            # انتخاب ایموجی بر اساس نوع محصول
            emoji = "💰"  # پیش‌فرض
            if 'coin' in product.product_code or 'سکه' in product.name:
                emoji = "🥇"
            elif 'dollar' in product.product_code or 'دلار' in product.name:
                emoji = "💵"
            elif 'euro' in product.product_code or 'یورو' in product.name:
                emoji = "💶"
            elif 'pound' in product.product_code or 'پوند' in product.name:
                emoji = "💷"
            elif 'yuan' in product.product_code or 'یوان' in product.name:
                emoji = "💴"
            elif 'lira' in product.product_code or 'لیر' in product.name:
                emoji = "💵"
            elif 'dirham' in product.product_code or 'درهم' in product.name:
                emoji = "💸"
            elif 'gold' in product.product_code or 'طلا' in product.name:
                emoji = "🪙"
            
            button = InlineKeyboardButton(
                f"{emoji} {product.name}", 
                callback_data=f"price_{product.product_code}"
            )
            row.append(button)
            
            # هر 2 دکمه یک ردیف
            if len(row) == 2 or i == len(products) - 1:
                keyboard.append(row)
                row = []
        
        # دکمه مشاهده همه
        keyboard.append([InlineKeyboardButton("📊 مشاهده همه قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)])
    else:
        # Fallback به دکمه‌های قدیمی
        keyboard = [
            [
                InlineKeyboardButton("🪙 طلای آبشده", callback_data=CALLBACK_PRICE_GOLD),
                InlineKeyboardButton("🥇 سکه تمام", callback_data=CALLBACK_PRICE_COIN),
            ],
            [InlineKeyboardButton("💵 دلار", callback_data=CALLBACK_PRICE_DOLLAR)],
            [InlineKeyboardButton("📊 مشاهده همه قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)],
        ]
    
    return InlineKeyboardMarkup(keyboard)


def get_product_detail_keyboard(product_code: str, can_trade: bool = True, is_expired: bool = False) -> InlineKeyboardMarkup:
    """
    کیبورد جزئیات محصول با گزینه خرید/فروش
    
    Args:
        product_code: کد محصول (gold, coin, dollar)
        can_trade: آیا کاربر می‌تواند معامله کند
        is_expired: آیا قیمت منقضی شده است (بیش از 1 دقیقه)
    """
    keyboard = []
    
    if is_expired:
        # اگر منقضی شده، فقط دکمه رفرش نمایش بده
        keyboard.append([
            InlineKeyboardButton("🔄 بروزرسانی قیمت", callback_data=f"{CALLBACK_PRICE_REFRESH}{product_code}")
        ])
    elif can_trade:
        # اگر هنوز معتبر است، دکمه‌های خرید/فروش نمایش بده
        keyboard.append([
            InlineKeyboardButton("🟢 خرید", callback_data=f"{CALLBACK_TRADE_PRODUCT_PREFIX}{product_code}_{CALLBACK_ACTION_BUY}"),
            InlineKeyboardButton("🔴 فروش", callback_data=f"{CALLBACK_TRADE_PRODUCT_PREFIX}{product_code}_{CALLBACK_ACTION_SELL}"),
        ])
        keyboard.append([
            InlineKeyboardButton("🔄 بروزرسانی قیمت", callback_data=f"{CALLBACK_PRICE_REFRESH}{product_code}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_PRICES_MENU)])
    
    return InlineKeyboardMarkup(keyboard)


def get_amount_method_keyboard(product_code: str | None = None) -> InlineKeyboardMarkup:
    """دریافت کیبورد انتخاب روش محاسبه - استایل شیشه‌ای
    
    Args:
        product_code: کد محصول (gold, coin, dollar)
    """
    keyboard = []
    
    # همیشه گزینه مقدار را نمایش بده
    keyboard.append([InlineKeyboardButton("⚖️ محاسبه بر اساس مقدار (گرم/عدد)", callback_data=CALLBACK_METHOD_GRAM)])
    
    # فقط برای طلای آبشده گزینه مبلغ را نمایش بده
    if product_code == PRODUCT_GOLD:
        keyboard.append([InlineKeyboardButton("💰 محاسبه بر اساس مبلغ (ریال)", callback_data=CALLBACK_METHOD_RIAL)])
    
    keyboard.append([InlineKeyboardButton("🔙 انصراف", callback_data=CALLBACK_CONFIRM_NO)])
    
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد تایید نهایی - استایل شیشه‌ای"""
    keyboard = [
        [InlineKeyboardButton("✨ تایید و ثبت سفارش ✨", callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data=CALLBACK_CONFIRM_NO)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد لغو"""
    keyboard = [[MENU_CANCEL]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_to_prices_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد بازگشت به قیمت‌ها (Inline)"""
    keyboard = [
        [InlineKeyboardButton("📊 مشاهده قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)],
    ]
    return InlineKeyboardMarkup(keyboard)

