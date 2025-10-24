"""
Keyboard layouts for the Telegram bot.

This module contains functions to generate various keyboard layouts
used throughout the bot conversations.
"""

from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from typing import List

from .constants import (
    MENU_PRICE,
    MENU_BUY,
    MENU_SELL,
    MENU_PORTFOLIO,
    MENU_HISTORY,
    BTN_SHARE_CONTACT,
    BTN_METHOD_GRAMS,
    BTN_METHOD_RIAL,
    BTN_CONFIRM,
    BTN_CANCEL,
    PRODUCT_PREFIX,
    METHOD_PREFIX,
    CONFIRM_PREFIX,
    CANCEL_PREFIX,
    METHOD_GRAMS,
    METHOD_RIAL,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    Get the main menu keyboard.
    
    Returns:
        ReplyKeyboardMarkup with main menu options.
    """
    keyboard = [
        [MENU_PRICE, MENU_BUY],
        [MENU_SELL, MENU_PORTFOLIO],
        [MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """
    Get the keyboard for sharing contact information.
    
    Returns:
        ReplyKeyboardMarkup with contact sharing button.
    """
    keyboard = [
        [KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True
    )


def get_products_keyboard(products: list) -> InlineKeyboardMarkup:
    """
    Generate inline keyboard for product selection.
    
    Args:
        products: List of Product objects
        
    Returns:
        InlineKeyboardMarkup with product buttons.
    """
    keyboard = []
    for product in products:
        button = InlineKeyboardButton(
            text=product.name,
            callback_data=f"{PRODUCT_PREFIX}{product.id}"
        )
        keyboard.append([button])
    
    return InlineKeyboardMarkup(keyboard)


def get_method_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for calculation method selection.
    
    Returns:
        InlineKeyboardMarkup with method selection buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=BTN_METHOD_GRAMS,
                callback_data=f"{METHOD_PREFIX}{METHOD_GRAMS}"
            )
        ],
        [
            InlineKeyboardButton(
                text=BTN_METHOD_RIAL,
                callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Get keyboard for order confirmation.
    
    Returns:
        InlineKeyboardMarkup with confirm/cancel buttons.
    """
    keyboard = [
        [
            InlineKeyboardButton(
                text=BTN_CONFIRM,
                callback_data=f"{CONFIRM_PREFIX}yes"
            ),
            InlineKeyboardButton(
                text=BTN_CANCEL,
                callback_data=f"{CANCEL_PREFIX}no"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Get keyboard with cancel button.
    
    Returns:
        ReplyKeyboardMarkup with cancel button.
    """
    keyboard = [[BTN_CANCEL]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )

