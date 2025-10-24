"""
Management command برای اجرای ربات تلگرام
"""
import logging
import os
import django
from decimal import Decimal
from typing import Optional

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gold_shop.settings')
django.setup()

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.exceptions import ValidationError
from asgiref.sync import sync_to_async

from telegram import Update, ReplyKeyboardRemove
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
from bot.constants import (
    SELECTING_PRODUCT, SELECTING_METHOD, ENTERING_AMOUNT,
    CONFIRMING_BUY, CONFIRMING_SELL,
    MENU_PRICES, MENU_BUY, MENU_SELL, MENU_PORTFOLIO, MENU_HISTORY, MENU_CANCEL,
    CALLBACK_PRODUCT_PREFIX, CALLBACK_METHOD_GRAM, CALLBACK_METHOD_RIAL,
    CALLBACK_CONFIRM_YES, CALLBACK_CONFIRM_NO, CALLBACK_BUY_PREFIX, CALLBACK_SELL_PREFIX
)
from bot.keyboards import (
    get_main_menu_keyboard,
    get_contact_keyboard,
    get_products_keyboard,
    get_amount_method_keyboard,
    get_confirmation_keyboard,
    get_cancel_keyboard,
)
from bot.utils import format_number, parse_decimal, validate_amount, format_datetime

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'اجرای ربات تلگرام'

    def handle(self, *args, **options):
        """اجرای ربات"""
        token = settings.TELEGRAM_BOT_TOKEN
        
        if not token:
            self.stdout.write(
                self.style.ERROR('❌ توکن تلگرام تنظیم نشده است. لطفا TELEGRAM_BOT_TOKEN را در .env تنظیم کنید.')
            )
            return
        
        # Create application
        application = Application.builder().token(token).build()
        
        # Add handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(get_buy_conversation_handler())
        application.add_handler(get_sell_conversation_handler())
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PRICES}$'), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PORTFOLIO}$'), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_HISTORY}$'), show_history))
        application.add_error_handler(handle_error)
        
        # Start bot
        self.stdout.write(self.style.SUCCESS('✅ ربات تلگرام شروع به کار کرد...'))
        application.run_polling(allowed_updates=Update.ALL_TYPES)


# ==================== Handler Functions ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    user = update.effective_user
    telegram_id = str(user.id)
    
    # بررسی وجود کاربر
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if profile is None:
        # کاربر جدید - درخواست ثبت‌نام
        await update.message.reply_text(
            f"👋 سلام {user.first_name} عزیز!\n\n"
            "به سامانه معاملات طلای آنلاین خوش آمدید.\n\n"
            "🔹 برای شروع، لطفا شماره تماس خود را با استفاده از دکمه زیر ارسال کنید:",
            reply_markup=get_contact_keyboard()
        )
    elif not is_approved:
        # کاربر ثبت‌نام کرده اما تایید نشده
        await update.message.reply_text(
            "⏳ حساب کاربری شما در انتظار تایید مدیر است.\n\n"
            "لطفاً صبور باشید. پس از تایید، می‌توانید از تمامی امکانات استفاده کنید.\n\n"
            "ادمین در اسرع وقت حساب شما را بررسی خواهد کرد. 🙏"
        )
    else:
        # کاربر تایید شده - نمایش منوی اصلی
        await update.message.reply_text(
            f"👋 سلام {profile.user.get_full_name()}!\n\n"
            "به سامانه معاملات طلای آنلاین خوش آمدید.\n"
            "از منوی زیر می‌توانید عملیات مورد نظر را انتخاب کنید:",
            reply_markup=get_main_menu_keyboard()
        )


