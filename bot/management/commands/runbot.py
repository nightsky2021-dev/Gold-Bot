"""
Management command to run the Telegram bot
Usage: python manage.py runbot
"""
import logging
from typing import Optional, Dict, Any
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand
from django.conf import settings

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)

from bot.constants import (
    # States
    WAITING_FOR_PHONE,
    SELECTING_PRODUCT_BUY,
    SELECTING_METHOD_BUY,
    ENTERING_AMOUNT_BUY,
    CONFIRMING_BUY,
    SELECTING_PRODUCT_SELL,
    SELECTING_METHOD_SELL,
    ENTERING_AMOUNT_SELL,
    CONFIRMING_SELL,
    # Callbacks
    CALLBACK_PRODUCT_BUY,
    CALLBACK_PRODUCT_SELL,
    CALLBACK_METHOD_RIAL,
    CALLBACK_METHOD_GRAM,
    CALLBACK_CONFIRM_YES,
    CALLBACK_CONFIRM_NO,
    CALLBACK_CANCEL,
    # Menu
    MENU_PRICES,
    MENU_BUY,
    MENU_SELL,
    MENU_PORTFOLIO,
    MENU_HISTORY,
    # Messages
    MSG_WELCOME_NEW,
    MSG_REGISTRATION_PENDING,
    MSG_NOT_APPROVED,
    MSG_WELCOME_APPROVED,
    MSG_INVALID_INPUT,
    MSG_INSUFFICIENT_BALANCE,
    MSG_ORDER_SUCCESS,
    MSG_CANCELLED,
    MSG_ERROR,
    # Buttons
    BTN_SHARE_CONTACT,
    BTN_RIAL,
    BTN_GRAM,
    BTN_CONFIRM,
    BTN_CANCEL,
    # Validation
    MIN_ORDER_RIAL,
    MIN_ORDER_GRAM,
    MAX_ORDER_RIAL,
    MAX_ORDER_GRAM,
)

