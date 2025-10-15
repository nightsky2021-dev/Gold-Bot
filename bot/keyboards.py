"""
کیبوردهای مورد استفاده در ربات تلگرام
"""
from typing import List
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from trading.models import Product
from .constants import (
    MENU_PRICES, MENU_BUY, MENU_SELL, MENU_PORTFOLIO, MENU_HISTORY, MENU_CANCEL,
    CALLBACK_PRODUCT_PREFIX, CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL,
    CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO, CALLBACK_BUY_PREFIX, CALLBACK_SELL_PREFIX
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد منوی اصلی"""
    keyboard = [
        [MENU_PRICES],
        [MENU_BUY, MENU_SELL],
        [MENU_PORTFOLIO, MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد درخواست شماره تماس"""
    keyboard = [
        [KeyboardButton("📱 ارسال شماره تماس", request_contact=True)],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def get_products_keyboard(products: List[Product], action_prefix: str) -> InlineKeyboardMarkup:
    """
    دریافت کیبورد محصولات
    
    Args:
        products: لیست محصولات
        action_prefix: پیشوند برای callback (مثلا 'buy_' یا 'sell_')
    """
    keyboard = []
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                f"{product.name}",
                callback_data=f"{action_prefix}{CALLBACK_PRODUCT_PREFIX}{product.id}"
            )
        ])
    keyboard.append([InlineKeyboardButton("❌ لغو", callback_data="cancel")])
    return InlineKeyboardMarkup(keyboard)


def get_amount_method_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد انتخاب روش محاسبه"""
    keyboard = [
        [InlineKeyboardButton("💵 مبلغ (ریال)", callback_data=CALLBACK_METHOD_RIAL)],
        [InlineKeyboardButton("⚖️ مقدار (گرم)", callback_data=CALLBACK_METHOD_GRAM)],
        [InlineKeyboardButton("❌ لغو", callback_data="cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """دریافت کیبورد تایید نهایی"""
    keyboard = [
        [InlineKeyboardButton("✅ تایید نهایی", callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton("❌ لغو", callback_data=CALLBACK_CONFIRM_NO)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """دریافت کیبورد لغو"""
    keyboard = [[MENU_CANCEL]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
