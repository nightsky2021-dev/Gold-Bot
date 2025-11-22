"""
Wallet helper functions for error handling and flow management.

Provides utilities for managing wallet-related conversation flows
and handling errors consistently.
"""

import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from django.core.exceptions import ValidationError

from bot.constants import ERROR_GENERAL

logger = logging.getLogger('bot.wallet.helpers')


def handle_wallet_error(update: Update, context: ContextTypes.DEFAULT_TYPE, error: Exception) -> None:
    """
    Handle wallet-related errors consistently.
    
    Args:
        update: Telegram update object
        context: Conversation context
        error: Exception that occurred
    """
    error_message = str(error) if error else ERROR_GENERAL
    
    if update.callback_query:
        try:
            update.callback_query.edit_message_text(error_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")
    elif update.message:
        try:
            update.message.reply_text(error_message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Error displaying error message: {e}")
    
    logger.error(f"Wallet error: {error}", exc_info=True)


class DepositFlowManager:
    """Manages deposit flow context data."""
    
    @staticmethod
    def clear_deposit_context(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all deposit-related data from context."""
        if context.user_data is None:
            return
        
        keys_to_remove = [
            'deposit_currency',
            'deposit_amount',
            'deposit_system_bank_id',
            'deposit_source_bank_id',
            'deposit_receipt_path',
            'deposit_receipt_file_id',
        ]
        
        for key in keys_to_remove:
            context.user_data.pop(key, None)


class WithdrawFlowManager:
    """Manages withdrawal flow context data."""
    
    @staticmethod
    def clear_withdraw_context(context: ContextTypes.DEFAULT_TYPE) -> None:
        """Clear all withdrawal-related data from context."""
        if context.user_data is None:
            return
        
        keys_to_remove = [
            'withdraw_currency',
            'withdraw_amount',
            'withdraw_bank_id',
        ]
        
        for key in keys_to_remove:
            context.user_data.pop(key, None)
