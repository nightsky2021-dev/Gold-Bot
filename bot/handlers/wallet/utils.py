"""
Common utilities for wallet handlers.

Provides shared helper functions for message editing, error handling,
and common operations used across wallet-related handlers.
"""

import logging
from typing import Optional
from telegram import Update, CallbackQuery
from telegram.ext import ContextTypes
from telegram.error import BadRequest

logger = logging.getLogger('bot.wallet.utils')


async def safe_edit_message(
    query: CallbackQuery,
    text: str,
    reply_markup=None,
    parse_mode: str = 'Markdown',
    bot=None,
    chat_id: Optional[int] = None
) -> None:
    """
    Safely edit a message, falling back to sending a new message if edit fails.
    
    This handles the case where Telegram returns "Message is not modified" error
    when trying to edit a message with the same content.
    
    Args:
        query: CallbackQuery object
        text: Message text
        reply_markup: Optional reply markup
        parse_mode: Parse mode for the message
        bot: Bot instance (required if chat_id is provided)
        chat_id: Chat ID (required if bot is provided)
    """
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        # If message is not modified (same content), ignore the error
        error_str = str(e).lower()
        if (
            isinstance(e, BadRequest) and 
            ("message is not modified" in error_str or "not modified" in error_str)
        ):
            logger.debug("Ignoring 'message is not modified' error.")
            # Optionally answer the query to remove the loading spinner on the button
            try:
                await query.answer()
            except Exception:
                pass  # Ignore if answering fails
        else:
            # Re-raise if it's a different error
            logger.error(f"Error editing message: {e}", exc_info=True)
            # We can try to send a new message as a last resort for other errors
            try:
                if query.message:
                    await query.message.reply_text(
                        text,
                        reply_markup=reply_markup,
                        parse_mode=parse_mode
                    )
            except Exception as send_e:
                logger.error(f"Failed to send fallback message after edit error: {send_e}")


def get_callback_data(update: Update, prefix: str) -> Optional[int]:
    """
    Extract numeric ID from callback data with a given prefix.
    
    Args:
        update: Telegram update object
        prefix: Prefix to remove from callback data
        
    Returns:
        Extracted ID or None if extraction fails
    """
    if not update.callback_query or not update.callback_query.data:
        return None
    
    try:
        return int(update.callback_query.data.replace(prefix, ""))
    except (ValueError, AttributeError):
        return None


def get_amount_from_text(text: str) -> Optional[float]:
    """
    Parse amount from user input text.
    
    Args:
        text: User input text
        
    Returns:
        Parsed amount as float or None if parsing fails
    """
    try:
        # Remove commas and whitespace, then convert
        cleaned = text.replace(',', '').strip()
        return float(cleaned)
    except (ValueError, AttributeError):
        return None
