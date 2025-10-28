"""
Management command برای اجرای ربات تلگرام - نسخه حرفه‌ای
"""
import logging
import os
import django
from decimal import Decimal
from typing import Optional, cast, Any
from datetime import datetime, timedelta
import hashlib
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from telegram import Update, ReplyKeyboardRemove, ForceReply, Message
import telegram.error
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from users.services import UserService
from users.models import Profile
from users.wallet_services import WalletService
from trading.services import TradingService
from trading.models import Product, Order
from bot.constants import (
    # Conversation States
    SELECTING_PRODUCT, SELECTING_METHOD, ENTERING_AMOUNT, CONFIRMING_BUY, CONFIRMING_SELL,
    WALLET_MAIN, WALLET_DEPOSIT_STATE, WALLET_WITHDRAW_STATE, WALLET_HISTORY_STATE,
    ACCOUNT_MAIN, ACCOUNT_ADD_BANK, ACCOUNT_EDIT_BANK, ACCOUNT_VERIFY_BANK,
    DEPOSIT_SELECT_CURRENCY, DEPOSIT_ENTER_AMOUNT, DEPOSIT_SELECT_BANK, DEPOSIT_UPLOAD_RECEIPT, DEPOSIT_CONFIRM,
    WITHDRAW_SELECT_CURRENCY, WITHDRAW_ENTER_AMOUNT, WITHDRAW_SELECT_BANK, WITHDRAW_CONFIRM,
    SELECTING_ACTION, CONFIRMING_TRADE, ENTERING_FIRST_NAME, ENTERING_LAST_NAME,
    
    # Callback Data Prefixes
    PRODUCT_PREFIX, METHOD_PREFIX, CONFIRM_PREFIX, CANCEL_PREFIX,
    WALLET_PREFIX, ACCOUNT_PREFIX, CURRENCY_PREFIX, BANK_PREFIX, DEPOSIT_PREFIX, WITHDRAW_PREFIX,
    
    # Calculation Methods
    METHOD_GRAMS, METHOD_RIAL,
    
    # Main Menu Buttons
    MENU_PRICE, MENU_BUY, MENU_SELL, MENU_WALLET, MENU_ACCOUNT, MENU_HISTORY, MENU_CANCEL,
    MENU_TRADE, MENU_PORTFOLIO, MENU_REFRESH, MENU_PRICES,
    
    # Wallet Menu Buttons
    WALLET_BALANCE, WALLET_DEPOSIT, WALLET_WITHDRAW, WALLET_HISTORY,
    
    # Account Menu Buttons
    ACCOUNT_ADD, ACCOUNT_LIST, ACCOUNT_VERIFY,
    
    # Currency Types
    CURRENCY_RIAL, CURRENCY_GOLD, CURRENCY_COIN, CURRENCY_DOLLAR, CURRENCY_TYPES,
    
    # Iranian Banks
    IRANIAN_BANKS,
    
    # Validation Limits
    MIN_ORDER_GRAMS, MIN_ORDER_RIAL, MAX_ORDER_GRAMS, MAX_ORDER_RIAL,
    
    # Welcome Messages
    WELCOME_NEW_USER, WELCOME_PENDING_USER, WELCOME_APPROVED_USER, REGISTRATION_SUCCESS,
    
    # Error Messages
    ERROR_NOT_APPROVED, ERROR_INVALID_AMOUNT, ERROR_INSUFFICIENT_BALANCE_RIAL, ERROR_INSUFFICIENT_BALANCE_GOLD,
    ERROR_GENERAL, ERROR_NO_PRODUCTS, ERROR_AMOUNT_TOO_SMALL, ERROR_AMOUNT_TOO_LARGE,
    
    # Order Messages
    ORDER_SUCCESS, ORDER_CANCELLED,
    
    # Prompts
    PROMPT_SELECT_PRODUCT, PROMPT_SELECT_METHOD, PROMPT_ENTER_AMOUNT_GRAMS, PROMPT_ENTER_AMOUNT_RIAL,
    PROMPT_ENTER_AMOUNT_SELL_GRAMS, PROMPT_ENTER_AMOUNT_SELL_RIAL,
    
    # History Messages
    NO_ORDERS, ORDERS_HISTORY_HEADER,
    
    # Button Texts
    BTN_SHARE_CONTACT, BTN_METHOD_GRAMS, BTN_METHOD_RIAL, BTN_CONFIRM, BTN_CANCEL, BTN_BACK_TO_MENU,
    
    # Callback Data Patterns
    CALLBACK_PRICE_GOLD, CALLBACK_PRICE_COIN, CALLBACK_PRICE_DOLLAR, CALLBACK_PRICE_ALL, CALLBACK_PRICE_REFRESH,
    CALLBACK_BACK_TO_PRICES_MENU, CALLBACK_TRADE_PRODUCT_PREFIX, CALLBACK_ACTION_BUY, CALLBACK_ACTION_SELL,
    CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL, PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR,
    CALLBACK_BACK_TO_MAIN, CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO,
    
    # Account & Wallet Management States
    VIEWING_PROFILE, MANAGING_BANK_ACCOUNTS, ADDING_BANK_ACCOUNT, ENTERING_BANK_NAME, ENTERING_ACCOUNT_NUMBER,
    ENTERING_ACCOUNT_HOLDER, ENTERING_ACCOUNT_TYPE, SELECTING_DEPOSIT_CURRENCY, ENTERING_DEPOSIT_AMOUNT,
    SELECTING_DEPOSIT_BANK, UPLOADING_RECEIPT, CONFIRMING_DEPOSIT, SELECTING_WITHDRAW_CURRENCY,
    ENTERING_WITHDRAW_AMOUNT, SELECTING_WITHDRAW_BANK, CONFIRMING_WITHDRAW,
    
    # Callback Data for Account & Wallet
    CALLBACK_ACCOUNT_PROFILE, CALLBACK_ACCOUNT_BANKCARDS, CALLBACK_ACCOUNT_BALANCES, CALLBACK_ACCOUNT_TRANSACTIONS,
    CALLBACK_WALLET_DEPOSIT, CALLBACK_WALLET_WITHDRAW, CALLBACK_WALLET_BALANCES, CALLBACK_WALLET_TRANSACTIONS,
    CALLBACK_CURRENCY_RIAL, CALLBACK_CURRENCY_GOLD, CALLBACK_CURRENCY_COIN, CALLBACK_CURRENCY_DOLLAR,
    CALLBACK_SELECT_BANK_PREFIX, CALLBACK_ADD_BANK_ACCOUNT, CALLBACK_REMOVE_BANK_PREFIX
)
from bot.keyboards import (
    get_main_menu_keyboard, get_prices_menu_keyboard, get_product_detail_keyboard,
    get_amount_method_keyboard, get_confirmation_keyboard, get_cancel_keyboard,
    get_contact_keyboard, get_back_to_prices_keyboard
)
from bot.utils import format_number, parse_decimal, validate_amount, format_datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'اجرای ربات تلگرام - نسخه حرفه‌ای'

    def handle(self, *args, **options):
        """اجرای ربات"""
        token = settings.TELEGRAM_BOT_TOKEN
        
        if not token:
            self.stderr.write('❌ توکن تلگرام تنظیم نشده است.')
            return
        
        # Create application
        application = Application.builder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        # Registration conversation handler
        application.add_handler(get_registration_conversation_handler())
        
        # Trade conversation handler (MUST be FIRST - before other callback handlers)
        application.add_handler(get_trade_conversation_handler())
        
        # Menu handlers
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PRICES}$'), show_prices_menu))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_WALLET}$'), show_wallet))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_ACCOUNT}$'), show_account))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PORTFOLIO}$'), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_HISTORY}$'), show_history))
        
        # Price callbacks
        application.add_handler(CallbackQueryHandler(show_price_gold, pattern=f'^{CALLBACK_PRICE_GOLD}$'))
        application.add_handler(CallbackQueryHandler(show_price_coin, pattern=f'^{CALLBACK_PRICE_COIN}$'))
        application.add_handler(CallbackQueryHandler(show_price_dollar, pattern=f'^{CALLBACK_PRICE_DOLLAR}$'))
        application.add_handler(CallbackQueryHandler(show_all_prices, pattern=f'^{CALLBACK_PRICE_ALL}$'))
        
        # Price refresh callbacks
        application.add_handler(CallbackQueryHandler(refresh_price, pattern=f'^{CALLBACK_PRICE_REFRESH}(gold|coin|dollar)$'))
        
        # Back to prices menu callback
        application.add_handler(CallbackQueryHandler(back_to_prices_menu, pattern='^back_to_prices_menu$'))
        
        # Error handler (handles all unhandled exceptions)
        application.add_error_handler(handle_error)
        
        # Start bot
        self.stdout.write('✅ ربات تلگرام شروع به کار کرد...')
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# ==================== Basic Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    
    if not user:
        logger.warning("start command called but no effective_user found")
        return
    
    telegram_id = str(user.id)
    
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not update.message:
        logger.warning("start command called but no message found")
        return
    
    if profile is None:
        await update.message.reply_text(
            f"👋 سلام {user.first_name} عزیز!\n\n"
            "به ربات معاملات طلا و ارز خوش آمدید.\n\n"
            "🔹 برای شروع، لطفاً شماره تماس خود را ارسال کنید:",
            reply_markup=get_contact_keyboard()
        )
    elif not is_approved:
        await update.message.reply_text(
            "⏳ حساب کاربری شما در انتظار تایید مدیر است.\n\n"
            "پس از تایید، می‌توانید از تمامی امکانات استفاده کنید. 🙏",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        from django.contrib.auth.models import User
        full_name = "کاربر"
        if profile and profile.user:
            user_obj = cast(User, profile.user)
            full_name = user_obj.get_full_name() or "کاربر"
        await update.message.reply_text(
            f"👋 سلام {full_name}!\n\n"
            "به ربات معاملات طلا و ارز خوش آمدید.\n\n"
            "💰 *قیمت و معامله:* مشاهده قیمت‌های لحظه‌ای و خرید/فروش\n"
            "👛 *کیف پول:* مشاهده موجودی\n"
            "📋 *تاریخچه:* مشاهده سفارشات قبلی",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def handle_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.exception("خطا:", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=get_main_menu_keyboard()
            )
        except:
            pass


# ==================== Registration Handlers ====================

async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ثبت نام با دریافت شماره تلگرام"""
    if not update.message or not update.message.contact:
        logger.warning("registration_start called but no message or contact found")
        return ConversationHandler.END
    
    user = update.effective_user
    if not user:
        logger.warning("registration_start called but no effective_user found")
        return ConversationHandler.END
    
    contact = update.message.contact
    telegram_id = str(user.id)
    
    if str(contact.user_id) != telegram_id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            reply_markup=get_contact_keyboard()
        )
        return ConversationHandler.END
    
    # ذخیره اطلاعات اولیه
    user_data = context.user_data
    if user_data is not None:
        user_data['telegram_id'] = telegram_id
        user_data['phone_number'] = contact.phone_number
        user_data['telegram_username'] = user.username
    
    await update.message.reply_text(
        "📝 *ثبت نام*\n\n"
        "لطفاً *نام* خود را وارد کنید:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ENTERING_FIRST_NAME


async def registration_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام"""
    if not update.message or not update.message.text:
        logger.warning("registration_first_name called but no message or text found")
        return ConversationHandler.END
    
    first_name = update.message.text.strip()
    
    if not first_name or len(first_name) < 2:
        await update.message.reply_text(
            "❌ نام باید حداقل 2 کاراکتر باشد.\n\n"
            "لطفاً نام خود را وارد کنید:"
        )
        return ENTERING_FIRST_NAME
    
    user_data = context.user_data
    if user_data is not None:
        user_data['first_name'] = first_name
    
    await update.message.reply_text(
        f"✅ نام: *{first_name}*\n\n"
        "لطفاً *نام خانوادگی* خود را وارد کنید:",
        parse_mode='Markdown'
    )
    
    return ENTERING_LAST_NAME


async def registration_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام خانوادگی"""
    if not update.message or not update.message.text:
        logger.warning("registration_last_name called but no message or text found")
        return ConversationHandler.END
    
    last_name = update.message.text.strip()
    
    if not last_name or len(last_name) < 2:
        await update.message.reply_text(
            "❌ نام خانوادگی باید حداقل 2 کاراکتر باشد.\n\n"
            "لطفاً نام خانوادگی خود را وارد کنید:"
        )
        return ENTERING_LAST_NAME
    
    user_data = context.user_data
    if user_data is not None:
        user_data['last_name'] = last_name
    
    # ثبت کاربر در دیتابیس (بدون کد ملی)
    try:
        # Create async wrapper - type checker can't infer wrapped function signature
        user_obj, profile, created = await sync_to_async(  # type: ignore[misc,call-arg]
            UserService.create_user_from_telegram,
            thread_sensitive=True
        )(
            telegram_id=user_data.get('telegram_id', ''),  # type: ignore[arg-type]
            phone_number=user_data.get('phone_number', ''),  # type: ignore[arg-type]
            telegram_username=user_data.get('telegram_username'),  # type: ignore[arg-type]
            first_name=user_data.get('first_name', ''),  # type: ignore[arg-type]
            last_name=last_name,  # type: ignore[arg-type]
            national_code=""  # type: ignore[arg-type]
        )
        
        if created:
            await update.message.reply_text(
                "✅ *ثبت‌نام شما با موفقیت انجام شد!*\n\n"
                f"👤 نام: {user_data.get('first_name', '') if user_data else ''} {last_name}\n"
                f"📱 شماره تماس: {user_data.get('phone_number', '') if user_data else ''}\n\n"
                "⏳ حساب شما در انتظار تایید مدیر است.\n"
                "پس از تایید، از منوی ربات استفاده کنید. 🙏",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "✅ *اطلاعات شما به‌روزرسانی شد!*\n\n"
                f"👤 نام: {user_data.get('first_name', '') if user_data else ''} {last_name}\n"
                f"📱 شماره تماس: {user_data.get('phone_number', '') if user_data else ''}\n\n"
                "از منوی ربات استفاده کنید. 🙏",
                parse_mode='Markdown',
                reply_markup=ReplyKeyboardRemove()
            )
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        await update.message.reply_text(
            "❌ خطا در ثبت‌نام. لطفاً دوباره تلاش کنید.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END


def get_registration_conversation_handler() -> ConversationHandler:
    """دریافت ConversationHandler برای ثبت نام"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.CONTACT, registration_start)
        ],
        states={
            ENTERING_FIRST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_first_name),
            ],
            ENTERING_LAST_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_last_name),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
        ],
        name="registration_conversation",
        persistent=False,
    )


