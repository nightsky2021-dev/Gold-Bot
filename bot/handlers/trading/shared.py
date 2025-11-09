"""Shared handlers for both buy and sell operations."""

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from trading.models import Order
from trading.services import OrderService
from bot.constants import (
    ERROR_GENERAL,
    ERROR_INVALID_AMOUNT,
    CALLBACK_METHOD_GRAM,
    CALLBACK_METHOD_RIAL,
    CALLBACK_METHOD_COUNT,
    CALLBACK_CONFIRM_NO,
    METHOD_GRAMS,
    METHOD_RIAL,
    METHOD_COUNT,
    METHOD_PREFIX,
    PRODUCT_PREFIX,
    CANCEL_PREFIX,
    CURRENCY_PRODUCTS,
    COIN_PRODUCTS,
    GOLD_PRODUCTS,
    PROMPT_SELECT_METHOD,
    PROMPT_SELECT_METHOD_COUNT,
    PROMPT_ENTER_AMOUNT_GRAMS,
    PROMPT_ENTER_AMOUNT_RIAL,
    PROMPT_ENTER_AMOUNT_COUNT,
    PROMPT_ENTER_AMOUNT_SELL_GRAMS,
    PROMPT_ENTER_AMOUNT_SELL_RIAL,
    PROMPT_ENTER_AMOUNT_SELL_COUNT,
    BTN_METHOD_GRAMS,
    BTN_METHOD_RIAL,
    BTN_METHOD_COUNT,
    BTN_CANCEL,
    ENTERING_AMOUNT,
    CONFIRMING_BUY,
    CONFIRMING_SELL,
    SELECTING_METHOD,
    MENU_PRICES,
    MENU_WALLET,
    MENU_HISTORY,
    MENU_ACCOUNT,
    MENU_PORTFOLIO,
    MENU_SETTINGS,
    MENU_CANCEL,
    MENU_BUY,
    MENU_SELL,
    ORDER_CANCELLED,
)
from bot.keyboards import get_confirmation_keyboard
from .base import BaseTradeHandler, ProgressIndicator

logger = logging.getLogger('bot.trading.shared')


