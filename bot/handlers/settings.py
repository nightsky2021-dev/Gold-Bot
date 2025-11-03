"""
Settings and profile handlers.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from users.models import Profile
from trading.models import Order
from bot.constants import (
    ERROR_NOT_APPROVED,
    SETTINGS_MENU,
    PROFILE_DISPLAY,
    STATISTICS_DISPLAY,
    BTN_PROFILE,
    BTN_BANK_ACCOUNTS,
    BTN_STATISTICS,
)
from .base import get_or_create_profile

logger = logging.getLogger('bot.settings')


async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show settings menu with submenus."""
    if not update.message or not update.effective_user:
        return
        
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    keyboard = [
        [InlineKeyboardButton(BTN_PROFILE, callback_data="settings_profile")],
        [InlineKeyboardButton(BTN_BANK_ACCOUNTS, callback_data="settings_bank_accounts")],
        [InlineKeyboardButton(BTN_STATISTICS, callback_data="settings_statistics")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        SETTINGS_MENU,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user profile information."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    status = "✅ تأیید شده" if profile.is_approved else "⏳ در انتظار تأیید"
    display_name = await sync_to_async(profile.get_display_name)()
    
    profile_text = PROFILE_DISPLAY.format(
        full_name=display_name,
        phone_number=profile.phone_number,
        telegram_username=profile.telegram_username or "ندارد",
        created_at=profile.created_at.strftime('%Y/%m/%d'),
        status=status
    )
    
    await query.edit_message_text(profile_text, parse_mode='Markdown')


async def show_statistics(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user statistics dashboard."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Get statistics using sync_to_async for each query
    all_orders = profile.order_set.all()  # type: ignore[attr-defined]
    total_orders = await sync_to_async(all_orders.count)()
    completed_orders = await sync_to_async(all_orders.filter(status=Order.OrderStatus.COMPLETED).count)()
    pending_orders = await sync_to_async(all_orders.filter(status=Order.OrderStatus.PENDING).count)()
    cancelled_orders = await sync_to_async(all_orders.filter(status=Order.OrderStatus.CANCELLED).count)()
    
    # Calculate trade volume
    completed = all_orders.filter(status=Order.OrderStatus.COMPLETED)
    completed_list = await sync_to_async(list)(completed)
    trade_volume = sum(order.total_amount for order in completed_list)
    
    # Get favorite product
    completed_exists = await sync_to_async(completed.exists)()
    if completed_exists:
        from django.db.models import Count
        product_counts = await sync_to_async(lambda: list(completed.values('product__name').annotate(count=Count('id')).order_by('-count')))()
        favorite_product = product_counts[0]['product__name'] if product_counts else "ندارد"
    else:
        favorite_product = "ندارد"
    
    stats_text = STATISTICS_DISPLAY.format(
        total_orders=total_orders,
        completed_orders=completed_orders,
        pending_orders=pending_orders,
        cancelled_orders=cancelled_orders,
        trade_volume=trade_volume,
        favorite_product=favorite_product,
        member_since=profile.created_at.strftime('%Y/%m/%d')
    )
    
    await query.edit_message_text(stats_text, parse_mode='Markdown')