# ==================== Helper Functions for Price Timeout ====================

async def expire_price_buttons(context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف خودکار دکمه‌های خرید/فروش پس از 60 ثانیه"""
    job = context.job
    if not job or not job.data:
        logger.warning("expire_price_buttons called but no job or job data found")
        return
    
    data = cast(dict[str, Any], job.data)
    
    try:
        # نمایش پیام با دکمه بروزرسانی فقط
        message = (
            f"{data['product_name']}\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(data['buy_price'])}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(data['sell_price'])}` ریال\n\n"
            f"⚠️ *زمان معامله منقضی شده است*\n"
            f"🔄 برای خرید/فروش، ابتدا قیمت را بروزرسانی کنید.\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(data['updated_at'])}_"
        )
        
        await context.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=message,
            reply_markup=get_product_detail_keyboard(data['product_code'], can_trade=True, is_expired=True),
            parse_mode='Markdown'
        )
    except telegram.error.BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"خطا در حذف خودکار دکمه‌ها: {e}")


async def expire_invoice_buttons(context: ContextTypes.DEFAULT_TYPE) -> None:
    """حذف خودکار دکمه‌های پیش‌فاکتور پس از 60 ثانیه"""
    job = context.job
    if not job or not job.data:
        logger.warning("expire_invoice_buttons called but no job or job data found")
        return
    
    data = cast(dict[str, Any], job.data)
    
    try:
        # حذف تمام دکمه‌های inline و نمایش پیام منقضی شده
        expired_message = (
            f"⏰ *زمان معامله به پایان رسید*\n\n"
            f"{data['invoice_text']}\n\n"
            f"❌ *این پیش‌فاکتور منقضی شده است*\n"
            f"قیمت‌ها ممکن است تغییر کرده باشند."
        )
        
        # حذف کامل inline keyboard
        await context.bot.edit_message_text(
            chat_id=data['chat_id'],
            message_id=data['message_id'],
            text=expired_message,
            parse_mode='Markdown',
            reply_markup=None  # حذف کامل دکمه‌ها
        )
        
        # ارسال منوی اصلی به صورت keyboard
        await context.bot.send_message(
            chat_id=data['chat_id'],
            text="💡 برای معامله جدید، قیمت‌های جدید را مشاهده کنید:",
            reply_markup=get_main_menu_keyboard()
        )
    except telegram.error.BadRequest as e:
        if "Message is not modified" not in str(e):
            logger.error(f"خطا در حذف خودکار دکمه‌های پیش‌فاکتور: {e}")
    except Exception as e:
        logger.error(f"خطا در expire_invoice_buttons: {e}")


def is_price_expired(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> bool:
    """بررسی اینکه آیا قیمت منقضی شده است (بیش از 1 دقیقه)"""
    if context.user_data is None:
        return True
    
    price_timestamp_key = f'price_timestamp_{product_code}'
    timestamp = context.user_data.get(price_timestamp_key)
    
    if not timestamp:
        return True
    
    elapsed = datetime.now() - timestamp
    return elapsed > timedelta(minutes=1)


def set_price_timestamp(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """ذخیره timestamp نمایش قیمت"""
    if context.user_data is None:
        return
    
    price_timestamp_key = f'price_timestamp_{product_code}'
    context.user_data[price_timestamp_key] = datetime.now()


def get_time_remaining(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> str:
    """دریافت زمان باقیمانده تا انقضای قیمت"""
    if context.user_data is None:
        return "منقضی شده"
    
    price_timestamp_key = f'price_timestamp_{product_code}'
    timestamp = context.user_data.get(price_timestamp_key)
    
    if not timestamp:
        return "منقضی شده"
    
    elapsed = datetime.now() - timestamp
    remaining = timedelta(minutes=1) - elapsed
    
    if remaining.total_seconds() <= 0:
        return "منقضی شده"
    
    seconds = int(remaining.total_seconds())
    return f"{seconds} ثانیه"


def generate_invoice_number(user_id: int) -> str:
    """تولید شماره فاکتور یونیک"""
    timestamp = int(time.time() * 1000)  # milliseconds
    data = f"{user_id}_{timestamp}"
    hash_value = hashlib.md5(data.encode()).hexdigest()[:8].upper()
    return f"INV-{hash_value}"


# ==================== Price Display Handlers ====================

async def show_prices_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش منوی قیمت‌ها"""
    if not update.effective_user or not update.message:
        logger.warning("show_prices_menu called but no effective_user or message found")
        return
    
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    await update.message.reply_text(
        "📊 *قیمت‌های لحظه‌ای*\n\n"
        "لطفاً محصول مورد نظر را انتخاب کنید:",
        reply_markup=get_prices_menu_keyboard(),
        parse_mode='Markdown'
    )


async def show_price_gold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت طلای آبشده"""
    query = update.callback_query
    if not query:
        logger.warning("show_price_gold called but no callback_query found")
        return
    
    await query.answer()
    
    try:
        get_product_async = sync_to_async(Product.get_by_code)
        product = await get_product_async(Product.PRODUCT_CODE_GOLD)
        
        # ثبت timestamp برای تایم‌اوت 1 دقیقه
        set_price_timestamp(context, PRODUCT_GOLD)
        
        # محاسبه زمان باقیمانده
        time_remaining = get_time_remaining(context, PRODUCT_GOLD)
        is_expired = is_price_expired(context, PRODUCT_GOLD)
        
        if is_expired:
            warning = "\n\n⚠️ *زمان معامله منقضی شده است*\n🔄 برای خرید/فروش، ابتدا قیمت را بروزرسانی کنید."
        else:
            warning = f"\n\n💡 *توجه:* شما {time_remaining} برای معامله با این قیمت فرصت دارید."
        
        message = (
            "🪙 *طلای آبشده (هر گرم)*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(cast(Decimal, product.buy_price))}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(cast(Decimal, product.sell_price))}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(cast(datetime, product.updated_at))}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_GOLD, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired and context.job_queue and isinstance(query.message, Message):
            context.job_queue.run_once(
                expire_price_buttons,
                60,
                data={
                    'chat_id': query.message.chat_id,
                    'message_id': query.message.message_id,
                    'product_code': PRODUCT_GOLD,
                    'product_name': '🪙 طلای آبشده (هر گرم)',
                    'buy_price': product.buy_price,
                    'sell_price': product.sell_price,
                    'updated_at': product.updated_at
                },
                name=f'expire_price_{query.message.chat_id}_{query.message.message_id}'
            )
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")


async def show_price_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت سکه"""
    query = update.callback_query
    if not query:
        logger.warning("show_price_coin called but no callback_query found")
        return
    
    await query.answer()
    
    try:
        get_product_async = sync_to_async(Product.get_by_code)
        product = await get_product_async(Product.PRODUCT_CODE_COIN)
        
        # ثبت timestamp برای تایم‌اوت 1 دقیقه
        set_price_timestamp(context, PRODUCT_COIN)
        
        # محاسبه زمان باقیمانده
        time_remaining = get_time_remaining(context, PRODUCT_COIN)
        is_expired = is_price_expired(context, PRODUCT_COIN)
        
        if is_expired:
            warning = "\n\n⚠️ *زمان معامله منقضی شده است*\n🔄 برای خرید/فروش، ابتدا قیمت را بروزرسانی کنید."
        else:
            warning = f"\n\n💡 *توجه:* شما {time_remaining} برای معامله با این قیمت فرصت دارید."
        
        message = (
            "🥇 *سکه تمام غیربانکی*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(cast(Decimal, product.buy_price))}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(cast(Decimal, product.sell_price))}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(cast(datetime, product.updated_at))}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_COIN, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired and context.job_queue and isinstance(query.message, Message):
            context.job_queue.run_once(
                expire_price_buttons,
                60,
                data={
                    'chat_id': query.message.chat_id,
                    'message_id': query.message.message_id,
                    'product_code': PRODUCT_COIN,
                    'product_name': '🥇 سکه تمام غیربانکی',
                    'buy_price': product.buy_price,
                    'sell_price': product.sell_price,
                    'updated_at': product.updated_at
                },
                name=f'expire_price_{query.message.chat_id}_{query.message.message_id}'
            )
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")


async def show_price_dollar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت دلار"""
    query = update.callback_query
    if not query:
        logger.warning("show_price_dollar called but no callback_query found")
        return
    
    await query.answer()
    
    try:
        get_product_async = sync_to_async(Product.get_by_code)
        product = await get_product_async(Product.PRODUCT_CODE_DOLLAR)
        
        # ثبت timestamp برای تایم‌اوت 1 دقیقه
        set_price_timestamp(context, PRODUCT_DOLLAR)
        
        # محاسبه زمان باقیمانده
        time_remaining = get_time_remaining(context, PRODUCT_DOLLAR)
        is_expired = is_price_expired(context, PRODUCT_DOLLAR)
        
        if is_expired:
            warning = "\n\n⚠️ *زمان معامله منقضی شده است*\n🔄 برای خرید/فروش، ابتدا قیمت را بروزرسانی کنید."
        else:
            warning = f"\n\n💡 *توجه:* شما {time_remaining} برای معامله با این قیمت فرصت دارید."
        
        message = (
            "💵 *دلار آمریکا*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(cast(Decimal, product.buy_price))}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(cast(Decimal, product.sell_price))}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(cast(datetime, product.updated_at))}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_DOLLAR, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired and context.job_queue and isinstance(query.message, Message):
            context.job_queue.run_once(
                expire_price_buttons,
                60,
                data={
                    'chat_id': query.message.chat_id,
                    'message_id': query.message.message_id,
                    'product_code': PRODUCT_DOLLAR,
                    'product_name': '💵 دلار آمریکا',
                    'buy_price': product.buy_price,
                    'sell_price': product.sell_price,
                    'updated_at': product.updated_at
                },
                name=f'expire_price_{query.message.chat_id}_{query.message.message_id}'
            )
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")


async def show_all_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش تمام قیمت‌ها"""
    query = update.callback_query
    if not query:
        logger.warning("show_all_prices called but no callback_query found")
        return
    
    await query.answer()
    
    get_products_async = sync_to_async(TradingService.get_active_products)
    products = await get_products_async()
    
    if not products:
        await query.edit_message_text("❌ هیچ محصولی فعال نیست.")
        return
    
    message = "📊 *قیمت‌های لحظه‌ای*\n\n"
    
    # نمایش هر محصول
    for product in products:
        if product.product_code == Product.PRODUCT_CODE_GOLD:
            emoji = "🪙"
        elif product.product_code == Product.PRODUCT_CODE_COIN:
            emoji = "🥇"
        elif product.product_code == Product.PRODUCT_CODE_DOLLAR:
            emoji = "💵"
        else:
            emoji = "🔸"
        
        message += f"{emoji} *{product.name}*\n"
        message += f"   💰 خرید: `{format_number(cast(Decimal, product.buy_price))}` ریال\n"
        message += f"   💵 فروش: `{format_number(cast(Decimal, product.sell_price))}` ریال\n\n"
    
    message += f"─────────────────\n"
    message += f"_به‌روزرسانی: {format_datetime(cast(datetime, products[0].updated_at))}_"
    
    # کیبورد با فقط دکمه بازگشت
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 بازگشت به منوی قیمت‌ها", callback_data="back_to_prices_menu")]
    ])
    
    await safe_edit_message_text(
        query,
        message,
        reply_markup=back_keyboard,
        parse_mode='Markdown'
    )


