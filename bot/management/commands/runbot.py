"""
Management command برای اجرای ربات تلگرام - نسخه حرفه‌ای
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
        application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        
        # Menu handlers
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PRICES}$'), show_prices_menu))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PORTFOLIO}$'), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_HISTORY}$'), show_history))
        
        # Price callbacks
        application.add_handler(CallbackQueryHandler(show_price_gold, pattern=f'^{CALLBACK_PRICE_GOLD}$'))
        application.add_handler(CallbackQueryHandler(show_price_coin, pattern=f'^{CALLBACK_PRICE_COIN}$'))
        application.add_handler(CallbackQueryHandler(show_price_dollar, pattern=f'^{CALLBACK_PRICE_DOLLAR}$'))
        application.add_handler(CallbackQueryHandler(show_all_prices, pattern=f'^{CALLBACK_PRICE_ALL}$'))
        
        # Trade conversation handler (MUST be before other callback handlers)
        application.add_handler(get_trade_conversation_handler())
        
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
            "به ربات معاملات طلا و ارز خوش آمدید.\n"
            "از منوی زیر می‌توانید استفاده کنید:",
            reply_markup=get_main_menu_keyboard()
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


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact sharing"""
    contact = update.message.contact
    user = update.effective_user
    telegram_id = str(user.id)
    
    if str(contact.user_id) != telegram_id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            reply_markup=get_contact_keyboard()
        )
        return
    
    phone_number = contact.phone_number
    
    try:
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
                "پس از تایید، از منوی ربات استفاده کنید. 🙏",
                reply_markup=ReplyKeyboardRemove()
            )
            logger.info(f"کاربر جدید: {phone_number} ({telegram_id})")
        else:
            await update.message.reply_text(
                "ℹ️ شما قبلاً ثبت‌نام کرده‌اید.",
                reply_markup=ReplyKeyboardRemove()
            )
    
    except Exception as e:
        logger.error(f"خطا در ثبت‌نام: {e}")
        await update.message.reply_text(
            "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید."
        )


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
        
        message = (
            "🪙 *طلای آبشده (هر گرم)*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال\n\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_GOLD),
            parse_mode='Markdown'
        )
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")


async def show_price_coin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت سکه"""
    query = update.callback_query
    await query.answer()
    
    try:
        product = await sync_to_async(Product.get_by_code)(Product.PRODUCT_CODE_COIN)
        
        message = (
            "🥇 *سکه تمام غیربانکی*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال\n\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_COIN),
            parse_mode='Markdown'
        )
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")


async def show_price_dollar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """نمایش قیمت دلار"""
    query = update.callback_query
    await query.answer()
    
    try:
        product = await sync_to_async(Product.get_by_code)(Product.PRODUCT_CODE_DOLLAR)
        
        message = (
            "💵 *دلار آمریکا*\n\n"
            f"💰 *قیمت خرید از شما:*\n"
            f"   `{format_number(product.buy_price)}` ریال\n\n"
            f"💵 *قیمت فروش به شما:*\n"
            f"   `{format_number(product.sell_price)}` ریال\n\n"
            f"─────────────────\n"
            f"_به‌روزرسانی: {format_datetime(product.updated_at)}_"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_product_detail_keyboard(PRODUCT_DOLLAR),
            parse_mode='Markdown'
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
    
    await query.edit_message_text(
        message,
        reply_markup=get_prices_menu_keyboard(),
        parse_mode='Markdown'
    )


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

async def trade_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """شروع معامله"""
    telegram_id = str(update.effective_user.id)
    is_approved, profile = await UserService.acheck_user_approval_status(telegram_id)
    
    if not profile or not is_approved:
        await update.message.reply_text("❌ شما مجاز به استفاده از این بخش نیستید.")
        return ConversationHandler.END
    
    products = await sync_to_async(TradingService.get_active_products)()
    
    if not products:
        await update.message.reply_text("❌ هیچ محصولی فعال نیست.")
        return ConversationHandler.END
    
    context.user_data['profile'] = profile
    
    await update.message.reply_text(
        "💎 *منوی معامله*\n\n"
        "لطفاً محصول مورد نظر را انتخاب کنید:",
        reply_markup=get_trade_menu_keyboard(products),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT


async def trade_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """محصول انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.info(f"Callback received: {callback_data}")
    
    # استخراج product_code از callback_data
    # فرمت: trade_gold یا trade_gold_action_buy یا trade_gold_action_sell
    parts = callback_data.replace(CALLBACK_TRADE_PRODUCT_PREFIX, "").split("_")
    product_code = parts[0]
    
    logger.info(f"Product code: {product_code}")
    
    # Map short codes to full codes
    product_code_map = {
        PRODUCT_GOLD: Product.PRODUCT_CODE_GOLD,
        PRODUCT_COIN: Product.PRODUCT_CODE_COIN,
        PRODUCT_DOLLAR: Product.PRODUCT_CODE_DOLLAR,
    }
    
    if product_code not in product_code_map:
        await query.edit_message_text("❌ محصول نامعتبر.")
        return ConversationHandler.END
    
    try:
        product = await sync_to_async(Product.get_by_code)(product_code_map[product_code])
        context.user_data['product'] = product
        context.user_data['product_code'] = product_code
        
        # نمایش قیمت و گزینه‌های خرید/فروش
        message = (
            f"💎 *{product.name}*\n\n"
            f"💰 قیمت خرید از شما: `{format_number(product.buy_price)}` ریال\n"
            f"💵 قیمت فروش به شما: `{format_number(product.sell_price)}` ریال\n\n"
            "چه کاری می‌خواهید انجام دهید?"
        )
        
        await query.edit_message_text(
            message,
            reply_markup=get_buy_sell_keyboard(product_code),
            parse_mode='Markdown'
        )
        
        return SELECTING_ACTION
    
    except Product.DoesNotExist:
        await query.edit_message_text("❌ محصول یافت نشد.")
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error in trade_product_selected: {e}")
        await query.edit_message_text("❌ خطایی رخ داد.")
        return ConversationHandler.END


