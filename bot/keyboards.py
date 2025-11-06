"""
کیبوردهای مورد استفاده در ربات تلگرام
"""
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from typing import List, TYPE_CHECKING
from .constants import (
    MENU_PRICES, MENU_PORTFOLIO, MENU_HISTORY, MENU_CANCEL, MENU_WALLET, MENU_ACCOUNT,
    CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH, CALLBACK_BACK_TO_PRICES_MENU,
    CALLBACK_TRADE_PRODUCT_PREFIX, CALLBACK_ACTION_BUY, CALLBACK_ACTION_SELL,
    CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL, CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO,
    CALLBACK_BACK_TO_MAIN, PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR,
    CURRENCY_PRODUCTS, COIN_PRODUCTS, GOLD_PRODUCTS
)

if TYPE_CHECKING:
    from trading.models import Product


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد منوی اصلی بهینه شده"""
    keyboard = [
        [MENU_PRICES],
        [MENU_WALLET, MENU_ACCOUNT],
        [MENU_PORTFOLIO, MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد درخواست شماره تماس"""
    keyboard = [
        [KeyboardButton("📱 ارسال شماره تماس", request_contact=True)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_prices_menu_keyboard(products: List['Product'] | None = None) -> InlineKeyboardMarkup:
    """
    کیبورد منوی قیمت‌ها با دکمه‌های اینلاین - پشتیبانی از تمام محصولات
    
    Args:
        products: لیست محصولات فعال (اگر None باشد، کیبورد ساده برگردانده می‌شود)
    """
    keyboard = []
    
    if products:
        # Group products by category for better layout
        # Add emoji based on product type
        product_emojis = {
            # Currencies
            'dollar_usa': '💵',
            'euro': '💶',
            'lira_turkey': '🇹🇷',
            'yuan_china': '💴',
            'pound_uk': '💷',
            'dirham_uae': '🇦🇪',
            
            # Coins
            'coin_full': '🥇',
            'coin_half': '🥈',
            'coin_quarter': '🥉',
            
            # Gold
            'gold_abshodeh': '🪙',
        }
        
        # Create buttons in rows of 2
        row = []
        for product in products:
            emoji = product_emojis.get(product.product_code, '💰')
            button = InlineKeyboardButton(
                f"{emoji} {product.name}",
                callback_data=f"price_{product.product_code}"
            )
            row.append(button)
            
            # Add row when we have 2 buttons
            if len(row) == 2:
                keyboard.append(row)
                row = []
        
        # Add remaining button if any
        if row:
            keyboard.append(row)
    
    # Add "View All Prices" button
    keyboard.append([InlineKeyboardButton("📊 مشاهده همه قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)])
    
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

