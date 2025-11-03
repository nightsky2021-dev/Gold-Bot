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
from asgiref.sync import sync_to_async

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

from users.models import Profile, BankAccount
from users.services import WalletService
from trading.models import Product, Order, Transaction, WithdrawRequest
from trading.services import (
    ProductService, OrderService, BalanceService,
    TransactionService, WithdrawalService, BankAccountService  # type: ignore[attr-defined]
)
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
        
        # Combined Buy/Sell conversation handler (handles both from trade action buttons and legacy menu)
        trade_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex(f"^{MENU_BUY}$"), buy_start),
                MessageHandler(filters.Regex(f"^{MENU_SELL}$"), sell_start),
                CallbackQueryHandler(handle_trade_action, pattern=f"^{CALLBACK_TRADE_PRODUCT_PREFIX}")
            ],
            states={
                SELECTING_PRODUCT: [
                    CallbackQueryHandler(buy_product_selected, pattern=f"^{PRODUCT_PREFIX}")
                ],
                SELECTING_METHOD: [
                    CallbackQueryHandler(trade_method_selected, pattern=f"^{METHOD_PREFIX}|^{CALLBACK_METHOD_GRAM}$|^{CALLBACK_METHOD_RIAL}$")
                ],
                ENTERING_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, trade_amount_entered)
                ],
                CONFIRMING_BUY: [
                    CallbackQueryHandler(buy_confirm, pattern=f"^{CONFIRM_PREFIX}"),
                    CallbackQueryHandler(trade_cancel, pattern=f"^{CANCEL_PREFIX}|^{CALLBACK_CONFIRM_NO}$")
                ],
                CONFIRMING_SELL: [
                    CallbackQueryHandler(sell_confirm, pattern=f"^{CONFIRM_PREFIX}"),
                    CallbackQueryHandler(trade_cancel, pattern=f"^{CANCEL_PREFIX}|^{CALLBACK_CONFIRM_NO}$")
                ],
            },
            fallbacks=[
                MessageHandler(filters.Regex(f"^{MENU_CANCEL}$"), cancel),
                CommandHandler("cancel", cancel),
                CallbackQueryHandler(trade_cancel, pattern=f"^{CALLBACK_CONFIRM_NO}$")
            ],
            per_message=True,
        )
        
        application.add_handler(trade_handler)
        
        # Deposit conversation handler
        deposit_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(deposit_start, pattern="^wallet_deposit$")],
            states={
                DEPOSIT_SELECT_CURRENCY: [
                    CallbackQueryHandler(deposit_currency_selected, pattern=f"^{CURRENCY_PREFIX}"),
                    CallbackQueryHandler(deposit_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                DEPOSIT_ENTER_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_entered)
                ],
                DEPOSIT_UPLOAD_RECEIPT: [
                    MessageHandler(filters.PHOTO, deposit_receipt_uploaded)
                ],
                DEPOSIT_CONFIRM: [
                    CallbackQueryHandler(deposit_confirm, pattern=f"^{CONFIRM_PREFIX}deposit"),
                    CallbackQueryHandler(deposit_cancel, pattern=f"^{CANCEL_PREFIX}deposit")
                ],
            },
            fallbacks=[
                CallbackQueryHandler(deposit_cancel, pattern=f"^{CANCEL_PREFIX}"),
                CommandHandler("cancel", cancel)
            ],
            per_message=True,
        )
        
        # Withdraw conversation handler
        withdraw_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(withdraw_start, pattern="^wallet_withdraw$")],
            states={
                WITHDRAW_SELECT_CURRENCY: [
                    CallbackQueryHandler(withdraw_currency_selected, pattern=f"^{CURRENCY_PREFIX}"),
                    CallbackQueryHandler(withdraw_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                WITHDRAW_ENTER_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, withdraw_amount_entered)
                ],
                WITHDRAW_SELECT_BANK: [
                    CallbackQueryHandler(withdraw_bank_selected, pattern=f"^{BANK_PREFIX}"),
                    CallbackQueryHandler(withdraw_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                WITHDRAW_CONFIRM: [
                    CallbackQueryHandler(withdraw_confirm, pattern=f"^{CONFIRM_PREFIX}withdraw"),
                    CallbackQueryHandler(withdraw_cancel, pattern=f"^{CANCEL_PREFIX}withdraw")
                ],
            },
            fallbacks=[
                CallbackQueryHandler(withdraw_cancel, pattern=f"^{CANCEL_PREFIX}"),
                CommandHandler("cancel", cancel)
            ],
            per_message=True,
        )
        
        # Bank account add conversation handler
        bank_account_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(bank_account_add_start, pattern="^add_bank_account$")],
            states={
                ACCOUNT_ADD_BANK: [
                    CallbackQueryHandler(bank_account_bank_selected, pattern=f"^{BANK_PREFIX}"),
                    CallbackQueryHandler(bank_account_add_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                ACCOUNT_ADD_HOLDER_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bank_account_holder_entered)
                ],
                ACCOUNT_ADD_NUMBER: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, bank_account_number_entered)
                ],
                ACCOUNT_ADD_CONFIRM: [
                    CallbackQueryHandler(bank_account_add_confirm, pattern=f"^{CONFIRM_PREFIX}bank"),
                    CallbackQueryHandler(bank_account_add_cancel, pattern=f"^{CANCEL_PREFIX}bank")
                ],
            },
            fallbacks=[
                CallbackQueryHandler(bank_account_add_cancel, pattern=f"^{CANCEL_PREFIX}"),
                CommandHandler("cancel", cancel)
            ],
            per_message=True,
        )
        
        application.add_handler(deposit_handler)
        application.add_handler(withdraw_handler)
        application.add_handler(bank_account_handler)
        
        # Main menu handlers
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICE}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICES}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_WALLET}$"), show_wallet))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PORTFOLIO}$"), show_wallet))  # Portfolio shows wallet
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_ACCOUNT}$"), show_account))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_HISTORY}$"), show_history))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_SETTINGS}$"), show_settings))
        
        # Price menu callback handlers (must be before generic handlers)
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_GOLD}$"))
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_COIN}$"))
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_DOLLAR}$"))
        application.add_handler(CallbackQueryHandler(handle_product_price_all, pattern=f"^{CALLBACK_PRICE_ALL}$"))
        application.add_handler(CallbackQueryHandler(handle_price_refresh, pattern=f"^{CALLBACK_PRICE_REFRESH}"))
        application.add_handler(CallbackQueryHandler(handle_back_to_prices_menu, pattern=f"^{CALLBACK_BACK_TO_PRICES_MENU}$"))
        
        # Note: Trade action handler is handled by ConversationHandler (entry_points) - no separate handler needed
        
        # Settings and wallet callback query handlers
        application.add_handler(CallbackQueryHandler(show_wallet_transactions, pattern="^wallet_transactions$"))
        application.add_handler(CallbackQueryHandler(show_profile, pattern="^settings_profile$"))
        application.add_handler(CallbackQueryHandler(show_bank_accounts, pattern="^settings_bank_accounts$"))
        application.add_handler(CallbackQueryHandler(show_statistics, pattern="^settings_statistics$"))
        
        # Contact handler for registration
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# Helper Functions

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Generate main menu keyboard matching the keyboards.py layout."""
    keyboard = [
        [MENU_PRICES],
        [MENU_WALLET, MENU_ACCOUNT],
        [MENU_PORTFOLIO, MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_or_create_profile(telegram_user) -> Optional[Profile]:
    """Get or return None if user doesn't have a profile."""
    try:
        return await sync_to_async(
            Profile.objects.select_related('user').get
        )(telegram_id=str(telegram_user.id))
    except Profile.DoesNotExist:
        return None