async def unified_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Unified handler for product selection (works for both buy and sell)."""
    query = update.callback_query
    if not query or not query.data:
        return ConversationHandler.END
    
    await query.answer()
    
    # Extract and validate product
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = await BaseTradeHandler.get_product_by_id(product_id)
    
    if not product:
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Get context and store product
    ctx = BaseTradeHandler.get_context(context)
    ctx.product_id = product_id
    
    # Order type should already be set by buy_start or sell_start
    # If not set, this is an error
    if not ctx.order_type:
        logger.error("Order type not set in context during product selection")
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Show method selection based on product type
    # Currencies and Coins use count-based, Gold uses weight-based
    if product.product_code in CURRENCY_PRODUCTS or product.product_code in COIN_PRODUCTS:
        keyboard = [
            [InlineKeyboardButton(BTN_METHOD_COUNT, callback_data=f"{METHOD_PREFIX}{METHOD_COUNT}")],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}{ctx.order_type.lower()}")]
        ]
        prompt = PROMPT_SELECT_METHOD_COUNT
    else:
        # Gold products
        keyboard = [
            [InlineKeyboardButton(BTN_METHOD_GRAMS, callback_data=f"{METHOD_PREFIX}{METHOD_GRAMS}")],
            [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}{ctx.order_type.lower()}")]
        ]
        prompt = PROMPT_SELECT_METHOD
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        prompt,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Store message ID for future editing
    if query.message:
        ctx.last_message_id = query.message.message_id
    
    return SELECTING_METHOD


async def trade_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle calculation method selection (unified for buy/sell)."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
    
    await ProgressIndicator.show_processing(query, "در حال آماده‌سازی...")
    
    # Get context manager
    ctx = BaseTradeHandler.get_context(context)
    
    # Parse method
    if query.data == CALLBACK_METHOD_GRAM:
        method = METHOD_GRAMS
    elif query.data == CALLBACK_METHOD_RIAL:
        method = METHOD_RIAL
    elif query.data == CALLBACK_METHOD_COUNT:
        method = METHOD_COUNT
    else:
        # Fallback for legacy prefixed callbacks
        from bot.constants import METHOD_PREFIX
        method = query.data.replace(METHOD_PREFIX, "")
    
    ctx.calculation_method = method
    
    # Validate product_id is set
    if ctx.product_id is None:
        logger.error("Product ID not set in context during method selection")
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Get product details
    product = await BaseTradeHandler.get_product_by_id(ctx.product_id)
    if not product:
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Validate order_type is set
    if ctx.order_type is None:
        logger.error("Order type not set in context during method selection")
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Get profile for sell orders (to show balance)
    profile = None
    if ctx.order_type == Order.OrderType.SELL:
        profile = await BaseTradeHandler.get_profile(update)
        if not profile:
            return await BaseTradeHandler.send_error_and_end(update)
    
    # Prepare prompt based on method and order type
    prompt = await _get_amount_prompt(ctx.order_type, method, product, profile)
    
    if not prompt:
        return await BaseTradeHandler.send_error_and_end(update)
    
    # Build cancel keyboard
    cancel_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ لغو عملیات", callback_data=CALLBACK_CONFIRM_NO)
    ]])
    
    # Edit the same message with amount prompt (replace the method selection)
    full_prompt = (
        f"{prompt}\n\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💡 مقدار مورد نظر خود را تایپ کنید"
    )
    
    await query.edit_message_text(
        full_prompt,
        reply_markup=cancel_keyboard,
        parse_mode='Markdown'
    )
    
    # Store message ID for later editing
    if query.message:
        ctx.last_message_id = query.message.message_id
    
    return ENTERING_AMOUNT


async def trade_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for both buy and sell."""
    if not update.message or not update.message.text or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    # Get context
    ctx = BaseTradeHandler.get_context(context)
    
    # Filter main menu buttons
    if _is_main_menu_button(update.message.text):
        # Try to edit the last bot message with error
        if ctx.last_message_id and update.effective_chat and context.bot:
            try:
                cancel_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ لغو عملیات", callback_data=CALLBACK_CONFIRM_NO)
                ]])
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=ctx.last_message_id,
                    text="⚠️ *لطفاً عدد وارد کنید*\n\n"
                         "شما باید مقدار یا مبلغ مورد نظر را تایپ کنید.\n"
                         "━━━━━━━━━━━━━━━━\n"
                         "برای لغو، دکمه زیر را بفشارید.",
                    reply_markup=cancel_keyboard,
                    parse_mode='Markdown'
                )
                # Delete user's invalid message
                try:
                    await update.message.delete()
                except Exception:
                    pass  # Ignore if can't delete
            except Exception as e:
                logger.error(f"Error editing message: {e}")
                await update.message.reply_text(
                    "⚠️ *لطفاً عدد وارد کنید*\n\n"
                    "برای لغو، روی دکمه \"❌ لغو عملیات\" کلیک کنید.",
                    parse_mode='Markdown'
                )
        else:
            await update.message.reply_text(
                "⚠️ *لطفاً عدد وارد کنید*\n\n"
                "برای لغو، روی دکمه \"❌ لغو عملیات\" کلیک کنید.",
                parse_mode='Markdown'
            )
        return ENTERING_AMOUNT
    
    try:
        # Parse and validate amount
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        # Validate context data
        if ctx.product_id is None:
            logger.error("Product ID not set in context during amount entry")
            return await BaseTradeHandler.send_error_and_end(update)
        if ctx.order_type is None:
            logger.error("Order type not set in context during amount entry")
            return await BaseTradeHandler.send_error_and_end(update)
        if ctx.calculation_method is None:
            logger.error("Calculation method not set in context during amount entry")
            return await BaseTradeHandler.send_error_and_end(update)
        
        # Get profile
        profile = await BaseTradeHandler.get_profile(update)
        if not profile:
            return await BaseTradeHandler.send_error_and_end(update)
        
        # Get product
        product = await BaseTradeHandler.get_product_by_id(ctx.product_id)
        if not product:
            return await BaseTradeHandler.send_error_and_end(update)
        
        # Calculate order details
        calc_method = 'grams' if ctx.calculation_method == METHOD_COUNT else ctx.calculation_method
        quantity_grams, price_per_gram, total_amount = await sync_to_async(
            OrderService.calculate_order_details
        )(
            product=product,
            order_type=ctx.order_type,
            amount=amount,
            calculation_method=calc_method
        )
        
        # Validate balances BEFORE showing invoice
        is_valid, error_msg = await _validate_order_balance(
            profile, product, ctx.order_type, quantity_grams, total_amount
        )
        
        if not is_valid:
            # Try to edit the last message with error
            if ctx.last_message_id and update.effective_chat and context.bot:
                try:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=ctx.last_message_id,
                        text=error_msg,
                        parse_mode='Markdown'
                    )
                    # Delete user's message
                    try:
                        await update.message.delete()
                    except Exception:
                        pass
                    return ConversationHandler.END
                except Exception as e:
                    logger.error(f"Error editing message: {e}")
            await update.message.reply_text(error_msg, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Store in context
        ctx.quantity_grams = quantity_grams
        ctx.price_per_gram = price_per_gram
        ctx.total_amount = total_amount
        
        # Show invoice
        invoice = await sync_to_async(OrderService.format_order_invoice)(
            profile=profile,
            product=product,
            order_type=ctx.order_type,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )
        
        # Edit the last bot message to show invoice (replace the amount prompt)
        if ctx.last_message_id and update.effective_chat and context.bot:
            try:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=ctx.last_message_id,
                    text=invoice,
                    reply_markup=get_confirmation_keyboard(),
                    parse_mode='Markdown'
                )
                # Delete user's amount message for cleaner chat
                try:
                    await update.message.delete()
                except Exception:
                    pass  # Ignore if can't delete
            except Exception as e:
                logger.error(f"Error editing message for invoice: {e}")
                # Fallback to reply if edit fails
                await update.message.reply_text(
                    invoice,
                    reply_markup=get_confirmation_keyboard(),
                    parse_mode='Markdown'
                )
        else:
            # Fallback to reply if we don't have message_id
            await update.message.reply_text(
                invoice,
                reply_markup=get_confirmation_keyboard(),
                parse_mode='Markdown'
            )
        
        # Return appropriate confirmation state
        return CONFIRMING_BUY if ctx.order_type == Order.OrderType.BUY else CONFIRMING_SELL
        
    except (ValueError, InvalidOperation, ValidationError) as e:
        logger.error(f"Error processing amount: {str(e)}")
        # Try to edit the last message with error
        if ctx.last_message_id and update.effective_chat and context.bot:
            try:
                cancel_keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("❌ لغو عملیات", callback_data=CALLBACK_CONFIRM_NO)
                ]])
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=ctx.last_message_id,
                    text=f"{ERROR_INVALID_AMOUNT}\n\n━━━━━━━━━━━━━━━━\n💡 لطفاً مقدار صحیح وارد کنید",
                    reply_markup=cancel_keyboard,
                    parse_mode='Markdown'
                )
                # Delete user's invalid message
                try:
                    await update.message.delete()
                except Exception:
                    pass
            except Exception as edit_error:
                logger.error(f"Error editing message: {edit_error}")
                await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        else:
            await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return ENTERING_AMOUNT


