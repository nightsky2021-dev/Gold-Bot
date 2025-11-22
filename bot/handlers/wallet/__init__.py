"""
Wallet handlers module.

This module provides a modular structure for wallet-related handlers:
- display: Wallet display and transaction history
- deposit: Deposit flow handlers
- withdraw: Withdrawal flow handlers
- utils: Common utilities

All handlers are exported from this module for easy importing.
"""

# Display handlers
from .display import (
    show_wallet,
    wallet_refresh,
    show_wallet_transactions,
    wallet_back,
)

# Deposit handlers
from .deposit import (
    deposit_start,
    deposit_system_bank_selected,
    deposit_amount_entered,
    deposit_source_bank_selected,
    deposit_receipt_uploaded,
    deposit_confirm,
    deposit_cancel,
    deposit_back_to_bank_select,
    deposit_back_to_amount,
    deposit_back_to_source_bank,
    deposit_back_to_receipt,
)

# Withdrawal handlers
from .withdraw import (
    withdraw_start,
    withdraw_currency_selected,
    withdraw_amount_entered,
    withdraw_bank_selected,
    withdraw_confirm,
    withdraw_cancel,
    withdraw_back_to_start,
    withdraw_back_to_amount,
    withdraw_back_to_bank,
)

# Utilities
from .utils import (
    safe_edit_message,
    get_callback_data,
    get_amount_from_text,
)

__all__ = [
    # Display
    'show_wallet',
    'wallet_refresh',
    'show_wallet_transactions',
    'wallet_back',
    # Deposit
    'deposit_start',
    'deposit_system_bank_selected',
    'deposit_amount_entered',
    'deposit_source_bank_selected',
    'deposit_receipt_uploaded',
    'deposit_confirm',
    'deposit_cancel',
    'deposit_back_to_bank_select',
    'deposit_back_to_amount',
    'deposit_back_to_source_bank',
    'deposit_back_to_receipt',
    # Withdrawal
    'withdraw_start',
    'withdraw_currency_selected',
    'withdraw_amount_entered',
    'withdraw_bank_selected',
    'withdraw_confirm',
    'withdraw_cancel',
    'withdraw_back_to_start',
    'withdraw_back_to_amount',
    'withdraw_back_to_bank',
    # Utilities
    'safe_edit_message',
    'get_callback_data',
    'get_amount_from_text',
]
