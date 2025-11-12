"""
Telegram bot handlers module.
All conversation handlers organized by feature.
"""

from .auth import (
    start, 
    help_command, 
    handle_contact,
)
from .prices import (
    show_prices,
    handle_product_price_view,
    handle_product_price_all,
    handle_price_refresh,
    handle_back_to_prices_menu,
)
from .trading import (
    # Buy handlers
    buy_start,
    buy_product_selected,
    buy_confirm,
    # Sell handlers
    sell_start,
    sell_confirm,
    # Unified handlers
    trade_method_selected,
    trade_amount_entered,
    trade_cancel,
    handle_trade_action,
)
from .wallet import (
    show_wallet,
    show_wallet_transactions,
    # Deposit
    deposit_start,
    deposit_currency_selected,
    deposit_amount_entered,
    deposit_receipt_uploaded,
    deposit_confirm,
    deposit_cancel,
    # Withdraw
    withdraw_start,
    withdraw_currency_selected,
    withdraw_amount_entered,
    withdraw_bank_selected,
    withdraw_confirm,
    withdraw_cancel,
)
from .bank import (
    show_bank_accounts,
    bank_account_add_start,
    bank_account_bank_selected,
    bank_account_holder_entered,
    bank_account_number_entered,
    bank_account_add_confirm,
    bank_account_add_cancel,
)
from .settings import (
    show_settings,
    show_profile,
    show_statistics,
)
from .profile import (
    profile_update_start,
    profile_update_choice_selected,
    profile_name_entered,
    profile_national_code_entered,
    profile_update_confirm,
    profile_update_cancel,
)
from .menu import (
    show_account,
    show_history,
    cancel,
)
from .base import (
    get_or_create_profile,
    get_main_menu_keyboard,
)

__all__ = [
    # Auth
    'start', 'help_command', 'handle_contact',
    # Prices
    'show_prices', 'handle_product_price_view', 'handle_product_price_all',
    'handle_price_refresh', 'handle_back_to_prices_menu',
    # Trading
    'buy_start', 'buy_product_selected', 'buy_confirm',
    'sell_start', 'sell_confirm',
    'trade_method_selected', 'trade_amount_entered', 'trade_cancel',
    'handle_trade_action',
    # Wallet
    'show_wallet', 'show_wallet_transactions',
    'deposit_start', 'deposit_currency_selected', 'deposit_amount_entered',
    'deposit_receipt_uploaded', 'deposit_confirm', 'deposit_cancel',
    'withdraw_start', 'withdraw_currency_selected', 'withdraw_amount_entered',
    'withdraw_bank_selected', 'withdraw_confirm', 'withdraw_cancel',
    # Bank
    'show_bank_accounts', 'bank_account_add_start', 'bank_account_bank_selected',
    'bank_account_holder_entered', 'bank_account_number_entered',
    'bank_account_add_confirm', 'bank_account_add_cancel',
    # Settings
    'show_settings', 'show_profile', 'show_statistics',
    # Profile Update
    'profile_update_start', 'profile_update_choice_selected',
    'profile_name_entered', 'profile_national_code_entered',
    'profile_update_confirm', 'profile_update_cancel',
    # Menu
    'show_account', 'show_history', 'cancel',
    # Base
    'get_or_create_profile', 'get_main_menu_keyboard',
]
