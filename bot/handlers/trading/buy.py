"""Buy operation handlers."""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler

from trading.models import Order
from bot.constants import (
    PROMPT_SELECT_PRODUCT,
    PROMPT_SELECT_METHOD,
    PROMPT_SELECT_METHOD_COUNT,
    BTN_CANCEL,
    BTN_METHOD_GRAMS,
    BTN_METHOD_RIAL,
    BTN_METHOD_COUNT,
    PRODUCT_PREFIX,
    CANCEL_PREFIX,
    METHOD_PREFIX,
    PRODUCT_COIN,
    PRODUCT_DOLLAR,
    SELECTING_PRODUCT,
    SELECTING_METHOD,
)
from .base import BaseTradeHandler

logger = logging.getLogger('bot.trading.buy')


async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start buy conversation - shows product list."""
    if not update.message:
        return ConversationHandler.END
    
    # Get and validate profile
    profile = await BaseTradeHandler.get_profile(update)
    if not await BaseTradeHandler.validate_user_approved(update, profile):
        return ConversationHandler.END
    
    # Get active products
    products = await BaseTradeHandler.get_active_products()
    if not products:
        from bot.constants import ERROR_NO_PRODUCTS
        return await BaseTradeHandler.send_error_and_end(update, ERROR_NO_PRODUCTS)
    
    # Build keyboard
    keyboard = [
        [InlineKeyboardButton(
            f"{product.name} ({product.sell_price:,} ریال)",
            callback_data=f"{PRODUCT_PREFIX}{product.id}"
        )]
        for product in products
    ]
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")])
    
    await update.message.reply_text(
        PROMPT_SELECT_PRODUCT,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def buy_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection and show method selection."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END
    
    await query.answer()
    
    # Extract and validate product
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = await BaseTradeHandler.get_product_by_id(product_id)
    
    if not product:
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Store in context
    ctx = BaseTradeHandler.get_context(context)
    ctx.product_id = product_id
    ctx.order_type = Order.OrderType.BUY
    
    # Show method selection based on product type
    from bot.constants import METHOD_GRAMS, METHOD_RIAL, METHOD_COUNT
    
    if product.product_code in [PRODUCT_COIN, PRODUCT_DOLLAR]:
        keyboard = [
            [InlineKeyboardButton(BTN_METHOD_COUNT, callback_data=f"{METHOD_PREFIX}{METHOD_COUNT}")],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")]
        ]
        prompt = PROMPT_SELECT_METHOD_COUNT
    else:
        keyboard = [
            [InlineKeyboardButton(BTN_METHOD_GRAMS, callback_data=f"{METHOD_PREFIX}{METHOD_GRAMS}")],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")]
        ]
        prompt = PROMPT_SELECT_METHOD
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        prompt,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD
