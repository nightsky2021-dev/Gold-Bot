"""
Deposit flow handlers.

Handles the complete deposit conversation flow including:
- System bank account selection
- Amount entry
- Source bank account selection
- Receipt upload
- Confirmation and transaction creation
"""

import logging
from decimal import Decimal, InvalidOperation
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from users.models import Profile, BankAccount
from users.services import WalletService
from trading.services import TransactionService, BankAccountService
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_GENERAL,
    ERROR_INVALID_AMOUNT,
    ORDER_CANCELLED,
    BTN_CANCEL,
    BTN_CONFIRM,
    BTN_BACK,
    BANK_PREFIX,
    SYSBANK_PREFIX,
    CANCEL_PREFIX,
    CONFIRM_PREFIX,
    DEPOSIT_SELECT_SYSTEM_BANK,
    DEPOSIT_ENTER_AMOUNT,
    DEPOSIT_SELECT_SOURCE_BANK,
    DEPOSIT_UPLOAD_RECEIPT,
    DEPOSIT_CONFIRM,
)
from bot.handlers.base import get_or_create_profile
from bot.utils.wallet_helpers import handle_wallet_error, DepositFlowManager
from ..utils import safe_edit_message

logger = logging.getLogger('bot.wallet.deposit')


async def deposit_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start deposit conversation - show system bank accounts.
    
    Business rule: Users can only deposit in RIAL currency.
    Other wallet assets (gold/coin/dollar) can only be converted to Rial
    via trading flows and are not directly depositable.
    They must first select which company bank account to deposit to.
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
    
    # Force Rial currency for deposits
    if context.user_data is not None:
        context.user_data['deposit_currency'] = 'RIAL'
    
    # Get active system bank accounts using service layer
    system_accounts = await sync_to_async(list)(
        BankAccountService.get_active_system_accounts()
    )
    
    if not system_accounts:
        await query.edit_message_text(
            "⚠️ *عدم وجود حساب بانکی فعال*\n\n"
            "در حال حاضر حساب بانکی برای واریز فعال نیست.\n"
            "لطفاً با پشتیبانی تماس بگیرید.\n\n"
            "📞 @support",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Build keyboard with system bank accounts
    keyboard = []
    message = "💳 *واریز ریال*\n\n"
    message += "لطفاً ابتدا حساب بانکی را که می‌خواهید به آن واریز کنید انتخاب کنید:\n\n"
    
    for i, account in enumerate(system_accounts, 1):
        button_text = f"{account.bank_name} - {account.get_masked_account_number()}"
        keyboard.append([InlineKeyboardButton(
            button_text,
            callback_data=f"{SYSBANK_PREFIX}{account.pk}"
        )])
        
        # Add account details to message
        message += f"*{i}. {account.bank_name}*\n"
        message += f"  صاحب حساب: {account.account_holder_name}\n"
        if account.description:
            message += f"  💡 {account.description}\n"
        message += "\n"
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    message += "⚠️ *توجه:* فقط واریز به حساب‌های بالا معتبر است."
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            message,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return DEPOSIT_SELECT_SYSTEM_BANK


async def deposit_system_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle system bank account selection for deposit.
    Show full account details and ask for deposit amount.
    """
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Extract system bank account ID
    system_bank_id = int(query.data.replace(SYSBANK_PREFIX, ""))
    context.user_data['deposit_system_bank_id'] = system_bank_id
    
    # Get system bank account details
    from users.models import SystemBankAccount
    try:
        system_account = await sync_to_async(SystemBankAccount.objects.get)(
            id=system_bank_id, is_active=True
        )
    except SystemBankAccount.DoesNotExist:
        await query.edit_message_text(
            "❌ حساب بانکی انتخابی یافت نشد یا غیرفعال شده است.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Show full account details
    message = "💳 *اطلاعات حساب بانکی*\n\n"
    message += f"🏦 بانک: *{system_account.bank_name}*\n"
    message += f"👤 صاحب حساب: {system_account.account_holder_name}\n"
    message += f"💳 شماره کارت:\n`{system_account.account_number}`\n"
    
    if system_account.iban:
        message += f"🔢 شماره شبا:\n`{system_account.iban}`\n"
    
    if system_account.description:
        message += f"\n💡 {system_account.description}\n"
    
    message += "\n" + "━" * 30 + "\n\n"
    message += "💰 *وارد کردن مبلغ*\n\n"
    message += "لطفاً مبلغ واریزی خود را به *ریال* وارد کنید:\n\n"
    message += "مثال: `1000000` (یک میلیون ریال)\n\n"
    message += "⚠️ حداقل واریز: 100,000 ریال"
    
    # Add back and cancel buttons while user is entering the amount
    keyboard = [
        [
            InlineKeyboardButton(BTN_BACK, callback_data="deposit_back_to_bank_select"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            message,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return DEPOSIT_ENTER_AMOUNT


async def deposit_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle amount input for deposit.
    Now asks user to select their source bank account.
    """
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
             amount = context.user_data.get('deposit_amount')
        
        if amount is None or amount <= 0:
             # Should handle error here but for now we can return to previous step or show error
             if query:
                 # Probably came here by mistake or lost context
                 return await deposit_start(update, context)
             raise ValueError("Amount must be positive")
        
        # Validate minimum deposit amount using service layer
        try:
            await sync_to_async(WalletService.validate_deposit_amount)(amount)
        except ValidationError as e:
            if query:
                await query.edit_message_text(str(e), parse_mode='Markdown')
            elif update.message:
                await update.message.reply_text(str(e), parse_mode='Markdown')
            return DEPOSIT_ENTER_AMOUNT
        
        if context.user_data:
            context.user_data['deposit_amount'] = amount
        
        # For deposits, allow using any existing bank account (verified or not)
        user_banks = await sync_to_async(BankAccountService.get_user_bank_accounts)(
            profile, verified_only=False
        )
        
        if not user_banks:
            msg = (
                "❌ *حساب بانکی ندارید*\n\n"
                "برای واریز، ابتدا باید یک حساب بانکی ثبت کنید.\n\n"
                "📋 *مراحل ثبت حساب:*\n"
                "1. به منوی *حساب من* بروید\n"
                "2. گزینه *🏦 حساب‌های بانکی* را انتخاب کنید\n"
                "3. روی *➕ افزودن حساب* کلیک کنید\n"
                "4. اطلاعات حساب خود را وارد کنید\n\n"
                "⚠️ این اطلاعات برای امنیت و تطابق با قوانین ضروری است."
            )
            if query:
                 await query.edit_message_text(msg, parse_mode='Markdown')
            elif update.message:
                 await update.message.reply_text(msg, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Ask user to select source bank account
        keyboard = []
        message = "🏦 *انتخاب حساب بانکی مبدأ*\n\n"
        message += "لطفاً حساب بانکی خود را که *از آن واریز کرده‌اید* انتخاب کنید:\n\n"
        
        for account in user_banks:
            button_text = f"{account.bank_name} - {account.get_masked_account_number()}"
            keyboard.append([InlineKeyboardButton(
                button_text,
                callback_data=f"{BANK_PREFIX}{account.pk}"
            )])
        
        keyboard.append([
            InlineKeyboardButton(BTN_BACK, callback_data="deposit_back_to_amount"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")
        ])
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message += "⚠️ *توجه مهم:*\n"
        message += "حساب بانکی باید به نام خودتان باشد و از همین حساب واریز کرده باشید.\n"
        message += "این برای امنیت و احراز هویت ضروری است."
        
        if query:
             await safe_edit_message(query, message, reply_markup=reply_markup, parse_mode='Markdown')
        elif update.message:
             await update.message.reply_text(
                message,
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
        
        return DEPOSIT_SELECT_SOURCE_BANK
        
    except (ValueError, InvalidOperation) as e:
        logger.error(f"Error processing deposit amount: {str(e)}")
        if query:
             await query.edit_message_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        elif update.message:
             await update.message.reply_text(ERROR_INVALID_AMOUNT, parse_mode='Markdown')
        return DEPOSIT_ENTER_AMOUNT


async def deposit_source_bank_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle source bank account selection for deposit.
    Ask user to upload receipt image.
    """
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Extract source bank account ID
    source_bank_id = int(query.data.replace(BANK_PREFIX, ""))
    context.user_data['deposit_source_bank_id'] = source_bank_id
    
    # Get source bank account details
    try:
        source_account = await sync_to_async(BankAccount.objects.get)(id=source_bank_id)
    except BankAccount.DoesNotExist:
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show confirmation and ask for receipt
    message = "📷 *آپلود رسید واریز*\n\n"
    message += "✅ اطلاعات ثبت شد:\n"
    message += f"• حساب مبدأ شما: {source_account.bank_name} - {source_account.get_masked_account_number()}\n\n"
    
    message += "لطفاً *تصویر رسید* واریز بانکی خود را ارسال کنید:\n\n"
    message += "📌 *نکات مهم:*\n"
    message += "• تصویر باید واضح و خوانا باشد\n"
    message += "• تاریخ و مبلغ واریز باید مشخص باشد\n"
    message += "• اطلاعات حساب مقصد باید مطابق باشد\n"
    message += "• حداکثر حجم فایل: 5 مگابایت\n\n"
    message += "⚠️ رسید برای بررسی توسط ادمین استفاده می‌شود."
    
    # Add back and cancel buttons while user is uploading the receipt
    keyboard = [
        [
            InlineKeyboardButton(BTN_BACK, callback_data="deposit_back_to_source_bank"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            message,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return DEPOSIT_UPLOAD_RECEIPT


async def deposit_receipt_uploaded(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handle receipt image upload for deposit.
    Download image from Telegram and save to storage.
    """
    if not update.message or not update.message.photo or context.user_data is None:
        return ConversationHandler.END
        
    from django.core.files.storage import default_storage
    from django.core.files.base import ContentFile
    from django.utils import timezone
    
    # Get the photo (highest resolution)
    photo = update.message.photo[-1]
    
    try:
        # Download image from Telegram
        photo_file = await photo.get_file()
        file_bytes = await photo_file.download_as_bytearray()
        
        # Validate file size (max 5MB)
        if len(file_bytes) > 5 * 1024 * 1024:
            await update.message.reply_text(
                "❌ *حجم فایل خیلی بزرگ است*\n\n"
                "حداکثر حجم مجاز: 5 مگابایت\n"
                "لطفاً تصویر کوچکتری ارسال کنید.",
                parse_mode='Markdown'
            )
            return DEPOSIT_UPLOAD_RECEIPT
        
        # Generate unique filename
        if not update.effective_user:
            return ConversationHandler.END
            
        telegram_user = update.effective_user
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f"receipt_{telegram_user.id}_{timestamp}.jpg"
        
        # Save to media/receipts/YYYY/MM/
        now = timezone.now()
        file_path = f'receipts/{now.year}/{now.month:02d}/{filename}'
        saved_path = default_storage.save(file_path, ContentFile(bytes(file_bytes)))
        
        # Store file path in context
        context.user_data['deposit_receipt_path'] = saved_path
        
        logger.info(f"Receipt image downloaded and saved: {saved_path}")
        
    except Exception as e:
        logger.error(f"Error downloading receipt image: {str(e)}")
        await update.message.reply_text(
            "❌ خطا در دریافت تصویر. لطفاً دوباره تلاش کنید.",
            parse_mode='Markdown'
        )
        return DEPOSIT_UPLOAD_RECEIPT
    
    # Get all stored data
    amount = context.user_data.get('deposit_amount')
    system_bank_id = context.user_data.get('deposit_system_bank_id')
    source_bank_id = context.user_data.get('deposit_source_bank_id')
    
    if not amount or not system_bank_id or not source_bank_id:
        await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Get account details for display
    from users.models import SystemBankAccount
    try:
        system_account = await sync_to_async(SystemBankAccount.objects.get)(id=system_bank_id)
        source_account = await sync_to_async(BankAccount.objects.get)(id=source_bank_id)
    except (SystemBankAccount.DoesNotExist, BankAccount.DoesNotExist):
        await update.message.reply_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show confirmation with all details
    confirm_msg = (
        f"✅ *تأیید نهایی واریز*\n\n"
        f"💰 مبلغ: *{amount:,.0f} ریال*\n"
        f"🏦 واریز به: {system_account.bank_name}\n"
        f"📤 از حساب: {source_account.bank_name} - {source_account.get_masked_account_number()}\n"
        f"📷 رسید: دریافت شد ✓\n\n"
        f"⚠️ *توجه:* پس از تأیید، درخواست شما به ادمین ارسال می‌شود.\n"
        f"موجودی شما پس از تأیید ادمین به‌روزرسانی خواهد شد.\n\n"
        f"آیا اطلاعات را تأیید می‌کنید؟"
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}deposit")],
        [
            InlineKeyboardButton(BTN_BACK, callback_data="deposit_back_to_receipt"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return DEPOSIT_CONFIRM


async def deposit_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm and create deposit transaction with all new fields.
    Saves system bank account, source bank account, and receipt image.
    """
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
        
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        return ConversationHandler.END
    
    try:
        # Get all stored data
        currency = context.user_data.get('deposit_currency')  # Will be 'RIAL'
        amount = context.user_data.get('deposit_amount')
        system_bank_id = context.user_data.get('deposit_system_bank_id')
        source_bank_id = context.user_data.get('deposit_source_bank_id')
        receipt_path = context.user_data.get('deposit_receipt_path')
        
        if not currency or not amount or not system_bank_id or not source_bank_id:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Get bank account objects
        from users.models import SystemBankAccount
        from trading.models import Transaction
        
        try:
            system_account = await sync_to_async(SystemBankAccount.objects.get)(id=system_bank_id)
            source_account = await sync_to_async(BankAccount.objects.get)(id=source_bank_id)
        except (SystemBankAccount.DoesNotExist, BankAccount.DoesNotExist):
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        # Create deposit transaction with all new fields
        @sync_to_async
        def create_deposit_transaction():
            return Transaction.objects.create(
                profile=profile,
                transaction_type='DEPOSIT',
                currency=currency,
                amount=amount,
                system_bank_account=system_account,
                source_bank_account=source_account,
                receipt_image=receipt_path if receipt_path else None,
                description=f"واریز {amount:,.0f} ریال به حساب {system_account.bank_name}",
                status='PENDING'
            )
        
        txn = await create_deposit_transaction()
        
        logger.info(
            f"Deposit transaction {txn.id} created: "
            f"{amount} {currency} from user {profile.get_display_name()} "
            f"(System Bank: {system_account.bank_name}, "
            f"Source Bank: {source_account.bank_name})"
        )
        
        # Send notification to admins
        try:
            from bot.services.notification_service import AdminNotificationService
            notification_result = await AdminNotificationService.notify_deposit_submitted(
                txn, context.application.bot
            )
            logger.info(
                f"Admin notification result for transaction {txn.id}: "
                f"{notification_result['success']}/{notification_result['total']} admins notified"
            )
        except Exception as e:
            # Don't fail the deposit if notification fails
            logger.error(f"Failed to send admin notification for transaction {txn.id}: {e}")
        
        # Success message to user
        success_msg = (
            f"✅ *درخواست واریز ثبت شد*\n\n"
            f"شناسه تراکنش: `{txn.id}`\n"
            f"مبلغ: *{amount:,.0f} ریال*\n"
            f"وضعیت: ⏳ در انتظار تأیید ادمین\n\n"
            f"📌 *مراحل بعدی:*\n"
            f"• درخواست شما به ادمین ارسال شد\n"
            f"• پس از بررسی رسید، موجودی شما به‌روزرسانی می‌شود\n"
            f"• معمولاً تأیید 1-24 ساعت طول می‌کشد\n\n"
            f"از صبر و شکیبایی شما سپاسگزاریم 🙏"
        )
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        
        # Clear context data using helper
        DepositFlowManager.clear_deposit_context(context)
        return ConversationHandler.END
        
    except ValidationError as e:
        await handle_wallet_error(update, context, e)
        return ConversationHandler.END
    except Exception as e:
        await handle_wallet_error(update, context, e)
        return ConversationHandler.END


async def deposit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel deposit conversation."""
    if context.user_data is None:
        return ConversationHandler.END
    
    # Handle both callback queries and messages
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(ORDER_CANCELLED, parse_mode='Markdown')
    elif update.message:
        await update.message.reply_text(ORDER_CANCELLED, parse_mode='Markdown')
    
    DepositFlowManager.clear_deposit_context(context)
    
    return ConversationHandler.END


async def deposit_back_to_bank_select(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to bank selection step in deposit flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Clear amount from context but keep bank selection
    if 'deposit_amount' in context.user_data:
        del context.user_data['deposit_amount']
    
    # Restart bank selection
    return await deposit_start(update, context)


async def deposit_back_to_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to amount entry step in deposit flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Clear source bank from context but keep system bank and amount
    if 'deposit_source_bank_id' in context.user_data:
        del context.user_data['deposit_source_bank_id']
    
    system_bank_id = context.user_data.get('deposit_system_bank_id')
    if not system_bank_id:
        return await deposit_start(update, context)
    
    # Get system bank account details to show again
    from users.models import SystemBankAccount
    try:
        system_account = await sync_to_async(SystemBankAccount.objects.get)(
            id=system_bank_id, is_active=True
        )
    except SystemBankAccount.DoesNotExist:
        await query.edit_message_text(
            "❌ حساب بانکی انتخابی یافت نشد یا غیرفعال شده است.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Show full account details and ask for deposit amount again
    message = "💳 *اطلاعات حساب بانکی*\n\n"
    message += f"🏦 بانک: *{system_account.bank_name}*\n"
    message += f"👤 صاحب حساب: {system_account.account_holder_name}\n"
    message += f"💳 شماره کارت:\n`{system_account.account_number}`\n"
    
    if system_account.iban:
        message += f"🔢 شماره شبا:\n`{system_account.iban}`\n"
    
    if system_account.description:
        message += f"\n💡 {system_account.description}\n"
    
    message += "\n" + "━" * 30 + "\n\n"
    message += "💰 *وارد کردن مبلغ*\n\n"
    message += "لطفاً مبلغ واریزی خود را به *ریال* وارد کنید:\n\n"
    message += "مثال: `1000000` (یک میلیون ریال)\n\n"
    message += "⚠️ حداقل واریز: 100,000 ریال"
    
    # Add back and cancel buttons while user is entering the amount
    keyboard = [
        [
            InlineKeyboardButton(BTN_BACK, callback_data="deposit_back_to_bank_select"),
            InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}deposit")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Use safe edit to handle "message not modified" errors
    if update.effective_chat:
        await safe_edit_message(
            query,
            message,
            reply_markup=reply_markup,
            bot=context.bot,
            chat_id=update.effective_chat.id
        )
    else:
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    return DEPOSIT_ENTER_AMOUNT


async def deposit_back_to_source_bank(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to source bank selection step in deposit flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    # Clear receipt from context
    if 'deposit_receipt_path' in context.user_data:
        del context.user_data['deposit_receipt_path']
    
    # Simulate amount entry to go back to source bank selection
    amount = context.user_data.get('deposit_amount')
    if not amount:
        return await deposit_start(update, context)
    
    # Call deposit_amount_entered directly - it will detect callback query and use context amount
    return await deposit_amount_entered(update, context)


async def deposit_back_to_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Go back to receipt upload step in deposit flow."""
    query = update.callback_query
    if not query or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
        
    await query.answer()
    
    source_bank_id = context.user_data.get('deposit_source_bank_id')
    if not source_bank_id:
        return await deposit_start(update, context)
    
    # Simulate source bank selection to go back to receipt upload
    query.data = f"{BANK_PREFIX}{source_bank_id}"
    return await deposit_source_bank_selected(update, context)
