"""
Profile management handlers for updating user information.
"""

import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from asgiref.sync import sync_to_async
from django.core.exceptions import ValidationError

from users.models import Profile
from users.validators import check_national_code_format
from bot.constants import (
    ERROR_NOT_APPROVED,
    ERROR_GENERAL,
    BTN_CONFIRM,
    BTN_CANCEL,
    CONFIRM_PREFIX,
    CANCEL_PREFIX,
)
from .base import get_or_create_profile

logger = logging.getLogger('bot.profile')

# Conversation states
PROFILE_UPDATE_CHOICE = 0
PROFILE_UPDATE_NAME = 1
PROFILE_UPDATE_NATIONAL_CODE = 2
PROFILE_UPDATE_CONFIRM = 3


async def profile_update_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start profile update conversation."""
    query = update.callback_query
    if not query or not update.effective_user:
        return ConversationHandler.END
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    # Show update options
    keyboard = [
        [InlineKeyboardButton("🏷️ به‌روزرسانی نام", callback_data="update_name")],
        [InlineKeyboardButton("🆔 به‌روزرسانی کد ملی", callback_data="update_national_code")],
        [InlineKeyboardButton("❌ انصراف", callback_data=f"{CANCEL_PREFIX}profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "🔧 *به‌روزرسانی پروفایل*\n\n"
        "لطفاً گزینه مورد نظر خود را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return PROFILE_UPDATE_CHOICE


async def profile_update_choice_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle profile update choice."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None:
        return ConversationHandler.END
    
    await query.answer()
    
    if query.data == "update_name":
        await query.edit_message_text(
            "🏷️ *به‌روزرسانی نام*\n\n"
            "لطفاً نام و نام خانوادگی کامل خود را وارد کنید:\n"
            "(مثال: علی احمدی)",
            parse_mode='Markdown'
        )
        return PROFILE_UPDATE_NAME
    
    elif query.data == "update_national_code":
        await query.edit_message_text(
            "🆔 *به‌روزرسانی کد ملی*\n\n"
            "لطفاً کد ملی 10 رقمی خود را وارد کنید:\n"
            "(مثال: 1234567890)",
            parse_mode='Markdown'
        )
        return PROFILE_UPDATE_NATIONAL_CODE
    
    return ConversationHandler.END


async def profile_name_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle name input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
    
    full_name = update.message.text.strip()
    
    # Basic validation
    if len(full_name) < 3:
        await update.message.reply_text(
            "❌ نام وارد شده خیلی کوتاه است. لطفاً نام کامل خود را وارد کنید.",
            parse_mode='Markdown'
        )
        return PROFILE_UPDATE_NAME
    
    # Split name
    name_parts = full_name.split(maxsplit=1)
    first_name = name_parts[0]
    last_name = name_parts[1] if len(name_parts) > 1 else ""
    
    context.user_data['new_first_name'] = first_name
    context.user_data['new_last_name'] = last_name
    
    # Show confirmation
    confirm_msg = (
        f"✅ *تأیید اطلاعات*\n\n"
        f"نام: {first_name}\n"
        f"نام خانوادگی: {last_name}\n\n"
        f"آیا اطلاعات صحیح است؟"
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}name")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return PROFILE_UPDATE_CONFIRM


async def profile_national_code_entered(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle national code input."""
    if not update.message or not update.message.text or context.user_data is None:
        return ConversationHandler.END
    
    national_code = update.message.text.strip().replace(' ', '').replace('-', '')
    
    # Validate national code
    is_valid, error_msg = check_national_code_format(national_code)
    if not is_valid:
        await update.message.reply_text(
            f"❌ {error_msg}\n\nلطفاً دوباره تلاش کنید:",
            parse_mode='Markdown'
        )
        return PROFILE_UPDATE_NATIONAL_CODE
    
    context.user_data['new_national_code'] = national_code
    
    # Show confirmation
    confirm_msg = (
        f"✅ *تأیید کد ملی*\n\n"
        f"کد ملی: {national_code}\n\n"
        f"آیا کد ملی صحیح است؟"
    )
    
    keyboard = [
        [InlineKeyboardButton(BTN_CONFIRM, callback_data=f"{CONFIRM_PREFIX}national_code")],
        [InlineKeyboardButton(BTN_CANCEL, callback_data=f"{CANCEL_PREFIX}profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        confirm_msg,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    return PROFILE_UPDATE_CONFIRM


async def profile_update_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm and save profile updates."""
    query = update.callback_query
    if not query or not query.data or context.user_data is None or not update.effective_user:
        return ConversationHandler.END
    
    await query.answer()
    
    telegram_user = update.effective_user
    profile = await get_or_create_profile(telegram_user)
    
    if not profile:
        await query.edit_message_text(ERROR_NOT_APPROVED, parse_mode='Markdown')
        return ConversationHandler.END
    
    try:
        if query.data == f"{CONFIRM_PREFIX}name":
            # Update name
            first_name = context.user_data.get('new_first_name', '')
            last_name = context.user_data.get('new_last_name', '')
            
            @sync_to_async
            def update_name():
                profile.user.first_name = first_name
                profile.user.last_name = last_name
                profile.user.save(update_fields=['first_name', 'last_name'])
            
            await update_name()
            
            success_msg = (
                f"✅ *نام با موفقیت به‌روزرسانی شد*\n\n"
                f"نام جدید: {first_name} {last_name}"
            )
            
        elif query.data == f"{CONFIRM_PREFIX}national_code":
            # Update national code
            national_code = context.user_data.get('new_national_code', '')
            
            @sync_to_async
            def update_national_code():
                profile.national_code = national_code
                profile.save(update_fields=['national_code'])
            
            await update_national_code()
            
            success_msg = (
                f"✅ *کد ملی با موفقیت به‌روزرسانی شد*\n\n"
                f"کد ملی جدید: {national_code}"
            )
        else:
            await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
            return ConversationHandler.END
        
        await query.edit_message_text(success_msg, parse_mode='Markdown')
        context.user_data.clear()
        return ConversationHandler.END
        
    except ValidationError as e:
        await query.edit_message_text(
            f"❌ خطا در به‌روزرسانی: {str(e)}",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        await query.edit_message_text(ERROR_GENERAL, parse_mode='Markdown')
        return ConversationHandler.END


async def profile_update_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel profile update conversation."""
    query = update.callback_query
    if not query or context.user_data is None:
        return ConversationHandler.END
    
    await query.answer()
    
    await query.edit_message_text(
        "❌ به‌روزرسانی پروفایل لغو شد.",
        parse_mode='Markdown'
    )
    context.user_data.clear()
    
    return ConversationHandler.END

