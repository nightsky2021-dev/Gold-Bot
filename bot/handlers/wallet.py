"""
Wallet handlers for deposits, withdrawals, and transactions.
"""

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from users.models import Profile, BankAccount
from users.services import WalletService
from trading.services import TransactionService, WithdrawalService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_GENERAL,
    ERROR_INVALID_AMOUNT,
    ERROR_NO_VERIFIED_BANKS,
    ERROR_INSUFFICIENT_BALANCE,
    ORDER_CANCELLED,
    NO_TRANSACTIONS,
    TRANSACTION_HISTORY_HEADER,
    PROMPT_SELECT_DEPOSIT_CURRENCY,
    PROMPT_ENTER_DEPOSIT_AMOUNT,
    PROMPT_UPLOAD_RECEIPT,
    PROMPT_SELECT_WITHDRAW_CURRENCY,
    PROMPT_ENTER_WITHDRAW_AMOUNT,
    PROMPT_SELECT_WITHDRAW_BANK,
    DEPOSIT_SUCCESS,
    WITHDRAW_SUCCESS,
    WITHDRAW_PREVIEW,
    BTN_DEPOSIT,
    BTN_WITHDRAW,
    BTN_TRANSACTIONS,
    BTN_CANCEL,
    BTN_CONFIRM,
    CURRENCY_PREFIX,
    BANK_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    DEPOSIT_SELECT_CURRENCY,
    DEPOSIT_ENTER_AMOUNT,
    DEPOSIT_UPLOAD_RECEIPT,
    DEPOSIT_CONFIRM,
    WITHDRAW_SELECT_CURRENCY,
    WITHDRAW_ENTER_AMOUNT,
    WITHDRAW_SELECT_BANK,
    WITHDRAW_CONFIRM,
)
from .base import get_or_create_profile

logger = logging.getLogger('bot.wallet')


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


# ==================== Deposit Handlers ====================

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


# ==================== Withdraw Handlers ====================

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
        from trading.services import BankAccountService
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
