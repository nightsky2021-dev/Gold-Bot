"""
Telegram bot management command.

Run with: python manage.py runbot

This command starts the Telegram bot and handles all user interactions
using python-telegram-bot library with async/await support.
"""

import logging
import os
import django
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.core.exceptions import ValidationError

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    KeyboardButton,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from users.models import Profile
from trading.models import Product, Order
from trading.services import ProductService, OrderService, BalanceService
from bot.constants import *

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger('bot')


class TelegramBotCommand(BaseCommand):
    """Django management command to run the Telegram bot."""
    
    help = 'Runs the Telegram bot for gold trading'

    def handle(self, *args, **options):
        """Entry point for the management command."""
        bot_token = settings.TELEGRAM_BOT_TOKEN
        
        if not bot_token:
            self.stdout.write(
                self.style.ERROR(
                    'TELEGRAM_BOT_TOKEN is not set in environment variables!'
                )
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Starting Telegram bot...')
        )
        
        # Build application
        application = Application.builder().token(bot_token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Buy conversation handler
        buy_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f"^{MENU_BUY}$"), buy_start)],
            states={
                SELECTING_PRODUCT: [
                    CallbackQueryHandler(buy_product_selected, pattern=f"^{PRODUCT_PREFIX}")
                ],
                SELECTING_METHOD: [
                    CallbackQueryHandler(buy_method_selected, pattern=f"^{METHOD_PREFIX}")
                ],
                ENTERING_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, buy_amount_entered)
                ],
                CONFIRMING_BUY: [
                    CallbackQueryHandler(buy_confirm, pattern=f"^{CONFIRM_PREFIX}"),
                    CallbackQueryHandler(buy_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex(f"^{MENU_CANCEL}$"), cancel),
                CommandHandler("cancel", cancel)
            ],
        )
        
        # Sell conversation handler
        sell_handler = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f"^{MENU_SELL}$"), sell_start)],
            states={
                SELECTING_PRODUCT: [
                    CallbackQueryHandler(sell_product_selected, pattern=f"^{PRODUCT_PREFIX}")
                ],
                SELECTING_METHOD: [
                    CallbackQueryHandler(sell_method_selected, pattern=f"^{METHOD_PREFIX}")
                ],
                ENTERING_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, sell_amount_entered)
                ],
                CONFIRMING_SELL: [
                    CallbackQueryHandler(sell_confirm, pattern=f"^{CONFIRM_PREFIX}"),
                    CallbackQueryHandler(sell_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex(f"^{MENU_CANCEL}$"), cancel),
                CommandHandler("cancel", cancel)
            ],
        )
        
        application.add_handler(buy_handler)
        application.add_handler(sell_handler)
        
        # Other menu handlers
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICE}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PORTFOLIO}$"), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_HISTORY}$"), show_history))
        
        # Contact handler for registration
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# Helper Functions

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Generate main menu keyboard."""
    keyboard = [
        [MENU_PRICE],
        [MENU_BUY, MENU_SELL],
        [MENU_PORTFOLIO, MENU_HISTORY],
        [MENU_ACCOUNT, MENU_WALLET]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_or_create_profile(telegram_user) -> Optional[Profile]:
    """Get or return None if user doesn't have a profile."""
    try:
        return Profile.objects.get(telegram_id=str(telegram_user.id))
    except Profile.DoesNotExist:
        return None


