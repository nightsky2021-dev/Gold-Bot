"""
Withdrawal flow handlers.

Handles the complete withdrawal conversation flow including:
- Currency selection (Rial only)
- Amount entry
- Bank account selection
- Confirmation and withdrawal request creation
"""

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from users.models import Profile, BankAccount
from users.services import WalletService
from trading.services import WithdrawalService, BankAccountService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_GENERAL,
    ERROR_INVALID_AMOUNT,
    ERROR_NO_VERIFIED_BANKS,
    ORDER_CANCELLED,
    BTN_CANCEL,
    BTN_CONFIRM,
    BTN_BACK,
    CURRENCY_PREFIX,
    BANK_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    WITHDRAW_SELECT_CURRENCY,
    WITHDRAW_ENTER_AMOUNT,
    WITHDRAW_SELECT_BANK,
    WITHDRAW_CONFIRM,
)
from bot.handlers.base import get_or_create_profile
from bot.utils.wallet_helpers import handle_wallet_error, WithdrawFlowManager
from ..utils import safe_edit_message

logger = logging.getLogger('bot.wallet.withdraw')


async def withdraw_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start withdrawal conversation.
    
    Now supports dynamic currencies - shows all active currencies with available balances.
    """
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Check if profile is complete (has national code) - required for withdrawals
    if not profile.national_code:
        await query.edit_message_text(
            "⚠️ *برای برداشت، تکمیل پروفایل الزامی است*\n\n"
            "لطفاً ابتدا از منوی *حساب من* کد ملی خود را ثبت کنید.\n\n"
            "این اطلاعات برای امنیت معاملات و تطابق با قوانین بانکی ضروری است.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Only allow Rial withdrawals - get Rial currency only
    from trading.models import Currency
    
    try:
        rial_currency = await sync_to_async(Currency.objects.get)(
            code__iexact='RIAL', is_active=True
        )
    except Currency.DoesNotExist:
        await query.edit_message_text(
            "❌ *خطای سیستم*\n\n"
            "ارز ریال در سیستم یافت نشد.\n"
            "لطفاً با پشتیبانی تماس بگیرید.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Get wallet balances for Rial only
    balances = await sync_to_async(WalletService.get_wallet_balance)(profile)
    rial_balance_data = balances.get('rial', {})
    rial_available = rial_balance_data.get('available', Decimal('0'))
    
    # Check if user has Rial balance
    available_currencies = []
    if rial_available > 0:
        available_currencies.append((rial_currency, rial_available))
    
    if not available_currencies:
        await query.edit_message_text(
            "❌ *موجودی ریالی قابل برداشت ندارید.*\n\n"
            "برای برداشت باید موجودی ریالی قابل استفاده داشته باشید.\n"
            "⚠️ *توجه:* فقط ریال قابل برداشت است.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Since only Rial is available for withdrawal, go directly to amount entry
    currency, available = available_currencies[0]  # Will always be Rial
    if context.user_data is not None:
        context.user_data['withdraw_currency'] = currency.code
    
    currency_name = await sync_to_async(WalletService.get_currency_display_name)(currency.code)
    
    # Format amount using service layer helper
    available_formatted = await sync_to_async(WalletService.format_currency_amount)(
        available, currency.code
    )
    
    prompt = (
        f"💳 *برداشت {currency_name}*\n\n"
        f"موجودی قابل برداشت: *{available_formatted} ریال*\n\n"
        f"لطفاً مبلغ مورد نظر برای برداشت را به *ریال* وارد کنید:\n\n"
        f"مثال: `500000` (پانصد هزار ریال)\n\n"
        f"⚠️ *توجه:* فقط ریال قابل برداشت است."
    )
    
    keyboard = [
        [
            InlineKeyboardButton(BTN_BACK, callback_data="wallet_back"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            prompt,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            prompt,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return WITHDRAW_ENTER_AMOUNT


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
    
    currency_code = query.data.replace(CURRENCY_PREFIX, "")
    context.user_data['withdraw_currency'] = currency_code
    
    # Get available balance using WalletService (supports dynamic currencies)
    available = await sync_to_async(WalletService.get_available_balance)(profile, currency_code)
    currency_name = await sync_to_async(WalletService.get_currency_display_name)(currency_code)
    
    # Format amount using service layer helper
    available_formatted = await sync_to_async(WalletService.format_currency_amount)(
        available, currency_code
    )
    
    from bot.constants import PROMPT_ENTER_WITHDRAW_AMOUNT
    prompt = PROMPT_ENTER_WITHDRAW_AMOUNT.format(
        available=available_formatted,
        currency=currency_name
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        prompt,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return WITHDRAW_ENTER_AMOUNT


async def withdraw_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle amount input for withdrawal."""
    query = None
    amount = None
    
    # Check if this is a callback query (back button) or a message (user input)
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        # When called from back button, amount should be in context
        # Don't try to parse from message text in callback query case
    elif update.message and update.message.text is not None:
        text = update.message.text
        try:
            amount = Decimal(text.replace(',', ''))
        except:
            pass
    else:
        return ConversationHandler.END

    telegram_user = update.effective_user
    if not telegram_user:
        return ConversationHandler.END
        
    profile = await get_or_create_profile(telegram_user)
    if not profile:
        return ConversationHandler.END
    
    # Ensure context.user_data is available
    if context.user_data is None:
        if query:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        elif update.message:
            await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    try:
        if amount is None:
             # Try to get from context if not in update (e.g., when called from back button)
             amount = context.user_data.get('withdraw_amount')
        
        if amount is None or amount <= 0:
            if update.message and hasattr(update.message, 'reply_text'):
                 await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
            elif query:
                 await query.edit_message_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
            return WITHDRAW_ENTER_AMOUNT
        
        currency = context.user_data.get('withdraw_currency')
        if not currency:
            if query:
                 await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            elif update.message:
                 await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Validate sufficient balance using WalletService (supports all dynamic currencies)
        # Final authority is WalletService.freeze_balance inside WithdrawalService,
        # whose ValidationError message is shown verbatim if anything slips through.
        has_sufficient = await sync_to_async(WalletService.check_sufficient_balance)(
            profile, currency, amount
        )
        
        if not has_sufficient:
            available = await sync_to_async(WalletService.get_available_balance)(profile, currency)
            currency_name = await sync_to_async(WalletService.get_currency_display_name)(currency)
            
            # Format amounts using service layer helper
            available_formatted = await sync_to_async(WalletService.format_currency_amount)(
                available, currency
            )
            required_formatted = await sync_to_async(WalletService.format_currency_amount)(
                amount, currency
            )
            
            error_msg = (
                f"❌ موجودی {currency_name} کافی نیست.\n\n"
                f"موجودی قابل استفاده: {available_formatted}\n"
                f"مقدار درخواستی: {required_formatted}"
            )
            
            if query:
                 await safe_edit_message(query, error_msg, parse_mode='Markdown')
            elif update.message:
                 await update.message.reply_text(error_msg, parse_mode='Markdown')
                 
            return WITHDRAW_ENTER_AMOUNT
        
        if context.user_data:
            context.user_data['withdraw_amount'] = amount
        
        # Get verified bank accounts using service layer
        bank_accounts = await sync_to_async(BankAccountService.get_user_bank_accounts)(
            profile, verified_only=True
        )
        
        if not bank_accounts:
            msg = ERROR_NO_VERIFIED_BANKS
            if query:
                 await query.edit_message_text(msg, parse_mode='Markdown')
            elif update.message:
                 await update.message.reply_text(msg, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Show bank account selection
        keyboard = []
        for account in bank_accounts:
            button_text = f"{account.bank_name} - {account.get_masked_account_number()}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"{BANK_PREFIX}{account.id}"  # type: ignore[attr-defined]
            )])
        
        keyboard.append([
            InlineKeyboardButton(BTN_BACK, callback_data="withdraw_back_to_amount"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        from bot.constants import PROMPT_SELECT_WITHDRAW_BANK
        if query:
             await safe_edit_message(query, PROMPT_SELECT_WITHDRAW_BANK, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.message:
             await update.message.reply_text(
                PROMPT_SELECT_WITHDRAW_BANK,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return WITHDRAW_SELECT_BANK
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error processing withdraw amount: {str(e)}")
        if query:
             await query.edit_message_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        elif update.message:
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
            
        currency_name = await sync_to_async(WalletService.get_currency_display_name)(currency)
        
        # Get currency info for formatting
        from trading.models import Currency as CurrencyModel
        try:
            currency_obj = await sync_to_async(CurrencyModel.objects.get)(
                code=currency, is_active=True
            )
            decimal_places = currency_obj.decimal_places
        except CurrencyModel.DoesNotExist:
            decimal_places = 2  # Default to 2 decimal places
        
        # Format amount based on decimal places
        if decimal_places == 0:
            amount_formatted = f"{amount:,.0f}"
        elif decimal_places == 2:
            amount_formatted = f"{amount:,.2f}"
        elif decimal_places == 4:
            amount_formatted = f"{amount:,.4f}"
        else:
            format_spec = f",.{decimal_places}f"
            amount_formatted = f"{amount:{format_spec}}"
        
        # Show preview
        preview = (
            f"💵 *پیش‌فاکتور برداشت*\n\n"
            f"ارز: {currency_name}\n"
            f"مبلغ: {amount_formatted}\n"
            f"حساب بانکی: {bank_account.bank_name}\n"
            f"شماره حساب: {bank_account.get_masked_account_number()}\n\n"
            f"آیا از ثبت درخواست برداشت مطمئن هستید؟"
        )
        
        keyboard = [
            [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}withdraw")],
            [
                InlineKeyboardButton(BTN_BACK, callback_data="withdraw_back_to_bank"),
                InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}withdraw")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Use safe edit to handle "message not modified" errors
        if update.effective_chat:
            await safe_edit_message(
                query,
                preview,
                reply_markup=reply_markup,
                bot=context.bot,
                chat_id=update.effective_chat.id
            )
        else:
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
        
        currency_name = await sync_to_async(WalletService.get_currency_display_name)(currency)
        
        # Format amount using service layer helper
        amount_formatted = await sync_to_async(WalletService.format_currency_amount)(
            amount, currency
        )
        
        success_msg = (
            f"✅ *درخواست برداشت شما با موفقیت ثبت شد!*\n\n"
            f"شماره درخواست: #{withdraw_request.id}\n"
            f"مبلغ: {amount_formatted} {currency_name}\n\n"
            f"موجودی مورد نظر مسدود شد.\n"
            f"پس از تأیید مدیر، واریز به حساب شما انجام خواهد شد."
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context data using helper
        WithdrawFlowManager.clear_withdraw_context(context)
        return ConversationHandler.END
        
    except ValidationError as e:
        await handle_wallet_error(update, context, e)
        return ConversationHandler.END
    except Exception as e:
        await handle_wallet_error(update, context, e)
        return ConversationHandler.END


async def withdraw_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel withdrawal conversation."""
    if context.user_data is None:
        return ConversationHandler.END
    
    # Handle both callback queries and messages
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    elif update.message:
        await update.message.reply_text(ORDER_CANCELLED, parse_mode='Markdown')
    
    WithdrawFlowManager.clear_withdraw_context(context)
    
    return ConversationHandler.END


async def withdraw_back_to_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to withdrawal start (amount entry for Rial)."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Clear amount from context
    if 'withdraw_amount' in context.user_data:
        del context.user_data['withdraw_amount']
    
    # Restart withdrawal flow
    return await withdraw_start(update, context)


async def withdraw_back_to_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to amount entry step in withdrawal flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Clear bank selection from context
    if 'withdraw_bank_id' in context.user_data:
        del context.user_data['withdraw_bank_id']
    
    # Go back to amount entry (which is the start for Rial-only withdrawal)
    return await withdraw_start(update, context)


async def withdraw_back_to_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to bank selection step in withdrawal flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Verify amount is in context (should be if we got this far)
    amount = context.user_data.get('withdraw_amount')
    if not amount:
        return await withdraw_start(update, context)
    
    # Instead of using FakeMessage which breaks reply_text, just call withdraw_amount_entered
    # It will detect callback_query and use edit_message_text/safe_edit_message
    return await withdraw_amount_entered(update, context)
