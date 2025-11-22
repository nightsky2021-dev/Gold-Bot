"""
Wallet display and transaction history handlers.

Handles displaying wallet balances, refreshing wallet information,
and showing transaction history to users.
"""

import logging
from decimal import Decimal
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from users.models import Profile
from users.services import WalletService
from trading.services import TransactionService
from bot.constants import (
    ERROR_NOT_APPROVED,
    NO_TRANSACTIONS,
    TRANSACTION_HISTORY_HEADER,
    BTN_DEPOSIT,
    BTN_WITHDRAW,
    BTN_TRANSACTIONS,
)
from bot.handlers.base import get_or_create_profile
from .utils import safe_edit_message

logger = logging.getLogger('bot.wallet.display')


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
    
    # Create action buttons with refresh functionality
    keyboard = [
        [
            InlineKeyboardButton(BTN_DEPOSIT, callback_data="wallet_deposit"),
            InlineKeyboardButton(BTN_WITHDRAW, callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton(BTN_TRANSACTIONS, callback_data="wallet_transactions")
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="wallet_refresh")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        wallet_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def wallet_refresh(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Refresh wallet display with updated balances."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer("🔄 در حال بروزرسانی موجودی...")
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    # Refresh profile from database to get latest balances
    await sync_to_async(profile.refresh_from_db)()
    
    # Format wallet display with real-time data
    wallet_text = await sync_to_async(WalletService.format_wallet_display)(profile)
    
    # Create action buttons with refresh functionality
    keyboard = [
        [
            InlineKeyboardButton(BTN_DEPOSIT, callback_data="wallet_deposit"),
            InlineKeyboardButton(BTN_WITHDRAW, callback_data="wallet_withdraw")
        ],
        [
            InlineKeyboardButton(BTN_TRANSACTIONS, callback_data="wallet_transactions")
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="wallet_refresh")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            wallet_text,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            wallet_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


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
        back_keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data="wallet_back")]
        ]
        reply_markup = InlineKeyboardMarkup(back_keyboard)
        
        await query.edit_message_text(
            NO_TRANSACTIONS,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    message = TRANSACTION_HISTORY_HEADER
    
    # Telegram message limit is 4096 characters
    MAX_MESSAGE_LENGTH = 4000  # Leave some buffer
    
    displayed_count = 0
    for txn in transactions:
        txn_text = TransactionService.format_transaction_for_display(txn) + "\n"
        
        # Check if adding this transaction would exceed the limit
        if len(message) + len(txn_text) > MAX_MESSAGE_LENGTH:
            # Add a note that more transactions exist
            remaining_count = len(transactions) - displayed_count
            message += f"\n... و {remaining_count} تراکنش دیگر (برای مشاهده کامل به پورتال وب مراجعه کنید)"
            break
        
        message += txn_text
        displayed_count += 1
    
    # Add back button
    back_keyboard = [
        [InlineKeyboardButton("🔙 بازگشت به کیف پول", callback_data="wallet_back")]
    ]
    reply_markup = InlineKeyboardMarkup(back_keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def wallet_back(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Return to main wallet display."""
    query = update.callback_query
    if not query or not update.effective_user:
        return
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
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
            InlineKeyboardButton(BTN_TRANSACTIONS, callback_data="wallet_transactions"),
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="wallet_refresh")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            wallet_text,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            wallet_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