async def trade_action_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """خرید یا فروش انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    callback_data = query.data
    logger.info(f"Action callback: {callback_data}")
    
    # استخراج action از callback
    # فرمت: trade_gold_action_buy یا trade_gold_action_sell
    if CALLBACK_ACTION_BUY in callback_data:
        action = "buy"
        action_text = "خرید"
    elif CALLBACK_ACTION_SELL in callback_data:
        action = "sell"
        action_text = "فروش"
    else:
        await query.edit_message_text("❌ عملیات نامعتبر.")
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
    
    await query.edit_message_text(
        f"💎 {action_text} *{product.name}*\n\n"
        "مقدار را بر اساس چه واحدی وارد می‌کنید؟",
        reply_markup=get_amount_method_keyboard(),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD


async def trade_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """روش محاسبه انتخاب شد"""
    query = update.callback_query
    await query.answer()
    
    method = "gram" if query.data == CALLBACK_METHOD_GRAM else "rial"
    context.user_data['amount_type'] = method
    
    product = context.user_data.get('product')
    action = context.user_data.get('action')
    action_text = "خرید" if action == "buy" else "فروش"
    
    if method == "gram":
        unit = "گرم" if product.product_code != Product.PRODUCT_CODE_DOLLAR else "عدد"
        prompt = f"💎 {action_text} *{product.name}*\n\nلطفاً مقدار را به *{unit}* وارد کنید:\n\nمثال: 2.5"
    else:
        prompt = f"💎 {action_text} *{product.name}*\n\nلطفاً مبلغ را به *ریال* وارد کنید:\n\nمثال: 5000000"
    
    await query.edit_message_text(prompt, parse_mode='Markdown')
    
    return ENTERING_AMOUNT


async def trade_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """مقدار وارد شد"""
    amount = parse_decimal(update.message.text)
    
    if amount is None:
        await update.message.reply_text(
            "❌ مقدار نامعتبر است. لطفاً یک عدد معتبر وارد کنید.\n\nمثال: 2.5 یا 5000000"
        )
        return ENTERING_AMOUNT
    
    is_valid, error_msg = validate_amount(amount)
    if not is_valid:
        await update.message.reply_text(error_msg)
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
        
        # نمایش پیش‌فاکتور
        invoice = (
            f"🧾 *پیش‌فاکتور {action_text}*\n\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💵 قیمت هر واحد: *{format_number(price)}* ریال\n"
            f"💰 مبلغ کل: *{format_number(total_amount)}* ریال\n\n"
            "─────────────────\n"
            "آیا تایید می‌کنید؟"
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
        if action == "buy":
            order = await sync_to_async(TradingService.create_buy_order)(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams,
                total_amount=total_amount
            )
            action_text = "خرید"
        else:
            order = await sync_to_async(TradingService.create_sell_order)(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams,
                total_amount=total_amount
            )
            action_text = "فروش"
        
        await query.edit_message_text(
            f"✅ *سفارش {action_text} با موفقیت ثبت شد!*\n\n"
            f"🆔 شماره سفارش: *{order.id}*\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{format_number(quantity_grams, 4)}* گرم\n"
            f"💰 مبلغ: *{format_number(total_amount)}* ریال\n\n"
            "⏳ سفارش در انتظار تایید مدیر است.\n"
            "پس از تایید، موجودی شما به‌روزرسانی خواهد شد.",
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
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text("❌ معامله لغو شد.")
    context.user_data.clear()
    
    return ConversationHandler.END


def get_trade_conversation_handler() -> ConversationHandler:
    """دریافت ConversationHandler برای معامله"""
    return ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex(f'^{MENU_TRADE}$'), trade_start)
        ],
        states={
            SELECTING_PRODUCT: [
                CallbackQueryHandler(trade_product_selected, pattern=f'^{CALLBACK_TRADE_PRODUCT_PREFIX}(gold|coin|dollar)$'),
                CallbackQueryHandler(trade_cancelled, pattern=f'^{CALLBACK_BACK_TO_MAIN}$'),
            ],
            SELECTING_ACTION: [
                CallbackQueryHandler(
                    trade_action_selected,
                    pattern=f'^{CALLBACK_TRADE_PRODUCT_PREFIX}(gold|coin|dollar)_{CALLBACK_ACTION_BUY}$'
                ),
                CallbackQueryHandler(
                    trade_action_selected,
                    pattern=f'^{CALLBACK_TRADE_PRODUCT_PREFIX}(gold|coin|dollar)_{CALLBACK_ACTION_SELL}$'
                ),
                CallbackQueryHandler(trade_cancelled, pattern=f'^{CALLBACK_BACK_TO_MAIN}$'),
            ],
            SELECTING_METHOD: [
                CallbackQueryHandler(trade_method_selected, pattern=f'^{CALLBACK_METHOD_GRAM}$'),
                CallbackQueryHandler(trade_method_selected, pattern=f'^{CALLBACK_METHOD_RIAL}$'),
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
            MessageHandler(filters.Regex(f'^{MENU_CANCEL}$'), trade_cancelled),
        ],
        name="trade_conversation",
        persistent=False,
    )
