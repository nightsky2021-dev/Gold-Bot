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
    def get_wallet_balance(profile: Profile) -> Dict[str, Any]:
        """
        Get complete wallet balance information for a user.
        
        Note: In the Profile model:
        - rial_balance, gold_balance_grams, etc. represent AVAILABLE (unfrozen) balance
        - frozen_*_balance fields represent FROZEN balance
        - Total = Available + Frozen
        
        Args:
            profile: User profile.
            
        Returns:
            Dict containing all balance information.
        """
        return {
            'rial': {
                'available': profile.rial_balance,
                'frozen': profile.frozen_rial_balance,
                'total': profile.rial_balance + profile.frozen_rial_balance
            },
            'gold': {
                'available': profile.gold_balance_grams,
                'frozen': profile.frozen_gold_balance,
                'total': profile.gold_balance_grams + profile.frozen_gold_balance
            },
            'coin': {
                'available': profile.coin_balance,
                'frozen': profile.frozen_coin_balance,
                'total': profile.coin_balance + profile.frozen_coin_balance
            },
            'dollar': {
                'available': profile.dollar_balance,
                'frozen': profile.frozen_dollar_balance,
                'total': profile.dollar_balance + profile.frozen_dollar_balance
            }
        }
    
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
        
        # Freeze the balance
        if currency_type == 'RIAL':
            profile.rial_balance -= amount
            profile.frozen_rial_balance += amount
        elif currency_type == 'GOLD':
            profile.gold_balance_grams -= amount
            profile.frozen_gold_balance += amount
        elif currency_type == 'COIN':
            profile.coin_balance -= amount
            profile.frozen_coin_balance += amount
        elif currency_type == 'DOLLAR':
            profile.dollar_balance -= amount
            profile.frozen_dollar_balance += amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
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
        if currency_type == 'RIAL':
            if profile.frozen_rial_balance < amount:
                raise ValidationError(
                    f"خطای سیستمی: موجودی مسدود شده ریال کافی نیست. "
                    f"این نباید رخ دهد. لطفاً با پشتیبانی تماس بگیرید."
                )
            profile.frozen_rial_balance -= amount
            profile.rial_balance += amount
        elif currency_type == 'GOLD':
            if profile.frozen_gold_balance < amount:
                raise ValidationError(
                    f"خطای سیستمی: موجودی مسدود شده طلا کافی نیست. "
                    f"این نباید رخ دهد. لطفاً با پشتیبانی تماس بگیرید."
                )
            profile.frozen_gold_balance -= amount
            profile.gold_balance_grams += amount
        elif currency_type == 'COIN':
            if profile.frozen_coin_balance < amount:
                raise ValidationError(
                    f"خطای سیستمی: موجودی مسدود شده سکه کافی نیست. "
                    f"این نباید رخ دهد. لطفاً با پشتیبانی تماس بگیرید."
                )
            profile.frozen_coin_balance -= amount
            profile.coin_balance += amount
        elif currency_type == 'DOLLAR':
            if profile.frozen_dollar_balance < amount:
                raise ValidationError(
                    f"خطای سیستمی: موجودی مسدود شده دلار کافی نیست. "
                    f"این نباید رخ دهد. لطفاً با پشتیبانی تماس بگیرید."
                )
            profile.frozen_dollar_balance -= amount
            profile.dollar_balance += amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
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
        if currency_type == 'RIAL':
            profile.rial_balance -= amount
        elif currency_type == 'GOLD':
            profile.gold_balance_grams -= amount
        elif currency_type == 'COIN':
            profile.coin_balance -= amount
        elif currency_type == 'DOLLAR':
            profile.dollar_balance -= amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
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
        if currency_type == 'RIAL':
            profile.rial_balance += amount
        elif currency_type == 'GOLD':
            profile.gold_balance_grams += amount
        elif currency_type == 'COIN':
            profile.coin_balance += amount
        elif currency_type == 'DOLLAR':
            profile.dollar_balance += amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
        new_balance = WalletService.get_available_balance(profile, currency_type)
        logger.info(
            f"Added {amount} {currency_type} to user {profile.get_display_name()} "
            f"(Profile ID: {profile.pk}, Old Balance: {old_balance}, New Balance: {new_balance})"
        )
    
    @staticmethod
    def check_sufficient_balance(profile: Profile, currency_type: str, amount: Decimal) -> bool:
        """
        Check if user has sufficient balance for a transaction.
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            amount: Amount to check.
            
        Returns:
            True if sufficient balance, False otherwise.
        """
        if currency_type == 'RIAL':
            return profile.rial_balance >= amount
        elif currency_type == 'GOLD':
            return profile.gold_balance_grams >= amount
        elif currency_type == 'COIN':
            return profile.coin_balance >= amount
        elif currency_type == 'DOLLAR':
            return profile.dollar_balance >= amount
        else:
            return False
    
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
        
        Args:
            profile: User profile.
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Frozen balance amount.
        """
        if currency_type == 'RIAL':
            return profile.frozen_rial_balance
        elif currency_type == 'GOLD':
            return profile.frozen_gold_balance
        elif currency_type == 'COIN':
            return profile.frozen_coin_balance
        elif currency_type == 'DOLLAR':
            return profile.frozen_dollar_balance
        else:
            return Decimal('0')
    
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
        
        # Deduct from frozen balance (permanently remove)
        if currency_type == 'RIAL':
            if profile.frozen_rial_balance < amount:
                raise ValidationError("خطای سیستمی: موجودی مسدود شده ریال کافی نیست.")
            profile.frozen_rial_balance -= amount
        elif currency_type == 'GOLD':
            if profile.frozen_gold_balance < amount:
                raise ValidationError("خطای سیستمی: موجودی مسدود شده طلا کافی نیست.")
            profile.frozen_gold_balance -= amount
        elif currency_type == 'COIN':
            if profile.frozen_coin_balance < amount:
                raise ValidationError("خطای سیستمی: موجودی مسدود شده سکه کافی نیست.")
            profile.frozen_coin_balance -= amount
        elif currency_type == 'DOLLAR':
            if profile.frozen_dollar_balance < amount:
                raise ValidationError("خطای سیستمی: موجودی مسدود شده دلار کافی نیست.")
            profile.frozen_dollar_balance -= amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
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
        
        Args:
            currency_type: Type of currency ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
            
        Returns:
            Persian display name for the currency.
        """
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
        
        Args:
            profile: User profile.
            
        Returns:
            Formatted wallet display string.
        """
        balances = WalletService.get_wallet_balance(profile)
        
        text = "💼 *کیف پول شما:*\n\n"
        
        # Rial balance - consistent formatting with :,.0f for all amounts
        text += "💵 *موجودی ریالی:*\n"
        text += f"├─ کل: {balances['rial']['total']:,.0f} ریال\n"
        text += f"├─ قابل استفاده: {balances['rial']['available']:,.0f} ریال\n"
        text += f"└─ مسدود شده: {balances['rial']['frozen']:,.0f} ریال\n\n"
        
        # Gold balance - consistent formatting with ,.4f for precision
        text += "🪙 *موجودی طلا:*\n"
        text += f"├─ کل: {balances['gold']['total']:,.4f} گرم\n"
        text += f"├─ قابل استفاده: {balances['gold']['available']:,.4f} گرم\n"
        text += f"└─ مسدود شده: {balances['gold']['frozen']:,.4f} گرم\n\n"
        
        # Coin balance - consistent formatting with :,.0f for whole numbers
        text += "🥇 *موجودی سکه:*\n"
        text += f"├─ کل: {balances['coin']['total']:,.0f} عدد\n"
        text += f"├─ قابل استفاده: {balances['coin']['available']:,.0f} عدد\n"
        text += f"└─ مسدود شده: {balances['coin']['frozen']:,.0f} عدد\n\n"
        
        # Dollar balance - consistent formatting with :,.2f for currency
        text += "💵 *موجودی دلار:*\n"
        text += f"├─ کل: ${balances['dollar']['total']:,.2f}\n"
        text += f"├─ قابل استفاده: ${balances['dollar']['available']:,.2f}\n"
        text += f"└─ مسدود شده: ${balances['dollar']['frozen']:,.2f}\n\n"
        
        # Format date consistently - handle potential None value
        if profile.updated_at:
            last_update = profile.updated_at.strftime('%Y/%m/%d - %H:%M')
        else:
            last_update = "نامشخص"
        
        text += f"⏰ آخرین بروزرسانی: {last_update}"
        
        return text
