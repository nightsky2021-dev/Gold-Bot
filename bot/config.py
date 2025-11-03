"""
Bot configuration and settings.
"""

from dataclasses import dataclass
from typing import Final


@dataclass
class BotConfig:
    """Bot configuration settings."""
    
    # Limits
    MIN_ORDER_GRAMS: Final[float] = 0.01
    MIN_ORDER_RIAL: Final[float] = 10000
    MAX_ORDER_GRAMS: Final[float] = 1000.0
    MAX_ORDER_RIAL: Final[float] = 10_000_000_000
    
    # Timeouts
    PRICE_VALIDITY_SECONDS: Final[int] = 60
    SESSION_TIMEOUT_MINUTES: Final[int] = 15
    
    # Pagination
    HISTORY_PAGE_SIZE: Final[int] = 10
    TRANSACTION_PAGE_SIZE: Final[int] = 20
    
    # Display
    MAX_BANKS_PER_PAGE: Final[int] = 15


config = BotConfig()
