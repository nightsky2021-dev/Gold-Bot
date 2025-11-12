"""
Portal access handlers for Telegram bot.

Handles generating secure access links for the web portal.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from trading.portal_services import PortalTokenService
from bot.handlers.base import get_or_create_profile
from bot.constants import ERROR_NOT_APPROVED
from django.conf import settings

logger = logging.getLogger('bot.portal')


async def portal_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate and send portal access link to user.
    
    Command: /portal or button click
    """
    if not update.message or not update.effective_user:
        return
    
    # Get or create profile
    profile = await get_or_create_profile(update.effective_user)
    
    if not profile:
        await update.message.reply_text(
            "❌ خطا در دریافت اطلاعات کاربر.\n"
            "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
        return
    
    # Check if user is approved
    if not profile.is_approved:
        await update.message.reply_text(
            ERROR_NOT_APPROVED,
            parse_mode='Markdown'
        )
        return
    
    # Generate access token
    token = await sync_to_async(PortalTokenService.generate_token)(profile)
    
    # Get base URL from settings (or hardcode for now)
    base_url = getattr(settings, 'PORTAL_BASE_URL', 'https://yourdomain.com')
    portal_url = f"{base_url}/portal/auth/{token.token}/"
    
    # Send message with access link
    message = (
        "🌐 *دسترسی به پورتال معاملات*\n\n"
        "✅ لینک دسترسی شما آماده است!\n\n"
        "با کلیک روی دکمه زیر، می‌توانید به پورتال وب دسترسی پیدا کنید:\n\n"
        "📊 **امکانات پورتال:**\n"
        "   • مشاهده داشبورد کامل\n"
        "   • تاریخچه تراکنش‌ها با فیلترهای پیشرفته\n"
        "   • تحلیل سود و زیان\n"
        "   • صورتحساب کامل\n"
        "   • دریافت خروجی Excel و PDF\n\n"
        "⏰ این لینک برای 24 ساعت معتبر است.\n"
        "🔒 از این لینک به صورت شخصی استفاده کنید.\n\n"
        f"🔗 **لینک دسترسی:**\n{portal_url}\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 *نکته:* پورتال برای موبایل بهینه‌سازی شده است."
    )
    
    # Create inline keyboard with access button
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [InlineKeyboardButton("🌐 ورود به پورتال", url=portal_url)],
        [InlineKeyboardButton("🔄 لینک جدید", callback_data="portal_refresh")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    logger.info(f"Portal access link generated for user {profile.get_display_name()}")


async def portal_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for refreshing portal access link.
    
    Callback: portal_refresh
    """
    query = update.callback_query
    if not query or not update.effective_user:
        return
    
    await query.answer("در حال ایجاد لینک جدید...")
    
    # Get profile
    profile = await get_or_create_profile(update.effective_user)
    
    if not profile or not profile.is_approved:
        await query.edit_message_text(
            ERROR_NOT_APPROVED,
            parse_mode='Markdown'
        )
        return
    
    # Generate new token
    token = await sync_to_async(PortalTokenService.generate_token)(profile)
    
    # Get base URL
    base_url = getattr(settings, 'PORTAL_BASE_URL', 'https://yourdomain.com')
    portal_url = f"{base_url}/portal/auth/{token.token}/"
    
    # Update message
    message = (
        "🔄 *لینک جدید ایجاد شد!*\n\n"
        "✅ لینک دسترسی جدید شما آماده است.\n\n"
        f"🔗 **لینک دسترسی:**\n{portal_url}\n\n"
        "⏰ این لینک برای 24 ساعت معتبر است.\n"
        "🔒 از این لینک به صورت شخصی استفاده کنید.\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "💡 *نکته:* پورتال برای موبایل بهینه‌سازی شده است."
    )
    
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = [
        [InlineKeyboardButton("🌐 ورود به پورتال", url=portal_url)],
        [InlineKeyboardButton("🔄 لینک جدید", callback_data="portal_refresh")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        message,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )
    
    logger.info(f"Portal access link refreshed for user {profile.get_display_name()}")


async def portal_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show information about the portal.
    
    Command: /portal_info
    """
    if not update.message:
        return
    
    message = (
        "ℹ️ *درباره پورتال معاملات*\n\n"
        "پورتال وب، یک رابط کاربری پیشرفته برای مدیریت معاملات شماست.\n\n"
        "📊 **امکانات:**\n\n"
        "1️⃣ *داشبورد:*\n"
        "   • نمای کلی از پورتفولیو\n"
        "   • ارزش کل دارایی‌ها\n"
        "   • آخرین معاملات\n\n"
        "2️⃣ *تراکنش‌ها:*\n"
        "   • لیست کامل تراکنش‌ها\n"
        "   • فیلتر بر اساس محصول، تاریخ، نوع\n"
        "   • جستجو در تراکنش‌ها\n\n"
        "3️⃣ *سود و زیان:*\n"
        "   • تحلیل سود/زیان هر محصول\n"
        "   • محاسبه ROI\n"
        "   • بهترین و بدترین عملکردها\n\n"
        "4️⃣ *صورتحساب:*\n"
        "   • موجودی دارایی‌ها\n"
        "   • جریان نقدی\n"
        "   • آمار کامل معاملات\n\n"
        "5️⃣ *خروجی‌گیری:*\n"
        "   • دانلود Excel/CSV\n"
        "   • دانلود PDF\n"
        "   • آماده برای چاپ\n\n"
        "🔒 **امنیت:**\n"
        "   • لینک‌های دسترسی رمزنگاری شده\n"
        "   • اعتبار 24 ساعته\n"
        "   • جلسه امن 1 ساعته\n\n"
        "📱 **سازگاری:**\n"
        "   • موبایل، تبلت، دسکتاپ\n"
        "   • طراحی واکنش‌گرا\n"
        "   • سرعت بالا\n\n"
        "💡 برای دسترسی به پورتال، از دستور /portal استفاده کنید."
    )
    
    await update.message.reply_text(
        message,
        parse_mode='Markdown'
    )