async def handle_error(update: Optional[Update], context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors globally to avoid silent failures."""
    logger.exception("Unhandled error in update handler", exc_info=context.error)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact sharing"""
    contact = update.message.contact
    user = update.effective_user
    telegram_id = str(user.id)
    
    # بررسی اینکه کاربر شماره خودش را فرستاده
    if str(contact.user_id) != telegram_id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            reply_markup=get_contact_keyboard()
        )
        return
    
    phone_number = contact.phone_number
    
    try:
        # ایجاد کاربر و پروفایل
        user_obj, profile, created = await sync_to_async(UserService.create_user_from_telegram)(
            telegram_id=telegram_id,
            phone_number=phone_number,
            telegram_username=user.username,
            first_name=user.first_name or "",
            last_name=user.last_name or ""
        )
        
        if created:
            await update.message.reply_text(
                "✅ ثبت‌نام شما با موفقیت انجام شد!\n\n"
                "⏳ حساب شما در انتظار تایید مدیر است.\n"
                "لطفاً منتظر بمانید تا ادمین حساب شما را بررسی و تایید کند.\n\n"
                "پس از تایید، می‌توانید از تمامی امکانات سامانه استفاده کنید. 🙏",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"کاربر جدید ثبت‌نام کرد: {phone_number} (telegram_id: {telegram_id})")
        else:
            await update.message.reply_text(
                "ℹ️ شما قبلاً ثبت‌نام کرده‌اید.\n\n"
                "در صورتی که هنوز تایید نشده‌اید، لطفاً صبور باشید.",
                reply_markup=ReplyKeyboardRemove()
            )
    
    except Exception as e:
        logger.error(f"خطا در ثبت‌نام کاربر: {e}")
        await update.message.reply_text(
            "❌ خطایی در ثبت‌نام رخ داد. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )


async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت‌های لحظه‌ای"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return
    
    products = await sync_to_async(TradingService.get_active_products)()
    
    if not products:
        await update.message.reply_text("❌ هیچ محصولی در حال حاضر فعال نیست.")
        return
    
    message = "📈 *قیمت‌های لحظه‌ای*\n\n"
    
    # گروه‌بندی محصولات برای نمایش بهتر
    gold_product = None
    coin_product = None
    dollar_product = None
    
    for product in products:
        if product.product_code == Product.PRODUCT_CODE_GOLD:
            gold_product = product
        elif product.product_code == Product.PRODUCT_CODE_COIN:
            coin_product = product
        elif product.product_code == Product.PRODUCT_CODE_DOLLAR:
            dollar_product = product
    
    # نمایش قیمت طلای آبشده
    if gold_product:
        message += "🪙 *طلای آبشده (هر گرم)*\n"
        message += f"   💰 قیمت خرید از شما: *{format_number(gold_product.buy_price)}* ریال\n"
        message += f"   💵 قیمت فروش به شما: *{format_number(gold_product.sell_price)}* ریال\n\n"
    
    # نمایش قیمت سکه تمام
    if coin_product:
        message += "🥇 *سکه تمام غیربانکی*\n"
        message += f"   💰 قیمت خرید از شما: *{format_number(coin_product.buy_price)}* ریال\n"
        message += f"   💵 قیمت فروش به شما: *{format_number(coin_product.sell_price)}* ریال\n\n"
    
    # نمایش قیمت دلار
    if dollar_product:
        message += "💵 *دلار آمریکا*\n"
        message += f"   💰 قیمت خرید از شما: *{format_number(dollar_product.buy_price)}* ریال\n"
        message += f"   💵 قیمت فروش به شما: *{format_number(dollar_product.sell_price)}* ریال\n\n"
    
    # سایر محصولات
    other_products = [p for p in products if p.product_code not in [
        Product.PRODUCT_CODE_GOLD,
        Product.PRODUCT_CODE_COIN,
        Product.PRODUCT_CODE_DOLLAR
    ]]
    
    for product in other_products:
        message += f"🔸 *{product.name}*\n"
        message += f"   💰 قیمت خرید از شما: *{format_number(product.buy_price)}* ریال\n"
        message += f"   💵 قیمت فروش به شما: *{format_number(product.sell_price)}* ریال\n\n"
    
    message += "─────────────────\n"
    message += f"_آخرین به‌روزرسانی: {format_datetime(products[0].updated_at)}_\n"
    message += "_برای به‌روزرسانی قیمت‌ها دوباره این گزینه را انتخاب کنید._"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش پورتفولیو کاربر"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return
    
    message = "📊 *پورتفولیوی شما*\n\n"
    message += f"💰 *موجودی ریالی:* {format_number(profile.rial_balance)} ریال\n\n"
    message += f"⚖️ *موجودی طلا:* {format_number(profile.gold_balance_grams, 4)} گرم\n\n"
    message += "─────────────────\n"
    message += f"_آخرین به‌روزرسانی: {format_datetime(profile.updated_at)}_"
    
    await update.message.reply_text(message, parse_mode='Markdown')


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش تاریخچه سفارشات"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return
    
    orders = await sync_to_async(TradingService.get_user_recent_orders)(profile, limit=5)
    
    if not orders:
        await update.message.reply_text("📜 شما هنوز هیچ سفارشی ثبت نکرده‌اید.")
        return
    
    message = "📜 *تاریخچه ۵ سفارش آخر*\n\n"
    
    for order in orders:
        status_emoji = {
            Order.OrderStatus.PENDING: "⏳",
            Order.OrderStatus.COMPLETED: "✅",
            Order.OrderStatus.CANCELLED: "❌"
        }
        
        type_emoji = "🟢" if order.order_type == Order.OrderType.BUY else "🔴"
        
        message += f"{type_emoji} *سفارش #{order.id}*\n"
        message += f"   نوع: {order.get_order_type_display()}\n"
        message += f"   محصول: {order.product.name}\n"
        message += f"   مقدار: {format_number(order.quantity_grams, 4)} گرم\n"
        message += f"   مبلغ: {format_number(order.total_amount)} ریال\n"
        message += f"   وضعیت: {status_emoji.get(order.status, '❓')} {order.get_status_display()}\n"
        message += f"   تاریخ: {format_datetime(order.created_at)}\n\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')


# ==================== Buy Conversation ====================

async def buy_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند خرید"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await sync_to_async(UserService.check_user_approval_status)(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    products = await sync_to_async(TradingService.get_active_products)()
    
    if not products:
        await update.message.reply_text(
            "❌ هیچ محصولی در حال حاضر برای خرید فعال نیست.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # ذخیره پروفایل در context
    context.user_data['profile'] = profile
    
    await update.message.reply_text(
        "💰 *خرید طلا*\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:",
        reply_markup=get_products_keyboard(products, CALLBACK_BUY_PREFIX),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def buy_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محصول برای خرید انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    # استخراج product_id
    product_id = int(query.data.replace(CALLBACK_BUY_PREFIX + CALLBACK_PRODUCT_PREFIX, ''))
    
    product = await sync_to_async(TradingService.get_product_by_id)(product_id)
    if not product:
        await query.edit_message_text(
            "❌ محصول انتخاب شده یافت نشد.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # ذخیره محصول در context
    context.user_data['product'] = product
    
    await query.edit_message_text(
        f"محصول انتخاب شده: *{product.name}*\n"
        f"قیمت فروش: *{format_number(product.sell_price)}* ریال/گرم\n\n"
        "خرید را بر اساس کدام معیار انجام می‌دهید؟",
        reply_markup=get_amount_method_keyboard(),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def buy_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """روش محاسبه انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    method = query.data
    context.user_data['amount_type'] = 'gram' if method == CALLBACK_METHOD_GRAM else 'rial'
    
    if method == CALLBACK_METHOD_GRAM:
        prompt = "لطفاً مقدار مورد نظر را به *گرم* وارد کنید:\n\nمثال: 2.5"
    else:
        prompt = "لطفاً مبلغ مورد نظر را به *ریال* وارد کنید:\n\nمثال: 5000000"
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return ENTERING_AMOUNT


async def buy_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مقدار وارد شد"""
    amount = parse_decimal(update.message.text)
    
    if amount is None:
        await update.message.reply_text(
            "❌ مقدار وارد شده معتبر نیست. لطفاً یک عدد معتبر وارد کنید.\n\n"
            "مثال: 2.5 یا 5000000"
        )
        return ENTERING_AMOUNT
    
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return ENTERING_AMOUNT
    
    product = context.user_data['product']
    amount_type = context.user_data['amount_type']
    
    # محاسبه جزئیات
    quantity_grams, total_amount = TradingService.calculate_buy_details(
        product, amount_type, amount
    )
    
    # ذخیره در context
    context.user_data['quantity_grams'] = quantity_grams
    context.user_data['total_amount'] = total_amount
    
    # نمایش پیش‌فاکتور
    invoice = (
        "🧾 *پیش‌فاکتور خرید*\n\n"
        f"📦 محصول: *{product.name}*\n"
        f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
        f"💵 قیمت هر گرم: *{format_number(product.sell_price)}* ریال\n"
        f"💰 مبلغ کل: *{format_number(total_amount)}* ریال\n\n"
        "─────────────────\n"
        "آیا تایید می‌کنید؟"
    )
    
    await update.message.reply_text(
        invoice,
        reply_markup=get_confirmation_keyboard(),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_BUY


async def buy_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """خرید تایید شد"""
    query = update.callback_query
    await query.answer()
    
    profile = context.user_data['profile']
    product = context.user_data['product']
    quantity_grams = context.user_data['quantity_grams']
    total_amount = context.user_data['total_amount']
    
    try:
        # ثبت سفارش
        order = await sync_to_async(TradingService.create_buy_order)(
            profile=profile,
            product=product,
            quantity_grams=quantity_grams,
            total_amount=total_amount
        )
        
        await query.edit_message_text(
            "✅ *سفارش خرید شما با موفقیت ثبت شد!*\n\n"
            f"🆔 شماره سفارش: *{order.id}*\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💰 مبلغ: *{format_number(total_amount)}* ریال\n\n"
            "⏳ سفارش شما در انتظار بررسی و تایید مدیر است.\n"
            "پس از تایید، موجودی شما به‌روزرسانی خواهد شد.",
            parse_mode='Markdown'
        )
        
        logger.info(f"سفارش خرید جدید: {order.id} - {profile.phone_number}")
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}")
    
    except Exception as e:
        logger.error(f"خطا در ثبت سفارش خرید: {e}")
        await query.edit_message_text("❌ خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.")
    
    # پاک کردن داده‌ها
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """لغو فرآیند"""
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "❌ عملیات لغو شد.",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "❌ عملیات لغو شد.",
            reply_markup=get_main_menu_keyboard()
        )
    
    context.user_data.clear()
    return ConversationHandler.END


def get_buy_conversation_handler() -> ConversationHandler:
    """دریافت ConversationHandler برای خرید"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f'^{MENU_BUY}$'), buy_start)
        ],
        states={
            SELECTING_PRODUCT: [
                CallbackQueryHandler(
                    buy_product_selected,
                    pattern=f'^{CALLBACK_BUY_PREFIX}{CALLBACK_PRODUCT_PREFIX}'
                ),
                CallbackQueryHandler(cancel_conversation, pattern='^cancel$'),
            ],
            SELECTING_METHOD: [
                CallbackQueryHandler(buy_method_selected, pattern=f'^{CALLBACK_METHOD_GRAM}$'),
                CallbackQueryHandler(buy_method_selected, pattern=f'^{CALLBACK_METHOD_RIAL}$'),
                CallbackQueryHandler(cancel_conversation, pattern='^cancel$'),
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, buy_amount_entered),
                MessageHandler(filters.Regex(f'^{MENU_CANCEL}$'), cancel_conversation),
            ],
            CONFIRMING_BUY: [
                CallbackQueryHandler(buy_confirmed, pattern=f'^{CALLBACK_CONFIRM_YES}$'),
                CallbackQueryHandler(cancel_conversation, pattern=f'^{CALLBACK_CONFIRM_NO}$'),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex(f'^{MENU_CANCEL}$'), cancel_conversation),
        ],
    )


# ==================== Sell Conversation ====================

async def sell_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع فرآیند فروش"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await sync_to_async(UserService.check_user_approval_status)(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text(
            "❌ شما مجاز به استفاده از این بخش نیستید.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # بررسی موجودی طلا
    if profile.gold_balance_grams == 0:
        await update.message.reply_text(
            "❌ موجودی طلای شما صفر است. ابتدا باید طلا خریداری کنید.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    products = await sync_to_async(TradingService.get_active_products)()
    
    if not products:
        await update.message.reply_text(
            "❌ هیچ محصولی در حال حاضر برای فروش فعال نیست.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    context.user_data['profile'] = profile
    
    await update.message.reply_text(
        f"🛒 *فروش طلا*\n\n"
        f"موجودی شما: *{format_number(profile.gold_balance_grams, 4)}* گرم\n\n"
        "لطفاً محصول مورد نظر خود را انتخاب کنید:",
        reply_markup=get_products_keyboard(products, CALLBACK_SELL_PREFIX),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def sell_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محصول برای فروش انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.replace(CALLBACK_SELL_PREFIX + CALLBACK_PRODUCT_PREFIX, ''))
    
    product = await sync_to_async(TradingService.get_product_by_id)(product_id)
    if not product:
        await query.edit_message_text("❌ محصول انتخاب شده یافت نشد.")
        return ConversationHandler.END
    
    context.user_data['product'] = product
    
    await query.edit_message_text(
        f"محصول انتخاب شده: *{product.name}*\n"
        f"قیمت خرید از شما: *{format_number(product.buy_price)}* ریال/گرم\n\n"
        "فروش را بر اساس کدام معیار انجام می‌دهید؟",
        reply_markup=get_amount_method_keyboard(),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def sell_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """روش محاسبه برای فروش انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    method = query.data
    context.user_data['amount_type'] = 'gram' if method == CALLBACK_METHOD_GRAM else 'rial'
    
    profile = context.user_data['profile']
    
    if method == CALLBACK_METHOD_GRAM:
        prompt = (
            f"لطفاً مقدار مورد نظر را به *گرم* وارد کنید:\n\n"
            f"موجودی شما: {format_number(profile.gold_balance_grams, 4)} گرم\n\n"
            f"مثال: 1.5"
        )
    else:
        prompt = "لطفاً مبلغ مورد نظر را به *ریال* وارد کنید:\n\nمثال: 3000000"
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return ENTERING_AMOUNT


async def sell_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مقدار فروش وارد شد"""
    amount = parse_decimal(update.message.text)
    
    if amount is None:
        await update.message.reply_text(
            "❌ مقدار وارد شده معتبر نیست. لطفاً یک عدد معتبر وارد کنید."
        )
        return ENTERING_AMOUNT
    
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(error_msg)
        return ENTERING_AMOUNT
    
    product = context.user_data['product']
    amount_type = context.user_data['amount_type']
    profile = context.user_data['profile']
    
    # محاسبه جزئیات
    quantity_grams, total_amount = TradingService.calculate_sell_details(
        product, amount_type, amount
    )
    
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
    
    # نمایش پیش‌فاکتور
    invoice = (
        "🧾 *پیش‌فاکتور فروش*\n\n"
        f"📦 محصول: *{product.name}*\n"
        f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
        f"💵 قیمت هر گرم: *{format_number(product.buy_price)}* ریال\n"
        f"💰 مبلغ دریافتی: *{format_number(total_amount)}* ریال\n\n"
        "─────────────────\n"
        "آیا تایید می‌کنید؟"
    )
    
    await update.message.reply_text(
        invoice,
        reply_markup=get_confirmation_keyboard(),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_SELL


async def sell_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """فروش تایید شد"""
    query = update.callback_query
    await query.answer()
    
    profile = context.user_data['profile']
    product = context.user_data['product']
    quantity_grams = context.user_data['quantity_grams']
    total_amount = context.user_data['total_amount']
    
    try:
        # ثبت سفارش
        order = await sync_to_async(TradingService.create_sell_order)(
            profile=profile,
            product=product,
            quantity_grams=quantity_grams,
            total_amount=total_amount
        )
        
        await query.edit_message_text(
            "✅ *سفارش فروش شما با موفقیت ثبت شد!*\n\n"
            f"🆔 شماره سفارش: *{order.id}*\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💰 مبلغ دریافتی: *{format_number(total_amount)}* ریال\n\n"
            "⏳ سفارش شما در انتظار بررسی و تایید مدیر است.\n"
            "پس از تایید، موجودی شما به‌روزرسانی خواهد شد.",
            parse_mode='Markdown'
        )
        
        logger.info(f"سفارش فروش جدید: {order.id} - {profile.phone_number}")
        
    except ValidationError as e:
        await query.edit_message_text(f"❌ {str(e)}")
    
    except Exception as e:
        logger.error(f"خطا در ثبت سفارش فروش: {e}")
        await query.edit_message_text("❌ خطایی در ثبت سفارش رخ داد. لطفاً دوباره تلاش کنید.")
    
    context.user_data.clear()
    
    return ConversationHandler.END


def get_sell_conversation_handler() -> ConversationHandler:
    """دریافت ConversationHandler برای فروش"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f'^{MENU_SELL}$'), sell_start)
        ],
        states={
            SELECTING_PRODUCT: [
                CallbackQueryHandler(
                    sell_product_selected,
                    pattern=f'^{CALLBACK_SELL_PREFIX}{CALLBACK_PRODUCT_PREFIX}'
                ),
                CallbackQueryHandler(cancel_conversation, pattern='^cancel$'),
            ],
            SELECTING_METHOD: [
                CallbackQueryHandler(sell_method_selected, pattern=f'^{CALLBACK_METHOD_GRAM}$'),
                CallbackQueryHandler(sell_method_selected, pattern=f'^{CALLBACK_METHOD_RIAL}$'),
                CallbackQueryHandler(cancel_conversation, pattern='^cancel$'),
            ],
            ENTERING_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sell_amount_entered),
                MessageHandler(filters.Regex(f'^{MENU_CANCEL}$'), cancel_conversation),
            ],
            CONFIRMING_SELL: [
                CallbackQueryHandler(sell_confirmed, pattern=f'^{CALLBACK_CONFIRM_YES}$'),
                CallbackQueryHandler(cancel_conversation, pattern=f'^{CALLBACK_CONFIRM_NO}$'),
            ],
        },
        fallbacks=[
            CommandHandler('start', start),
            MessageHandler(filters.Regex(f'^{MENU_CANCEL}$'), cancel_conversation),
        ],
    )