async def trade_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel trade conversation (handles both callback and message)."""
    query = update.callback_query
    
    if query:
        await query.answer()
        await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    elif update.message:
        from bot.handlers.base import get_main_menu_keyboard
        await update.message.reply_text(
            ORDER_CANCELLED,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    if context.user_data is not None:
        context.user_data.clear()
    
    return ConversationHandler.END


def _get_method_display_text(method: str) -> str:
    """Get display text for calculation method."""
    return {
        METHOD_GRAMS: "گرم",
        METHOD_COUNT: "تعداد",
        METHOD_RIAL: "ریال"
    }.get(method, method)


def _is_main_menu_button(text: str) -> bool:
    """Check if text is a main menu button."""
    return text in [
        MENU_PRICES, MENU_WALLET, MENU_HISTORY, MENU_ACCOUNT,
        MENU_PORTFOLIO, MENU_SETTINGS, MENU_CANCEL, MENU_BUY, MENU_SELL
    ]


async def _get_amount_prompt(order_type: str, method: str, product, profile) -> str:
    """Get appropriate amount prompt based on context."""
    if order_type == Order.OrderType.BUY:
        if method == METHOD_GRAMS:
            return PROMPT_ENTER_AMOUNT_GRAMS
        elif method == METHOD_COUNT:
            return PROMPT_ENTER_AMOUNT_COUNT
        else:
            return PROMPT_ENTER_AMOUNT_RIAL
    elif order_type == Order.OrderType.SELL:
        # Get balance
        balance = await sync_to_async(OrderService.get_product_balance)(profile, product) if profile else Decimal('0')
        
        if method == METHOD_GRAMS:
            return PROMPT_ENTER_AMOUNT_SELL_GRAMS.format(balance=balance)
        elif method == METHOD_COUNT:
            return PROMPT_ENTER_AMOUNT_SELL_COUNT.format(balance=balance)
        else:
            return PROMPT_ENTER_AMOUNT_SELL_RIAL.format(balance=balance)
    
    return ""


async def _validate_order_balance(profile, product, order_type, quantity_grams, total_amount):
    """Validate order balance before confirmation."""
    if order_type == Order.OrderType.BUY:
        return await sync_to_async(OrderService.validate_buy_balance)(
            profile=profile,
            total_amount=total_amount
        )
    else:
        return await sync_to_async(OrderService.validate_sell_balance)(
            profile=profile,
            product=product,
            quantity_grams=quantity_grams
        )
