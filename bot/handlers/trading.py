"""
Trading handlers for buy and sell operations.
"""

import logging
import time
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from trading.models import Order, Product
from trading.services import OrderService, ProductService
from users.models import Profile
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_NO_PRODUCTS,
    ERROR_GENERAL,
    ERROR_INVALID_AMOUNT,
    ORDER_CANCELLED,
    PROMPT_SELECT_PRODUCT,
    PROMPT_SELECT_METHOD,
    PROMPT_SELECT_METHOD_COUNT,
    PROMPT_ENTER_AMOUNT_GRAMS,
    PROMPT_ENTER_AMOUNT_RIAL,
    PROMPT_ENTER_AMOUNT_COUNT,
    PROMPT_ENTER_AMOUNT_SELL_GRAMS,
    PROMPT_ENTER_AMOUNT_SELL_RIAL,
    PROMPT_ENTER_AMOUNT_SELL_COUNT,
    BTN_CANCEL,
    BTN_CONFIRM,
    BTN_METHOD_GRAMS,
    BTN_METHOD_RIAL,
    BTN_METHOD_COUNT,
    PRODUCT_PREFIX,
    METHOD_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    METHOD_GRAMS,
    METHOD_RIAL,
    METHOD_COUNT,
    PRODUCT_GOLD,
    PRODUCT_COIN,
    PRODUCT_DOLLAR,
    CALLBACK_TRADE_PRODUCT_PREFIX,
    CALLBACK_ACTION_BUY,
    CALLBACK_METHOD_GRAM,
    CALLBACK_METHOD_RIAL,
    CALLBACK_METHOD_COUNT,
    CALLBACK_CONFIRM_NO,
    SELECTING_PRODUCT,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_BUY,
    CONFIRMING_SELL,
    MENU_PRICES,
    MENU_WALLET,
    MENU_HISTORY,
    MENU_ACCOUNT,
    MENU_PORTFOLIO,
    MENU_SETTINGS,
    MENU_CANCEL,
    MENU_BUY,
    MENU_SELL,
)
from bot.keyboards import get_amount_method_keyboard, get_confirmation_keyboard
from .base import get_or_create_profile

logger = logging.getLogger('bot.trading')


