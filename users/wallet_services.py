"""
Wallet services for managing user balances and financial operations.

This module contains services for balance management, freezing/unfreezing
balances, and wallet-related operations.
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Profile

if TYPE_CHECKING:
    from trading.models import Transaction

logger = logging.getLogger('wallet')

# Withdrawal limits (in Rial and grams)
MIN_WITHDRAWAL_RIAL = Decimal('100000')  # 100,000 Rial minimum
MAX_WITHDRAWAL_RIAL = Decimal('100000000')  # 100 million Rial maximum
MIN_WITHDRAWAL_GOLD = Decimal('0.1')  # 0.1 gram minimum
MAX_WITHDRAWAL_GOLD = Decimal('1000')  # 1000 grams maximum
MIN_WITHDRAWAL_COIN = Decimal('1')  # 1 coin minimum
MAX_WITHDRAWAL_COIN = Decimal('100')  # 100 coins maximum
MIN_WITHDRAWAL_DOLLAR = Decimal('10')  # $10 minimum
MAX_WITHDRAWAL_DOLLAR = Decimal('50000')  # $50,000 maximum


class WalletService:
    """Service class for wallet and balance operations."""
    
    @staticmethod
    def _update_balance(profile: Profile, currency_type: str, amount: Decimal, operation: str) -> None:
        """
        Internal helper to update balance (available or frozen) for a currency.
        
        Supports both WalletBalance model (new) and legacy Profile fields.
        Updates both to maintain backward compatibility during transition.
        
        Args:
            profile: User profile.
            currency_type: Currency code ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to update (positive for add, negative for deduct).
            operation: 'available' or 'frozen' - which balance to update.
        """
        from trading.models import Currency, WalletBalance
        
        # Try to update WalletBalance (new dynamic system)
        try:
            currency = Currency.objects.get(code=currency_type, is_active=True)
            wallet_balance = profile.get_or_create_wallet_balance(currency_type)
            
            if operation == 'available':
                wallet_balance.available_balance += amount
            elif operation == 'frozen':
                wallet_balance.frozen_balance += amount
            
            wallet_balance.save()
        except (Currency.DoesNotExist, Exception) as e:
            logger.debug(f"Could not update WalletBalance for {currency_type}: {e}")
        
        # Also update legacy Profile fields for backward compatibility
        if currency_type == 'RIAL':
            if operation == 'available':
                profile.rial_balance += amount
            elif operation == 'frozen':
                profile.frozen_rial_balance += amount
        elif currency_type == 'GOLD':
            if operation == 'available':
                profile.gold_balance_grams += amount
            elif operation == 'frozen':
                profile.frozen_gold_balance += amount
        elif currency_type == 'COIN':
            if operation == 'available':
                profile.coin_balance += amount
            elif operation == 'frozen':
                profile.frozen_coin_balance += amount
        elif currency_type == 'DOLLAR':
            if operation == 'available':
                profile.dollar_balance += amount
            elif operation == 'frozen':
                profile.frozen_dollar_balance += amount
        
        profile.save()
    
    @staticmethod
    def get_wallet_balance(profile: Profile) -> Dict[str, Any]:
        """
        Get complete wallet balance information for a user.
        
        Now dynamically queries active currencies from the Currency model.
        Supports both new WalletBalance model and legacy Profile fields.
        
        Args:
            profile: User profile.
            
        Returns:
            Dict containing all balance information, keyed by currency code (lowercase).
        """
        from trading.models import Currency
        
        balances = {}
        
        # Get all active currencies
        active_currencies = Currency.objects.filter(is_active=True).order_by('display_order', 'code')
        
        for currency in active_currencies:
            currency_code_lower = currency.code.lower()
            available = profile.get_balance(currency.code)
            frozen = profile.get_frozen_balance(currency.code)
            
            balances[currency_code_lower] = {
                'available': available,
                'frozen': frozen,
                'total': available + frozen,
                'currency': currency  # Include currency object for metadata
            }
        
        return balances
    
    @staticmethod
    def validate_withdrawal_amount(currency_type: str, amount: Decimal) -> None:
        """
        Validate withdrawal amount against minimum and maximum limits.
        
        Args:
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to validate.
            
        Raises:
            ValidationError: If amount is outside allowed limits.
        """
        if currency_type == 'RIAL':
            if amount < MIN_WITHDRAWAL_RIAL:
                raise ValidationError(
                    f"حداقل مبلغ برداشت {MIN_WITHDRAWAL_RIAL:,.0f} ریال است."
                )
            if amount > MAX_WITHDRAWAL_RIAL:
                raise ValidationError(
                    f"حداکثر مبلغ برداشت {MAX_WITHDRAWAL_RIAL:,.0f} ریال است."
                )
        elif currency_type == 'GOLD':
            if amount < MIN_WITHDRAWAL_GOLD:
                raise ValidationError(
                    f"حداقل مقدار برداشت {MIN_WITHDRAWAL_GOLD} گرم طلا است."
                )
            if amount > MAX_WITHDRAWAL_GOLD:
                raise ValidationError(
                    f"حداکثر مقدار برداشت {MAX_WITHDRAWAL_GOLD} گرم طلا است."
                )
        elif currency_type == 'COIN':
            if amount < MIN_WITHDRAWAL_COIN:
                raise ValidationError(
                    f"حداقل مقدار برداشت {MIN_WITHDRAWAL_COIN} سکه است."
                )
            if amount > MAX_WITHDRAWAL_COIN:
                raise ValidationError(
                    f"حداکثر مقدار برداشت {MAX_WITHDRAWAL_COIN} سکه است."
                )
        elif currency_type == 'DOLLAR':
            if amount < MIN_WITHDRAWAL_DOLLAR:
                raise ValidationError(
                    f"حداقل مبلغ برداشت ${MIN_WITHDRAWAL_DOLLAR} است."
                )
            if amount > MAX_WITHDRAWAL_DOLLAR:
                raise ValidationError(
                    f"حداکثر مبلغ برداشت ${MAX_WITHDRAWAL_DOLLAR} است."
                )
    
    @staticmethod
    @transaction.atomic
    def freeze_balance(profile: Profile, currency_type: str, amount: Decimal) -> None:
        """
        Freeze balance for pending transactions.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to freeze.
            
        Raises:
            ValidationError: If insufficient balance or invalid currency.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Validate withdrawal limits
        WalletService.validate_withdrawal_amount(currency_type, amount)
        
        # Check sufficient balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            available = WalletService.get_available_balance(profile, currency_type)
            currency_name = WalletService.get_currency_display_name(currency_type)
            raise ValidationError(
                f"موجودی {currency_name} کافی نیست. "
                f"موجودی قابل استفاده: {available}, مقدار درخواستی: {amount}"
            )
        
        # Freeze the balance (move from available to frozen)
        WalletService._update_balance(profile, currency_type, -amount, 'available')
        WalletService._update_balance(profile, currency_type, amount, 'frozen')
        
        logger.info(
            f"Froze {amount} {currency_type} for user {profile.get_display_name()}"
        )
    
    @staticmethod
    @transaction.atomic
    def unfreeze_balance(profile: Profile, currency_type: str, amount: Decimal) -> None:
        """
        Unfreeze balance (return from frozen to available).
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to unfreeze.
            
        Raises:
            ValidationError: If insufficient frozen balance or invalid currency.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Check sufficient frozen balance with detailed error
        frozen_balance = WalletService.get_frozen_balance(profile, currency_type)
        if frozen_balance < amount:
            raise ValidationError(
                f"موجودی مسدود شده {currency_type} کافی نیست. "
                f"موجودی مسدود شده: {frozen_balance}, مقدار درخواستی: {amount}"
            )
        
        # Validate that unfreezing won't cause negative balances
        frozen_balance = WalletService.get_frozen_balance(profile, currency_type)
        if frozen_balance < amount:
            currency_name = WalletService.get_currency_display_name(currency_type)
            raise ValidationError(
                f"خطای سیستمی: موجودی مسدود شده {currency_name} کافی نیست. "
                f"این نباید رخ دهد. لطفاً با پشتیبانی تماس بگیرید."
            )
        
        # Unfreeze the balance (move from frozen to available)
        WalletService._update_balance(profile, currency_type, -amount, 'frozen')
        WalletService._update_balance(profile, currency_type, amount, 'available')
        
        logger.info(
            f"Unfroze {amount} {currency_type} for user {profile.get_display_name()} "
            f"(Profile ID: {profile.pk})"
        )
    
    @staticmethod
    @transaction.atomic
    def deduct_balance(profile: Profile, currency_type: str, amount: Decimal) -> None:
        """
        Deduct balance (for completed transactions).
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to deduct.
            
        Raises:
            ValidationError: If insufficient balance or invalid currency.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Check sufficient balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            available = WalletService.get_available_balance(profile, currency_type)
            currency_name = WalletService.get_currency_display_name(currency_type)
            raise ValidationError(
                f"موجودی {currency_name} کافی نیست. "
                f"موجودی فعلی: {available}, مقدار درخواستی: {amount}"
            )
        
        # Store old balance for logging
        old_balance = WalletService.get_available_balance(profile, currency_type)
        
        # Deduct the balance
        WalletService._update_balance(profile, currency_type, -amount, 'available')
        
        new_balance = WalletService.get_available_balance(profile, currency_type)
        logger.info(
            f"Deducted {amount} {currency_type} from user {profile.get_display_name()} "
            f"(Profile ID: {profile.pk}, Old Balance: {old_balance}, New Balance: {new_balance})"
        )
    
    @staticmethod
    @transaction.atomic
    def add_balance(profile: Profile, currency_type: str, amount: Decimal) -> None:
        """
        Add balance (for completed transactions).
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to add.
            
        Raises:
            ValidationError: If invalid currency or amount.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Store old balance for logging
        old_balance = WalletService.get_available_balance(profile, currency_type)
        
        # Add the balance
        WalletService._update_balance(profile, currency_type, amount, 'available')
        
        new_balance = WalletService.get_available_balance(profile, currency_type)
        logger.info(
            f"Added {amount} {currency_type} to user {profile.get_display_name()} "
            f"(Profile ID: {profile.pk}, Old Balance: {old_balance}, New Balance: {new_balance})"
        )
    
    @staticmethod
    def check_sufficient_balance(profile: Profile, currency_type: str, amount: Decimal) -> bool:
        """
        Check if user has sufficient balance for a transaction.
        
        Uses Profile.get_balance() which supports both dynamic and legacy systems.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to check.
            
        Returns:
            True if sufficient balance, False otherwise.
        """
        available_balance = profile.get_balance(currency_type)
        return available_balance >= amount
    
    @staticmethod
    def get_available_balance(profile: Profile, currency_type: str) -> Decimal:
        """
        Get available (unfrozen) balance for a currency type.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Available balance amount.
        """
        return profile.get_available_balance(currency_type)
    
    @staticmethod
    def get_frozen_balance(profile: Profile, currency_type: str) -> Decimal:
        """
        Get frozen balance for a currency type.
        
        Uses Profile.get_frozen_balance() which supports both dynamic and legacy systems.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Frozen balance amount.
        """
        return profile.get_frozen_balance(currency_type)
    
    @staticmethod
    @transaction.atomic
    def process_withdrawal(
        profile: Profile, 
        currency_type: str, 
        amount: Decimal,
        create_transaction: bool = True,
        withdrawal_request_id: Optional[int] = None
    ) -> Optional['Transaction']:
        """
        Process a withdrawal by deducting from frozen balance.
        
        This permanently removes the frozen balance (completes the withdrawal).
        The balance should have been frozen when the withdrawal request was created.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to withdraw.
            create_transaction: Whether to create a Transaction record (default True).
            withdrawal_request_id: ID of related WithdrawRequest (optional).
            
        Returns:
            Transaction instance if create_transaction=True, None otherwise.
            
        Raises:
            ValidationError: If insufficient frozen balance or invalid currency.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Check sufficient frozen balance
        frozen_balance = WalletService.get_frozen_balance(profile, currency_type)
        if frozen_balance < amount:
            raise ValidationError(
                f"موجودی مسدود شده {currency_type} کافی نیست. "
                f"موجودی مسدود شده: {frozen_balance}, مقدار درخواستی: {amount}"
            )
        
        # Validate sufficient frozen balance
        frozen_balance = WalletService.get_frozen_balance(profile, currency_type)
        if frozen_balance < amount:
            currency_name = WalletService.get_currency_display_name(currency_type)
            raise ValidationError(f"خطای سیستمی: موجودی مسدود شده {currency_name} کافی نیست.")
        
        # Deduct from frozen balance (permanently remove)
        WalletService._update_balance(profile, currency_type, -amount, 'frozen')
        
        logger.info(
            f"Processed withdrawal of {amount} {currency_type} for user {profile.get_display_name()} "
            f"(Profile ID: {profile.pk}, WithdrawRequest ID: {withdrawal_request_id})"
        )
        
        # Create Transaction record for audit trail
        transaction_obj: Optional['Transaction'] = None
        if create_transaction:
            from trading.models import Transaction
            from django.utils import timezone
            
            transaction_obj = Transaction.objects.create(
                profile=profile,
                transaction_type='WITHDRAW',
                currency=currency_type,
                amount=amount,
                status='COMPLETED',
                description=f"برداشت {amount} {WalletService.get_currency_display_name(currency_type)}",
                completed_at=timezone.now()
            )
            
            logger.info(
                f"Created Transaction {transaction_obj.pk} for withdrawal "  # type: ignore[attr-defined]
                f"(Profile ID: {profile.pk}, Amount: {amount} {currency_type})"
            )
        
        return transaction_obj
    
    @staticmethod
    def get_currency_display_name(currency_type: str) -> str:
        """
        Get display name for a currency type.
        
        Now queries the Currency model dynamically, with fallback to hardcoded names.
        
        Args:
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Persian display name for the currency.
        """
        try:
            from trading.models import Currency
            currency = Currency.objects.get(code=currency_type, is_active=True)
            return currency.get_display_name()
        except Currency.DoesNotExist:
            # Fallback to hardcoded names for backward compatibility
            currency_names = {
                'RIAL': 'ریال',
                'GOLD': 'طلا',
                'COIN': 'سکه',
                'DOLLAR': 'دلار'
            }
            return currency_names.get(currency_type, currency_type)
    
    @staticmethod
    def has_pending_transactions(profile: Profile, currency_type: Optional[str] = None) -> bool:
        """
        Check if user has pending transactions (deposits or withdrawals).
        
        Args:
            profile: User profile.
            currency_type: Optional currency type to check for specific currency.
            
        Returns:
            True if user has pending transactions, False otherwise.
        """
        from trading.models import Transaction, WithdrawRequest
        
        # Check for pending deposits
        pending_deposits_query = Transaction.objects.filter(
            profile=profile,
            transaction_type='DEPOSIT',
            status='PENDING'
        )
        
        if currency_type:
            pending_deposits_query = pending_deposits_query.filter(currency=currency_type)
        
        if pending_deposits_query.exists():
            return True
        
        # Check for pending withdrawals
        pending_withdrawals_query = WithdrawRequest.objects.filter(
            profile=profile,
            status__in=['PENDING', 'PROCESSING']
        )
        
        if currency_type:
            pending_withdrawals_query = pending_withdrawals_query.filter(currency=currency_type)
        
        return pending_withdrawals_query.exists()
    
    @staticmethod
    def format_wallet_display(profile: Profile) -> str:
        """
        Format wallet balance for display in Telegram.
        
        Now dynamically formats all active currencies using Currency model metadata.
        
        Args:
            profile: User profile.
            
        Returns:
            Formatted wallet display string.
        """
        balances = WalletService.get_wallet_balance(profile)
        
        text = "💼 *کیف پول شما:*\n\n"
        
        # Currency emoji mapping (fallback if not in currency metadata)
        currency_emojis = {
            'rial': '💵',
            'gold': '🪙',
            'coin': '🥇',
            'dollar': '💵',
        }
        
        # Format each currency dynamically
        for currency_code_lower, balance_data in balances.items():
            currency = balance_data.get('currency')
            if not currency:
                continue
            
            # Get emoji (could be stored in Currency model in future)
            emoji = currency_emojis.get(currency_code_lower, '💰')
            
            # Format based on decimal places
            decimal_places = currency.decimal_places
            symbol = currency.display_symbol
            name = currency.get_display_name()
            
            # Format based on decimal places
            if decimal_places == 0:
                total_formatted = f"{balance_data['total']:,.0f}"
                available_formatted = f"{balance_data['available']:,.0f}"
                frozen_formatted = f"{balance_data['frozen']:,.0f}"
            elif decimal_places == 2:
                total_formatted = f"{balance_data['total']:,.2f}"
                available_formatted = f"{balance_data['available']:,.2f}"
                frozen_formatted = f"{balance_data['frozen']:,.2f}"
            elif decimal_places == 4:
                total_formatted = f"{balance_data['total']:,.4f}"
                available_formatted = f"{balance_data['available']:,.4f}"
                frozen_formatted = f"{balance_data['frozen']:,.4f}"
            else:
                # Dynamic decimal places - use format with spec
                format_spec = f",.{decimal_places}f"
                total_formatted = f"{balance_data['total']:{format_spec}}"
                available_formatted = f"{balance_data['available']:{format_spec}}"
                frozen_formatted = f"{balance_data['frozen']:{format_spec}}"
            
            # Add symbol prefix/suffix based on currency
            if currency_code_lower == 'dollar':
                total_display = f"${total_formatted}"
                available_display = f"${available_formatted}"
                frozen_display = f"${frozen_formatted}"
            else:
                total_display = f"{total_formatted} {symbol}"
                available_display = f"{available_formatted} {symbol}"
                frozen_display = f"{frozen_formatted} {symbol}"
            
            text += f"{emoji} *موجودی {name}:*\n"
            text += f"├─ کل: {total_display}\n"
            text += f"├─ قابل استفاده: {available_display}\n"
            text += f"└─ مسدود شده: {frozen_display}\n\n"
        
        # Format date consistently - handle potential None value
        if profile.updated_at:
            last_update = profile.updated_at.strftime('%Y/%m/%d - %H:%M')
        else:
            last_update = "نامشخص"
        
        text += f"⏰ آخرین بروزرسانی: {last_update}"
        
        return text