# Command Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if profile is None:
        # New user - request contact
        keyboard = [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            WELCOME_NEW_USER,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif not profile.is_approved:
        # User registered but not approved
        await update.message.reply_text(
            WELCOME_PENDING_USER,
            parse_mode='Markdown'
        )
    else:
        # Approved user - show main menu
        welcome_msg = WELCOME_APPROVED_USER.format(name=profile.get_display_name())
        await update.message.reply_text(
            welcome_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    help_text = (
        "📖 *راهنمای استفاده از ربات*\n\n"
        "• *قیمت لحظه‌ای:* مشاهده قیمت‌های روز طلا\n"
        "• *خرید طلا:* ثبت سفارش خرید طلا از ما\n"
        "• *فروش طلا:* ثبت سفارش فروش طلا به ما\n"
        "• *پورتفولیو:* مشاهده موجودی ریالی و طلای خود\n"
        "• *تاریخچه:* مشاهده سفارشات قبلی\n\n"
        "برای شروع، از منوی پایین گزینه مورد نظر را انتخاب کنید."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact sharing for registration."""
    contact = update.message.contact
    telegram_user = update.effective_user
    
    # Check if contact is user's own contact
    if contact.user_id != telegram_user.id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            parse_mode='Markdown'
        )
        return
    
    # Check if user already exists
    existing_profile = get_or_create_profile(telegram_user)
    if existing_profile:
        await update.message.reply_text(
            "شما قبلاً ثبت‌نام کرده‌اید.",
            parse_mode='Markdown'
        )
        return
    
    # Create user and profile
    try:
        with transaction.atomic():
            # Create Django User
            username = f"tg_{telegram_user.id}"
            user = User.objects.create_user(
                username=username,
                first_name=telegram_user.first_name or "",
                last_name=telegram_user.last_name or "",
            )
            
            # Create Profile
            profile = Profile.objects.create(
                user=user,
                telegram_id=str(telegram_user.id),
                telegram_username=telegram_user.username or "",
                phone_number=contact.phone_number,
                is_approved=False
            )
            
            success_msg = REGISTRATION_SUCCESS.format(phone=contact.phone_number)
            await update.message.reply_text(
                success_msg,
                parse_mode='Markdown'
            )
            
            logger.info(f"New user registered: {profile.phone_number} (TG: {telegram_user.id})")
            
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        await update.message.reply_text(
            ERROR_GENERAL,
            parse_mode='Markdown'
        )


# Menu Handlers

async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current gold prices."""
    products = ProductService.get_active_products()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    message = "📈 *قیمت‌های لحظه‌ای طلا:*\n\n"
    
    for product in products:
        message += ProductService.format_product_prices(product) + "\n\n"
    
    message += "💡 قیمت‌ها به ریال برای هر گرم است."
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's portfolio."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    portfolio_text = BalanceService.format_portfolio(profile)
    await update.message.reply_text(portfolio_text, parse_mode='Markdown')


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's order history."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    orders = OrderService.get_user_orders(profile, limit=5)
    
    if not orders:
        await update.message.reply_text(NO_ORDERS, parse_mode='Markdown')
        return
    
    message = ORDERS_HISTORY_HEADER
    
    for order in orders:
        message += OrderService.format_order_for_display(order) + "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


# Buy Flow Handlers

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start buy conversation."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    products = ProductService.get_active_products()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Create inline keyboard with products
    keyboard = []
    for product in products:
        button_text = f"{product.name} ({product.sell_price:,} ریال/گرم)"
        callback_data = f"{PRODUCT_PREFIX}{product.id}"
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
    await query.answer()
    
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = ProductService.get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text(ERROR_GENERAL)
        return ConversationHandler.END
    
    # Store product in context
    context.user_data['product_id'] = product_id
    context.user_data['order_type'] = Order.OrderType.BUY
    
    # Ask for calculation method
    keyboard = [
        [InlineKeyboardButton(BTN_METHOD_GRAMS, callback_data=f"{METHOD_PREFIX}{METHOD_GRAMS}")],
        [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMPT_SELECT_METHOD,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def buy_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle calculation method selection for buy."""
    query = update.callback_query
    await query.answer()
    
    method = query.data.replace(METHOD_PREFIX, "")
    context.user_data['calculation_method'] = method
    
    if method == METHOD_GRAMS:
        prompt = PROMPT_ENTER_AMOUNT_GRAMS
    else:
        prompt = PROMPT_ENTER_AMOUNT_RIAL
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return ENTERING_AMOUNT


async def buy_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for buy."""
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        product_id = context.user_data['product_id']
        product = ProductService.get_product_by_id(product_id)
        method = context.user_data['calculation_method']
        
        # Calculate order details
        quantity_grams, price_per_gram, total_amount = OrderService.calculate_order_details(
            product=product,
            order_type=Order.OrderType.BUY,
            amount=amount,
            calculation_method=method
        )
        
        # Store in context
        context.user_data['quantity_grams'] = quantity_grams
        context.user_data['price_per_gram'] = price_per_gram
        context.user_data['total_amount'] = total_amount
        
        # Show preview
        preview = OrderService.format_order_preview(
            product=product,
            order_type=Order.OrderType.BUY,
            quantity_grams=quantity_grams,
            total_amount=total_amount
        )
        
        keyboard = [
            [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}buy")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}buy")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            preview,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return CONFIRMING_BUY
        
    except (ValueError, InvalidOperation, ValidationError) as e:
        logger.error(f"Error processing buy amount: {str(e)}")
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return ENTERING_AMOUNT


async def buy_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create buy order."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    try:
        product = ProductService.get_product_by_id(context.user_data['product_id'])
        
        order = OrderService.create_order(
            profile=profile,
            product=product,
            order_type=Order.OrderType.BUY,
            quantity_grams=context.user_data['quantity_grams'],
            price_per_gram=context.user_data['price_per_gram'],
            total_amount=context.user_data['total_amount']
        )
        
        success_msg = ORDER_SUCCESS.format(order_id=order.id)
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(str(e), parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating buy order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def buy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel buy conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


# Sell Flow Handlers (similar to buy)

async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start sell conversation."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    products = ProductService.get_active_products()
    
    if not products:
        await update.message.reply_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return ConversationHandler.END
    
    keyboard = []
    for product in products:
        button_text = f"{product.name} ({product.buy_price:,} ریال/گرم)"
        callback_data = f"{PRODUCT_PREFIX}{product.id}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}sell")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        PROMPT_SELECT_PRODUCT,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def sell_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection for sell."""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = ProductService.get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text(ERROR_GENERAL)
        return ConversationHandler.END
    
    context.user_data['product_id'] = product_id
    context.user_data['order_type'] = Order.OrderType.SELL
    
    keyboard = [
        [InlineKeyboardButton(BTN_METHOD_GRAMS, callback_data=f"{METHOD_PREFIX}{METHOD_GRAMS}")],
        [InlineKeyboardButton(BTN_METHOD_RIAL, callback_data=f"{METHOD_PREFIX}{METHOD_RIAL}")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}sell")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMPT_SELECT_METHOD,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def sell_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle calculation method selection for sell."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    method = query.data.replace(METHOD_PREFIX, "")
    context.user_data['calculation_method'] = method
    
    balance = profile.gold_balance_grams
    
    if method == METHOD_GRAMS:
        prompt = PROMPT_ENTER_AMOUNT_SELL_GRAMS.format(balance=balance)
    else:
        prompt = PROMPT_ENTER_AMOUNT_SELL_RIAL.format(balance=balance)
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return ENTERING_AMOUNT


async def sell_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for sell."""
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        product_id = context.user_data['product_id']
        product = ProductService.get_product_by_id(product_id)
        method = context.user_data['calculation_method']
        
        quantity_grams, price_per_gram, total_amount = OrderService.calculate_order_details(
            product=product,
            order_type=Order.OrderType.SELL,
            amount=amount,
            calculation_method=method
        )
        
        context.user_data['quantity_grams'] = quantity_grams
        context.user_data['price_per_gram'] = price_per_gram
        context.user_data['total_amount'] = total_amount
        
        preview = OrderService.format_order_preview(
            product=product,
            order_type=Order.OrderType.SELL,
            quantity_grams=quantity_grams,
            total_amount=total_amount
        )
        
        keyboard = [
            [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}sell")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}sell")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            preview,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return CONFIRMING_SELL
        
    except (ValueError, InvalidOperation, ValidationError) as e:
        logger.error(f"Error processing sell amount: {str(e)}")
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return ENTERING_AMOUNT


async def sell_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create sell order."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    try:
        product = ProductService.get_product_by_id(context.user_data['product_id'])
        
        order = OrderService.create_order(
            profile=profile,
            product=product,
            order_type=Order.OrderType.SELL,
            quantity_grams=context.user_data['quantity_grams'],
            price_per_gram=context.user_data['price_per_gram'],
            total_amount=context.user_data['total_amount']
        )
        
        success_msg = ORDER_SUCCESS.format(order_id=order.id)
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(str(e), parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating sell order: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def sell_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel sell conversation."""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current conversation."""
    await update.message.reply_text(
        ORDER_CANCELLED,
        reply_markup=get_main_menu_keyboard(),
        parse_mode='Markdown'
    )
    context.user_data.clear()
    
    return ConversationHandler.END


# Command class
Command = TelegramBotCommand
