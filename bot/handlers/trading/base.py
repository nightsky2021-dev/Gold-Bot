"""Base utilities and classes for trading handlers."""

import logging
import time
from abc import ABC
from typing import Optional, List
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async

from users.models import Profile
from trading.models import Product, Order
from trading.services import ProductService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_NO_PRODUCTS,
    ERROR_GENERAL,
    CALLBACK_TRADE_PRODUCT_PREFIX,
    CALLBACK_ACTION_BUY,
    CALLBACK_ACTION_SELL,
    CALLBACK_METHOD_GRAM,
    CALLBACK_METHOD_RIAL,
    CALLBACK_METHOD_COUNT,
    CALLBACK_CONFIRM_NO,
    BTN_METHOD_COUNT,
    BTN_METHOD_GRAMS,
    BTN_METHOD_RIAL,
    BTN_CANCEL,
    PROMPT_SELECT_METHOD,
    PROMPT_SELECT_METHOD_COUNT,
    PRODUCT_COIN,
    PRODUCT_DOLLAR,
    SELECTING_METHOD,
)
from .context_manager import TradingContext

logger = logging.getLogger('bot.trading')


class BaseTradeHandler(ABC):
    """Base class for trade handlers with common functionality."""
    
    @staticmethod
    async def get_profile(update: Update) -> Optional[Profile]:
        """Get user profile with error handling."""
        if not update.effective_user:
            return None
        
        try:
            from bot.handlers.base import get_or_create_profile
            return await get_or_create_profile(update.effective_user)
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    @staticmethod
    async def validate_user_approved(update: Update, profile: Optional[Profile]) -> bool:
        """Validate user is approved and send error if not."""
        if not profile or not profile.is_approved:
            if update.message:
                await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
            return False
        return True
    
    @staticmethod
    async def get_active_products() -> List[Product]:
        """Get all active products."""
        return await sync_to_async(ProductService.get_active_products)()
    
    @staticmethod
    async def get_product_by_id(product_id: int) -> Optional[Product]:
        """Get product by ID."""
        return await sync_to_async(ProductService.get_product_by_id)(product_id)
    
    @staticmethod
    def get_context(context: ContextTypes.DEFAULT_TYPE) -> TradingContext:
        """Get trading context manager."""
        return TradingContext(context)
    
    @staticmethod
    async def send_error_and_end(update: Update, message: str = ERROR_GENERAL) -> int:
        """Send error message and end conversation."""
        if update.message:
            await update.message.reply_text(message, parse_mode='Markdown')
        elif update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode='Markdown')
        return ConversationHandler.END


class ProgressIndicator:
    """Helper class for showing operation progress."""
    
    @staticmethod
    async def show_processing(query, text: str = "در حال پردازش..."):
        """Show processing indicator."""
        if query:
            await query.answer(text)
    
    @staticmethod
    async def show_calculating(query):
        """Show calculating indicator."""
        await ProgressIndicator.show_processing(query, "در حال محاسبه...")
    
    @staticmethod
    async def show_validating(query):
        """Show validating indicator."""
        await ProgressIndicator.show_processing(query, "در حال بررسی...")


async def handle_trade_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle buy/sell action from product detail view."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await BaseTradeHandler.get_profile(update)
    
    if not await BaseTradeHandler.validate_user_approved(update, profile):
        return ConversationHandler.END
    
    # Parse callback data: "trade_gold_buy" or "trade_coin_sell"
    parts = query.data.replace(CALLBACK_TRADE_PRODUCT_PREFIX, "").split("_")
    if len(parts) != 2:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    product_code = parts[0]
    action = parts[1]  # 'buy' or 'sell'
    
    # Check if price has expired (more than 60 seconds)
    ctx = BaseTradeHandler.get_context(context)
    current_time = int(time.time())
    price_time = ctx.get_price_timestamp(product_code)
    
    if current_time - price_time > 60:
        # Price expired, show refresh message
        message = (
            "⚠️ *قیمت منقضی شده است!*\n\n"
            "قیمت‌ها بیش از 1 دقیقه قدیمی هستند.\n"
            "لطفاً قیمت را بروزرسانی کنید."
        )
        
        from bot.keyboards import get_product_detail_keyboard
        keyboard = get_product_detail_keyboard(product_code, can_trade=True, is_expired=True)
        
        await query.edit_message_text(
            message,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Get product
    product = await sync_to_async(
        lambda: Product.objects.filter(product_code=product_code, is_active=True).first()
    )()
    
    if not product:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Store in context and start buy/sell flow
    ctx.product_id = product.id  # type: ignore[attr-defined]
    ctx.order_type = Order.OrderType.BUY if action == CALLBACK_ACTION_BUY else Order.OrderType.SELL
    
    # Ask for calculation method based on product type
    # Coin and Dollar use count-based calculation, Gold uses weight-based
    if product.product_code in [PRODUCT_COIN, PRODUCT_DOLLAR]:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(BTN_METHOD_COUNT, callback_data=CALLBACK_METHOD_COUNT)],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=CALLBACK_METHOD_RIAL)],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CONFIRM_NO)]
        ])
        prompt_text = PROMPT_SELECT_METHOD_COUNT
    else:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(BTN_METHOD_GRAMS, callback_data=CALLBACK_METHOD_GRAM)],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=CALLBACK_METHOD_RIAL)],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CONFIRM_NO)]
        ])
        prompt_text = PROMPT_SELECT_METHOD
    
    await query.edit_message_text(
        prompt_text,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD
