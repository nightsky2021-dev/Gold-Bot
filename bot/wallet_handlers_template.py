"""
Template for Wallet and Account Management Bot Handlers

This file provides a comprehensive template for implementing wallet and account 
management conversation handlers in the Telegram bot.

To use this template:
1. Copy the relevant handlers to bot/management/commands/runbot.py
2. Import necessary services and models
3. Add the conversation handlers to the application
4. Test each flow thoroughly

Note: This is a template with detailed comments. Implement error handling,
validation, and user feedback as needed.
"""

from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from users.models import Profile, BankAccount
from users.services import add_bank_account, get_user_bank_accounts, remove_bank_account
from trading.models import Transaction, WithdrawRequest, TransferRequest
from trading.services import (
    WalletService,
    TransactionService,
    DepositService,
    WithdrawService,
    TransferService
)
from bot.constants import *


# ========== Helper Functions ==========

def get_currency_selection_keyboard(action_type: str) -> InlineKeyboardMarkup:
    """Create keyboard for currency selection."""
    keyboard = [
        [InlineKeyboardButton("💵 ریال", callback_data=f"{action_type}_RIAL")],
        [InlineKeyboardButton("🪙 طلا", callback_data=f"{action_type}_GOLD")],
        [InlineKeyboardButton("🥇 سکه", callback_data=f"{action_type}_COIN")],
        [InlineKeyboardButton("💵 دلار", callback_data=f"{action_type}_DOLLAR")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_WALLET)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_bank_accounts_keyboard(bank_accounts, action_prefix: str) -> InlineKeyboardMarkup:
    """Create keyboard for bank account selection."""
    keyboard = []
    for account in bank_accounts:
        card_display = account.account_number[-4:] if len(account.account_number) >= 4 else account.account_number
        keyboard.append([
            InlineKeyboardButton(
                f"💳 {account.bank_name} - ****{card_display}",
                callback_data=f"{action_prefix}_{account.id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton("➕ افزودن حساب جدید", callback_data=CALLBACK_ADD_BANK_ACCOUNT)])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_WALLET)])
    
    return InlineKeyboardMarkup(keyboard)


def get_wallet_menu_keyboard() -> InlineKeyboardMarkup:
    """Create wallet menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("➕ واریز وجه", callback_data=CALLBACK_WALLET_DEPOSIT)],
        [InlineKeyboardButton("➖ برداشت وجه", callback_data=CALLBACK_WALLET_WITHDRAW)],
        [InlineKeyboardButton("🔄 انتقال وجه", callback_data=CALLBACK_WALLET_TRANSFER)],
        [InlineKeyboardButton("💰 موجودی‌ها", callback_data=CALLBACK_WALLET_BALANCES)],
        [InlineKeyboardButton("📜 تراکنش‌ها", callback_data=CALLBACK_WALLET_TRANSACTIONS)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_account_menu_keyboard() -> InlineKeyboardMarkup:
    """Create account menu keyboard."""
    keyboard = [
        [InlineKeyboardButton("👤 مشخصات من", callback_data=CALLBACK_ACCOUNT_PROFILE)],
        [InlineKeyboardButton("💳 کارت‌های بانکی", callback_data=CALLBACK_ACCOUNT_BANKCARDS)],
        [InlineKeyboardButton("💰 موجودی‌ها", callback_data=CALLBACK_ACCOUNT_BALANCES)],
        [InlineKeyboardButton("📊 تراکنش‌ها", callback_data=CALLBACK_ACCOUNT_TRANSACTIONS)],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_MAIN)],
    ]
    return InlineKeyboardMarkup(keyboard)


# ========== Account Menu Handlers ==========

async def account_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show account menu."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    await update.message.reply_text(
        MSG_ACCOUNT_MENU,
        reply_markup=get_account_menu_keyboard(),
        parse_mode='Markdown'
    )


async def account_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle account menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if query.data == CALLBACK_ACCOUNT_PROFILE:
        # Show user profile
        text = (
            f"👤 *مشخصات شما:*\n\n"
            f"نام: {profile.user.get_full_name()}\n"
            f"شماره تماس: {profile.phone_number}\n"
            f"تلگرام: @{profile.telegram_username or 'ندارد'}\n"
            f"وضعیت حساب: {'✅ تایید شده' if profile.is_approved else '⏳ در انتظار تایید'}\n"
            f"تاریخ عضویت: {profile.created_at.strftime('%Y/%m/%d')}"
        )
        await query.edit_message_text(text, parse_mode='Markdown')
    
    elif query.data == CALLBACK_ACCOUNT_BANKCARDS:
        # Show bank accounts
        bank_accounts = get_user_bank_accounts(profile)
        
        if not bank_accounts:
            text = "💳 شما هیچ حساب بانکی ثبت نکرده‌اید.\n\nبرای افزودن حساب جدید روی دکمه زیر کلیک کنید."
        else:
            text = "💳 *حساب‌های بانکی شما:*\n\n"
            for account in bank_accounts:
                status = "✅ تایید شده" if account.is_verified else "⏳ در انتظار تایید"
                text += f"🏦 {account.bank_name}\n"
                text += f"   {account.get_masked_account_number()}\n"
                text += f"   {status}\n\n"
        
        keyboard = [
            [InlineKeyboardButton("➕ افزودن حساب جدید", callback_data=CALLBACK_ADD_BANK_ACCOUNT)],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_ACCOUNT)]
        ]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == CALLBACK_ACCOUNT_BALANCES:
        # Show balances
        text = WalletService.format_wallet_display(profile)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_ACCOUNT)]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == CALLBACK_ACCOUNT_TRANSACTIONS:
        # Show recent transactions
        transactions = TransactionService.get_user_transactions(profile, limit=5)
        
        if not transactions:
            text = "📜 شما هنوز هیچ تراکنشی نداشته‌اید."
        else:
            text = "📜 *آخرین تراکنش‌های شما:*\n\n"
            for txn in transactions:
                emoji = "🟢" if txn.status == "COMPLETED" else "🟡" if txn.status == "PENDING" else "🔴"
                text += f"{emoji} {txn.get_transaction_type_display()}\n"
                text += f"   {txn.amount} {txn.get_currency_type_display()}\n"
                text += f"   {txn.created_at.strftime('%Y/%m/%d %H:%M')}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_ACCOUNT)]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif query.data == CALLBACK_BACK_TO_ACCOUNT:
        await query.edit_message_text(
            MSG_ACCOUNT_MENU,
            reply_markup=get_account_menu_keyboard(),
            parse_mode='Markdown'
        )


# ========== Wallet Menu Handlers ==========

async def wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show wallet menu."""
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return
    
    await update.message.reply_text(
        MSG_WALLET_MENU,
        reply_markup=get_wallet_menu_keyboard(),
        parse_mode='Markdown'
    )


async def wallet_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle wallet menu callbacks."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    if query.data == CALLBACK_WALLET_BALANCES:
        # Show wallet balances
        text = WalletService.format_wallet_display(profile)
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_WALLET)]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    elif query.data == CALLBACK_WALLET_TRANSACTIONS:
        # Show transaction history
        transactions = TransactionService.get_user_transactions(profile, limit=10)
        
        if not transactions:
            text = "📜 شما هنوز هیچ تراکنشی نداشته‌اید."
        else:
            text = "📜 *تاریخچه تراکنش‌ها:*\n\n"
            for txn in transactions:
                emoji = "🟢" if txn.status == "COMPLETED" else "🟡" if txn.status == "PENDING" else "🔴"
                text += f"{emoji} {txn.get_transaction_type_display()}\n"
                text += f"   💰 مبلغ: {txn.amount} {txn.get_currency_type_display()}\n"
                text += f"   📅 {txn.created_at.strftime('%Y/%m/%d %H:%M')}\n"
                text += f"   🔢 {txn.transaction_number}\n\n"
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data=CALLBACK_BACK_TO_WALLET)]]
        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    elif query.data == CALLBACK_BACK_TO_WALLET:
        await query.edit_message_text(
            MSG_WALLET_MENU,
            reply_markup=get_wallet_menu_keyboard(),
            parse_mode='Markdown'
        )
        return ConversationHandler.END


