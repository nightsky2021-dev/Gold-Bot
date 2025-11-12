"""
Professional registration handler with complete profile collection.

This module handles the complete user registration process:
1. Phone number collection (via contact sharing)
2. Full name collection
3. National code collection
4. Profile confirmation
5. Submission for admin approval
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler
from django.contrib.auth.models import User
from django.db import transaction
from asgiref.sync import sync_to_async

from users.models import Profile
from users.validators import check_national_code_format
from bot.constants import (
    BTN_SHARE_CONTACT,
    BTN_CONFIRM,
    BTN_CANCEL,
    CONFIRM_PREFIX,
    CANCEL_PREFIX,
    ERROR_GENERAL,
    REG_COLLECT_CONTACT,
    REG_COLLECT_NAME,
    REG_COLLECT_NATIONAL_CODE,
    REG_CONFIRM_PROFILE,
)

logger = logging.getLogger('bot.registration')


# ==================== Messages ====================
REGISTRATION_WELCOME = (
    "👋 *سلام! به ربات معاملات طلا خوش آمدید*\n\n"
    "برای استفاده از خدمات ما، لطفاً اطلاعات خود را تکمیل کنید.\n"
    "این فرآیند تنها چند دقیقه زمان می‌برد.\n\n"
    "🔒 *اطلاعات شما کاملاً محرمانه است*\n\n"
    "📱 *مرحله ۱ از ۳:* اشتراک شماره تماس\n\n"
    "لطفاً روی دکمه زیر کلیک کنید تا شماره تماس خود را با ما به اشتراک بگذارید.\n"
    "این برای احراز هویت و امنیت حساب شما ضروری است."
)

REGISTRATION_ASK_NAME = (
    "✅ *شماره تماس شما دریافت شد*\n\n"
    "📝 *مرحله ۲ از ۳:* نام و نام خانوادگی\n\n"
    "لطفاً نام و نام خانوادگی کامل خود را وارد کنید:\n\n"
    "💡 *مثال:* علی احمدی\n\n"
    "⚠️ توجه: نام باید دقیقاً همان نامی باشد که روی کارت ملی و حساب بانکی شما ثبت شده است."
)

REGISTRATION_ASK_NATIONAL_CODE = (
    "✅ *نام شما ثبت شد*\n\n"
    "🆔 *مرحله ۳ از ۳:* کد ملی\n\n"
    "لطفاً کد ملی 10 رقمی خود را وارد کنید:\n\n"
    "💡 *مثال:* 1234567890\n\n"
    "⚠️ توجه: کد ملی برای احراز هویت و تطابق با اطلاعات بانکی شما ضروری است."
)

REGISTRATION_CONFIRM_PROFILE = (
    "📋 *تأیید اطلاعات ثبت‌نام*\n\n"
    "لطفاً اطلاعات خود را بررسی کنید:\n\n"
    "👤 *نام:* {first_name}\n"
    "👤 *نام خانوادگی:* {last_name}\n"
    "📱 *شماره تماس:* {phone}\n"
    "🆔 *کد ملی:* {national_code}\n\n"
    "⚠️ *توجه مهم:* اطلاعات باید دقیقاً با مدارک شناسایی شما مطابقت داشته باشد.\n\n"
    "آیا اطلاعات فوق صحیح است؟"
)

REGISTRATION_SUCCESS = (
    "✅ *ثبت‌نام شما با موفقیت انجام شد!*\n\n"
    "📋 *خلاصه اطلاعات:*\n"
    "👤 نام: {full_name}\n"
    "📱 شماره تماس: {phone}\n"
    "🆔 کد ملی: {national_code}\n\n"
    "⏳ *وضعیت حساب:* در انتظار تأیید\n\n"
    "کارشناسان ما در اسرع وقت اطلاعات شما را بررسی می‌کنند.\n"
    "پس از تأیید حساب، می‌توانید:\n"
    "   • خرید و فروش طلا، سکه و دلار\n"
    "   • مدیریت کیف پول خود\n"
    "   • واریز و برداشت وجه\n\n"
    "🔔 به محض تأیید حساب، به شما اطلاع‌رسانی خواهد شد.\n\n"
    "💬 *سوالی دارید؟* با پشتیبانی تماس بگیرید."
)

REGISTRATION_CANCELLED = (
    "❌ *ثبت‌نام لغو شد*\n\n"
    "اطلاعات شما ذخیره نشد.\n"
    "برای شروع مجدد، دستور /start را ارسال کنید."
)

ERROR_INVALID_CONTACT = (
    "❌ *خطا در دریافت شماره تماس*\n\n"
    "لطفاً شماره تماس خودتان را ارسال کنید.\n"
    "از دکمه زیر استفاده کنید."
)

ERROR_NAME_TOO_SHORT = (
    "❌ *نام وارد شده خیلی کوتاه است*\n\n"
    "لطفاً نام و نام خانوادگی کامل خود را وارد کنید.\n\n"
    "💡 مثال: علی احمدی"
)

ERROR_NAME_INVALID = (
    "❌ *نام وارد شده نامعتبر است*\n\n"
    "نام باید شامل حروف فارسی یا انگلیسی باشد.\n"
    "لطفاً نام صحیح خود را وارد کنید.\n\n"
    "💡 مثال: علی احمدی"
)

ERROR_NATIONAL_CODE_EXISTS = (
    "❌ *کد ملی قبلاً ثبت شده است*\n\n"
    "این کد ملی قبلاً در سیستم ثبت شده است.\n"
    "اگر حساب کاربری دارید، از دستور /start استفاده کنید.\n\n"
    "اگر مشکلی دارید، با پشتیبانی تماس بگیرید."
)


async def check_user_is_new(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if the user is new and needs registration.
    This is used as a filter for the conversation handler.
    """
    if not update.effective_user:
        return False
    
    telegram_user = update.effective_user
    
    # Check if user already exists
    @sync_to_async
    def check_user_exists():
        return Profile.objects.filter(telegram_id=str(telegram_user.id)).exists()
    
    user_exists = await check_user_exists()
    return not user_exists  # Return True only if user is NEW


