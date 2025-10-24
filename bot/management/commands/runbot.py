"""
Management command برای اجرای ربات تلگرام - نسخه حرفه‌ای
"""
import logging
import os
import django
from decimal import Decimal
from typing import Optional
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

from telegram import Update, ReplyKeyboardRemove, ForceReply
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
from trading.services import TradingService
from trading.models import Product, Order
from bot.constants import *
from bot.keyboards import *
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
            self.stdout.write(
                self.style.ERROR('❌ توکن تلگرام تنظیم نشده است.')
            )
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
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PORTFOLIO}$'), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_HISTORY}$'), show_history))
        # دکمه معامله حذف شد - معامله از طریق بخش قیمت‌ها انجام می‌شود
        
        # Price callbacks
        application.add_handler(CallbackQueryHandler(show_price_gold, pattern=f'^{CALLBACK_PRICE_GOLD}$'))
        application.add_handler(CallbackQueryHandler(show_price_coin, pattern=f'^{CALLBACK_PRICE_COIN}$'))
        application.add_handler(CallbackQueryHandler(show_price_dollar, pattern=f'^{CALLBACK_PRICE_DOLLAR}$'))
        application.add_handler(CallbackQueryHandler(show_all_prices, pattern=f'^{CALLBACK_PRICE_ALL}$'))
        
        # Price refresh callbacks
        application.add_handler(CallbackQueryHandler(refresh_price, pattern=f'^{CALLBACK_PRICE_REFRESH}(gold|coin|dollar)$'))
        
        # Error handler
        application.add_error_handler(handle_error)
        
        # Start bot
        self.stdout.write(self.style.SUCCESS('✅ ربات تلگرام شروع به کار کرد...'))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# ==================== Basic Handlers ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
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
            "پس از تایید، می‌توانید از تمامی امکانات استفاده کنید. 🙏"
        )
    else:
        await update.message.reply_text(
            f"👋 سلام {profile.user.get_full_name()}!\n\n"
            "به ربات معاملات طلا و ارز خوش آمدید.\n\n"
            "📊 *قیمت‌ها:* مشاهده قیمت‌های لحظه‌ای و خرید/فروش\n"
            "👛 *کیف پول:* مشاهده موجودی\n"
            "📋 *تاریخچه:* مشاهده سفارشات قبلی",
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def handle_error(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors"""
    logger.exception("خطا:", exc_info=context.error)
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
        except:
            pass


# ==================== Registration Handlers ====================

async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند ثبت نام با دریافت شماره تلگرام"""
    contact = update.message.contact
    user = update.effective_user
    telegram_id = str(user.id)
    
    if str(contact.user_id) != telegram_id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            reply_markup=get_contact_keyboard()
        )
        return ConversationHandler.END
    
    # ذخیره اطلاعات اولیه
    context.user_data['telegram_id'] = telegram_id
    context.user_data['phone_number'] = contact.phone_number
    context.user_data['telegram_username'] = user.username
    
    await update.message.reply_text(
        "📝 *ثبت نام*\n\n"
        "لطفاً *نام* خود را وارد کنید:",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ENTERING_FIRST_NAME


async def registration_first_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام"""
    first_name = update.message.text.strip()
    
    if not first_name or len(first_name) < 2:
        await update.message.reply_text(
            "❌ نام باید حداقل 2 کاراکتر باشد.\n\n"
            "لطفاً نام خود را وارد کنید:"
        )
        return ENTERING_FIRST_NAME
    
    context.user_data['first_name'] = first_name
    
    await update.message.reply_text(
        f"✅ نام: *{first_name}*\n\n"
        "لطفاً *نام خانوادگی* خود را وارد کنید:",
        parse_mode='Markdown'
    )
    
    return ENTERING_LAST_NAME


async def registration_last_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت نام خانوادگی"""
    last_name = update.message.text.strip()
    
    if not last_name or len(last_name) < 2:
        await update.message.reply_text(
            "❌ نام خانوادگی باید حداقل 2 کاراکتر باشد.\n\n"
            "لطفاً نام خانوادگی خود را وارد کنید:"
        )
        return ENTERING_LAST_NAME
    
    context.user_data['last_name'] = last_name
    
    await update.message.reply_text(
        f"✅ نام خانوادگی: *{last_name}*\n\n"
        "لطفاً *کد ملی* (10 رقمی) خود را وارد کنید:",
        parse_mode='Markdown'
    )
    
    return ENTERING_NATIONAL_CODE


async def registration_national_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """دریافت کد ملی و تکمیل ثبت نام"""
    national_code = update.message.text.strip()
    
    # اعتبارسنجی کد ملی
    if not national_code.isdigit() or len(national_code) != 10:
        await update.message.reply_text(
            "❌ کد ملی باید دقیقاً 10 رقم باشد.\n\n"
            "لطفاً کد ملی خود را وارد کنید:"
        )
        return ENTERING_NATIONAL_CODE
    
    context.user_data['national_code'] = national_code
    
    # ثبت کاربر در دیتابیس
    try:
        user_obj, profile, created = await sync_to_async(UserService.create_user_from_telegram)(
            telegram_id=context.user_data['telegram_id'],
            phone_number=context.user_data['phone_number'],
            telegram_username=context.user_data.get('telegram_username'),
            first_name=context.user_data['first_name'],
            last_name=context.user_data['last_name'],
            national_code=national_code
        )
        
        if created:
            await update.message.reply_text(
                "✅ *ثبت‌نام شما با موفقیت انجام شد!*\n\n"
                f"👤 نام: {context.user_data['first_name']} {context.user_data['last_name']}\n"
                f"📱 شماره تماس: {context.user_data['phone_number']}\n"
                f"🆔 کد ملی: {national_code}\n\n"
                "⏳ حساب شما در انتظار تایید مدیر است.\n"
                "پس از تایید، از منوی ربات استفاده کنید. 🙏",
                parse_mode='Markdown'
            )
            logger.info(f"کاربر جدید: {context.user_data['first_name']} {context.user_data['last_name']} - {context.user_data['phone_number']} ({context.user_data['telegram_id']})")
        else:
            await update.message.reply_text(
                "ℹ️ شما قبلاً ثبت‌نام کرده‌اید.",
                parse_mode='Markdown'
            )
    
    except Exception as e:
        logger.error(f"خطا در ثبت‌نام: {e}")
        await update.message.reply_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
    
    context.user_data.clear()
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
            ENTERING_NATIONAL_CODE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, registration_national_code),
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
    data = job.data
    
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


def is_price_expired(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> bool:
    """بررسی اینکه آیا قیمت منقضی شده است (بیش از 1 دقیقه)"""
    price_timestamp_key = f'price_timestamp_{product_code}'
    timestamp = context.user_data.get(price_timestamp_key)
    
    if not timestamp:
        return True
    
    elapsed = datetime.now() - timestamp
    return elapsed > timedelta(minutes=1)


def set_price_timestamp(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> None:
    """ذخیره timestamp نمایش قیمت"""
    price_timestamp_key = f'price_timestamp_{product_code}'
    context.user_data[price_timestamp_key] = datetime.now()


def get_time_remaining(context: ContextTypes.DEFAULT_TYPE, product_code: str) -> str:
    """دریافت زمان باقیمانده تا انقضای قیمت"""
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
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
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
    await query.answer()
    
    try:
        product = await sync_to_async(Product.get_by_code)(Product.PRODUCT_CODE_GOLD)
        
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
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_GOLD, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired:
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
    await query.answer()
    
    try:
        product = await sync_to_async(Product.get_by_code)(Product.PRODUCT_CODE_COIN)
        
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
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_COIN, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired:
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
    await query.answer()
    
    try:
        product = await sync_to_async(Product.get_by_code)(Product.PRODUCT_CODE_DOLLAR)
        
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
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال"
            f"{warning}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await safe_edit_message_text(
            query,
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_DOLLAR, can_trade=True, is_expired=is_expired),
            parse_mode='Markdown'
        )
        
        # برنامه‌ریزی Job برای حذف خودکار دکمه‌ها پس از 60 ثانیه
        if not is_expired:
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
    await query.answer()
    
    products = await sync_to_async(TradingService.get_active_products)()
    
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
        message += f"   💰 خرید: `{format_number(product.buy_price)}` ریال\n"
        message += f"   💵 فروش: `{format_number(product.sell_price)}` ریال\n\n"
    
    message += f"─────────────────\n"
    message += f"_به‌روزرسانی: {format_datetime(products[0].updated_at)}_"
    
    await safe_edit_message_text(
        query,
        message,
        reply_markup=get_prices_menu_keyboard(),
        parse_mode='Markdown'
    )


async def refresh_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بروزرسانی قیمت و ریست تایمر"""
    query = update.callback_query
    await query.answer("🔄 در حال بروزرسانی...")
    
    # استخراج product_code از callback
    callback_data = query.data
    product_code = callback_data.replace(CALLBACK_PRICE_REFRESH, "")
    
    # Map short codes to full codes
    product_code_map = {
        PRODUCT_GOLD: Product.PRODUCT_CODE_GOLD,
        PRODUCT_COIN: Product.PRODUCT_CODE_COIN,
        PRODUCT_DOLLAR: Product.PRODUCT_CODE_DOLLAR,
    }
    
    full_product_code = product_code_map.get(product_code)
    if not full_product_code:
        await query.edit_message_text("❌ محصول نامعتبر.")
        return
    
    try:
        # بروزرسانی قیمت‌ها از API
        await sync_to_async(TradingService.update_all_prices)()
        
        # دریافت قیمت جدید
        product = await sync_to_async(Product.get_by_code)(full_product_code)
        
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
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال\n\n"
            f"⏱ *زمان باقیمانده:* {time_remaining}\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
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
    """نمایش پورتفولیو"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return
    
    message = (
        "👛 *کیف پول شما*\n\n"
        f"💰 *موجودی ریالی:*\n   {format_number(profile.rial_balance)} ریال\n\n"
        f"⚖️ *موجودی طلا:*\n   {format_number(profile.gold_balance_grams, 4)} گرم\n\n"
        f"─────────────────\n"
        f"_به‌روزرسانی: {format_datetime(profile.updated_at)}_"
    )
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش تاریخچه"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return
    
    orders = await sync_to_async(TradingService.get_user_recent_orders)(profile, limit=5)
    
    if not orders:
        await update.message.reply_text("📋 شما هنوز هیچ سفارشی ثبت نکرده‌اید.")
        return
    
    message = "📋 *تاریخچه ۵ سفارش آخر*\n\n"
    
    for order in orders:
        status_emoji = {
            Order.OrderStatus.PENDING: "⏳",
            Order.OrderStatus.COMPLETED: "✅",
            Order.OrderStatus.CANCELLED: "❌"
        }
        
        type_emoji = "🟢" if order.order_type == Order.OrderType.BUY else "🔴"
        
        message += f"{type_emoji} *سفارش #{order.id}*\n"
        message += f"   {order.get_order_type_display()} | {order.product.name}\n"
        message += f"   مقدار: {format_number(order.quantity_grams, 4)} گرم\n"
        message += f"   مبلغ: {format_number(order.total_amount)} ریال\n"
        message += f"   {status_emoji.get(order.status, '❓')} {order.get_status_display()}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


# ==================== Trade Conversation ====================
# توابع trade_start و trade_product_selected حذف شدند
# معاملات مستقیماً از دکمه‌های خرید/فروش در بخش قیمت‌ها شروع می‌شوند


async def trade_action_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """خرید یا فروش انتخاب شد"""
    query = update.callback_query
    
    callback_data = query.data
    logger.info(f"Action callback: {callback_data}")
    
    # استخراج product_code و action از callback
    # فرمت: trade_gold_action_buy یا trade_gold_action_sell
    parts = callback_data.replace(CALLBACK_TRADE_PRODUCT_PREFIX, "").split("_")
    product_code = parts[0]
    
    # اگر profile ذخیره نشده باشد، از دیتابیس دریافت کن
    if not context.user_data.get('profile'):
        telegram_id = str(update.effective_user.id)
        is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
        if not profile or not is_approved:
            await query.answer("❌ شما مجاز به استفاده از این بخش نیستید.", show_alert=True)
            return ConversationHandler.END
        context.user_data['profile'] = profile
    
    # بررسی انقضای قیمت
    if is_price_expired(context, product_code):
        await query.answer("⏰ قیمت منقضی شده است. لطفاً ابتدا قیمت را بروزرسانی کنید.", show_alert=True)
        return ConversationHandler.END
    
    await query.answer()
    
    if CALLBACK_ACTION_BUY in callback_data:
        action = "buy"
        action_text = "خرید"
    elif CALLBACK_ACTION_SELL in callback_data:
        action = "sell"
        action_text = "فروش"
    else:
        await query.edit_message_text("❌ عملیات نامعتبر.")
        return ConversationHandler.END
    
    # اگر محصول ذخیره نشده باشد، دریافت کن
    if not context.user_data.get('product'):
        product_code_map = {
            PRODUCT_GOLD: Product.PRODUCT_CODE_GOLD,
            PRODUCT_COIN: Product.PRODUCT_CODE_COIN,
            PRODUCT_DOLLAR: Product.PRODUCT_CODE_DOLLAR,
        }
        
        try:
            product = await sync_to_async(Product.get_by_code)(product_code_map[product_code])
            context.user_data['product'] = product
            context.user_data['product_code'] = product_code
        except (Product.DoesNotExist, KeyError):
            await query.edit_message_text("❌ خطا: محصول یافت نشد.")
        return ConversationHandler.END
    
    context.user_data['action'] = action
    product = context.user_data.get('product')
    
    if not product:
        await query.edit_message_text("❌ خطا: محصول یافت نشد.")
        return ConversationHandler.END
    
    # بررسی موجودی برای فروش
    if action == "sell":
        profile = context.user_data.get('profile')
        if profile.gold_balance_grams == 0:
            await query.edit_message_text(
                "❌ موجودی طلای شما صفر است.\n"
                "ابتدا باید طلا خریداری کنید."
            )
            return ConversationHandler.END
    
    # محاسبه زمان باقیمانده
    time_remaining = get_time_remaining(context, product_code)
    
    await query.edit_message_text(
        f"💎 {action_text} *{product.name}*\n\n"
        f"⏱ *زمان باقیمانده:* {time_remaining}\n\n"
        "⚠️ *توجه:* شما یک دقیقه برای تکمیل معامله فرصت دارید.\n"
        "پس از آن باید قیمت را بروزرسانی کنید.\n\n"
        "مقدار را بر اساس چه واحدی وارد می‌کنید؟",
        reply_markup=get_amount_method_keyboard(),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def trade_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """روش محاسبه انتخاب شد"""
    query = update.callback_query
    
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    if is_price_expired(context, product_code):
        await query.answer("⏰ زمان شما به پایان رسید. لطفاً قیمت را بروزرسانی کنید.", show_alert=True)
        await query.edit_message_text(
            "⏰ *زمان معامله به پایان رسید*\n\n"
            "قیمت‌ها ممکن است تغییر کرده باشند.\n"
            "برای ادامه، لطفاً به بخش قیمت‌ها بروید و قیمت را بروزرسانی کنید.",
            parse_mode='Markdown'
        )
        # ارسال کیبورد جدید با دکمه قیمت‌ها
        await query.message.reply_text(
            "👇 از دکمه زیر استفاده کنید:",
            reply_markup=get_back_to_prices_keyboard()
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    await query.answer()
    
    method = "gram" if query.data == CALLBACK_METHOD_GRAM else "rial"
    context.user_data['amount_type'] = method
    
    product = context.user_data.get('product')
    action = context.user_data.get('action')
    action_text = "خرید" if action == "buy" else "فروش"
    
    # محاسبه زمان باقیمانده
    time_remaining = get_time_remaining(context, product_code)
    
    if method == "gram":
        unit = "گرم" if product.product_code != Product.PRODUCT_CODE_DOLLAR else "عدد"
        prompt = (
            f"💎 {action_text} *{product.name}*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n\n"
            f"📝 لطفاً مقدار را به *{unit}* وارد کنید:\n\n"
            f"💡 *راهنما:*\n"
            f"• برای نیم گرم: `0.5`\n"
            f"• برای دو و نیم گرم: `2.5`\n"
            f"• برای ده گرم: `10`"
        )
    else:
        prompt = (
            f"💎 {action_text} *{product.name}*\n\n"
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
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    if is_price_expired(context, product_code):
        await update.message.reply_text(
            "⏰ *زمان معامله به پایان رسید*\n\n"
            "قیمت‌ها ممکن است تغییر کرده باشند.\n"
            "برای ادامه، لطفاً به بخش قیمت‌ها بروید و قیمت را بروزرسانی کنید.\n\n"
            "👇 از دکمه زیر استفاده کنید:",
            reply_markup=get_back_to_prices_keyboard(),
            parse_mode='Markdown'
        )
        context.user_data.clear()
        return ConversationHandler.END
    
    amount = parse_decimal(update.message.text)
    
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
            parse_mode='Markdown'
        )
        return ENTERING_AMOUNT
    
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        time_remaining = get_time_remaining(context, product_code)
        await update.message.reply_text(
            f"{error_msg}\n\n⏱ زمان باقیمانده: {time_remaining}",
            parse_mode='Markdown'
        )
        return ENTERING_AMOUNT
    
    product = context.user_data['product']
    amount_type = context.user_data['amount_type']
    action = context.user_data['action']
    profile = context.user_data['profile']
    
    # محاسبه جزئیات
    try:
        if action == "buy":
            quantity_grams, total_amount = TradingService.calculate_buy_details(
                product, amount_type, amount
            )
            price = product.sell_price
            action_text = "خرید"
        else:
            quantity_grams, total_amount = TradingService.calculate_sell_details(
                product, amount_type, amount
            )
            price = product.buy_price
            action_text = "فروش"
            
            # بررسی موجودی
            if quantity_grams > profile.gold_balance_grams:
                await update.message.reply_text(
                    f"❌ موجودی طلای شما کافی نیست.\n\n"
                    f"موجودی شما: {format_number(profile.gold_balance_grams, 4)} گرم\n"
                    f"مقدار درخواستی: {format_number(quantity_grams, 4)} گرم"
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
        full_name = profile.user.get_full_name()
        if not full_name:
            full_name = "کاربر"
        
        # تاریخ و زمان فعلی
        now = datetime.now()
        persian_date = now.strftime("%Y/%m/%d")
        persian_time = now.strftime("%H:%M:%S")
        
        # دریافت کدملی
        national_code = profile.national_code or "ثبت نشده"
        
        # نمایش پیش‌فاکتور
        invoice = (
            f"🧾 *پیش‌فاکتور {action_text}*\n\n"
            f"📋 شماره فاکتور: `{invoice_number}`\n"
            f"👤 نام مشتری: *{full_name}*\n"
            f"🪪 کد ملی: `{national_code}`\n"
            f"📅 تاریخ: {persian_date}\n"
            f"🕐 ساعت: {persian_time}\n"
            f"─────────────────\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💵 قیمت واحد: *{format_number(price)}* ریال\n"
            f"💰 *مبلغ کل: {format_number(total_amount)} ریال*\n\n"
            f"⏱ زمان باقیمانده: {time_remaining}\n"
            "─────────────────\n"
            "⚠️ لطفاً سریع تصمیم بگیرید!\n"
            "آیا این سفارش را تایید می‌کنید؟"
        )
        
        await update.message.reply_text(
            invoice,
            reply_markup=get_confirmation_keyboard(),
            parse_mode='Markdown'
        )
        
        return CONFIRMING_TRADE
    
    except Exception as e:
        logger.error(f"Error in calculation: {e}")
        await update.message.reply_text("❌ خطا در محاسبه. لطفاً دوباره تلاش کنید.")
        return ConversationHandler.END


async def trade_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تایید نهایی"""
    query = update.callback_query
    
    # بررسی انقضای قیمت
    product_code = context.user_data.get('product_code')
    if is_price_expired(context, product_code):
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
        
        # فقط دکمه لغو را نمایش بده
        from telegram import InlineKeyboardMarkup, InlineKeyboardButton
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ بستن", callback_data=CALLBACK_CONFIRM_NO)]
        ])
        
        await query.edit_message_text(
            expired_invoice,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
        # ارسال کیبورد جدید با دکمه قیمت‌ها
        await query.message.reply_text(
            "👇 برای ادامه از دکمه زیر استفاده کنید:",
            reply_markup=get_back_to_prices_keyboard()
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
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        invoice_number = context.user_data.get('invoice_number')
        
        if action == "buy":
            order = await sync_to_async(TradingService.create_buy_order)(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams,
                total_amount=total_amount,
                invoice_number=invoice_number
            )
            action_text = "خرید"
        else:
            order = await sync_to_async(TradingService.create_sell_order)(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams,
                total_amount=total_amount,
                invoice_number=invoice_number
            )
            action_text = "فروش"
        
        # دریافت اطلاعات برای فاکتور نهایی
        invoice_number = context.user_data.get('invoice_number', 'N/A')
        full_name = profile.user.get_full_name()
        if not full_name:
            full_name = "کاربر"
        
        # دریافت کدملی
        national_code = profile.national_code or "ثبت نشده"
        
        now = datetime.now()
        persian_date = now.strftime("%Y/%m/%d")
        persian_time = now.strftime("%H:%M:%S")
        
        await query.edit_message_text(
            f"✅ *سفارش {action_text} با موفقیت ثبت شد!*\n\n"
            f"📋 شماره فاکتور: `{invoice_number}`\n"
            f"🆔 شماره سفارش: *{order.id}*\n"
            f"👤 نام مشتری: *{full_name}*\n"
            f"🪪 کد ملی: `{national_code}`\n"
            f"📅 تاریخ: {persian_date}\n"
            f"🕐 ساعت: {persian_time}\n"
            f"─────────────────\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💰 مبلغ: *{format_number(total_amount)}* ریال\n\n"
            f"⏳ *وضعیت:* در انتظار تایید مدیر\n"
            f"پس از تایید، موجودی شما به‌روزرسانی خواهد شد.",
            parse_mode='Markdown'
        )
        
        logger.info(f"سفارش {action_text} ثبت شد: {order.id} - {profile.phone_number}")
    
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}")
    except Exception as e:
        logger.error(f"خطا در ثبت سفارش: {e}")
        await query.edit_message_text("❌ خطایی در ثبت سفارش رخ داد.")
    
    context.user_data.clear()
    return ConversationHandler.END


async def trade_cancelled(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو معامله"""
    # ممکن است از callback query یا message عادی باشد
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(
            "❌ *معامله لغو شد*\n\n"
            "برای شروع معامله جدید، به بخش قیمت‌ها بروید.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ *معامله لغو شد*\n\n"
            "برای شروع معامله جدید، به بخش قیمت‌ها بروید.",
            parse_mode='Markdown'
        )
    
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