async def back_to_prices_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بازگشت به منوی قیمت‌ها"""
    query = update.callback_query
    if not query:
        logger.warning("back_to_prices_menu called but no callback_query found")
        return
    
    await query.answer()
    
    await query.edit_message_text(
        "📊 *قیمت‌های لحظه‌ای*\n\n"
        "لطفاً محصول مورد نظر را انتخاب کنید:",
        reply_markup=get_prices_menu_keyboard(),
        parse_mode='Markdown'
    )


async def refresh_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بروزرسانی قیمت و ریست تایمر"""
    query = update.callback_query
    if not query or not query.data:
        logger.warning("refresh_price called but no callback_query or data found")
        return
    
    await query.answer("🔄 در حال بروزرسانی...")
    
    # استخراج product_code از callback
    callback_data = query.data
    product_code = callback_data.replace(CALLBACK_PRICE_REFRESH, "")
    
    # بررسی معتبر بودن product_code
    if product_code not in [PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR]:
        await query.edit_message_text("❌ محصول نامعتبر.")
        return
    
    try:
        # بروزرسانی قیمت‌ها از API
        await sync_to_async(TradingService.update_all_prices, thread_sensitive=True)()  # type: ignore[misc]
        
        # دریافت قیمت جدید
        get_product_async = sync_to_async(Product.get_by_code)
        product = await get_product_async(product_code)
        
        # ریست timestamp
        set_price_timestamp(context, product_code)
        
        # نمایش قیمت بروز شده
        time_remaining = get_time_remaining(context, product_code)
        is_expired = is_price_expired(context, product_code)
        
        # ایموجی بر اساس نوع محصول
        if product_code == PRODUCT_GOLD:
            emoji = "🪙"
            name = "طلای آبشده (هر گرم)"
        elif product_code == PRODUCT_COIN:
            emoji = "🥇"
            name = "سکه تمام غیربانکی"
        elif product_code == PRODUCT_DOLLAR:
            emoji = "💵"
            name = "دلار آمریکا"
        else:
            emoji = "🔸"
            name = product.name
        
        message = (
            f"{emoji} *{name}*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(cast(Decimal, product.buy_price))}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(cast(Decimal, product.sell_price))}` ریال\n\n"
            f"⏱ *زمان باقیمانده:* {time_remaining}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(cast(datetime, product.updated_at))}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(product_code, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"خطا در بروزرسانی قیمت: {e}")
        await query.edit_message_text("❌ خطا در بروزرسانی قیمت. لطفاً دوباره تلاش کنید.")


# ==================== Portfolio & History ====================

async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش پورتفولیو و آمار کلی"""
    if not update.effective_user or not update.message:
        logger.warning("show_portfolio called but no effective_user or message found")
        return
    
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Get user's order statistics
    orders = await sync_to_async(list)(profile.orders.all())
    
    total_orders = len(orders)
    completed_orders = len([o for o in orders if o.status == 'COMPLETED'])
    pending_orders = len([o for o in orders if o.status == 'PENDING'])
    
    message = (
        "📊 *پورتفولیو و آمار شما*\n\n"
        f"👤 *اطلاعات کاربری:*\n"
        f"   📱 شماره تماس: {profile.phone_number}\n"
        f"   ✅ وضعیت: {'تایید شده' if profile.is_approved else 'در انتظار تایید'}\n\n"
        f"📈 *آمار معاملات:*\n"
        f"   📋 کل سفارشات: {total_orders}\n"
        f"   ✅ تکمیل شده: {completed_orders}\n"
        f"   ⏳ در انتظار: {pending_orders}\n\n"
        f"💰 *موجودی کلی:*\n"
        f"   💵 ریال: {format_number(Decimal(str(profile.rial_balance)))} ریال\n"
        f"   🪙 طلا: {format_number(Decimal(str(profile.gold_balance_grams)), 4)} گرم\n"
        f"   🥇 سکه: {format_number(Decimal(str(profile.coin_balance)))} عدد\n"
        f"   💵 دلار: {format_number(Decimal(str(profile.dollar_balance)))} دلار\n\n"
        f"📅 عضویت از: {profile.created_at.strftime('%Y/%m/%d')}"
    )
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def show_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش کیف پول با جزئیات کامل"""
    if not update.effective_user or not update.message:
        logger.warning("show_wallet called but no effective_user or message found")
        return
    
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Use the WalletService to format the wallet display
    wallet_text = WalletService.format_wallet_display(profile)
    
    await update.message.reply_text(
        wallet_text, 
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def show_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش حساب‌های بانکی کاربر"""
    if not update.effective_user or not update.message:
        logger.warning("show_account called but no effective_user or message found")
        return
    
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    # Get user's bank accounts
    bank_accounts = await sync_to_async(list)(profile.bank_accounts.all())
    
    if not bank_accounts:
        message = (
            "🏦 *حساب‌های بانکی*\n\n"
            "شما هنوز هیچ حساب بانکی ثبت نکرده‌اید.\n\n"
            "برای واریز و برداشت، ابتدا باید حساب بانکی خود را ثبت کنید.\n\n"
            "لطفاً با پشتیبانی تماس بگیرید تا راهنمایی لازم را دریافت کنید."
        )
    else:
        message = "🏦 *حساب‌های بانکی شما:*\n\n"
        
        for i, account in enumerate(bank_accounts, 1):
            status_icon = "✅" if account.is_verified else "⏳"
            status_text = "تایید شده" if account.is_verified else "در انتظار تایید"
            
            message += f"{i}. {status_icon} *{account.bank_name}*\n"
            message += f"   📋 صاحب حساب: {account.account_holder_name}\n"
            message += f"   💳 شماره: {account.account_number}\n"
            message += f"   📝 نوع: {account.account_type}\n"
            message += f"   🔍 وضعیت: {status_text}\n\n"
        
        message += f"📅 آخرین بروزرسانی: {profile.updated_at.strftime('%Y/%m/%d - %H:%M')}"
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش تاریخچه"""
    if not update.effective_user or not update.message:
        logger.warning("show_history called but no effective_user or message found")
        return
    
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    get_orders_async = sync_to_async(TradingService.get_user_recent_orders)
    orders = await get_orders_async(profile, limit=5)
    
    if not orders:
        await update.message.reply_text(
            "📋 شما هنوز هیچ سفارشی ثبت نکرده‌اید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    message = "📋 *تاریخچه ۵ سفارش آخر*\n\n"
    
    for order in orders:
        status_emoji: dict[str, str] = {
            Order.OrderStatus.PENDING.value: "⏳",
            Order.OrderStatus.COMPLETED.value: "✅",
            Order.OrderStatus.CANCELLED.value: "❌"
        }
        
        type_emoji = "🟢" if order.order_type == Order.OrderType.BUY else "🔴"
        
        message += f"{type_emoji} *سفارش #{order.id}*\n"  # type: ignore[attr-defined]
        message += f"   {order.order_type} | {order.product.name}\n"
        message += f"   مقدار: {format_number(order.quantity_grams, 4)} گرم\n"
        message += f"   مبلغ: {format_number(order.total_amount)} ریال\n"
        message += f"   {status_emoji.get(str(order.status), '❓')} {order.status}\n\n"
    
    await update.message.reply_text(
        message, 
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


# ==================== Trade Conversation ====================
# معاملات مستقیماً از دکمه‌های خرید/فروش در بخش قیمت‌ها انجام می‌شوند


async def trade_action_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """خرید یا فروش انتخاب شد"""
    query = update.callback_query
    if not query or not query.data:
        logger.warning("trade_action_selected called but no callback_query or data found")
        return ConversationHandler.END
    
    if not update.effective_user:
        logger.warning("trade_action_selected called but no effective_user found")
        return ConversationHandler.END
    
    callback_data = query.data
    logger.info(f"Action callback: {callback_data}")
    
    # استخراج product_code و action از callback
    # فرمت: trade_gold_action_buy یا trade_coin_action_sell
    # حذف پیشوند trade_
    data_without_prefix = callback_data.replace(CALLBACK_TRADE_PRODUCT_PREFIX, "")
    
    # استخراج action و product_code
    if CALLBACK_ACTION_BUY in data_without_prefix:
        product_code = data_without_prefix.replace(f"_{CALLBACK_ACTION_BUY}", "")
    elif CALLBACK_ACTION_SELL in data_without_prefix:
        product_code = data_without_prefix.replace(f"_{CALLBACK_ACTION_SELL}", "")
    else:
        await query.edit_message_text("❌ عملیات نامعتبر.")
        return ConversationHandler.END
    
    # اگر profile ذخیره نشده باشد، از دیتابیس دریافت کن
    if context.user_data is None or not context.user_data.get('profile'):
        telegram_id = str(update.effective_user.id)
        is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
        if not profile or not is_approved:
            await query.answer("❌ شما مجاز به استفاده از این بخش نیستید.", show_alert=True)
            return ConversationHandler.END
        if context.user_data is None:
            context.user_data = {}
        context.user_data['profile'] = profile
    
    # بررسی انقضای قیمت
    if is_price_expired(context, product_code):
        await query.answer("⏰ قیمت منقضی شده است. لطفاً ابتدا قیمت را بروزرسانی کنید.", show_alert=True)
        return ConversationHandler.END
    
    # تعیین نوع عملیات
    if CALLBACK_ACTION_BUY in callback_data:
        action = "buy"
        action_text = "خرید"
    elif CALLBACK_ACTION_SELL in callback_data:
        action = "sell"
        action_text = "فروش"
    else:
        await query.edit_message_text("❌ عملیات نامعتبر.")
        return ConversationHandler.END
    
    await query.answer()
    
    # اگر محصول ذخیره نشده باشد، دریافت کن
    if context.user_data is None or not context.user_data.get('product'):
        try:
            get_product_async = sync_to_async(Product.get_by_code)
            product = await get_product_async(product_code)
            if context.user_data is None:
                context.user_data = {}
            context.user_data['product'] = product
            context.user_data['product_code'] = product_code
        except Product.DoesNotExist:
            await query.edit_message_text("❌ خطا: محصول یافت نشد.")
            return ConversationHandler.END
    
    if context.user_data is None:
        context.user_data = {}
    
    context.user_data['action'] = action
    product = context.user_data.get('product')
    
    if not product:
        await query.edit_message_text("❌ خطا: محصول یافت نشد.")
        return ConversationHandler.END
    
    # بررسی موجودی برای فروش
    if action == "sell":
        profile = context.user_data.get('profile')
        if profile and profile.gold_balance_grams == 0:
            await query.edit_message_text(
                "❌ موجودی طلای شما صفر است.\n"
                "ابتدا باید طلا خریداری کنید."
            )
            return ConversationHandler.END
    
    # محاسبه زمان باقیمانده
    time_remaining = get_time_remaining(context, product_code)
    
    # برای سکه و دلار، مستقیم به وارد کردن تعداد می‌رویم
    if product_code in [PRODUCT_COIN, PRODUCT_DOLLAR]:
        context.user_data['amount_type'] = 'grams'  # برای سکه و دلار فقط تعداد
        
        unit = "عدد"
        if product_code == PRODUCT_COIN:
            examples = (
                f"💡 *راهنما:*\n"
                f"• برای یک سکه: `1`\n"
                f"• برای دو سکه: `2`\n"
                f"• برای ده سکه: `10`\n\n"
                f"⚠️ *توجه:* فقط اعداد صحیح مثبت مجاز است."
            )
        else:  # PRODUCT_DOLLAR
            examples = (
                f"💡 *راهنما:*\n"
                f"• برای ده دلار: `10`\n"
                f"• برای صد دلار: `100`\n"
                f"• برای هزار دلار: `1000`\n\n"
                f"⚠️ *توجه:* فقط اعداد صحیح مثبت مجاز است."
            )
        
        prompt = (
            f"💎 {action_text} *{product.name}*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n\n"
            f"📝 لطفاً تعداد را وارد کنید:\n\n"
            f"{examples}"
        )
        
        # حذف پیام قبلی
        await query.delete_message()
        
        # ارسال پیام جدید با ForceReply برای باز کردن کیبورد تایپ
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                prompt,
                parse_mode='Markdown',
                reply_markup=ForceReply(
                    input_field_placeholder="تعداد مورد نظر را وارد کنید...",
                    selective=True
                )
            )
        
        return ENTERING_AMOUNT
    
    # برای طلای آبشده، انتخاب روش محاسبه نمایش داده می‌شود
    await query.edit_message_text(
        f"💎 {action_text} *{product.name}*\n\n"
        f"⏱ *زمان باقیمانده:* {time_remaining}\n\n"
        "⚠️ *توجه:* شما یک دقیقه برای تکمیل معامله فرصت دارید.\n"
        "پس از آن باید قیمت را بروزرسانی کنید.\n\n"
        "مقدار را بر اساس چه واحدی وارد می‌کنید؟",
        reply_markup=get_amount_method_keyboard(product_code),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def trade_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """روش محاسبه انتخاب شد"""
    query = update.callback_query
    if not query or not query.data:
        logger.warning("trade_method_selected called but no callback_query or data found")
        return ConversationHandler.END
    
    # بررسی وجود user_data
    if context.user_data is None:
        logger.warning("trade_method_selected called but user_data is None")
        await query.answer("❌ خطا: اطلاعات جلسه یافت نشد.", show_alert=True)
        return ConversationHandler.END
    
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    if not product_code or is_price_expired(context, product_code):
        await query.answer("⏰ زمان شما به پایان رسید. لطفاً قیمت را بروزرسانی کنید.", show_alert=True)
        
        try:
            await query.edit_message_text(
                "⏰ *زمان معامله به پایان رسید*\n\n"
                "قیمت‌ها ممکن است تغییر کرده باشند.\n"
                "💡 لطفاً از منوی اصلی استفاده کنید:",
                parse_mode='Markdown'
            )
        except:
            pass
        
        # نمایش منوی اصلی
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "📱 از منوی اصلی می‌توانید استفاده کنید:",
                reply_markup=get_main_menu_keyboard()
            )
        if context.user_data is not None:
            context.user_data.clear()
        return ConversationHandler.END
    
    await query.answer()
    
    method = "grams" if query.data == CALLBACK_METHOD_GRAM else "rial"
    context.user_data['amount_type'] = method
    
    product = context.user_data.get('product')
    action = context.user_data.get('action')
    action_text = "خرید" if action == "buy" else "فروش"
    
    # محاسبه زمان باقیمانده
    time_remaining = get_time_remaining(context, product_code)
    
    if method == "gram":
        # تعیین واحد بر اساس نوع محصول
        if product and product.product_code == Product.PRODUCT_CODE_GOLD:
            unit = "گرم"
            examples = (
                f"💡 *راهنما:*\n"
                f"• برای نیم گرم: `0.5`\n"
                f"• برای دو و نیم گرم: `2.5`\n"
                f"• برای ده گرم: `10`"
            )
        elif product and product.product_code == Product.PRODUCT_CODE_COIN:
            unit = "عدد"
            examples = (
                f"💡 *راهنما:*\n"
                f"• برای یک سکه: `1`\n"
                f"• برای دو سکه: `2`\n"
                f"• برای ده سکه: `10`"
            )
        elif product and product.product_code == Product.PRODUCT_CODE_DOLLAR:
            unit = "عدد"
            examples = (
                f"💡 *راهنما:*\n"
                f"• برای ده دلار: `10`\n"
                f"• برای صد دلار: `100`\n"
                f"• برای هزار دلار: `1000`"
            )
        else:
            unit = "واحد"
            examples = f"💡 *راهنما:* مقدار مورد نظر را وارد کنید"
        
        product_name = product.name if product else "محصول"
        prompt = (
            f"💎 {action_text} *{product_name}*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n\n"
            f"📝 لطفاً مقدار را به *{unit}* وارد کنید:\n\n"
            f"{examples}"
        )
    else:
        product_name = product.name if product else "محصول"
        prompt = (
            f"💎 {action_text} *{product_name}*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n\n"
            f"💰 لطفاً مبلغ را به *ریال* وارد کنید:\n\n"
            f"💡 *راهنما:*\n"
            f"• یک میلیون: `1000000`\n"
            f"• پنج میلیون: `5000000`\n"
            f"• ده میلیون: `10000000`"
        )
    
    # حذف پیام قبلی
    await query.delete_message()
    
    # ارسال پیام جدید با ForceReply برای باز کردن کیبورد تایپ
    if query.message and isinstance(query.message, Message):
        await query.message.reply_text(
            prompt,
            parse_mode='Markdown',
            reply_markup=ForceReply(
                input_field_placeholder="عدد مورد نظر را وارد کنید...",
                selective=True
            )
        )
    
    return ENTERING_AMOUNT


async def trade_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مقدار وارد شد"""
    if not update.message or not update.message.text:
        logger.warning("trade_amount_entered called but no message or text found")
        return ConversationHandler.END
    
    if not update.effective_user:
        logger.warning("trade_amount_entered called but no effective_user found")
        return ConversationHandler.END
    
    # بررسی وجود user_data
    if context.user_data is None:
        logger.error("trade_amount_entered: user_data is None")
        await update.message.reply_text(
            "❌ خطا: اطلاعات جلسه یافت نشد.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    product = context.user_data.get('product')
    
    if not product_code or is_price_expired(context, product_code):
        await update.message.reply_text(
            "⏰ *زمان معامله به پایان رسید*\n\n"
            "قیمت‌ها ممکن است تغییر کرده باشند.\n"
            "💡 لطفاً از منوی اصلی استفاده کنید:",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    amount = parse_decimal(update.message.text)
    
    # برای سکه و دلار، بررسی کن که عدد صحیح مثبت باشد
    product_name = product.name if product else "محصول"
    if product_code in [PRODUCT_COIN, PRODUCT_DOLLAR]:
        if amount is None or amount <= 0:
            time_remaining = get_time_remaining(context, product_code)
            await update.message.reply_text(
                f"❌ *مقدار نامعتبر است*\n\n"
                f"⏱ زمان باقیمانده: {time_remaining}\n\n"
                f"⚠️ برای {product_name} فقط اعداد صحیح مثبت مجاز است.\n\n"
                f"💡 *مثال‌ها:*\n"
                f"• `1` (یک {product_name})\n"
                f"• `5` (پنج {product_name})\n"
                f"• `10` (ده {product_name})",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            return ENTERING_AMOUNT
        
        # بررسی که عدد صحیح باشد
        if amount != int(amount):
            time_remaining = get_time_remaining(context, product_code)
            await update.message.reply_text(
                f"❌ *مقدار باید عدد صحیح باشد*\n\n"
                f"⏱ زمان باقیمانده: {time_remaining}\n\n"
                f"⚠️ برای {product_name} فقط اعداد صحیح مثبت مجاز است.\n\n"
                f"❌ غیرمجاز: `2.5` یا `3.7`\n"
                f"✅ مجاز: `1` یا `5` یا `10`",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            return ENTERING_AMOUNT
    
    if amount is None:
        time_remaining = get_time_remaining(context, product_code)
        await update.message.reply_text(
            f"❌ *مقدار نامعتبر است*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n\n"
            f"لطفاً یک عدد معتبر وارد کنید.\n\n"
            f"💡 *مثال‌ها:*\n"
            f"• `2.5` (دو و نیم)\n"
            f"• `10` (ده)\n"
            f"• `5000000` (پنج میلیون)",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return ENTERING_AMOUNT
    
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        time_remaining = get_time_remaining(context, product_code)
        await update.message.reply_text(
            f"{error_msg}\n\n⏱ زمان باقیمانده: {time_remaining}",
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        return ENTERING_AMOUNT
    
    product = context.user_data['product']
    amount_type = context.user_data['amount_type']
    action = context.user_data['action']
    profile = context.user_data['profile']
    
    # محاسبه جزئیات
    try:
        if action == "buy":
            quantity_grams, price_per_gram, total_amount = TradingService.calculate_buy_details(
                product, amount_type, amount
            )
            price = product.sell_price
            action_text = "خرید"
            
            # بررسی موجودی ریالی برای خرید
            if total_amount > profile.rial_balance:
                await update.message.reply_text(
                    f"❌ موجودی ریالی شما کافی نیست.\n\n"
                    f"💰 موجودی شما: {format_number(profile.rial_balance)} ریال\n"
                    f"💸 مبلغ مورد نیاز: {format_number(total_amount)} ریال\n"
                    f"📉 کمبود: {format_number(total_amount - profile.rial_balance)} ریال\n\n"
                    f"💡 برای افزایش موجودی، از بخش کیف پول استفاده کنید.",
                    reply_markup=get_main_menu_keyboard()
                )
                context.user_data.clear()
                return ConversationHandler.END
        else:
            quantity_grams, price_per_gram, total_amount = TradingService.calculate_sell_details(
                product, amount_type, amount
            )
            price = product.buy_price
            action_text = "فروش"
            
            # بررسی موجودی بر اساس نوع محصول
            if product_code == PRODUCT_GOLD:
                if quantity_grams > profile.gold_balance_grams:
                    await update.message.reply_text(
                        f"❌ موجودی طلای شما کافی نیست.\n\n"
                        f"موجودی شما: {format_number(profile.gold_balance_grams, 4)} گرم\n"
                        f"مقدار درخواستی: {format_number(quantity_grams, 4)} گرم"
                    )
                    return ENTERING_AMOUNT
            elif product_code == PRODUCT_COIN:
                if amount > profile.coin_balance:
                    await update.message.reply_text(
                        f"❌ موجودی سکه شما کافی نیست.\n\n"
                        f"موجودی شما: {format_number(profile.coin_balance, 4)} سکه\n"
                        f"مقدار درخواستی: {format_number(amount, 4)} سکه"
                    )
                    return ENTERING_AMOUNT
            elif product_code == PRODUCT_DOLLAR:
                if amount > profile.dollar_balance:
                    await update.message.reply_text(
                        f"❌ موجودی دلار شما کافی نیست.\n\n"
                        f"موجودی شما: {format_number(profile.dollar_balance, 2)} دلار\n"
                        f"مقدار درخواستی: {format_number(amount, 2)} دلار"
                    )
                    return ENTERING_AMOUNT
        
        context.user_data['quantity_grams'] = quantity_grams
        context.user_data['total_amount'] = total_amount
        
        # تولید شماره فاکتور
        invoice_number = generate_invoice_number(update.effective_user.id)
        context.user_data['invoice_number'] = invoice_number
        
        # محاسبه زمان باقیمانده
        time_remaining = get_time_remaining(context, product_code)
        
        # دریافت نام کامل کاربر از دیتابیس
        full_name = "کاربر"
        if profile and profile.user:
            full_name = profile.user.get_full_name() or "کاربر"
        
        # تاریخ و زمان فعلی
        now = datetime.now()
        persian_date = now.strftime("%Y/%m/%d")
        persian_time = now.strftime("%H:%M:%S")
        
        # دریافت کدملی (فیلد حذف شده است)
        national_code = "ثبت نشده"
        
        # نمایش پیش‌فاکتور
        invoice = (
            f"🧾 *پیش‌فاکتور {action_text}*\n\n"
            f"📋 شماره فاکتور: `{invoice_number}`\n"
            f"👤 نام مشتری: *{full_name}*\n"
            f"🪪 کد ملی: `{national_code}`\n"
            f"📅 تاریخ: {persian_date}\n"
            f"🕐 ساعت: {persian_time}\n"
            f"─────────────────\n"
            f"📦 محصول: *{product_name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams if quantity_grams else Decimal('0'), 4)}* گرم\n"
            f"💵 قیمت واحد: *{format_number(price)}* ریال\n"
            f"💰 *مبلغ کل: {format_number(total_amount if total_amount else Decimal('0'))} ریال*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n"
            "─────────────────\n"
            "⚠️ لطفاً سریع تصمیم بگیرید!\n"
            "آیا این سفارش را تایید می‌کنید؟"
        )
        
        sent_message = await update.message.reply_text(
            invoice,
            reply_markup=get_confirmation_keyboard(),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌های پیش‌فاکتور پس از 60 ثانیه
        if context.job_queue:
            context.job_queue.run_once(
                expire_invoice_buttons,
                60,
                data={
                    'chat_id': sent_message.chat_id,
                    'message_id': sent_message.message_id,
                    'invoice_text': invoice
                },
                name=f'expire_invoice_{sent_message.chat_id}_{sent_message.message_id}'
            )
        
        return CONFIRMING_TRADE
    
    except Exception as e:
        logger.error(f"Error in calculation: {e}", exc_info=True)
        logger.error(f"Product: {product}, Amount: {amount}, Amount Type: {amount_type}, Action: {action}")
        await update.message.reply_text("❌ خطا در محاسبه. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END


async def trade_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تایید نهایی"""
    query = update.callback_query
    if not query or not query.message:
        logger.warning("trade_confirmed called but no callback_query or message found")
        return ConversationHandler.END
    
    # بررسی وجود user_data
    if context.user_data is None:
        logger.error("trade_confirmed: user_data is None")
        await query.answer("❌ خطا: اطلاعات جلسه یافت نشد.", show_alert=True)
        return ConversationHandler.END
    
    # لغو Job انقضای پیش‌فاکتور (اگر وجود دارد)
    if context.job_queue and isinstance(query.message, Message):
        job_name = f'expire_invoice_{query.message.chat_id}_{query.message.message_id}'
        current_jobs = context.job_queue.get_jobs_by_name(job_name)
        for job in current_jobs:
            job.schedule_removal()
    
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    if not product_code or is_price_expired(context, product_code):
        await query.answer("⏰ زمان شما به پایان رسید!", show_alert=True)
        
        # دریافت اطلاعات برای نمایش پیش‌فاکتور منقضی شده
        profile = context.user_data.get('profile')
        product = context.user_data.get('product')
        invoice_number = context.user_data.get('invoice_number', 'N/A')
        
        full_name = "کاربر"
        if profile:
            full_name = profile.user.get_full_name()
            if not full_name:
                full_name = "کاربر"
        
        now = datetime.now()
        persian_date = now.strftime("%Y/%m/%d")
        persian_time = now.strftime("%H:%M:%S")
        
        expired_invoice = (
            f"⏰ *قیمت تغییر کرده است*\n\n"
            f"📋 شماره فاکتور: `{invoice_number}`\n"
            f"👤 نام مشتری: *{full_name}*\n"
            f"📅 تاریخ: {persian_date}\n"
            f"🕐 ساعت: {persian_time}\n"
            f"─────────────────\n"
            f"❌ *این فاکتور منقضی شده است*\n\n"
            f"⚠️ زمان معامله به پایان رسید.\n"
            f"قیمت‌ها ممکن است تغییر کرده باشند.\n\n"
            f"برای ادامه، لطفاً به بخش قیمت‌ها بروید\n"
            f"و قیمت را بروزرسانی کنید."
        )
        
        # دکمه انصراف و قیمت‌ها را نمایش بده (بدون دکمه تایید)
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 مشاهده قیمت‌ها", callback_data=CALLBACK_PRICE_ALL)],
            [InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data=CALLBACK_CONFIRM_NO)]
        ])
        
        await query.edit_message_text(
            expired_invoice,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.answer()
    
    profile = context.user_data.get('profile')
    product = context.user_data.get('product')
    quantity_grams = context.user_data.get('quantity_grams')
    total_amount = context.user_data.get('total_amount')
    action = context.user_data.get('action')
    
    if not all([profile, product, quantity_grams, total_amount, action]):
        await query.edit_message_text("❌ خطا: اطلاعات ناقص است.")
        if context.user_data is not None:
            context.user_data.clear()
        return ConversationHandler.END
    
    try:
        invoice_number = context.user_data.get('invoice_number')
        
        if action == "buy":
            order = await sync_to_async(TradingService.create_buy_order, thread_sensitive=True)(  # type: ignore[misc,call-arg]
                profile=profile,  # type: ignore[arg-type]
                product=product,  # type: ignore[arg-type]
                quantity_grams=quantity_grams,  # type: ignore[arg-type]
                total_amount=total_amount  # type: ignore[arg-type]
            )
            action_text = "خرید"
        else:
            order = await sync_to_async(TradingService.create_sell_order, thread_sensitive=True)(  # type: ignore[misc,call-arg]
                profile=profile,  # type: ignore[arg-type]
                product=product,  # type: ignore[arg-type]
                quantity_grams=quantity_grams,  # type: ignore[arg-type]
                total_amount=total_amount  # type: ignore[arg-type]
            )
            action_text = "فروش"
        
        # دریافت اطلاعات برای فاکتور نهایی
        invoice_number = context.user_data.get('invoice_number', 'N/A')
        full_name = "کاربر"
        if profile and profile.user:
            full_name = profile.user.get_full_name() or "کاربر"
        
        # دریافت کدملی (فیلد حذف شده است)
        national_code = "ثبت نشده"
        
        # دریافت نام محصول
        product_name = product.name if product else "محصول"
        
        now = datetime.now()
        persian_date = now.strftime("%Y/%m/%d")
        persian_time = now.strftime("%H:%M:%S")
        
        await query.edit_message_text(
            f"✅ *سفارش {action_text} با موفقیت ثبت شد!*\n\n"
            f"📋 شماره فاکتور: `{invoice_number}`\n"
            f"🆔 شماره سفارش: *{order.id}*\n"  # type: ignore[attr-defined]
            f"👤 نام مشتری: *{full_name}*\n"
            f"🪪 کد ملی: `{national_code}`\n"
            f"📅 تاریخ: {persian_date}\n"
            f"🕐 ساعت: {persian_time}\n"
            f"─────────────────\n"
            f"📦 محصول: *{product_name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams if quantity_grams else Decimal('0'), 4)}* گرم\n"
            f"💰 مبلغ: *{format_number(total_amount if total_amount else Decimal('0'))}* ریال\n\n"
            f"⏳ *وضعیت:* در انتظار تایید مدیر\n"
            f"پس از تایید، موجودی شما به‌روزرسانی خواهد شد.",
            parse_mode='Markdown'
        )
        
        # نمایش منوی اصلی
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "📱 از منوی اصلی می‌توانید استفاده کنید:",
                reply_markup=get_main_menu_keyboard()
            )
        
        # پاکسازی user_data پس از موفقیت
        if context.user_data is not None:
            # Log order info before clearing
            phone = context.user_data.get('profile', {})
            if hasattr(phone, 'phone_number'):
                logger.info(f"سفارش {action_text} ثبت شد: {order.id} - {phone.phone_number}")  # type: ignore[attr-defined]
            else:
                logger.info(f"سفارش {action_text} ثبت شد: {order.id}")  # type: ignore[attr-defined]
    
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}")
        # نمایش منوی اصلی
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "📱 از منوی اصلی می‌توانید استفاده کنید:",
                reply_markup=get_main_menu_keyboard()
            )
    except Exception as e:
        logger.error(f"خطا در ثبت سفارش: {e}")
        await query.edit_message_text("❌ خطایی در ثبت سفارش رخ داد.")
        # نمایش منوی اصلی
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "📱 از منوی اصلی می‌توانید استفاده کنید:",
                reply_markup=get_main_menu_keyboard()
            )
    
    if context.user_data is not None:
        context.user_data.clear()
    return ConversationHandler.END


