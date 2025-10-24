"""
کیبوردهای مورد استفاده در ربات تلگرام
"""
from typing import List, Optional
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from trading.models import Product
from .constants import (
    MENU_PRICES, MENU_PORTFOLIO, MENU_HISTORY, MENU_REFRESH, MENU_CANCEL,
    CALLBACK_PRICE_GOLD, CALLBACK_PRICE_COIN, CALLBACK_PRICE_DOLLAR, CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH,
    CALLBACK_TRADE_PRODUCT_PREFIX, CALLBACK_ACTION_BUY, CALLBACK_ACTION_SELL,
    CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL, CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO,
    CALLBACK_BACK_TO_MAIN, PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد منوی اصلی بهینه شده"""
    keyboard = [
        [MENU_PRICES],
        [MENU_PORTFOLIO, MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد درخواست شماره تماس"""
    keyboard = [
        [KeyboardButton("📱 ارسال شماره تماس", request_contact=True)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_prices_menu_keyboard() -> InlineKeyboardMarkup:
    """کیبورد منوی قیمت‌ها با دکمه‌های اینلاین"""
    keyboard = [
        [InlineKeyboardButton("🪙 طلای آبشده", callback_data=CALLBACK_PRICE_GOLD)],
        [InlineKeyboardButton("🥇 سکه تمام", callback_data=CALLBACK_PRICE_COIN)],
        [InlineKeyboardButton("💵 دلار", callback_data=CALLBACK_PRICE_DOLLAR)],
        [InlineKeyboardButton("📊 همه قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)],
        [InlineKeyboardButton("🔄 به‌روزرسانی", callback_data=CALLBACK_PRICE_ALL)],
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
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_PRICE_ALL)])
    
    return InlineKeyboardMarkup(keyboard)


# تابع get_trade_menu_keyboard حذف شد
# معاملات اکنون از طریق بخش قیمت‌ها انجام می‌شوند


# تابع get_buy_sell_keyboard حذف شد
# دکمه‌های خرید/فروش مستقیماً در get_product_detail_keyboard هستند


def get_amount_method_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد انتخاب روش محاسبه"""
    keyboard = [
        [InlineKeyboardButton("⚖️ مقدار (گرم/عدد)", callback_data=CALLBACK_METHOD_GRAM)],
        [InlineKeyboardButton("💵 مبلغ (ریال)", callback_data=CALLBACK_METHOD_RIAL)],
        [InlineKeyboardButton("❌ لغو معامله", callback_data=CALLBACK_CONFIRM_NO)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد تایید نهایی"""
    keyboard = [
        [InlineKeyboardButton("✅ تایید و ثبت", callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton("❌ انصراف", callback_data=CALLBACK_CONFIRM_NO)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد لغو"""
    keyboard = [[MENU_CANCEL]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_back_to_prices_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد بازگشت به قیمت‌ها"""
    keyboard = [[MENU_PRICES]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

