"""
Authentication and registration handlers.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from django.contrib.auth.models import User
from django.db import transaction
from asgiref.sync import sync_to_async

from users.models import Profile
from bot.constants import (
    BTN_SHARE_CONTACT,
    WELCOME_NEW_USER,
    WELCOME_PENDING_USER,
    WELCOME_APPROVED_USER,
    REGISTRATION_SUCCESS,
    ERROR_GENERAL,
)
from .base import get_or_create_profile, get_main_menu_keyboard

logger = logging.getLogger('bot.auth')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command."""
    if not update.message or not update.effective_user:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if profile is None:
        # New user - request contact
        keyboard = [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            WELCOME_NEW_USER,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    elif not profile.is_approved:
        # User registered but not approved
        await update.message.reply_text(
            WELCOME_PENDING_USER,
            parse_mode='Markdown'
        )
    else:
        # Approved user - show main menu
        display_name = await sync_to_async(profile.get_display_name)()
        welcome_msg = WELCOME_APPROVED_USER.format(name=display_name)
        await update.message.reply_text(
            welcome_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.message:
        return
    
    help_text = (
        "📖 *راهنمای استفاده از ربات*\n\n"
        "• *📈 قیمت‌ها و معامله:* مشاهده قیمت‌های روز و خرید/فروش\n"
        "• *💼 کیف پول:* مشاهده موجودی، واریز و برداشت\n"
        "• *📋 تاریخچه:* مشاهده سفارشات و تراکنش‌ها\n"
        "• *⚙️ تنظیمات:* پروفایل، حساب‌های بانکی و آمار\n\n"
        "برای شروع، از منوی پایین گزینه مورد نظر را انتخاب کنید."
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle contact sharing for registration."""
    if not update.message or not update.message.contact or not update.effective_user:
        return
    
    contact = update.message.contact
    telegram_user = update.effective_user
    
    # Check if contact is user's own contact
    if contact.user_id != telegram_user.id:
        await update.message.reply_text(
            "❌ لطفاً شماره تماس خودتان را ارسال کنید.",
            parse_mode='Markdown'
        )
        return
    
    # Check if user already exists
    existing_profile = await get_or_create_profile(telegram_user)
    if existing_profile:
        await update.message.reply_text(
            "شما قبلاً ثبت‌نام کرده‌اید.",
            parse_mode='Markdown'
        )
        return
    
    # Create user and profile
    try:
        @sync_to_async
        def create_user_and_profile():
            with transaction.atomic():
                # Create Django User
                username = f"tg_{telegram_user.id}"
                user = User.objects.create_user(
                    username=username,
                    first_name=telegram_user.first_name or "",
                    last_name=telegram_user.last_name or "",
                )
                
                # Create Profile
                profile = Profile.objects.create(
                    user=user,
                    telegram_id=str(telegram_user.id),
                    telegram_username=telegram_user.username or "",
                    phone_number=contact.phone_number,
                    is_approved=False
                )
                return profile
        
        profile = await create_user_and_profile()
        
        success_msg = REGISTRATION_SUCCESS.format(phone=contact.phone_number)
        await update.message.reply_text(
            success_msg,
            parse_mode='Markdown'
        )
        
        logger.info(f"New user registered: {profile.phone_number} (TG: {telegram_user.id})")
            
    except Exception as e:
        logger.error(f"Error during registration: {str(e)}")
        await update.message.reply_text(
            ERROR_GENERAL,
            parse_mode='Markdown'
        )
