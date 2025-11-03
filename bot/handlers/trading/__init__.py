"""
Enhanced trading module with modular architecture.

This package contains all trading-related handlers organized by functionality.
"""

from .buy import buy_start
from .sell import sell_start
from .shared import (
    unified_product_selected,
    trade_method_selected,
    trade_amount_entered,
    trade_cancel
)
from .confirmation import buy_confirm, sell_confirm
from .base import handle_trade_action

# Export old names for backward compatibility
buy_product_selected = unified_product_selected
sell_product_selected = unified_product_selected

__all__ = [
    'buy_start',
    'buy_product_selected',
    'sell_start',
    'sell_product_selected',
    'unified_product_selected',
    'trade_method_selected',
    'trade_amount_entered',
    'trade_cancel',
    'buy_confirm',
    'sell_confirm',
    'handle_trade_action',
]
