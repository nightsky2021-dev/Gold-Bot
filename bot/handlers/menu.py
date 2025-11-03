"""
Main menu and navigation handlers.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async

from users.models import Profile
from trading.services import OrderService
from bot.constants import (
    ERROR_NOT_APPROVED,
    NO_ORDERS,
    ORDERS_HISTORY_HEADER,
    ORDER_CANCELLED,
    PROFILE_DISPLAY,
    BTN_BANK_ACCOUNTS,
    BTN_STATISTICS,
)
from .base import get_or_create_profile, get_main_menu_keyboard

logger = logging.getLogger('bot.menu')


async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user account information (alias for settings)."""
    if not update.message or not update.effective_user:
        return
        
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Show profile information
    status = "✅ تأیید شده" if profile.is_approved else "⏳ در انتظار تأیید"
    display_name = await sync_to_async(profile.get_display_name)()
    
    profile_text = PROFILE_DISPLAY.format(
        full_name=display_name,
        phone_number=profile.phone_number,
        telegram_username=profile.telegram_username or "ندارد",
        created_at=profile.created_at.strftime('%Y/%m/%d'),
        status=status
    )
    
    # Add settings menu keyboard
    keyboard = [
        [InlineKeyboardButton(BTN_BANK_ACCOUNTS, callback_data="settings_bank_accounts")],
        [InlineKeyboardButton(BTN_STATISTICS, callback_data="settings_statistics")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        profile_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's order history (increased to 10 orders)."""
    if not update.message:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Increased from 5 to 10
    orders = await sync_to_async(OrderService.get_user_orders)(profile, limit=10)
    
    if not orders:
        await update.message.reply_text(NO_ORDERS, parse_mode='Markdown')
        return
    
    message = ORDERS_HISTORY_HEADER
    
    for order in orders:
        message += OrderService.format_order_for_display(order) + "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current conversation."""
    if not update.message or context.user_data is None:
        return ConversationHandler.END
        
    await update.message.reply_text(
        ORDER_CANCELLED,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    
    return ConversationHandler.END
