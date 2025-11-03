"""
Decorators for bot handlers.
"""

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

from .constants import ERROR_NOT_APPROVED

logger = logging.getLogger('bot.decorators')


def require_approved_user(func):
    """Decorator to require approved user for handler."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        from .handlers.base import get_or_create_profile
        profile = await get_or_create_profile(update.effective_user)
        
        if not profile or not profile.is_approved:
            if update.message:
                await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
            elif update.callback_query:
                await update.callback_query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
            return
        
        return await func(update, context, *args, **kwargs)
    
    return wrapper


def log_handler_execution(func):
    """Decorator to log handler execution."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id if update.effective_user else 'Unknown'
        logger.info(f"Handler {func.__name__} called by user {user_id}")
        
        try:
            result = await func(update, context, *args, **kwargs)
            logger.info(f"Handler {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Handler {func.__name__} failed: {str(e)}", exc_info=True)
            raise
    
    return wrapper
