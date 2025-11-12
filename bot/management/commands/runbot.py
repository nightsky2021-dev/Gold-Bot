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
    # Profile Update
    profile_update_start, profile_update_choice_selected,
    profile_name_entered, profile_national_code_entered,
    profile_update_confirm, profile_update_cancel,
    # Menu
    show_account, show_history, cancel,
    # Portal
    portal_access, portal_refresh_callback, portal_info,
    # Registration
    registration_contact_received,
    registration_name_received, registration_national_code_received,
    registration_confirm, registration_edit, registration_cancel,
)
from bot.constants import (
    MENU_BUY,
    MENU_SELL,
    MENU_PRICE,
    MENU_PRICES,
    MENU_WALLET,
    MENU_ACCOUNT,
    MENU_HISTORY,
    MENU_SETTINGS,
    MENU_CANCEL,
    MENU_PORTAL,
    CALLBACK_TRADE_PRODUCT_PREFIX,
    CALLBACK_PRICE_GOLD,
    CALLBACK_PRICE_COIN,
    CALLBACK_PRICE_DOLLAR,
    CALLBACK_PRICE_ALL,
    CALLBACK_PRICE_REFRESH,
    CALLBACK_BACK_TO_PRICES_MENU,
    CALLBACK_PORTAL_REFRESH,
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
    PROFILE_UPDATE_CHOICE,
    PROFILE_UPDATE_NAME,
    PROFILE_UPDATE_NATIONAL_CODE,
    PROFILE_UPDATE_CONFIRM,
    REG_COLLECT_CONTACT,
    REG_COLLECT_NAME,
    REG_COLLECT_NATIONAL_CODE,
    REG_CONFIRM_PROFILE,
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
        
        # Add command handlers in group 0 (default - highest priority for existing users)
        application.add_handler(CommandHandler("start", start), group=0)
        application.add_handler(CommandHandler("help", help_command), group=0)
        application.add_handler(CommandHandler("portal", portal_access), group=0)
        application.add_handler(CommandHandler("portal_info", portal_info), group=0)
        
        # Register registration handler in group 1 (lower priority - only for new users)
        # This will only trigger if the /start command wasn't handled in group 0
        self._register_registration_handler(application)
        
        # Register all conversation handlers
        self._register_trade_handler(application)
        self._register_deposit_handler(application)
        self._register_withdraw_handler(application)
        self._register_bank_account_handler(application)
        self._register_profile_update_handler(application)
        
        # Register menu handlers
        self._register_menu_handlers(application)
        
        # Register callback query handlers
        self._register_callback_handlers(application)
        
        # Start the bot
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    def _register_registration_handler(self, application):
        """
        Register registration conversation handler for new users.
        
        This handler uses MessageHandler for initial contact to avoid
        conflicting with the CommandHandler for /start.
        """
        registration_handler = ConversationHandler(
            entry_points=[
                # Use a callback that checks for new users
                MessageHandler(filters.CONTACT, registration_contact_received)
            ],
            states={
                REG_COLLECT_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, registration_name_received)
                ],
                REG_COLLECT_NATIONAL_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, registration_national_code_received)
                ],
                REG_CONFIRM_PROFILE: [
                    CallbackQueryHandler(registration_confirm, pattern=f"^{CONFIRM_PREFIX}registration$"),
                    CallbackQueryHandler(registration_edit, pattern="^edit_registration$"),
                    CallbackQueryHandler(registration_cancel, pattern=f"^{CANCEL_PREFIX}registration$")
                ],
            },
            fallbacks=[
                CommandHandler("cancel", registration_cancel),
                CallbackQueryHandler(registration_cancel, pattern=f"^{CANCEL_PREFIX}")
            ],
            per_user=True,
            allow_reentry=True,
        )
        application.add_handler(registration_handler)
    
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
    
    def _register_profile_update_handler(self, application):
        """Register profile update conversation handler."""
        profile_update_handler = ConversationHandler(
            entry_points=[CallbackQueryHandler(profile_update_start, pattern="^update_profile$")],
            states={
                PROFILE_UPDATE_CHOICE: [
                    CallbackQueryHandler(profile_update_choice_selected, pattern="^update_name$|^update_national_code$"),
                    CallbackQueryHandler(profile_update_cancel, pattern=f"^{CANCEL_PREFIX}profile")
                ],
                PROFILE_UPDATE_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, profile_name_entered)
                ],
                PROFILE_UPDATE_NATIONAL_CODE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, profile_national_code_entered)
                ],
                PROFILE_UPDATE_CONFIRM: [
                    CallbackQueryHandler(profile_update_confirm, pattern=f"^{CONFIRM_PREFIX}name$|^{CONFIRM_PREFIX}national_code$"),
                    CallbackQueryHandler(profile_update_cancel, pattern=f"^{CANCEL_PREFIX}profile")
                ],
            },
            fallbacks=[
                CallbackQueryHandler(profile_update_cancel, pattern=f"^{CANCEL_PREFIX}"),
                CommandHandler("cancel", cancel)
            ],
            per_message=True,
        )
        application.add_handler(profile_update_handler)
    
    def _register_menu_handlers(self, application):
        """Register main menu handlers."""
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICE}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PRICES}$"), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_WALLET}$"), show_wallet))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_ACCOUNT}$"), show_account))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_HISTORY}$"), show_history))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_SETTINGS}$"), show_settings))
        application.add_handler(MessageHandler(filters.Regex(f"^{MENU_PORTAL}$"), portal_access))
    
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
        
        # Portal callbacks
        application.add_handler(CallbackQueryHandler(portal_refresh_callback, pattern=f"^{CALLBACK_PORTAL_REFRESH}$"))


# Command class
Command = TelegramBotCommand
