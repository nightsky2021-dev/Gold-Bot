"""Order confirmation and execution handlers."""

import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from trading.models import Order
from trading.services import OrderService
from users.models import Profile
from bot.constants import ERROR_NOT_APPROVED, ERROR_GENERAL
from .base import BaseTradeHandler, ProgressIndicator

logger = logging.getLogger('bot.trading.confirmation')


async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create buy order with immediate execution."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
    
    await ProgressIndicator.show_processing(query, "در حال پردازش...")
    
    telegram_user = update.effective_user
    if not telegram_user:
        return ConversationHandler.END
    
    profile = await BaseTradeHandler.get_profile(update)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    try:
        # Get context
        ctx = BaseTradeHandler.get_context(context)
        
        # Validate all required data
        if not ctx.product_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        product = await BaseTradeHandler.get_product_by_id(ctx.product_id)
        if not product:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Get context values
        calculation_method = ctx.calculation_method or 'grams'
        
        # Use the calculation method to determine what was entered
        if calculation_method == 'rial':
            amount = ctx.total_amount
        else:  # grams or count
            amount = ctx.quantity_grams
        
        if not amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Execute instant order (atomic operation)
        order = await sync_to_async(OrderService.execute_instant_order)(
            profile=profile,
            product=product,
            order_type=Order.OrderType.BUY,
            amount=amount,
            calculation_method=calculation_method
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
            f"⚖️ *مقدار:* {order.quantity_grams} {product_unit}\n"
            f"💵 *مبلغ پرداختی:* {order.total_amount:,} ریال\n\n"
            f"{'═' * 25}\n"
            f"💼 *موجودی‌های جدید:*\n"
            f"💰 ریال: {updated_profile.rial_balance:,} ریال\n"
            f"📦 {product.name}: {product_balance} {product_unit}\n"
            f"{'═' * 25}\n\n"
            f"✨ معامله به صورت آنی اجرا شد\n"
            f"از خرید شما متشکریم! 🙏"
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context
        ctx.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}", parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating buy order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def sell_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create sell order with immediate execution."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    await ProgressIndicator.show_processing(query, "در حال پردازش...")
    
    telegram_user = update.effective_user
    profile = await BaseTradeHandler.get_profile(update)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        # Get context
        ctx = BaseTradeHandler.get_context(context)
        
        # Validate all required data
        if not ctx.product_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        product = await BaseTradeHandler.get_product_by_id(ctx.product_id)
        if not product:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Get context values
        calculation_method = ctx.calculation_method or 'grams'
        
        # Use the calculation method to determine what was entered
        if calculation_method == 'rial':
            amount = ctx.total_amount
        else:  # grams or count
            amount = ctx.quantity_grams
        
        if not amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Execute instant order (atomic operation)
        order = await sync_to_async(OrderService.execute_instant_order)(
            profile=profile,
            product=product,
            order_type=Order.OrderType.SELL,
            amount=amount,
            calculation_method=calculation_method
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
            f"⚖️ *مقدار:* {order.quantity_grams} {product_unit}\n"
            f"💰 *مبلغ دریافتی:* {order.total_amount:,} ریال\n\n"
            f"{'═' * 25}\n"
            f"💼 *موجودی‌های جدید:*\n"
            f"💵 ریال: {updated_profile.rial_balance:,} ریال\n"
            f"📦 {product.name}: {product_balance} {product_unit}\n"
            f"{'═' * 25}\n\n"
            f"✨ معامله به صورت آنی اجرا شد\n"
            f"از همراهی شما متشکریم! 🙏"
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context
        ctx.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}", parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating sell order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