# Command Handlers

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.message or not update.effective_user:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
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
        display_name = await sync_to_async(profile.get_display_name)()
        welcome_msg = WELCOME_APPROVED_USER.format(name=display_name)
        await update.message.reply_text(
            welcome_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.message:
        return
    
    help_text = (
        "📖 *راهنمای استفاده از ربات*\n\n"
        "• *📈 قیمت‌ها و معامله:* مشاهده قیمت‌های روز و خرید/فروش\n"
        "• *💼 کیف پول:* مشاهده موجودی، واریز و برداشت\n"
        "• *📋 تاریخچه:* مشاهده سفارشات و تراکنش‌ها\n"
        "• *⚙️ تنظیمات:* پروفایل، حساب‌های بانکی و آمار\n\n"
        "برای شروع، از منوی پایین گزینه مورد نظر را انتخاب کنید."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact sharing for registration."""
    if not update.message or not update.message.contact or not update.effective_user:
        return
    
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
    existing_profile = await get_or_create_profile(telegram_user)
    if existing_profile:
        await update.message.reply_text(
            "شما قبلاً ثبت‌نام کرده‌اید.",
            parse_mode='Markdown'
        )
        return
    
    # Create user and profile
    try:
        @sync_to_async
        def create_user_and_profile():
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
                return profile
        
        profile = await create_user_and_profile()
        
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


# ==================== Price Menu Handlers ====================

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
    
    # Map callback data to product code
    product_code_map = {
        CALLBACK_PRICE_GOLD: PRODUCT_GOLD,
        CALLBACK_PRICE_COIN: PRODUCT_COIN,
        CALLBACK_PRICE_DOLLAR: PRODUCT_DOLLAR,
    }
    
    product_code = product_code_map.get(query.data)
    if not product_code:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return
    
    # Get product by code
    product = await sync_to_async(
        lambda: Product.objects.filter(product_code=product_code, is_active=True).first()
    )()
    
    if not product:
        await query.edit_message_text(ERROR_NO_PRODUCTS, parse_mode='Markdown')
        return
    
    # Store timestamp for price expiration check
    import time
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
    from bot.keyboards import get_product_detail_keyboard
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
    from bot.keyboards import get_prices_menu_keyboard
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
    import time
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
    
    from bot.keyboards import get_product_detail_keyboard
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
    
    from bot.keyboards import get_prices_menu_keyboard
    keyboard = get_prices_menu_keyboard()
    
    message = (
        "📈 *قیمت‌ها و معامله*\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:"
    )
    
    await query.edit_message_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


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
    import time
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
    
    # Ask for calculation method
    from bot.keyboards import get_amount_method_keyboard
    keyboard = get_amount_method_keyboard(product_code)
    
    await query.edit_message_text(
        PROMPT_SELECT_METHOD,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


# Menu Handlers

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
    
    # Create inline keyboard with product buttons
    from bot.keyboards import get_prices_menu_keyboard
    keyboard = get_prices_menu_keyboard()
    
    message = (
        "📈 *قیمت‌ها و معامله*\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:"
    )
    
    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode='Markdown'
    )


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's wallet with action buttons."""
    if not update.message or not update.effective_user:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Format wallet display
    wallet_text = await sync_to_async(WalletService.format_wallet_display)(profile)
    
    # Create action buttons
    keyboard = [
        [
            InlineKeyboardButton(BTN_DEPOSIT, callback_data="wallet_deposit"),
            InlineKeyboardButton(BTN_WITHDRAW, callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton(BTN_TRANSACTIONS, callback_data="wallet_transactions")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        wallet_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


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


# Buy Flow Handlers

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
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
    
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
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
    
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        product_id = context.user_data.get('product_id')
        if not product_id:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        product = await sync_to_async(ProductService.get_product_by_id)(product_id)
        if not product:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        method = context.user_data.get('calculation_method')
        if not method:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Calculate order details
        quantity_grams, price_per_gram, total_amount = await sync_to_async(OrderService.calculate_order_details)(
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


async def buy_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel buy conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


# Sell Flow Handlers (similar to buy)

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


async def sell_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle product selection for sell."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    product_id = int(query.data.replace(PRODUCT_PREFIX, ""))
    product = await sync_to_async(ProductService.get_product_by_id)(product_id)
    
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
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
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
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
        
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        product_id = context.user_data.get('product_id')
        if not product_id:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        product = await sync_to_async(ProductService.get_product_by_id)(product_id)
        if not product:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        method = context.user_data.get('calculation_method')
        if not method:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        quantity_grams, price_per_gram, total_amount = await sync_to_async(OrderService.calculate_order_details)(
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


async def sell_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel sell conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


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


# ==================== Unified Trade Handlers ====================

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
    else:
        method = query.data.replace(METHOD_PREFIX, "")
    
    context.user_data['calculation_method'] = method
    
    # Get order type to show appropriate prompt
    order_type = context.user_data.get('order_type')
    
    if order_type == Order.OrderType.BUY:
        if method == METHOD_GRAMS:
            prompt = PROMPT_ENTER_AMOUNT_GRAMS
        else:
            prompt = PROMPT_ENTER_AMOUNT_RIAL
    elif order_type == Order.OrderType.SELL:
        telegram_user = update.effective_user
        profile = await get_or_create_profile(telegram_user)
        if not profile:
            return ConversationHandler.END
        
        balance = profile.gold_balance_grams
        if method == METHOD_GRAMS:
            prompt = PROMPT_ENTER_AMOUNT_SELL_GRAMS.format(balance=balance)
        else:
            prompt = PROMPT_ENTER_AMOUNT_SELL_RIAL.format(balance=balance)
    else:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Edit the inline message to confirm selection
    await query.edit_message_text(
        f"✅ روش محاسبه انتخاب شد.\n\n{prompt}",
        parse_mode='Markdown'
    )
    
    # Send a NEW message with cancel button to make it clear user needs to type
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    cancel_keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("❌ لغو", callback_data=CALLBACK_CONFIRM_NO)
    ]])
    
    # Use bot instance to send message to avoid MaybeInaccessibleMessage issue
    if update.effective_chat and context.bot:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="💬 *لطفاً مقدار مورد نظر را تایپ کنید:*\n\n"
                 "یا برای لغو، دکمه زیر را بفشارید.",
            reply_markup=cancel_keyboard,
            parse_mode='Markdown'
        )
    
    return ENTERING_AMOUNT


async def trade_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for both buy and sell."""
    if not update.message or not update.message.text or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
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
        
        # Calculate order details
        quantity_grams, price_per_gram, total_amount = await sync_to_async(OrderService.calculate_order_details)(
            product=product,
            order_type=order_type,
            amount=amount,
            calculation_method=method
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
        
        from bot.keyboards import get_confirmation_keyboard
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
        await update.message.reply_text(
            ORDER_CANCELLED,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
    
    if context.user_data is not None:
        context.user_data.clear()
    
    return ConversationHandler.END


# ==================== Settings Menu Handlers ====================

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


async def show_bank_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's bank accounts with management options."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    bank_accounts = await sync_to_async(BankAccountService.get_user_bank_accounts)(profile)
    
    if not bank_accounts:
        keyboard = [[InlineKeyboardButton(BTN_ADD_ACCOUNT, callback_data="add_bank_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            NO_BANK_ACCOUNTS,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    message = BANK_ACCOUNTS_LIST_HEADER
    keyboard = []
    
    for account in bank_accounts:
        message += BankAccountService.format_bank_account_for_display(account) + "\n"
    
    keyboard.append([InlineKeyboardButton(BTN_ADD_ACCOUNT, callback_data="add_bank_account")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


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


async def show_wallet_transactions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's transaction history."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Get last 20 transactions
    transactions = await sync_to_async(TransactionService.get_user_transactions)(profile, limit=20)
    
    if not transactions:
        await query.edit_message_text(NO_TRANSACTIONS, parse_mode='Markdown')
        return
    
    message = TRANSACTION_HISTORY_HEADER
    
    for txn in transactions:
        message += TransactionService.format_transaction_for_display(txn) + "\n"
    
    await query.edit_message_text(message, parse_mode='Markdown')


# ==================== Deposit Workflow Handlers ====================

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start deposit conversation."""
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show currency selection
    keyboard = [
        [InlineKeyboardButton("💰 ریال", callback_data=f"{CURRENCY_PREFIX}RIAL")],
        [InlineKeyboardButton("🪙 طلا", callback_data=f"{CURRENCY_PREFIX}GOLD")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMPT_SELECT_DEPOSIT_CURRENCY,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return DEPOSIT_SELECT_CURRENCY


async def deposit_currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection for deposit."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    currency = query.data.replace(CURRENCY_PREFIX, "")
    context.user_data['deposit_currency'] = currency
    
    await query.edit_message_text(
        PROMPT_ENTER_DEPOSIT_AMOUNT,
        parse_mode='Markdown'
    )
    
    return DEPOSIT_ENTER_AMOUNT


async def deposit_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for deposit."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
        
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        context.user_data['deposit_amount'] = amount
        currency = context.user_data.get('deposit_currency')
        if not currency:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # For RIAL deposits, ask for receipt image
        if currency == 'RIAL':
            await update.message.reply_text(
                PROMPT_UPLOAD_RECEIPT,
                parse_mode='Markdown'
            )
            return DEPOSIT_UPLOAD_RECEIPT
        else:
            # For non-RIAL, go directly to confirmation
            currency_name = WalletService.get_currency_display_name(currency)
            confirm_msg = (
                f"✅ *تأیید واریز*\n\n"
                f"ارز: {currency_name}\n"
                f"مقدار: {amount:,.2f}\n\n"
                f"آیا مطمئن هستید؟"
            )
            
            keyboard = [
                [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}deposit")],
                [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                confirm_msg,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            
            return DEPOSIT_CONFIRM
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error processing deposit amount: {str(e)}")
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return DEPOSIT_ENTER_AMOUNT


async def deposit_receipt_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle receipt image upload for deposit."""
    if not update.message or not update.message.photo or context.user_data is None:
        return ConversationHandler.END
        
    # Get the photo
    photo = update.message.photo[-1]  # Get highest resolution
    photo_file = await photo.get_file()
    
    # Store photo file_id for later
    context.user_data['deposit_receipt_file_id'] = photo.file_id
    
    currency = context.user_data.get('deposit_currency')
    amount = context.user_data.get('deposit_amount')
    if not currency or not amount:
        await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
        
    currency_name = WalletService.get_currency_display_name(currency)
    
    confirm_msg = (
        f"✅ *تأیید واریز*\n\n"
        f"ارز: {currency_name}\n"
        f"مقدار: {amount:,.2f}\n"
        f"رسید: دریافت شد ✓\n\n"
        f"آیا مطمئن هستید؟"
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}deposit")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return DEPOSIT_CONFIRM


async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create deposit transaction."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        currency = context.user_data.get('deposit_currency')
        amount = context.user_data.get('deposit_amount')
        if not currency or not amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        receipt_file_id = context.user_data.get('deposit_receipt_file_id')
        
        # Create deposit transaction
        txn = await sync_to_async(TransactionService.create_deposit)(
            profile=profile,
            currency=currency,
            amount=amount,
            description=f"واریز {WalletService.get_currency_display_name(currency)}"
        )
        
        # Note: In production, you'd download and save the receipt image
        # For now, we just log the file_id
        if receipt_file_id:
            logger.info(f"Receipt file_id: {receipt_file_id} for transaction {txn.id}")  # type: ignore[attr-defined]
        
        currency_name = WalletService.get_currency_display_name(currency)
        success_msg = DEPOSIT_SUCCESS.format(
            transaction_id=txn.id,  # type: ignore[attr-defined]
            amount=amount,
            currency=currency_name
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(str(e), parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating deposit: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def deposit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel deposit conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


# ==================== Withdrawal Workflow Handlers ====================

async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start withdrawal conversation."""
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show currency selection with available balances
    rial_available = profile.get_available_rial_balance()
    gold_available = profile.get_available_gold_balance()
    
    keyboard = []
    
    if rial_available > 0:
        keyboard.append([InlineKeyboardButton(
            f"💰 ریال ({rial_available:,.0f} ریال)",
            callback_data=f"{CURRENCY_PREFIX}RIAL"
        )])
    
    if gold_available > 0:
        keyboard.append([InlineKeyboardButton(
            f"🪙 طلا ({gold_available} گرم)",
            callback_data=f"{CURRENCY_PREFIX}GOLD"
        )])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")])
    
    if len(keyboard) == 1:  # Only cancel button
        await query.edit_message_text(
            "❌ موجودی قابل برداشت ندارید.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMPT_SELECT_WITHDRAW_CURRENCY,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WITHDRAW_SELECT_CURRENCY


async def withdraw_currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection for withdrawal."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    currency = query.data.replace(CURRENCY_PREFIX, "")
    context.user_data['withdraw_currency'] = currency
    
    # Get available balance
    if currency == 'RIAL':
        available = profile.get_available_rial_balance()
    else:
        available = profile.get_available_gold_balance()
    
    currency_name = WalletService.get_currency_display_name(currency)
    
    prompt = PROMPT_ENTER_WITHDRAW_AMOUNT.format(
        available=f"{available:,.2f}",
        currency=currency_name
    )
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return WITHDRAW_ENTER_AMOUNT


async def withdraw_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for withdrawal."""
    if not update.message or not update.message.text or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        currency = context.user_data.get('withdraw_currency')
        if not currency:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Validate sufficient balance
        if currency == 'RIAL':
            if not profile.has_sufficient_available_rial(amount):
                available = profile.get_available_rial_balance()
                error_msg = ERROR_INSUFFICIENT_BALANCE.format(
                    current=available,
                    currency='ریال',
                    required=amount
                )
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                return WITHDRAW_ENTER_AMOUNT
        else:
            if not profile.has_sufficient_available_gold(amount):
                available = profile.get_available_gold_balance()
                error_msg = ERROR_INSUFFICIENT_BALANCE.format(
                    current=available,
                    currency='گرم',
                    required=amount
                )
                await update.message.reply_text(error_msg, parse_mode='Markdown')
                return WITHDRAW_ENTER_AMOUNT
        
        context.user_data['withdraw_amount'] = amount
        
        # Get verified bank accounts
        bank_accounts = await sync_to_async(BankAccountService.get_user_bank_accounts)(profile, verified_only=True)
        
        if not bank_accounts:
            await update.message.reply_text(ERROR_NO_VERIFIED_BANKS, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Show bank account selection
        keyboard = []
        for account in bank_accounts:
            button_text = f"{account.bank_name} - {account.get_masked_account_number()}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"{BANK_PREFIX}{account.id}"  # type: ignore[attr-defined]
            )])
        
        keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            PROMPT_SELECT_WITHDRAW_BANK,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WITHDRAW_SELECT_BANK
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error processing withdraw amount: {str(e)}")
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return WITHDRAW_ENTER_AMOUNT


async def withdraw_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank account selection for withdrawal."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    bank_account_id = int(query.data.replace(BANK_PREFIX, ""))
    context.user_data['withdraw_bank_id'] = bank_account_id
    
    # Get bank account
    try:
        bank_account = await sync_to_async(BankAccount.objects.get)(id=bank_account_id)
        
        currency = context.user_data.get('withdraw_currency')
        amount = context.user_data.get('withdraw_amount')
        if not currency or not amount:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
            
        currency_name = WalletService.get_currency_display_name(currency)
        
        # Show preview
        preview = WITHDRAW_PREVIEW.format(
            currency=currency_name,
            amount=amount,
            bank_name=bank_account.bank_name,
            account_number=bank_account.get_masked_account_number()
        )
        
        keyboard = [
            [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}withdraw")],
            [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            preview,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        return WITHDRAW_CONFIRM
        
    except BankAccount.DoesNotExist:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def withdraw_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create withdrawal request."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        currency = context.user_data.get('withdraw_currency')
        amount = context.user_data.get('withdraw_amount')
        bank_account_id = context.user_data.get('withdraw_bank_id')
        
        if not currency or not amount or not bank_account_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        bank_account = await sync_to_async(BankAccount.objects.get)(id=bank_account_id)
        
        # Create withdrawal request (this will freeze the balance)
        withdraw_request = await sync_to_async(WithdrawalService.create_withdraw_request)(
            profile=profile,
            currency=currency,
            amount=amount,
            bank_account=bank_account
        )
        
        currency_name = WalletService.get_currency_display_name(currency)
        success_msg = WITHDRAW_SUCCESS.format(
            request_id=withdraw_request.id,  # type: ignore[attr-defined]
            amount=amount,
            currency=currency_name
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(str(e), parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating withdrawal: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel withdrawal conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


# ==================== Bank Account Management Handlers ====================

async def bank_account_add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start add bank account conversation."""
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show bank selection from IRANIAN_BANKS
    keyboard = []
    for bank in IRANIAN_BANKS[:15]:  # Show first 15 banks
        keyboard.append([InlineKeyboardButton(bank, callback_data=f"{BANK_PREFIX}{bank}")])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}bank")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        PROMPT_SELECT_BANK_NAME,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ACCOUNT_ADD_BANK


async def bank_account_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank selection."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    bank_name = query.data.replace(BANK_PREFIX, "")
    context.user_data['bank_name'] = bank_name
    
    await query.edit_message_text(
        PROMPT_ENTER_ACCOUNT_HOLDER,
        parse_mode='Markdown'
    )
    
    return ACCOUNT_ADD_HOLDER_NAME


async def bank_account_holder_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account holder name input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
        
    holder_name = update.message.text.strip()
    context.user_data['account_holder'] = holder_name
    
    await update.message.reply_text(
        PROMPT_ENTER_ACCOUNT_NUMBER,
        parse_mode='Markdown'
    )
    
    return ACCOUNT_ADD_NUMBER


async def bank_account_number_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle account number input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
        
    account_number = update.message.text.strip().replace(' ', '')
    
    # Validate account number
    if not account_number.isdigit() or len(account_number) != 16:
        await update.message.reply_text(
            ERROR_INVALID_ACCOUNT_NUMBER,
            parse_mode='Markdown'
        )
        return ACCOUNT_ADD_NUMBER
    
    context.user_data['account_number'] = account_number
    
    # Show confirmation
    bank_name = context.user_data.get('bank_name')
    holder_name = context.user_data.get('account_holder')
    
    if not bank_name or not holder_name:
        await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    confirm_msg = (
        f"✅ *تأیید اطلاعات حساب بانکی*\n\n"
        f"بانک: {bank_name}\n"
        f"صاحب حساب: {holder_name}\n"
        f"شماره حساب: {account_number}\n\n"
        f"آیا اطلاعات صحیح است؟"
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}bank")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}bank")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return ACCOUNT_ADD_CONFIRM


async def bank_account_add_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create bank account."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        bank_name = context.user_data.get('bank_name')
        holder_name = context.user_data.get('account_holder')
        account_number = context.user_data.get('account_number')
        
        if not bank_name or not holder_name or not account_number:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Create bank account
        bank_account = await sync_to_async(BankAccountService.create_bank_account)(
            profile=profile,
            bank_name=bank_name,
            account_holder_name=holder_name,
            account_number=account_number
        )
        
        success_msg = BANK_ACCOUNT_ADD_SUCCESS.format(
            bank_name=bank_name,
            holder_name=holder_name,
            account_number=bank_account.get_masked_account_number()
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(str(e), parse_mode='Markdown')
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error creating bank account: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def bank_account_add_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel bank account add conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    context.user_data.clear()
    
    return ConversationHandler.END


# Command class
Command = TelegramBotCommand