async def registration_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Start the registration process for new users only.
    
    This function should only be called for users who don't exist in the system.
    The conversation handler uses a filter to ensure this.
    """
    if not update.message or not update.effective_user:
        return ConversationHandler.END
    
    # Show welcome message with contact request
    keyboard = [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
    
    await update.message.reply_text(
        REGISTRATION_WELCOME,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return REG_COLLECT_CONTACT


async def registration_contact_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle contact sharing."""
    if not update.message or not update.message.contact or not update.effective_user or context.user_data is None:
        return ConversationHandler.END
    
    contact = update.message.contact
    telegram_user = update.effective_user
    
    # Verify it's the user's own contact
    if contact.user_id != telegram_user.id:
        await update.message.reply_text(
            ERROR_INVALID_CONTACT,
            parse_mode='Markdown'
        )
        return REG_COLLECT_CONTACT
    
    # Check if phone number already exists
    @sync_to_async
    def check_phone_exists():
        return Profile.objects.filter(phone_number=contact.phone_number).exists()
    
    if await check_phone_exists():
        await update.message.reply_text(
            "❌ این شماره تماس قبلاً ثبت شده است.\n"
            "برای ورود از دستور /start استفاده کنید.",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END
    
    # Store contact info in context
    context.user_data['phone_number'] = contact.phone_number
    context.user_data['telegram_id'] = str(telegram_user.id)
    context.user_data['telegram_username'] = telegram_user.username or ""
    context.user_data['telegram_first_name'] = telegram_user.first_name or ""
    context.user_data['telegram_last_name'] = telegram_user.last_name or ""
    
    # Ask for full name
    await update.message.reply_text(
        REGISTRATION_ASK_NAME,
        reply_markup=ReplyKeyboardRemove(),
        parse_mode='Markdown'
    )
    
    return REG_COLLECT_NAME


async def registration_name_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle full name input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
    
    full_name = update.message.text.strip()
    
    # Validate name length
    if len(full_name) < 3:
        await update.message.reply_text(
            ERROR_NAME_TOO_SHORT,
            parse_mode='Markdown'
        )
        return REG_COLLECT_NAME
    
    # Basic validation - check if it contains letters
    if not any(c.isalpha() for c in full_name):
        await update.message.reply_text(
            ERROR_NAME_INVALID,
            parse_mode='Markdown'
        )
        return REG_COLLECT_NAME
    
    # Split name into first and last name
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    # Store name in context
    context.user_data['first_name'] = first_name
    context.user_data['last_name'] = last_name
    
    # Ask for national code
    await update.message.reply_text(
        REGISTRATION_ASK_NATIONAL_CODE,
        parse_mode='Markdown'
    )
    
    return REG_COLLECT_NATIONAL_CODE


async def registration_national_code_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle national code input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
    
    national_code = update.message.text.strip().replace(' ', '').replace('-', '')
    
    # Validate national code format
    is_valid, error_msg = check_national_code_format(national_code)
    if not is_valid:
        await update.message.reply_text(
            f"❌ *خطا در کد ملی*\n\n{error_msg}\n\nلطفاً دوباره تلاش کنید:",
            parse_mode='Markdown'
        )
        return REG_COLLECT_NATIONAL_CODE
    
    # Check if national code already exists
    @sync_to_async
    def check_national_code_exists():
        return Profile.objects.filter(national_code=national_code).exists()
    
    if await check_national_code_exists():
        await update.message.reply_text(
            ERROR_NATIONAL_CODE_EXISTS,
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    
    # Store national code
    context.user_data['national_code'] = national_code
    
    # Show confirmation
    confirm_text = REGISTRATION_CONFIRM_PROFILE.format(
        first_name=context.user_data.get('first_name', ''),
        last_name=context.user_data.get('last_name', ''),
        phone=context.user_data.get('phone_number', ''),
        national_code=national_code
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}registration")],
        [InlineKeyboardButton("🔄 ویرایش اطلاعات", callback_data="edit_registration")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}registration")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return REG_CONFIRM_PROFILE


async def registration_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and save the registration."""
    query = update.callback_query
    if not query or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    await query.answer()
    
    try:
        # Extract data from context
        phone_number = context.user_data.get('phone_number')
        telegram_id = context.user_data.get('telegram_id')
        telegram_username = context.user_data.get('telegram_username', '')
        first_name = context.user_data.get('first_name')
        last_name = context.user_data.get('last_name')
        national_code = context.user_data.get('national_code')
        
        if not all([phone_number, telegram_id, first_name, national_code]):
            await query.edit_message_text(
                ERROR_GENERAL,
                parse_mode='Markdown'
            )
            return ConversationHandler.END
        
        # Create user and profile
        @sync_to_async
        def create_user_and_profile():
            with transaction.atomic():
                # Create Django User
                username = f"tg_{telegram_id}"
                user = User.objects.create_user(
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                )
                
                # Create Profile
                profile = Profile.objects.create(
                    user=user,
                    telegram_id=telegram_id,
                    telegram_username=telegram_username,
                    phone_number=phone_number,
                    national_code=national_code,
                    is_approved=False  # Requires admin approval
                )
                return profile
        
        profile = await create_user_and_profile()
        
        # Notify admins about new registration
        try:
            from trading.notifications import AdminNotificationService
            await sync_to_async(AdminNotificationService.notify_new_user_registration)(profile)
        except Exception as e:
            logger.warning(f"Failed to send admin notification: {str(e)}")
        
        # Send success message
        success_msg = REGISTRATION_SUCCESS.format(
            full_name=f"{first_name} {last_name}",
            phone=phone_number,
            national_code=national_code
        )
        
        await query.edit_message_text(
            success_msg,
            parse_mode='Markdown'
        )
        
        logger.info(f"New user registered: {phone_number} - {first_name} {last_name} (TG: {telegram_id})")
        
        # Clear user data
        context.user_data.clear()
        
        return ConversationHandler.END
        
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        await query.edit_message_text(
            ERROR_GENERAL,
            parse_mode='Markdown'
        )
        return ConversationHandler.END


async def registration_edit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit request - restart from name collection."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
    
    await query.answer()
    
    # Keep phone and telegram info, but restart from name
    await query.edit_message_text(
        REGISTRATION_ASK_NAME,
        parse_mode='Markdown'
    )
    
    return REG_COLLECT_NAME


async def registration_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the registration process."""
    if context.user_data is None:
        return ConversationHandler.END
    
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            REGISTRATION_CANCELLED,
            parse_mode='Markdown'
        )
    elif update.message:
        await update.message.reply_text(
            REGISTRATION_CANCELLED,
            reply_markup=ReplyKeyboardRemove(),
            parse_mode='Markdown'
        )
    
    # Clear user data
    context.user_data.clear()
    
    logger.info(f"Registration cancelled by user {update.effective_user.id if update.effective_user else 'unknown'}")
    
    return ConversationHandler.END

