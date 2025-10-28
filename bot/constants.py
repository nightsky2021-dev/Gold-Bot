"""
ثوابت و حالت‌های مورد استفاده در ربات تلگرام
"""
from typing import Final
from decimal import Decimal

# حالت‌های ConversationHandler
(
    SELECTING_PRODUCT,
    SELECTING_ACTION,
    SELECTING_METHOD,
    ENTERING_AMOUNT,
    CONFIRMING_TRADE,
    ENTERING_FIRST_NAME,
    ENTERING_LAST_NAME,
    ENTERING_NATIONAL_CODE,
) = range(8)

# متن‌های منو اصلی
MENU_TRADE = "💎 معامله"
MENU_PORTFOLIO = "👛 کیف پول"
MENU_HISTORY = "📋 تاریخچه"
MENU_REFRESH = "🔄 به‌روزرسانی قیمت‌ها"
MENU_CANCEL = "❌ بازگشت"

# Callback Data Patterns - قیمت‌ها
CALLBACK_PRICE_GOLD = "price_gold"
CALLBACK_PRICE_COIN = "price_coin"
CALLBACK_PRICE_DOLLAR = "price_dollar"
CALLBACK_PRICE_ALL = "price_all"
CALLBACK_PRICE_REFRESH = "price_refresh_"  # + product_code
CALLBACK_BACK_TO_PRICES_MENU = "back_to_prices_menu"

# Callback Data Patterns - معامله
CALLBACK_TRADE_PRODUCT_PREFIX = "trade_"
CALLBACK_ACTION_BUY = "action_buy"
CALLBACK_ACTION_SELL = "action_sell"
CALLBACK_METHOD_GRAM = "method_gram"
CALLBACK_METHOD_RIAL = "method_rial"

# Product Codes (for callbacks) - Must match trading.models.Product constants
PRODUCT_GOLD = "GOLD_ABSHODEH"
PRODUCT_COIN = "COIN_FULL"
PRODUCT_DOLLAR = "DOLLAR"

# ==================== Account & Wallet Management States ====================
# Account Management States
VIEWING_PROFILE: Final[str] = "viewing_profile"
MANAGING_BANK_ACCOUNTS: Final[str] = "managing_bank_accounts"
ADDING_BANK_ACCOUNT: Final[str] = "adding_bank_account"
ENTERING_BANK_NAME: Final[str] = "entering_bank_name"
ENTERING_ACCOUNT_NUMBER: Final[str] = "entering_account_number"
ENTERING_ACCOUNT_HOLDER: Final[str] = "entering_account_holder"
ENTERING_ACCOUNT_TYPE: Final[str] = "entering_account_type"

# Deposit States
SELECTING_DEPOSIT_CURRENCY: Final[str] = "selecting_deposit_currency"
ENTERING_DEPOSIT_AMOUNT: Final[str] = "entering_deposit_amount"
SELECTING_DEPOSIT_BANK: Final[str] = "selecting_deposit_bank"
UPLOADING_RECEIPT: Final[str] = "uploading_receipt"
CONFIRMING_DEPOSIT: Final[str] = "confirming_deposit"

# Withdraw States
SELECTING_WITHDRAW_CURRENCY: Final[str] = "selecting_withdraw_currency"
ENTERING_WITHDRAW_AMOUNT: Final[str] = "entering_withdraw_amount"
SELECTING_WITHDRAW_BANK: Final[str] = "selecting_withdraw_bank"
CONFIRMING_WITHDRAW: Final[str] = "confirming_withdraw"

# ==================== Callback Data for Account & Wallet ====================
CALLBACK_ACCOUNT_PROFILE: Final[str] = "account_profile"
CALLBACK_ACCOUNT_BANKCARDS: Final[str] = "account_bankcards"
CALLBACK_ACCOUNT_BALANCES: Final[str] = "account_balances"
CALLBACK_ACCOUNT_TRANSACTIONS: Final[str] = "account_transactions"

CALLBACK_WALLET_DEPOSIT: Final[str] = "wallet_deposit"
CALLBACK_WALLET_WITHDRAW: Final[str] = "wallet_withdraw"
CALLBACK_WALLET_BALANCES: Final[str] = "wallet_balances"
CALLBACK_WALLET_TRANSACTIONS: Final[str] = "wallet_transactions"

CALLBACK_CURRENCY_RIAL: Final[str] = "currency_rial"
CALLBACK_CURRENCY_GOLD: Final[str] = "currency_gold"
CALLBACK_CURRENCY_COIN: Final[str] = "currency_coin"
CALLBACK_CURRENCY_DOLLAR: Final[str] = "currency_dollar"

CALLBACK_SELECT_BANK_PREFIX: Final[str] = "select_bank_"
CALLBACK_ADD_BANK_ACCOUNT: Final[str] = "add_bank_account"
CALLBACK_REMOVE_BANK_PREFIX: Final[str] = "remove_bank_"

# Generic callback data
CALLBACK_BACK_TO_MAIN: Final[str] = "back_to_main"
CALLBACK_CONFIRM_YES: Final[str] = "confirm_yes"
CALLBACK_CONFIRM_NO: Final[str] = "confirm_no"

# ==================== Menu Buttons ====================
MENU_ACCOUNT: Final[str] = "👤 حساب کاربری"
MENU_WALLET: Final[str] = "💼 کیف پول"
MENU_PRICES: Final[str] = "📈 قیمت‌ها"

# ==================== Currency Types ====================
CURRENCY_TYPES: Final[dict] = {
    'RIAL': 'ریال',
    'GOLD': 'طلا',
    'COIN': 'سکه',
    'DOLLAR': 'دلار',
}

# ==================== Iranian Banks ====================
IRANIAN_BANKS: Final[list] = [
    'ملی ایران', 'ملت', 'تجارت', 'صادرات', 'سپه',
    'رفاه', 'پاسارگاد', 'پارسیان', 'اقتصاد نوین', 'سامان',
    'سینا', 'کارآفرین', 'آینده', 'شهر', 'دی',
    'صنعت و معدن', 'توسعه تعاون', 'قوامین', 'مهر اقتصاد', 'حکمت ایرانیان'
]