# ==================== Buy Handlers ====================

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start buy conversation."""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    products = await sync_to_async(ProductService.get_active_products)()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Create inline keyboard with products
    keyboard = []
    for product in products:
        button_text = f"{product.name} ({product.sell_price:,} ریال/گرم)"
        callback_data = f"{PRODUCT_PREFIX}{product.id}"  # type: ignore[attr-defined]
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        PROMPT_SELECT_PRODUCT,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def buy_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection for buy."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = await sync_to_async(ProductService.get_product_by_id)(product_id)
    
    if not product:
        await query.edit_message_text(ERROR_GENERAL)
        return ConversationHandler.END
    
    # Store product in context
    context.user_data['product_id'] = product_id
    context.user_data['order_type'] = Order.OrderType.BUY
    
    # Ask for calculation method based on product type
    # Coin and Dollar use count-based calculation, Gold uses weight-based
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


async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create buy order with immediate execution."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
    
    await query.answer("در حال پردازش...")
    
    telegram_user = update.effective_user
    if not telegram_user:
        return ConversationHandler.END
        
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    try:
        product_id = context.user_data.get('product_id')
        if not product_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        product = await sync_to_async(ProductService.get_product_by_id)(product_id)
        if not product:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        quantity_grams = context.user_data.get('quantity_grams')
        price_per_gram = context.user_data.get('price_per_gram')
        total_amount = context.user_data.get('total_amount')
        
        if not quantity_grams or not price_per_gram or not total_amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Re-validate balance before execution (safety check)
        is_valid, error_msg = await sync_to_async(OrderService.validate_buy_balance)(
            profile=profile,
            total_amount=total_amount
        )
        if not is_valid:
            await query.edit_message_text(error_msg, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Create order
        order = await sync_to_async(OrderService.create_order)(
            profile=profile,
            product=product,
            order_type=Order.OrderType.BUY,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )
        
        # Complete order immediately (execute balance changes)
        order = await sync_to_async(OrderService.complete_order)(
            order=order,
            execute_immediately=True
        )
        
        # Get updated balances for confirmation message
        updated_profile = await sync_to_async(
            Profile.objects.select_related('user').get
        )(id=profile.id)  # type: ignore[attr-defined]
        
        product_unit = await sync_to_async(OrderService.get_product_unit)(product)
        product_balance = await sync_to_async(OrderService.get_product_balance)(updated_profile, product)
        
        success_msg = (
            f"✅ *خرید شما با موفقیت انجام شد!*\n\n"
            f"🧾 *شماره سفارش:* #{order.id}\n"  # type: ignore[attr-defined]
            f"📦 *محصول:* {product.name}\n"
            f"⚖️ *مقدار:* {quantity_grams} {product_unit}\n"
            f"💵 *مبلغ پرداختی:* {total_amount:,} ریال\n\n"
            f"{'═' * 25}\n"
            f"💼 *موجودی‌های جدید:*\n"
            f"💰 ریال: {updated_profile.rial_balance:,} ریال\n"
            f"📦 {product.name}: {product_balance} {product_unit}\n"
            f"{'═' * 25}\n\n"
            f"از خرید شما متشکریم! 🙏"
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}", parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating buy order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


# ==================== Sell Handlers ====================

async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start sell conversation."""
    if not update.message or not update.effective_user:
        return ConversationHandler.END
        
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    products = await sync_to_async(ProductService.get_active_products)()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return ConversationHandler.END
    
    keyboard = []
    for product in products:
        button_text = f"{product.name} ({product.buy_price:,} ریال/گرم)"
        callback_data = f"{PRODUCT_PREFIX}{product.id}"  # type: ignore[attr-defined]
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}sell")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        PROMPT_SELECT_PRODUCT,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def sell_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create sell order with immediate execution."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer("در حال پردازش...")
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        product_id = context.user_data.get('product_id')
        if not product_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        product = await sync_to_async(ProductService.get_product_by_id)(product_id)
        if not product:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        quantity_grams = context.user_data.get('quantity_grams')
        price_per_gram = context.user_data.get('price_per_gram')
        total_amount = context.user_data.get('total_amount')
        
        if not quantity_grams or not price_per_gram or not total_amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Re-validate balance before execution (safety check)
        is_valid, error_msg = await sync_to_async(OrderService.validate_sell_balance)(
            profile=profile,
            product=product,
            quantity_grams=quantity_grams
        )
        if not is_valid:
            await query.edit_message_text(error_msg, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Create order
        order = await sync_to_async(OrderService.create_order)(
            profile=profile,
            product=product,
            order_type=Order.OrderType.SELL,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )
        
        # Complete order immediately (execute balance changes)
        order = await sync_to_async(OrderService.complete_order)(
            order=order,
            execute_immediately=True
        )
        
        # Get updated balances for confirmation message
        updated_profile = await sync_to_async(
            Profile.objects.select_related('user').get
        )(id=profile.id)  # type: ignore[attr-defined]
        
        product_unit = await sync_to_async(OrderService.get_product_unit)(product)
        product_balance = await sync_to_async(OrderService.get_product_balance)(updated_profile, product)
        
        success_msg = (
            f"✅ *فروش شما با موفقیت انجام شد!*\n\n"
            f"🧾 *شماره سفارش:* #{order.id}\n"  # type: ignore[attr-defined]
            f"📦 *محصول:* {product.name}\n"
            f"⚖️ *مقدار:* {quantity_grams} {product_unit}\n"
            f"💰 *مبلغ دریافتی:* {total_amount:,} ریال\n\n"
            f"{'═' * 25}\n"
            f"💼 *موجودی‌های جدید:*\n"
            f"💵 ریال: {updated_profile.rial_balance:,} ریال\n"
            f"📦 {product.name}: {product_balance} {product_unit}\n"
            f"{'═' * 25}\n\n"
            f"از همراهی شما متشکریم! 🙏"
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}", parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating sell order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


# ==================== Unified Handlers ====================

async def trade_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle calculation method selection for both buy and sell."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    # Extract method from callback data
    if query.data == CALLBACK_METHOD_GRAM:
        method = METHOD_GRAMS
    elif query.data == CALLBACK_METHOD_RIAL:
        method = METHOD_RIAL
    elif query.data == CALLBACK_METHOD_COUNT:
        method = METHOD_COUNT
    else:
        method = query.data.replace(METHOD_PREFIX, "")
    
    context.user_data['calculation_method'] = method
    
    # Get order type and product to show appropriate prompt
    order_type = context.user_data.get('order_type')
    product_id = context.user_data.get('product_id')
    
    if not product_id:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    product = await sync_to_async(ProductService.get_product_by_id)(product_id)
    if not product:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    if order_type == Order.OrderType.BUY:
        if method == METHOD_GRAMS:
            prompt = PROMPT_ENTER_AMOUNT_GRAMS
        elif method == METHOD_COUNT:
            prompt = PROMPT_ENTER_AMOUNT_COUNT
        else:
            prompt = PROMPT_ENTER_AMOUNT_RIAL
    elif order_type == Order.OrderType.SELL:
        telegram_user = update.effective_user
        profile = await get_or_create_profile(telegram_user)
        if not profile:
            return ConversationHandler.END
        
        # Get balance based on product type
        balance = await sync_to_async(OrderService.get_product_balance)(profile, product)
        
        if method == METHOD_GRAMS:
            prompt = PROMPT_ENTER_AMOUNT_SELL_GRAMS.format(balance=balance)
        elif method == METHOD_COUNT:
            prompt = PROMPT_ENTER_AMOUNT_SELL_COUNT.format(balance=balance)
        else:
            prompt = PROMPT_ENTER_AMOUNT_SELL_RIAL.format(balance=balance)
    else:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Edit the inline message to confirm selection
    if method == METHOD_GRAMS:
        method_text = "گرم"
    elif method == METHOD_COUNT:
        method_text = "تعداد"
    else:
        method_text = "ریال"
    
    await query.edit_message_text(
        f"✅ *روش محاسبه انتخاب شد*\n\n"
        f"📌 روش انتخابی: محاسبه بر اساس *{method_text}*",
        parse_mode='Markdown'
    )
    
    # Send a NEW message with cancel button to make it clear user needs to type
    cancel_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ لغو عملیات", callback_data=CALLBACK_CONFIRM_NO)
    ]])
    
    # Use bot instance to send message to avoid MaybeInaccessibleMessage issue
    if update.effective_chat and context.bot:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"{prompt}\n\n"
                 f"━━━━━━━━━━━━━━━━\n"
                 f"برای لغو عملیات، دکمه زیر را بفشارید.",
            reply_markup=cancel_keyboard,
            parse_mode='Markdown'
        )
    
    return ENTERING_AMOUNT