from users.services import (
    get_profile_by_telegram_id,
    get_or_create_profile_by_telegram,
)
from trading.services import (
    get_active_products,
    get_product_by_id,
    calculate_buy_order,
    calculate_sell_order,
    create_order,
    get_user_orders,
    get_price_list,
)


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ==================== Helper Functions ====================

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """
    ایجاد صفحه کلید منوی اصلی
    """
    keyboard = [
        [MENU_PRICES],
        [MENU_BUY, MENU_SELL],
        [MENU_PORTFOLIO, MENU_HISTORY],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    """
    ایجاد صفحه کلید برای درخواست شماره تماس
    """
    keyboard = [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)


def format_number(number: Decimal) -> str:
    """
    فرمت کردن اعداد با جداکننده هزارگان
    """
    return f"{int(number):,}" if number == int(number) else f"{float(number):,.4f}"


# ==================== Start & Registration ====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[int]:
    """
    هندلر دستور /start - ورود و ثبت‌نام کاربران
    """
    user = update.effective_user
    telegram_id = str(user.id)
    
    # بررسی وجود پروفایل
    profile = get_profile_by_telegram_id(telegram_id)
    
    if profile is None:
        # کاربر جدید - درخواست شماره تماس
        await update.message.reply_text(
            MSG_WELCOME_NEW,
            reply_markup=get_contact_keyboard()
        )
        return WAITING_FOR_PHONE
    
    elif not profile.is_approved:
        # کاربر در انتظار تایید
        await update.message.reply_text(
            MSG_NOT_APPROVED,
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    else:
        # کاربر تایید شده - نمایش منوی اصلی
        await update.message.reply_text(
            MSG_WELCOME_APPROVED,
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END


async def receive_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    دریافت شماره تماس از کاربر و ثبت‌نام
    """
    contact = update.message.contact
    user = update.effective_user
    
    if contact.user_id != user.id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            reply_markup=get_contact_keyboard()
        )
        return WAITING_FOR_PHONE
    
    telegram_id = str(user.id)
    phone_number = contact.phone_number
    
    # ایجاد پروفایل
    profile, created = get_or_create_profile_by_telegram(
        telegram_id=telegram_id,
        phone_number=phone_number,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        telegram_username=user.username
    )
    
    if created:
        logger.info(f"New user registered: {telegram_id} - {phone_number}")
        await update.message.reply_text(
            MSG_REGISTRATION_PENDING,
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await update.message.reply_text(
            MSG_NOT_APPROVED,
            reply_markup=ReplyKeyboardRemove()
        )
    
    return ConversationHandler.END


# ==================== Menu Handlers ====================

async def show_prices(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    نمایش قیمت‌های لحظه‌ای
    """
    price_list = get_price_list()
    await update.message.reply_text(
        price_list,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def show_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    نمایش پورتفولیو کاربر
    """
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(MSG_NOT_APPROVED)
        return
    
    portfolio_text = f"""
📊 *پورتفولیوی شما*

💰 *موجودی ریالی:* `{profile.get_formatted_rial_balance()}` ریال

⚖️ *موجودی طلا:* `{profile.get_formatted_gold_balance()}` گرم

_آخرین به‌روزرسانی: {profile.updated_at.strftime('%Y-%m-%d %H:%M')}_
"""
    
    await update.message.reply_text(
        portfolio_text,
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    نمایش تاریخچه سفارشات
    """
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(MSG_NOT_APPROVED)
        return
    
    orders = get_user_orders(profile, limit=5)
    
    if not orders:
        await update.message.reply_text(
            "📜 شما هنوز سفارشی ثبت نکرده‌اید.",
            reply_markup=get_main_menu_keyboard()
        )
        return
    
    history_lines = ["📜 *تاریخچه ۵ سفارش اخیر شما:*\n"]
    
    for order in orders:
        status_emoji = {
            'PENDING': '⏳',
            'COMPLETED': '✅',
            'CANCELLED': '❌'
        }.get(order.status, '❓')
        
        type_emoji = '💰' if order.order_type == 'BUY' else '🛒'
        
        history_lines.append(f"{status_emoji} *سفارش #{order.id}*")
        history_lines.append(f"{type_emoji} {order.get_order_type_display()}: {order.product.name}")
        history_lines.append(f"   مقدار: `{order.get_formatted_quantity()}` گرم")
        history_lines.append(f"   مبلغ: `{order.get_formatted_total_amount()}` ریال")
        history_lines.append(f"   وضعیت: {order.get_status_display()}")
        history_lines.append(f"   تاریخ: {order.created_at.strftime('%Y-%m-%d %H:%M')}")
        history_lines.append("")
    
    await update.message.reply_text(
        "\n".join(history_lines),
        parse_mode='Markdown',
        reply_markup=get_main_menu_keyboard()
    )


# ==================== Buy Flow ====================

async def start_buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    شروع فرآیند خرید طلا
    """
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(MSG_NOT_APPROVED)
        return ConversationHandler.END
    
    products = get_active_products()
    
    if not products:
        await update.message.reply_text(
            "در حال حاضر محصولی برای فروش موجود نیست.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # ایجاد دکمه‌های انتخاب محصول
    keyboard = []
    for product in products:
        callback_data = CALLBACK_PRODUCT_BUY.format(product.id)
        button_text = f"{product.name} - {product.get_formatted_sell_price()} ریال/گرم"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CANCEL)])
    
    await update.message.reply_text(
        "💰 *خرید طلا*\n\nلطفاً محصول مورد نظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT_BUY


async def buy_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    محصول برای خرید انتخاب شد
    """
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ محصول یافت نشد.")
        return ConversationHandler.END
    
    # ذخیره محصول در context
    context.user_data['buy_product'] = product
    
    # انتخاب روش محاسبه
    keyboard = [
        [InlineKeyboardButton(BTN_RIAL, callback_data=CALLBACK_METHOD_RIAL)],
        [InlineKeyboardButton(BTN_GRAM, callback_data=CALLBACK_METHOD_GRAM)],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CANCEL)]
    ]
    
    await query.edit_message_text(
        f"شما *{product.name}* را انتخاب کردید.\n\n"
        f"قیمت فروش: `{product.get_formatted_sell_price()}` ریال/گرم\n\n"
        f"خرید را بر اساس کدام معیار انجام می‌دهید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD_BUY


async def buy_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    روش محاسبه برای خرید انتخاب شد
    """
    query = update.callback_query
    await query.answer()
    
    method = 'rial' if query.data == CALLBACK_METHOD_RIAL else 'gram'
    context.user_data['buy_method'] = method
    
    product = context.user_data.get('buy_product')
    
    if method == 'rial':
        prompt = f"لطفاً مبلغ مورد نظر را به ریال وارد کنید:\n\n" \
                 f"(حداقل: {format_number(MIN_ORDER_RIAL)} ریال)"
    else:
        prompt = f"لطفاً مقدار مورد نظر را به گرم وارد کنید:\n\n" \
                 f"(حداقل: {MIN_ORDER_GRAM} گرم)"
    
    await query.edit_message_text(prompt)
    
    return ENTERING_AMOUNT_BUY


async def buy_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    مقدار برای خرید وارد شد
    """
    try:
        amount = Decimal(update.message.text.replace(',', ''))
    except (InvalidOperation, ValueError):
        await update.message.reply_text(MSG_INVALID_INPUT)
        return ENTERING_AMOUNT_BUY
    
    method = context.user_data.get('buy_method')
    product = context.user_data.get('buy_product')
    
    # اعتبارسنجی مقدار
    if method == 'rial':
        if amount < MIN_ORDER_RIAL or amount > MAX_ORDER_RIAL:
            await update.message.reply_text(
                f"❌ مبلغ باید بین {format_number(MIN_ORDER_RIAL)} تا "
                f"{format_number(MAX_ORDER_RIAL)} ریال باشد."
            )
            return ENTERING_AMOUNT_BUY
    else:
        if amount < MIN_ORDER_GRAM or amount > MAX_ORDER_GRAM:
            await update.message.reply_text(
                f"❌ مقدار باید بین {MIN_ORDER_GRAM} تا "
                f"{format_number(MAX_ORDER_GRAM)} گرم باشد."
            )
            return ENTERING_AMOUNT_BUY
    
    # محاسبه جزئیات سفارش
    order_details = calculate_buy_order(product, method, amount)
    context.user_data['order_details'] = order_details
    
    # نمایش پیش‌فاکتور
    invoice = f"""
📋 *پیش‌فاکتور خرید*

🔸 محصول: *{order_details['product'].name}*
⚖️ مقدار: `{format_number(order_details['quantity_grams'])}` گرم
💵 قیمت هر گرم: `{format_number(order_details['price_per_gram'])}` ریال
💰 *مبلغ کل: `{format_number(order_details['total_amount'])}` ریال*

آیا تایید می‌کنید؟
"""
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CONFIRM_NO)]
    ]
    
    await update.message.reply_text(
        invoice,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_BUY


async def buy_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    خرید تایید شد
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    order_details = context.user_data.get('order_details')
    
    try:
        # ایجاد سفارش
        order = create_order(
            profile=profile,
            product=order_details['product'],
            order_type=order_details['order_type'],
            quantity_grams=order_details['quantity_grams'],
            price_per_gram=order_details['price_per_gram'],
            total_amount=order_details['total_amount']
        )
        
        await query.edit_message_text(
            MSG_ORDER_SUCCESS.format(order_id=order.id),
            parse_mode='Markdown'
        )
        
        # پاک کردن داده‌های موقت
        context.user_data.clear()
        
        # بازگشت به منوی اصلی
        await query.message.reply_text(
            "از منوی زیر می‌توانید ادامه دهید:",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error creating buy order: {e}")
        await query.edit_message_text(MSG_ERROR.format(str(e)))
    
    return ConversationHandler.END


# ==================== Sell Flow ====================

async def start_sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    شروع فرآیند فروش طلا
    """
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    
    if not profile or not profile.is_approved:
        await update.message.reply_text(MSG_NOT_APPROVED)
        return ConversationHandler.END
    
    products = get_active_products()
    
    if not products:
        await update.message.reply_text(
            "در حال حاضر محصولی برای خرید موجود نیست.",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END
    
    # ایجاد دکمه‌های انتخاب محصول
    keyboard = []
    for product in products:
        callback_data = CALLBACK_PRODUCT_SELL.format(product.id)
        button_text = f"{product.name} - {product.get_formatted_buy_price()} ریال/گرم"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
    
    keyboard.append([InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CANCEL)])
    
    await update.message.reply_text(
        "🛒 *فروش طلا*\n\nلطفاً محصول مورد نظر خود را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECTING_PRODUCT_SELL


async def sell_product_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    محصول برای فروش انتخاب شد
    """
    query = update.callback_query
    await query.answer()
    
    product_id = int(query.data.split('_')[-1])
    product = get_product_by_id(product_id)
    
    if not product:
        await query.edit_message_text("❌ محصول یافت نشد.")
        return ConversationHandler.END
    
    # ذخیره محصول در context
    context.user_data['sell_product'] = product
    
    # انتخاب روش محاسبه
    keyboard = [
        [InlineKeyboardButton(BTN_RIAL, callback_data=CALLBACK_METHOD_RIAL)],
        [InlineKeyboardButton(BTN_GRAM, callback_data=CALLBACK_METHOD_GRAM)],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CANCEL)]
    ]
    
    await query.edit_message_text(
        f"شما *{product.name}* را انتخاب کردید.\n\n"
        f"قیمت خرید ما: `{product.get_formatted_buy_price()}` ریال/گرم\n\n"
        f"فروش را بر اساس کدام معیار انجام می‌دهید؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return SELECTING_METHOD_SELL


async def sell_method_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    روش محاسبه برای فروش انتخاب شد
    """
    query = update.callback_query
    await query.answer()
    
    method = 'rial' if query.data == CALLBACK_METHOD_RIAL else 'gram'
    context.user_data['sell_method'] = method
    
    product = context.user_data.get('sell_product')
    
    if method == 'rial':
        prompt = f"لطفاً مبلغ مورد نظر را به ریال وارد کنید:\n\n" \
                 f"(حداقل: {format_number(MIN_ORDER_RIAL)} ریال)"
    else:
        prompt = f"لطفاً مقدار مورد نظر را به گرم وارد کنید:\n\n" \
                 f"(حداقل: {MIN_ORDER_GRAM} گرم)"
    
    await query.edit_message_text(prompt)
    
    return ENTERING_AMOUNT_SELL


async def sell_amount_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    مقدار برای فروش وارد شد
    """
    try:
        amount = Decimal(update.message.text.replace(',', ''))
    except (InvalidOperation, ValueError):
        await update.message.reply_text(MSG_INVALID_INPUT)
        return ENTERING_AMOUNT_SELL
    
    method = context.user_data.get('sell_method')
    product = context.user_data.get('sell_product')
    
    # اعتبارسنجی مقدار
    if method == 'rial':
        if amount < MIN_ORDER_RIAL or amount > MAX_ORDER_RIAL:
            await update.message.reply_text(
                f"❌ مبلغ باید بین {format_number(MIN_ORDER_RIAL)} تا "
                f"{format_number(MAX_ORDER_RIAL)} ریال باشد."
            )
            return ENTERING_AMOUNT_SELL
    else:
        if amount < MIN_ORDER_GRAM or amount > MAX_ORDER_GRAM:
            await update.message.reply_text(
                f"❌ مقدار باید بین {MIN_ORDER_GRAM} تا "
                f"{format_number(MAX_ORDER_GRAM)} گرم باشد."
            )
            return ENTERING_AMOUNT_SELL
    
    # محاسبه جزئیات سفارش
    order_details = calculate_sell_order(product, method, amount)
    context.user_data['order_details'] = order_details
    
    # نمایش پیش‌فاکتور
    invoice = f"""
📋 *پیش‌فاکتور فروش*

🔸 محصول: *{order_details['product'].name}*
⚖️ مقدار: `{format_number(order_details['quantity_grams'])}` گرم
💵 قیمت هر گرم: `{format_number(order_details['price_per_gram'])}` ریال
💰 *مبلغ دریافتی شما: `{format_number(order_details['total_amount'])}` ریال*

آیا تایید می‌کنید؟
"""
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=CALLBACK_CONFIRM_YES)],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=CALLBACK_CONFIRM_NO)]
    ]
    
    await update.message.reply_text(
        invoice,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    
    return CONFIRMING_SELL


async def sell_confirmed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    فروش تایید شد
    """
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    profile = get_profile_by_telegram_id(str(user.id))
    order_details = context.user_data.get('order_details')
    
    try:
        # ایجاد سفارش
        order = create_order(
            profile=profile,
            product=order_details['product'],
            order_type=order_details['order_type'],
            quantity_grams=order_details['quantity_grams'],
            price_per_gram=order_details['price_per_gram'],
            total_amount=order_details['total_amount']
        )
        
        await query.edit_message_text(
            MSG_ORDER_SUCCESS.format(order_id=order.id),
            parse_mode='Markdown'
        )
        
        # پاک کردن داده‌های موقت
        context.user_data.clear()
        
        # بازگشت به منوی اصلی
        await query.message.reply_text(
            "از منوی زیر می‌توانید ادامه دهید:",
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Error creating sell order: {e}")
        await query.edit_message_text(MSG_ERROR.format(str(e)))
    
    return ConversationHandler.END


# ==================== Cancel Handler ====================

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    لغو عملیات جاری
    """
    # پاک کردن داده‌های موقت
    context.user_data.clear()
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(MSG_CANCELLED)
        await update.callback_query.message.reply_text(
            "از منوی زیر می‌توانید ادامه دهید:",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            MSG_CANCELLED,
            reply_markup=get_main_menu_keyboard()
        )
    
    return ConversationHandler.END


# ==================== Error Handler ====================

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    مدیریت خطاها
    """
    logger.error(f"Update {update} caused error {context.error}")
    
    try:
        if update.effective_message:
            await update.effective_message.reply_text(
                MSG_ERROR.format("لطفاً دوباره تلاش کنید.")
            )
    except Exception as e:
        logger.error(f"Error in error_handler: {e}")


# ==================== Command Class ====================

class Command(BaseCommand):
    help = 'Run the Telegram bot'

    def handle(self, *args, **options):
        """
        اجرای ربات تلگرام
        """
        token = settings.TELEGRAM_BOT_TOKEN
        
        if not token:
            self.stdout.write(
                self.style.ERROR('TELEGRAM_BOT_TOKEN is not set in settings!')
            )
            return
        
        # ایجاد Application
        application = Application.builder().token(token).build()
        
        # ==================== Conversation Handlers ====================
        
        # Registration conversation
        registration_conv = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                WAITING_FOR_PHONE: [MessageHandler(filters.CONTACT, receive_contact)],
            },
            fallbacks=[CommandHandler('cancel', cancel)],
            name="registration",
            persistent=False
        )
        
        # Buy conversation
        buy_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f'^{MENU_BUY}$'), start_buy)],
            states={
                SELECTING_PRODUCT_BUY: [
                    CallbackQueryHandler(buy_product_selected, pattern=r'^buy_product_\d+$')
                ],
                SELECTING_METHOD_BUY: [
                    CallbackQueryHandler(buy_method_selected, pattern=f'^({CALLBACK_METHOD_RIAL}|{CALLBACK_METHOD_GRAM})$')
                ],
                ENTERING_AMOUNT_BUY: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, buy_amount_entered)
                ],
                CONFIRMING_BUY: [
                    CallbackQueryHandler(buy_confirmed, pattern=f'^{CALLBACK_CONFIRM_YES}$'),
                    CallbackQueryHandler(cancel, pattern=f'^{CALLBACK_CONFIRM_NO}$')
                ],
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern=f'^{CALLBACK_CANCEL}$'),
                CommandHandler('cancel', cancel)
            ],
            name="buy_conversation",
            persistent=False
        )
        
        # Sell conversation
        sell_conv = ConversationHandler(
            entry_points=[MessageHandler(filters.Regex(f'^{MENU_SELL}$'), start_sell)],
            states={
                SELECTING_PRODUCT_SELL: [
                    CallbackQueryHandler(sell_product_selected, pattern=r'^sell_product_\d+$')
                ],
                SELECTING_METHOD_SELL: [
                    CallbackQueryHandler(sell_method_selected, pattern=f'^({CALLBACK_METHOD_RIAL}|{CALLBACK_METHOD_GRAM})$')
                ],
                ENTERING_AMOUNT_SELL: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, sell_amount_entered)
                ],
                CONFIRMING_SELL: [
                    CallbackQueryHandler(sell_confirmed, pattern=f'^{CALLBACK_CONFIRM_YES}$'),
                    CallbackQueryHandler(cancel, pattern=f'^{CALLBACK_CONFIRM_NO}$')
                ],
            },
            fallbacks=[
                CallbackQueryHandler(cancel, pattern=f'^{CALLBACK_CANCEL}$'),
                CommandHandler('cancel', cancel)
            ],
            name="sell_conversation",
            persistent=False
        )
        
        # ==================== Add Handlers ====================
        
        application.add_handler(registration_conv)
        application.add_handler(buy_conv)
        application.add_handler(sell_conv)
        
        # Menu handlers
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PRICES}$'), show_prices))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_PORTFOLIO}$'), show_portfolio))
        application.add_handler(MessageHandler(filters.Regex(f'^{MENU_HISTORY}$'), show_history))
        
        # Error handler
        application.add_error_handler(error_handler)
        
        # ==================== Start Bot ====================
        
        self.stdout.write(self.style.SUCCESS('Starting bot...'))
        application.run_polling(allowed_updates=Update.ALL_TYPES)
