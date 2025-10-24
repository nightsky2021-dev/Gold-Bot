"""
Rate limiting utilities for the Telegram bot.

Prevents abuse by limiting the number of operations a user can perform
within specific time windows.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from django.utils import timezone
from django.core.cache import cache

from users.models import Profile
from .constants import (
    MAX_ORDERS_PER_HOUR,
    MAX_ORDERS_PER_DAY,
    MIN_ORDER_INTERVAL_SECONDS
)

logger = logging.getLogger('bot')


class RateLimiter:
    """
    Rate limiter for bot operations.
    
    Uses Django cache backend for distributed rate limiting.
    Falls back to in-memory storage if cache is not available.
    """
    
    # Fallback in-memory storage
    _memory_cache = defaultdict(list)
    
    @classmethod
    def check_order_limit(cls, profile: Profile) -> tuple[bool, Optional[str]]:
        """
        Check if user has exceeded order limits.
        
        Args:
            profile: User profile
            
        Returns:
            Tuple of (is_allowed, error_message)
            If is_allowed is False, error_message contains the reason.
        """
        now = timezone.now()
        user_key = f"orders_{profile.telegram_id}"
        
        try:
            # Try to get from cache
            order_times = cache.get(user_key, [])
        except Exception:
            # Fallback to memory cache
            order_times = cls._memory_cache.get(user_key, [])
        
        # Filter out old timestamps
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_orders = [t for t in order_times if t > day_ago]
        hourly_orders = [t for t in recent_orders if t > hour_ago]
        
        # Check hourly limit
        if len(hourly_orders) >= MAX_ORDERS_PER_HOUR:
            return False, (
                f"⚠️ شما به حد مجاز سفارشات ساعتی ({MAX_ORDERS_PER_HOUR} سفارش) رسیده‌اید.\n"
                "لطفاً یک ساعت دیگر تلاش کنید."
            )
        
        # Check daily limit
        if len(recent_orders) >= MAX_ORDERS_PER_DAY:
            return False, (
                f"⚠️ شما به حد مجاز سفارشات روزانه ({MAX_ORDERS_PER_DAY} سفارش) رسیده‌اید.\n"
                "لطفاً فردا تلاش کنید."
            )
        
        # Check minimum interval
        if recent_orders:
            last_order = max(recent_orders)
            time_since_last = (now - last_order).total_seconds()
            
            if time_since_last < MIN_ORDER_INTERVAL_SECONDS:
                wait_time = int(MIN_ORDER_INTERVAL_SECONDS - time_since_last)
                return False, (
                    f"⚠️ لطفاً {wait_time} ثانیه صبر کنید قبل از ثبت سفارش بعدی."
                )
        
        return True, None
    
    @classmethod
    def record_order(cls, profile: Profile) -> None:
        """
        Record an order for rate limiting.
        
        Args:
            profile: User profile
        """
        now = timezone.now()
        user_key = f"orders_{profile.telegram_id}"
        
        try:
            order_times = cache.get(user_key, [])
            order_times.append(now)
            
            # Keep only last 24 hours
            day_ago = now - timedelta(days=1)
            order_times = [t for t in order_times if t > day_ago]
            
            # Store for 25 hours (1 day + 1 hour buffer)
            cache.set(user_key, order_times, timeout=60 * 60 * 25)
            
        except Exception as e:
            # Fallback to memory cache
            logger.warning(f"Cache not available, using memory: {str(e)}")
            order_times = cls._memory_cache.get(user_key, [])
            order_times.append(now)
            
            # Keep only last 24 hours
            day_ago = now - timedelta(days=1)
            cls._memory_cache[user_key] = [t for t in order_times if t > day_ago]
    
    @classmethod
    def reset_user_limits(cls, profile: Profile) -> None:
        """
        Reset rate limits for a specific user.
        
        Useful for administrative purposes.
        
        Args:
            profile: User profile
        """
        user_key = f"orders_{profile.telegram_id}"
        
        try:
            cache.delete(user_key)
        except Exception:
            pass
        
        if user_key in cls._memory_cache:
            del cls._memory_cache[user_key]
        
        logger.info(f"Rate limits reset for user {profile.telegram_id}")


class ErrorHandler:
    """
    Centralized error handler for bot operations.
    """
    
    @staticmethod
    def format_error_message(error: Exception, context: str = "") -> str:
        """
        Format an error message for display to users.
        
        Args:
            error: The exception that occurred
            context: Additional context about where the error occurred
            
        Returns:
            User-friendly error message
        """
        error_type = type(error).__name__
        error_msg = str(error)
        
        logger.error(f"Bot error [{context}]: {error_type} - {error_msg}")
        
        # User-friendly messages for common errors
        if "validation" in error_msg.lower():
            return f"❌ خطا در اعتبارسنجی: {error_msg}"
        elif "connection" in error_msg.lower():
            return "❌ خطا در اتصال به سرور. لطفاً بعداً تلاش کنید."
        elif "timeout" in error_msg.lower():
            return "❌ زمان درخواست تمام شد. لطفاً دوباره تلاش کنید."
        else:
            return (
                "❌ متأسفانه خطایی رخ داد.\n"
                "لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
