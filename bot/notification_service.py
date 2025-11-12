"""
Telegram notification service for sending messages to users.

This module provides utilities to send notifications via Telegram bot
to users about important events like account approval, order updates, etc.
"""

import logging
import asyncio
from typing import Optional
from django.conf import settings
from asgiref.sync import async_to_sync

logger = logging.getLogger('bot.notifications')


class TelegramNotificationService:
    """Service for sending Telegram notifications to users."""
    
    @staticmethod
    async def send_message_async(telegram_id: str, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send a message to a user via Telegram (async version).
        
        Args:
            telegram_id: User's Telegram ID
            message: Message text to send
            parse_mode: Telegram parse mode (Markdown or HTML)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            from telegram import Bot
            from telegram.error import TelegramError
            
            bot_token = settings.TELEGRAM_BOT_TOKEN
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return False
            
            bot = Bot(token=bot_token)
            
            try:
                await bot.send_message(
                    chat_id=telegram_id,
                    text=message,
                    parse_mode=parse_mode
                )
                logger.info(f"Notification sent successfully to user {telegram_id}")
                return True
                
            except TelegramError as e:
                logger.error(f"Failed to send Telegram message to {telegram_id}: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error in send_message_async: {str(e)}")
            return False
    
    @staticmethod
    def send_message(telegram_id: str, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Send a message to a user via Telegram (sync version).
        
        This wraps the async version for use in Django signals and sync contexts.
        
        Args:
            telegram_id: User's Telegram ID
            message: Message text to send
            parse_mode: Telegram parse mode (Markdown or HTML)
            
        Returns:
            bool: True if message sent successfully, False otherwise
        """
        try:
            # Create a new event loop for this thread if one doesn't exist
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Run the async function
            return loop.run_until_complete(
                TelegramNotificationService.send_message_async(telegram_id, message, parse_mode)
            )
        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}")
            return False
    
    @staticmethod
    def notify_user_approved(profile) -> bool:
        """
        Notify a user that their account has been approved.
        
        Args:
            profile: Profile instance
            
        Returns:
            bool: True if notification sent successfully
        """
        message = (
            "🎉 *خبر عالی!*\n\n"
            "حساب کاربری شما تأیید شد!\n\n"
            "✅ اکنون می‌توانید از تمام امکانات ربات استفاده کنید:\n"
            "   • خرید و فروش طلا، سکه و دلار\n"
            "   • مدیریت کیف پول\n"
            "   • واریز و برداشت وجه\n"
            "   • مشاهده تاریخچه معاملات\n"
            "   • دسترسی به پورتال وب\n\n"
            "🚀 *برای شروع، دستور /start را ارسال کنید.*\n\n"
            "💼 موفق باشید!"
        )
        
        return TelegramNotificationService.send_message(
            telegram_id=profile.telegram_id,
            message=message,
            parse_mode='Markdown'
        )
    
    @staticmethod
    def notify_user_disapproved(profile) -> bool:
        """
        Notify a user that their account approval has been revoked.
        
        Args:
            profile: Profile instance
            
        Returns:
            bool: True if notification sent successfully
        """
        message = (
            "⚠️ *اطلاعیه مهم*\n\n"
            "متأسفانه دسترسی حساب کاربری شما موقتاً محدود شده است.\n\n"
            "لطفاً برای اطلاعات بیشتر با پشتیبانی تماس بگیرید."
        )
        
        return TelegramNotificationService.send_message(
            telegram_id=profile.telegram_id,
            message=message,
            parse_mode='Markdown'
        )
    
    @staticmethod
    def notify_order_completed(profile, order) -> bool:
        """
        Notify a user that their order has been completed.
        
        Args:
            profile: Profile instance
            order: Order instance
            
        Returns:
            bool: True if notification sent successfully
        """
        order_type_text = "خرید" if order.order_type == 'BUY' else "فروش"
        
        message = (
            f"✅ *{order_type_text} شما انجام شد!*\n\n"
            f"📦 محصول: {order.product.name}\n"
            f"⚖️ مقدار: {order.quantity_grams}\n"
            f"💰 مبلغ: {order.total_amount:,.0f} ریال\n"
            f"🆔 شماره سفارش: #{order.id}\n\n"
            f"موجودی شما به‌روزرسانی شد."
        )
        
        return TelegramNotificationService.send_message(
            telegram_id=profile.telegram_id,
            message=message,
            parse_mode='Markdown'
        )
    
    @staticmethod
    def notify_withdrawal_approved(profile, withdrawal_request) -> bool:
        """
        Notify a user that their withdrawal request has been approved.
        
        Args:
            profile: Profile instance
            withdrawal_request: WithdrawalRequest instance
            
        Returns:
            bool: True if notification sent successfully
        """
        message = (
            f"✅ *درخواست برداشت شما تأیید شد!*\n\n"
            f"💰 مبلغ: {withdrawal_request.amount:,.0f}\n"
            f"🏦 حساب: {withdrawal_request.bank_account.bank_name}\n"
            f"🆔 شماره درخواست: #{withdrawal_request.id}\n\n"
            f"وجه به زودی به حساب شما واریز خواهد شد."
        )
        
        return TelegramNotificationService.send_message(
            telegram_id=profile.telegram_id,
            message=message,
            parse_mode='Markdown'
        )