async def trade_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for both buy and sell."""
    if not update.message or not update.message.text or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    # Define main menu buttons to filter out
    MAIN_MENU_BUTTONS = [
        MENU_PRICES, MENU_WALLET, MENU_HISTORY, MENU_ACCOUNT,
        MENU_PORTFOLIO, MENU_SETTINGS, MENU_CANCEL, MENU_BUY, MENU_SELL
    ]
    
    # Check if user pressed a main menu button instead of entering amount
    if update.message.text in MAIN_MENU_BUTTONS:
        await update.message.reply_text(
            "⚠️ *لطفاً عدد وارد کنید*\n\n"
            "شما باید مقدار یا مبلغ مورد نظر را تایپ کنید.\n"
            "اگر می‌خواهید عملیات را لغو کنید، روی دکمه \"❌ لغو عملیات\" کلیک کنید.",
            parse_mode='Markdown'
        )
        return ENTERING_AMOUNT
        
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        product_id = context.user_data.get('product_id')
        order_type = context.user_data.get('order_type')
        
        if not product_id or not order_type:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Get user profile
        telegram_user = update.effective_user
        profile = await get_or_create_profile(telegram_user)
        if not profile:
            await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
            return ConversationHandler.END
            
        product = await sync_to_async(ProductService.get_product_by_id)(product_id)
        if not product:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        method = context.user_data.get('calculation_method')
        if not method:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # For count-based method, treat it as grams (since quantity_grams field stores the count for coins/dollars)
        calc_method = 'grams' if method == METHOD_COUNT else method
        
        # Calculate order details
        quantity_grams, price_per_gram, total_amount = await sync_to_async(OrderService.calculate_order_details)(
            product=product,
            order_type=order_type,
            amount=amount,
            calculation_method=calc_method
        )
        
        # Validate balances BEFORE showing invoice
        if order_type == Order.OrderType.BUY:
            # Check if user has sufficient Rial balance
            is_valid, error_msg = await sync_to_async(OrderService.validate_buy_balance)(
                profile=profile,
                total_amount=total_amount
            )
            if not is_valid:
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                return ConversationHandler.END
        
        elif order_type == Order.OrderType.SELL:
            # Check if user has sufficient product balance
            is_valid, error_msg = await sync_to_async(OrderService.validate_sell_balance)(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams
            )
            if not is_valid:
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                return ConversationHandler.END
        
        # Store in context
        context.user_data['quantity_grams'] = quantity_grams
        context.user_data['price_per_gram'] = price_per_gram
        context.user_data['total_amount'] = total_amount
        
        # Show detailed invoice with balance information
        invoice = await sync_to_async(OrderService.format_order_invoice)(
            profile=profile,
            product=product,
            order_type=order_type,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )
        
        keyboard = get_confirmation_keyboard()
        
        await update.message.reply_text(
            invoice,
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        
        # Return appropriate state based on order type
        if order_type == Order.OrderType.BUY:
            return CONFIRMING_BUY
        else:
            return CONFIRMING_SELL
        
    except (ValueError, InvalidOperation, ValidationError) as e:
        logger.error(f"Error processing trade amount: {str(e)}")
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return ENTERING_AMOUNT


async def trade_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel trade conversation (handles both callback and message)."""
    query = update.callback_query
    
    if query:
        await query.answer()
        await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    elif update.message:
        from .base import get_main_menu_keyboard
        await update.message.reply_text(
            ORDER_CANCELLED,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    if context.user_data is not None:
        context.user_data.clear()
    
    return ConversationHandler.END


async def handle_trade_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle buy/sell action from product detail view."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Parse callback data: "trade_gold_buy" or "trade_coin_sell"
    parts = query.data.replace(CALLBACK_TRADE_PRODUCT_PREFIX, "").split("_")
    if len(parts) != 2:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    product_code = parts[0]
    action = parts[1]  # 'buy' or 'sell'
    
    # Check if price has expired (more than 60 seconds)
    current_time = int(time.time())
    price_time = context.user_data.get(f'price_time_{product_code}', 0)
    
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
    context.user_data['product_id'] = product.id  # type: ignore[attr-defined]
    context.user_data['order_type'] = Order.OrderType.BUY if action == CALLBACK_ACTION_BUY else Order.OrderType.SELL
    
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
