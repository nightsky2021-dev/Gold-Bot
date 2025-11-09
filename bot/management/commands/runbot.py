"""
Telegram bot management command.

Run with: python manage.py runbot

This command starts the Telegram bot and handles all user interactions
using python-telegram-bot library with async/await support.
"""

import logging
from django.core.management.base import BaseCommand
from django.conf import settings
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# Import all handlers from organized modules
from bot.handlers import (
    # Auth
    start, help_command, handle_contact,
    # Prices
    show_prices, handle_product_price_view, handle_product_price_all,
    handle_price_refresh, handle_back_to_prices_menu,
    # Trading
    buy_start, buy_product_selected, buy_confirm,
    sell_start, trade_method_selected, trade_amount_entered,
    sell_confirm, trade_cancel, handle_trade_action,
    # Wallet
    show_wallet, show_wallet_transactions,
    deposit_start, deposit_currency_selected, deposit_amount_entered,
    deposit_receipt_uploaded, deposit_confirm, deposit_cancel,
    withdraw_start, withdraw_currency_selected, withdraw_amount_entered,
    withdraw_bank_selected, withdraw_confirm, withdraw_cancel,
    # Bank
    show_bank_accounts, bank_account_add_start, bank_account_bank_selected,
    bank_account_holder_entered, bank_account_number_entered,
    bank_account_add_confirm, bank_account_add_cancel,
    # Settings
    show_settings, show_profile, show_statistics,
    # Menu
    show_account, show_history, cancel,
)
from bot.constants import (
    MENU_BUY,
    MENU_SELL,
    MENU_PRICE,
    MENU_PRICES,
    MENU_WALLET,
    MENU_PORTFOLIO,
    MENU_ACCOUNT,
    MENU_HISTORY,
    MENU_SETTINGS,
    MENU_CANCEL,
    CALLBACK_TRADE_PRODUCT_PREFIX,
    CALLBACK_PRICE_GOLD,
    CALLBACK_PRICE_COIN,
    CALLBACK_PRICE_DOLLAR,
    CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH,
    CALLBACK_BACK_TO_PRICES_MENU,
    PRODUCT_PREFIX,
    METHOD_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    CALLBACK_METHOD_GRAM,
    CALLBACK_METHOD_RIAL,
    CALLBACK_METHOD_COUNT,
    CALLBACK_CONFIRM_NO,
    CURRENCY_PREFIX,
    BANK_PREFIX,
    SELECTING_PRODUCT,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_BUY,
    CONFIRMING_SELL,
    DEPOSIT_SELECT_CURRENCY,
    DEPOSIT_ENTER_AMOUNT,
    DEPOSIT_UPLOAD_RECEIPT,
    DEPOSIT_CONFIRM,
    WITHDRAW_SELECT_CURRENCY,
    WITHDRAW_ENTER_AMOUNT,
    WITHDRAW_SELECT_BANK,
    WITHDRAW_CONFIRM,
    ACCOUNT_ADD_BANK,
    ACCOUNT_ADD_HOLDER_NAME,
    ACCOUNT_ADD_NUMBER,
    ACCOUNT_ADD_CONFIRM,
)

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
        
        # Add command handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Register all conversation handlers
        self._register_trade_handler(application)
        self._register_deposit_handler(application)
        self._register_withdraw_handler(application)
        self._register_bank_account_handler(application)
        
        # Register menu handlers
        self._register_menu_handlers(application)
        
        # Register callback query handlers
        self._register_callback_handlers(application)
        
        # Contact handler for registration
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def _register_trade_handler(self, application):
        """Register trading conversation handler."""
        trade_handler = ConversationHandler(
            entry_points=[
                MessageHandler(filters.Regex(f"^{MENU_BUY}$"), buy_start),
                MessageHandler(filters.Regex(f"^{MENU_SELL}$"), sell_start),
                CallbackQueryHandler(handle_trade_action, pattern=f"^{CALLBACK_TRADE_PRODUCT_PREFIX}")
            ],
            states={
                SELECTING_PRODUCT: [
                    # For buy flow, use buy_product_selected; for sell, we need sell_product_selected
                    # But since both use same pattern, we need to check context to determine which handler
                    # For now, keep as unified for simplicity
                    CallbackQueryHandler(buy_product_selected, pattern=f"^{PRODUCT_PREFIX}"),
                    CallbackQueryHandler(trade_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                SELECTING_METHOD: [
                    CallbackQueryHandler(trade_method_selected, pattern=f"^{METHOD_PREFIX}|^{CALLBACK_METHOD_GRAM}$|^{CALLBACK_METHOD_RIAL}$|^{CALLBACK_METHOD_COUNT}$"),
                    CallbackQueryHandler(trade_cancel, pattern=f"^{CANCEL_PREFIX}")
                ],
                ENTERING_AMOUNT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, trade_amount_entered),
                    CallbackQueryHandler(trade_cancel, pattern=f"^{CALLBACK_CONFIRM_NO}$")
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
            per_user=True,
        )
        application.add_handler(trade_handler)
    
    def _register_deposit_handler(self, application):
        """Register deposit conversation handler."""
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
        application.add_handler(deposit_handler)
    
    def _register_withdraw_handler(self, application):
        """Register withdrawal conversation handler."""
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
        application.add_handler(withdraw_handler)
    
    def _register_bank_account_handler(self, application):
        """Register bank account conversation handler."""
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
        application.add_handler(bank_account_handler)
    
    def _register_menu_handlers(self, application):
        """Register main menu handlers."""
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICE}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICES}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_WALLET}$"), show_wallet))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PORTFOLIO}$"), show_wallet))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_ACCOUNT}$"), show_account))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_HISTORY}$"), show_history))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_SETTINGS}$"), show_settings))
    
    def _register_callback_handlers(self, application):
        """Register callback query handlers."""
        # Price menu callbacks
        # OLD format (for backward compatibility)
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_GOLD}$"))
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_COIN}$"))
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=f"^{CALLBACK_PRICE_DOLLAR}$"))
        # NEW format - dynamic product code pattern (price_PRODUCT_CODE)
        application.add_handler(CallbackQueryHandler(handle_product_price_view, pattern=r"^price_[a-z_]+$"))
        
        application.add_handler(CallbackQueryHandler(handle_product_price_all, pattern=f"^{CALLBACK_PRICE_ALL}$"))
        application.add_handler(CallbackQueryHandler(handle_price_refresh, pattern=f"^{CALLBACK_PRICE_REFRESH}"))
        application.add_handler(CallbackQueryHandler(handle_back_to_prices_menu, pattern=f"^{CALLBACK_BACK_TO_PRICES_MENU}$"))
        
        # Settings and wallet callbacks
        application.add_handler(CallbackQueryHandler(show_wallet_transactions, pattern="^wallet_transactions$"))
        application.add_handler(CallbackQueryHandler(show_profile, pattern="^settings_profile$"))
        application.add_handler(CallbackQueryHandler(show_bank_accounts, pattern="^settings_bank_accounts$"))
        application.add_handler(CallbackQueryHandler(show_statistics, pattern="^settings_statistics$"))


# Command class
Command = TelegramBotCommand
