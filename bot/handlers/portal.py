"""
Portal access handlers for Telegram bot.

Handles generating secure access links for the web portal.
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from asgiref.sync import sync_to_async

from trading.portal_services import PortalTokenService
from bot.handlers.base import get_or_create_profile, get_main_menu_keyboard
from bot.constants import ERROR_NOT_APPROVED, CALLBACK_PORTAL_REFRESH, ERROR_GENERAL
from django.conf import settings

logger = logging.getLogger('bot.portal')


async def portal_access(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Generate and send portal access link to user.
    
    Command: /portal or button click
    """
    try:
        if not update.message or not update.effective_user:
            logger.warning("portal_access called without message or effective_user")
            return
        
        # Get or create profile
        profile = await get_or_create_profile(update.effective_user)
        
        if not profile:
            await update.message.reply_text(
                "❌ خطا در دریافت اطلاعات کاربر.\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.warning(f"Profile not found for user {update.effective_user.id}")
            return
        
        # Check if user is approved
        if not profile.is_approved:
            await update.message.reply_text(
                ERROR_NOT_APPROVED,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"Portal access denied for unapproved user {profile.get_display_name()}")
            return
        
        # Generate access token
        try:
            token = await sync_to_async(PortalTokenService.generate_token)(profile)
        except Exception as e:
            logger.error(f"Error generating portal token: {str(e)}", exc_info=True)
            await update.message.reply_text(
                "❌ خطا در ایجاد لینک دسترسی.\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Get base URL from settings
        base_url = getattr(settings, 'PORTAL_BASE_URL', 'https://yourdomain.com')
        if base_url == 'https://yourdomain.com':
            logger.warning("PORTAL_BASE_URL not configured, using default placeholder")
        
        portal_url = f"{base_url}/portal/auth/{token.token}/"
        
        # Check if URL is localhost (Telegram doesn't support localhost URLs in buttons)
        is_localhost = 'localhost' in base_url or '127.0.0.1' in base_url
        
        # Send message with access link
        if is_localhost:
            message = (
                "🌐 *دسترسی به پورتال معاملات*\n\n"
                "✅ لینک دسترسی شما آماده است!\n\n"
                "📊 **امکانات پورتال:**\n"
                "   • مشاهده داشبورد کامل\n"
                "   • تاریخچه تراکنش‌ها با فیلترهای پیشرفته\n"
                "   • تحلیل سود و زیان\n"
                "   • صورتحساب کامل\n"
                "   • دریافت خروجی Excel و PDF\n\n"
                "⏰ این لینک برای 24 ساعت معتبر است.\n"
                "🔒 از این لینک به صورت شخصی استفاده کنید.\n\n"
                f"🔗 **لینک دسترسی:**\n`{portal_url}`\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "💡 *نکته:* لینک را کپی کرده و در مرورگر خود باز کنید.\n"
                "⚠️ *برای استفاده عمومی، PORTAL_BASE_URL را به یک آدرس عمومی تغییر دهید.*"
            )
        else:
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
        
        # Only add URL button if not localhost (Telegram doesn't support localhost URLs)
        keyboard = []
        if not is_localhost:
            keyboard.append([InlineKeyboardButton("🌐 ورود به پورتال", url=portal_url)])
        keyboard.append([InlineKeyboardButton("🔄 لینک جدید", callback_data=CALLBACK_PORTAL_REFRESH)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"Portal access link generated for user {profile.get_display_name()}")
        
    except Exception as e:
        logger.error(f"Unexpected error in portal_access: {str(e)}", exc_info=True)
        if update.message:
            await update.message.reply_text(
                ERROR_GENERAL,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )


async def portal_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle callback for refreshing portal access link.
    
    Callback: portal_refresh
    """
    try:
        query = update.callback_query
        if not query or not update.effective_user:
            logger.warning("portal_refresh_callback called without query or effective_user")
            return
        
        await query.answer("در حال ایجاد لینک جدید...")
        
        # Get profile
        profile = await get_or_create_profile(update.effective_user)
        
        if not profile or not profile.is_approved:
            await query.edit_message_text(
                ERROR_NOT_APPROVED,
                parse_mode='Markdown'
            )
            logger.info(f"Portal refresh denied for user {update.effective_user.id}")
            return
        
        # Generate new token
        try:
            token = await sync_to_async(PortalTokenService.generate_token)(profile)
        except Exception as e:
            logger.error(f"Error generating portal token in refresh: {str(e)}", exc_info=True)
            await query.answer("❌ خطا در ایجاد لینک جدید", show_alert=True)
            return
        
        # Get base URL
        base_url = getattr(settings, 'PORTAL_BASE_URL', 'https://yourdomain.com')
        portal_url = f"{base_url}/portal/auth/{token.token}/"
        
        # Check if URL is localhost
        is_localhost = 'localhost' in base_url or '127.0.0.1' in base_url
        
        # Update message
        if is_localhost:
            message = (
                "🔄 *لینک جدید ایجاد شد!*\n\n"
                "✅ لینک دسترسی جدید شما آماده است.\n\n"
                f"🔗 **لینک دسترسی:**\n`{portal_url}`\n\n"
                "⏰ این لینک برای 24 ساعت معتبر است.\n"
                "🔒 از این لینک به صورت شخصی استفاده کنید.\n\n"
                "━━━━━━━━━━━━━━━━\n"
                "💡 *نکته:* لینک را کپی کرده و در مرورگر خود باز کنید."
            )
        else:
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
        
        # Only add URL button if not localhost
        keyboard = []
        if not is_localhost:
            keyboard.append([InlineKeyboardButton("🌐 ورود به پورتال", url=portal_url)])
        keyboard.append([InlineKeyboardButton("🔄 لینک جدید", callback_data=CALLBACK_PORTAL_REFRESH)])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            message,
            reply_markup=reply_markup,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
        logger.info(f"Portal access link refreshed for user {profile.get_display_name()}")
        
    except Exception as e:
        logger.error(f"Unexpected error in portal_refresh_callback: {str(e)}", exc_info=True)
        if update.callback_query:
            try:
                await update.callback_query.answer("❌ خطا در ایجاد لینک جدید", show_alert=True)
            except:
                pass


async def portal_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Show information about the portal.
    
    Command: /portal_info
    """
    try:
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
            "💡 برای دسترسی به پورتال، از دکمه 🌐 پورتال وب در منوی اصلی یا دستور /portal استفاده کنید."
        )
        
        await update.message.reply_text(
            message,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in portal_info: {str(e)}", exc_info=True)
        if update.message:
            await update.message.reply_text(
                ERROR_GENERAL,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
