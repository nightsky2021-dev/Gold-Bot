"""
Bank account management handlers.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from users.models import Profile, BankAccount
from trading.services import BankAccountService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_GENERAL,
    ERROR_INVALID_ACCOUNT_NUMBER,
    ORDER_CANCELLED,
    NO_BANK_ACCOUNTS,
    BANK_ACCOUNTS_LIST_HEADER,
    BANK_ACCOUNT_ADD_SUCCESS,
    PROMPT_SELECT_BANK_NAME,
    PROMPT_ENTER_ACCOUNT_HOLDER,
    PROMPT_ENTER_ACCOUNT_NUMBER,
    BTN_ADD_ACCOUNT,
    BTN_CANCEL,
    BTN_CONFIRM,
    BANK_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    ACCOUNT_ADD_BANK,
    ACCOUNT_ADD_HOLDER_NAME,
    ACCOUNT_ADD_NUMBER,
    ACCOUNT_ADD_CONFIRM,
    IRANIAN_BANKS,
)
from .base import get_or_create_profile

logger = logging.getLogger('bot.bank')


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
