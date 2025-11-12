"""
Authentication and registration handlers.

This module handles user authentication and initial bot interactions.
For the full registration flow (profile completion), see registration.py.
"""

import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from users.models import Profile
from bot.constants import (
    WELCOME_PENDING_USER,
    WELCOME_APPROVED_USER,
    BTN_SHARE_CONTACT,
)
from .base import get_or_create_profile, get_main_menu_keyboard

logger = logging.getLogger('bot.auth')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle /start command.
    
    This checks if the user exists:
    - If new user, shows registration welcome and contact button
    - If user exists but not approved, shows pending message
    - If user is approved, shows main menu with welcome message
    """
    if not update.message or not update.effective_user:
        return
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if profile is None:
        # New user - Show registration welcome message
        welcome_message = (
            "👋 *سلام! به ربات معاملات طلا خوش آمدید*\n\n"
            "برای استفاده از خدمات ما، لطفاً اطلاعات خود را تکمیل کنید.\n"
            "این فرآیند تنها چند دقیقه زمان می‌برد.\n\n"
            "🔒 *اطلاعات شما کاملاً محرمانه است*\n\n"
            "📱 *مرحله ۱ از ۳:* اشتراک شماره تماس\n\n"
            "لطفاً روی دکمه زیر کلیک کنید تا شماره تماس خود را با ما به اشتراک بگذارید.\n"
            "این برای احراز هویت و امنیت حساب شما ضروری است."
        )
        
        keyboard = [[KeyboardButton(BTN_SHARE_CONTACT, request_contact=True)]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        logger.info(f"New user {telegram_user.id} started registration process")
        return
        
    elif not profile.is_approved:
        # User registered but not approved
        # Show more detailed message with status
        await update.message.reply_text(
            WELCOME_PENDING_USER,
            parse_mode='Markdown'
        )
        logger.info(f"User {telegram_user.id} ({profile.phone_number}) waiting for approval")
        
    else:
        # Approved user - show main menu with personalized welcome
        display_name = await sync_to_async(profile.get_display_name)()
        welcome_msg = WELCOME_APPROVED_USER.format(name=display_name)
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=get_main_menu_keyboard(),
            parse_mode='Markdown'
        )
        logger.info(f"Approved user {telegram_user.id} ({profile.phone_number}) accessed bot")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.message:
        return
    
    help_text = (
        "📖 *راهنمای استفاده از ربات*\n\n"
        "• *📈 قیمت‌ها و معامله:* مشاهده قیمت‌های روز و خرید/فروش\n"
        "• *💼 کیف پول:* مشاهده موجودی، واریز و برداشت\n"
        "• *📋 تاریخچه:* مشاهده سفارشات و تراکنش‌ها\n"
        "• *👤 حساب من:* مدیریت پروفایل و اطلاعات کاربری\n"
        "• *🌐 پورتال وب:* دسترسی به پنل کاربری پیشرفته\n\n"
        "برای شروع، از منوی پایین گزینه مورد نظر را انتخاب کنید.\n\n"
        "💡 *دستورات مفید:*\n"
        "• /portal - دریافت لینک دسترسی به پورتال\n"
        "• /portal_info - اطلاعات بیشتر درباره پورتال\n"
        "• /help - نمایش این راهنما"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle contact sharing.
    
    This is now handled by the registration conversation handler.
    This function is kept for backward compatibility but shouldn't be called
    during normal registration flow.
    """
    if not update.message or not update.message.contact:
        return
    
    # Inform user that registration is handled through /start
    await update.message.reply_text(
        "لطفاً از دستور /start برای ثبت‌نام استفاده کنید.",
        parse_mode='Markdown'
    )
