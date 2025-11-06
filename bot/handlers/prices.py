"""
Price viewing and refresh handlers.
"""

import logging
import time
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from trading.models import Product
from trading.services import ProductService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_NO_PRODUCTS,
    ERROR_GENERAL,
    CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH,
    CALLBACK_BACK_TO_PRICES_MENU,
)
from bot.keyboards import get_prices_menu_keyboard, get_product_detail_keyboard
from .base import get_or_create_profile

logger = logging.getLogger('bot.prices')


async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show prices menu with product selection buttons."""
    if not update.message or not update.effective_user:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    products = await sync_to_async(ProductService.get_active_products)()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    # Create inline keyboard with all active products
    keyboard = get_prices_menu_keyboard(products)
    
    message = (
        "📈 *قیمت‌ها و معامله*\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_product_price_view(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle product price view from inline buttons."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Extract product code from callback data (format: "price_product_code")
    if not query.data.startswith('price_'):
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return
    
    product_code = query.data.replace('price_', '')
    
    # Get product by code
    product = await sync_to_async(
        lambda: Product.objects.filter(product_code=product_code, is_active=True).first()
    )()
    
    if not product:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    # Store timestamp for price expiration check
    current_time = int(time.time())
    
    # Format product details with prices
    message = (
        f"📊 *{product.name}*\n\n"
        f"💰 *قیمت خرید* (شما به ما می‌فروشید):\n"
        f"    {product.buy_price:,} ریال\n\n"
        f"💵 *قیمت فروش* (شما از ما می‌خرید):\n"
        f"    {product.sell_price:,} ریال\n\n"
        f"⏱ *زمان بروزرسانی:* {product.updated_at.strftime('%H:%M:%S')}\n"
        f"⚠️ قیمت‌ها تا 1 دقیقه معتبر هستند."
    )
    
    # Get keyboard with buy/sell buttons
    keyboard = get_product_detail_keyboard(product_code, can_trade=True, is_expired=False)
    
    # Store price timestamp in callback data for expiration check
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    # Store timestamp in context for this message
    if context.user_data is not None:
        context.user_data[f'price_time_{product_code}'] = current_time


async def handle_product_price_all(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all product prices."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    products = await sync_to_async(ProductService.get_active_products)()
    
    if not products:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    message = "📊 *قیمت‌های همه محصولات:*\n\n"
    
    for product in products:
        message += (
            f"*{product.name}*\n"
            f"💰 خرید: {product.buy_price:,} ریال\n"
            f"💵 فروش: {product.sell_price:,} ریال\n\n"
        )
    
    message += f"⏱ آخرین بروزرسانی: {products[0].updated_at.strftime('%Y/%m/%d %H:%M:%S')}\n"
    message += "⚠️ قیمت‌ها تا 1 دقیقه معتبر هستند."
    
    # Add back button
    keyboard = get_prices_menu_keyboard()
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_price_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle price refresh request."""
    query = update.callback_query
    if not query or not query.data or not update.effective_user:
        return
    
    await query.answer("🔄 در حال بروزرسانی قیمت...")
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Extract product code from callback data (e.g., "price_refresh_gold" -> "gold")
    product_code = query.data.replace(CALLBACK_PRICE_REFRESH, "")
    
    # Get fresh product data
    product = await sync_to_async(
        lambda: Product.objects.filter(product_code=product_code, is_active=True).first()
    )()
    
    if not product:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    # Update timestamp
    current_time = int(time.time())
    
    if context.user_data is not None:
        context.user_data[f'price_time_{product_code}'] = current_time
    
    # Format updated product details
    message = (
        f"📊 *{product.name}*\n\n"
        f"💰 *قیمت خرید* (شما به ما می‌فروشید):\n"
        f"    {product.buy_price:,} ریال\n\n"
        f"💵 *قیمت فروش* (شما از ما می‌خرید):\n"
        f"    {product.sell_price:,} ریال\n\n"
        f"⏱ *زمان بروزرسانی:* {product.updated_at.strftime('%H:%M:%S')}\n"
        f"⚠️ قیمت‌ها تا 1 دقیقه معتبر هستند."
    )
    
    keyboard = get_product_detail_keyboard(product_code, can_trade=True, is_expired=False)
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def handle_back_to_prices_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle back to prices menu."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    products = await sync_to_async(ProductService.get_active_products)()
    
    if not products:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    # Pass products list to keyboard function
    keyboard = get_prices_menu_keyboard(products)
    
    message = (
        "📈 *قیمت‌ها و معامله*\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
