# Wallet Handlers Module Structure

This directory contains a modular, well-organized structure for wallet-related handlers in the Telegram bot.

## Directory Structure

```
wallet/
├── __init__.py          # Main exports - all handlers exported here
├── display.py          # Wallet display and transaction history
├── deposit.py          # Complete deposit flow handlers
├── withdraw.py         # Complete withdrawal flow handlers
├── utils.py            # Common utilities (safe_edit_message, etc.)
└── README.md           # This file
```

## Module Responsibilities

### `display.py`
Handles wallet display and transaction viewing:
- `show_wallet()` - Display wallet with balances and action buttons
- `wallet_refresh()` - Refresh wallet display with latest balances
- `show_wallet_transactions()` - Show transaction history
- `wallet_back()` - Return to main wallet display

### `deposit.py`
Complete deposit flow with multiple steps:
- **Entry Point**: `deposit_start()` - Shows system bank accounts
- **Flow Steps**:
  - `deposit_system_bank_selected()` - System bank selection
  - `deposit_amount_entered()` - Amount input and validation
  - `deposit_source_bank_selected()` - User's source bank selection
  - `deposit_receipt_uploaded()` - Receipt image upload
  - `deposit_confirm()` - Final confirmation and transaction creation
- **Navigation**:
  - `deposit_back_to_bank_select()` - Back to bank selection
  - `deposit_back_to_amount()` - Back to amount entry
  - `deposit_back_to_source_bank()` - Back to source bank selection
  - `deposit_back_to_receipt()` - Back to receipt upload
- **Cancellation**: `deposit_cancel()` - Cancel deposit flow

### `withdraw.py`
Complete withdrawal flow:
- **Entry Point**: `withdraw_start()` - Currency selection (Rial only)
- **Flow Steps**:
  - `withdraw_currency_selected()` - Currency selection handler
  - `withdraw_amount_entered()` - Amount input and validation
  - `withdraw_bank_selected()` - Bank account selection
  - `withdraw_confirm()` - Final confirmation and withdrawal request creation
- **Navigation**:
  - `withdraw_back_to_start()` - Back to start
  - `withdraw_back_to_amount()` - Back to amount entry
  - `withdraw_back_to_bank()` - Back to bank selection
- **Cancellation**: `withdraw_cancel()` - Cancel withdrawal flow

### `utils.py`
Common utilities used across wallet handlers:
- `safe_edit_message()` - Safely edit messages, handling "not modified" errors
- `get_callback_data()` - Extract numeric ID from callback data
- `get_amount_from_text()` - Parse amount from user input text

## Key Design Principles

1. **Separation of Concerns**: Each module has a single, clear responsibility
2. **Modularity**: Handlers are organized by feature (display, deposit, withdraw)
3. **Reusability**: Common utilities are extracted to avoid duplication
4. **Maintainability**: Clear structure makes it easy to find and modify handlers
5. **Backward Compatibility**: Main `wallet.py` re-exports all handlers

## Usage

All handlers are exported from `bot.handlers.wallet`:

```python
from bot.handlers.wallet import (
    show_wallet,
    deposit_start,
    withdraw_start,
    # ... etc
)
```

Or from the main wallet module (backward compatible):

```python
from bot.handlers.wallet import (
    show_wallet,
    deposit_start,
    withdraw_start,
    # ... etc
)
```

## Dependencies

- `bot.constants` - Conversation states and message constants
- `bot.handlers.base` - Base utilities like `get_or_create_profile`
- `bot.utils.wallet_helpers` - Error handling and flow management
- `users.services` - WalletService for wallet operations
- `trading.services` - TransactionService, WithdrawalService, BankAccountService

## Future Improvements

- Consider extracting flow state management to a separate module
- Add type hints throughout for better IDE support
- Consider using dataclasses for flow context data
- Add unit tests for each module