async def show_prices_from_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """نمایش قیمت‌ها و خروج از conversation"""
    query = update.callback_query
    if not query:
        logger.warning("show_prices_from_conversation called but no callback_query found")
        return ConversationHandler.END
    
    await query.answer()
    
    # پاکسازی داده‌های conversation
    if context.user_data is not None:
        context.user_data.clear()
    
    # نمایش منوی قیمت‌ها
    await show_all_prices(update, context)
    
    return ConversationHandler.END


async def trade_cancelled(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو معامله"""
    # پاکسازی user_data
    if context.user_data is not None:
        context.user_data.clear()
    
    # ممکن است از callback query یا message عادی باشد
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        
        # لغو Job انقضای پیش‌فاکتور (اگر وجود دارد)
        if context.job_queue and isinstance(query.message, Message):
            job_name = f'expire_invoice_{query.message.chat_id}_{query.message.message_id}'
            current_jobs = context.job_queue.get_jobs_by_name(job_name)
            for job in current_jobs:
                job.schedule_removal()
        
        try:
            await query.edit_message_text(
                "❌ *معامله لغو شد*\n\n"
                "از منوی اصلی می‌توانید استفاده کنید.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"خطا در ویرایش پیام لغو: {e}")
            # اگر نتوانست پیام را ویرایش کند، پیام جدید بفرست
            if query.message and isinstance(query.message, Message):
                await query.message.reply_text(
                    "❌ *معامله لغو شد*\n\n"
                    "از منوی اصلی می‌توانید استفاده کنید.",
                    parse_mode='Markdown'
                )
        
        # نمایش منوی اصلی (کیبورد)
        if query.message and isinstance(query.message, Message):
            await query.message.reply_text(
                "📱 منوی اصلی:",
                reply_markup=get_main_menu_keyboard()
            )
    else:
        if update.message:
            await update.message.reply_text(
                "❌ *معامله لغو شد*\n\n"
                "از منوی اصلی می‌توانید استفاده کنید.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
    
    if context.user_data is not None:
        context.user_data.clear()
    return ConversationHandler.END


# ==================== Helper Functions ====================

async def safe_edit_message_text(query, text, reply_markup=None, parse_mode=None):
    """Safely edit message text, handling 'Message is not modified' errors"""
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except telegram.error.BadRequest as e:
        if "Message is not modified" in str(e):
            # Message is the same, just answer the callback without editing
            await query.answer("✅")
        else:
            # Other BadRequest error, log and re-raise
            logger.error(f"Telegram BadRequest: {e}")
            raise


def get_trade_conversation_handler() -> ConversationHandler:
    """دریافت ConversationHandler برای معامله"""
    return ConversationHandler(
        entry_points=[
            # ورود مستقیم از دکمه‌های خرید/فروش در بخش قیمت‌ها
            CallbackQueryHandler(
                trade_action_selected,
                pattern=f'^{CALLBACK_TRADE_PRODUCT_PREFIX}(gold|coin|dollar)_{CALLBACK_ACTION_BUY}$'
            ),
            CallbackQueryHandler(
                trade_action_selected,
                pattern=f'^{CALLBACK_TRADE_PRODUCT_PREFIX}(gold|coin|dollar)_{CALLBACK_ACTION_SELL}$'
            ),
        ],
        states={
            SELECTING_METHOD: [
                CallbackQueryHandler(trade_method_selected, pattern=f'^{CALLBACK_METHOD_GRAM}$'),
                CallbackQueryHandler(trade_method_selected, pattern=f'^{CALLBACK_METHOD_RIAL}$'),
                CallbackQueryHandler(trade_cancelled, pattern=f'^{CALLBACK_CONFIRM_NO}$'),
                CallbackQueryHandler(trade_cancelled, pattern=f'^{CALLBACK_BACK_TO_MAIN}$'),
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, trade_amount_entered),
            ],
            CONFIRMING_TRADE: [
                CallbackQueryHandler(trade_confirmed, pattern=f'^{CALLBACK_CONFIRM_YES}$'),
                CallbackQueryHandler(trade_cancelled, pattern=f'^{CALLBACK_CONFIRM_NO}$'),
                CallbackQueryHandler(show_prices_from_conversation, pattern=f'^{CALLBACK_PRICE_ALL}$'),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('cancel', trade_cancelled),
            MessageHandler(filters.Regex('^(لغو|انصراف|cancel)$'), trade_cancelled),
        ],
        name="trade_conversation",
        persistent=False,
    )