# ========== Deposit Flow Handlers ==========

async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start deposit flow."""
    query = update.callback_query
    await query.answer()
    
    # Show currency selection
    await query.edit_message_text(
        MSG_SELECT_CURRENCY,
        reply_markup=get_currency_selection_keyboard("deposit"),
        parse_mode='Markdown'
    )
    
    return SELECTING_DEPOSIT_CURRENCY


async def deposit_currency_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle currency selection for deposit."""
    query = update.callback_query
    await query.answer()
    
    # Extract currency from callback data (e.g., "deposit_RIAL" -> "RIAL")
    currency = query.data.split('_')[1]
    context.user_data['deposit_currency'] = currency
    
    # Ask for amount
    await query.edit_message_text(
        MSG_ENTER_AMOUNT,
        parse_mode='Markdown'
    )
    
    return ENTERING_DEPOSIT_AMOUNT


async def deposit_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for deposit."""
    try:
        amount = Decimal(update.message.text.replace(',', ''))
        
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        context.user_data['deposit_amount'] = amount
        
        # Get user's bank accounts
        telegram_user = update.effective_user
        profile = get_or_create_profile(telegram_user)
        bank_accounts = get_user_bank_accounts(profile, only_verified=True)
        
        if not bank_accounts:
            await update.message.reply_text(MSG_NO_BANK_ACCOUNTS, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Show bank account selection
        await update.message.reply_text(
            MSG_SELECT_BANK_ACCOUNT,
            reply_markup=get_bank_accounts_keyboard(bank_accounts, "deposit_bank"),
            parse_mode='Markdown'
        )
        
        return SELECTING_DEPOSIT_BANK
        
    except (ValueError, InvalidOperation):
        await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return ENTERING_DEPOSIT_AMOUNT


async def deposit_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle bank account selection for deposit."""
    query = update.callback_query
    await query.answer()
    
    # Extract bank account ID from callback data
    bank_account_id = int(query.data.split('_')[-1])
    context.user_data['deposit_bank_id'] = bank_account_id
    
    # Show confirmation
    currency = context.user_data['deposit_currency']
    amount = context.user_data['deposit_amount']
    
    currency_name = CURRENCY_TYPES.get(currency, currency)
    
    text = (
        f"✅ *تایید درخواست واریز*\n\n"
        f"💰 مبلغ: {amount:,.4f} {currency_name}\n\n"
        f"آیا از ثبت این درخواست مطمئن هستید؟"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ تایید نهایی", callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton("❌ لغو", callback_data=CALLBACK_CONFIRM_NO)]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_DEPOSIT


async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and create deposit request."""
    query = update.callback_query
    await query.answer()
    
    telegram_user = update.effective_user
    profile = get_or_create_profile(telegram_user)
    
    try:
        currency = context.user_data['deposit_currency']
        amount = context.user_data['deposit_amount']
        bank_account_id = context.user_data.get('deposit_bank_id')
        
        # Create deposit request
        txn, message = DepositService.create_deposit_request(
            profile=profile,
            currency_type=currency,
            amount=amount,
            bank_account_id=bank_account_id
        )
        
        success_msg = MSG_DEPOSIT_SUCCESS.format(transaction_number=txn.transaction_number)
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        await query.edit_message_text(
            f"❌ خطا در ثبت درخواست: {str(e)}",
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END


# ========== Withdraw Flow Handlers ==========
# Similar structure to deposit flow
# TODO: Implement withdraw handlers following the same pattern


# ========== Transfer Flow Handlers ==========
# TODO: Implement transfer handlers


# ========== Add Bank Account Flow ==========
# TODO: Implement bank account addition flow


# ========== Conversation Handler Definitions ==========

def get_deposit_conversation_handler():
    """Create deposit conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(deposit_start, pattern=f"^{CALLBACK_WALLET_DEPOSIT}$")
        ],
        states={
            SELECTING_DEPOSIT_CURRENCY: [
                CallbackQueryHandler(deposit_currency_selected, pattern="^deposit_")
            ],
            ENTERING_DEPOSIT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, deposit_amount_entered)
            ],
            SELECTING_DEPOSIT_BANK: [
                CallbackQueryHandler(deposit_bank_selected, pattern="^deposit_bank_")
            ],
            CONFIRMING_DEPOSIT: [
                CallbackQueryHandler(deposit_confirm, pattern=f"^{CALLBACK_CONFIRM_YES}$"),
                CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CALLBACK_CONFIRM_NO}$")
            ],
        },
        fallbacks=[
            CallbackQueryHandler(lambda u, c: ConversationHandler.END, pattern=f"^{CALLBACK_BACK_TO_WALLET}$")
        ],
    )


# Add similar conversation handlers for:
# - Withdraw
# - Transfer
# - Add Bank Account

# In runbot.py, add these handlers to the application:
# application.add_handler(MessageHandler(filters.Regex(f"^{MENU_ACCOUNT}$"), account_menu))
# application.add_handler(MessageHandler(filters.Regex(f"^{MENU_WALLET}$"), wallet_menu))
# application.add_handler(CallbackQueryHandler(account_callback_handler, pattern="^account_"))
# application.add_handler(CallbackQueryHandler(wallet_callback_handler, pattern="^wallet_"))
# application.add_handler(get_deposit_conversation_handler())
# ... etc
