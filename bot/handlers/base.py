"""
Base utilities for bot handlers.
"""

import logging
from typing import Optional
from asgiref.sync import sync_to_async
from telegram import ReplyKeyboardMarkup
from users.models import Profile
from bot.constants import (
    MENU_PRICES,
    MENU_WALLET,
    MENU_ACCOUNT,
    MENU_HISTORY,
    MENU_PORTAL,
)

logger = logging.getLogger('bot.base')


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Generate main menu keyboard matching the keyboards.py layout."""
    keyboard = [
        [MENU_PRICES],
        [MENU_WALLET, MENU_ACCOUNT],
        [MENU_HISTORY, MENU_PORTAL],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def get_or_create_profile(telegram_user) -> Optional[Profile]:
    """Get or return None if user doesn't have a profile."""
    try:
        return await sync_to_async(
            Profile.objects.select_related('user').get
        )(telegram_id=str(telegram_user.id))
    except Profile.DoesNotExist:
        return None
