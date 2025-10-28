"""
Wallet services for managing user balances and financial operations.

This module contains services for balance management, freezing/unfreezing
balances, and wallet-related operations.
"""

import logging
from typing import Dict, Any
from decimal import Decimal

from django.db import transaction
from django.core.exceptions import ValidationError

from .models import Profile

logger = logging.getLogger('wallet')


class WalletService:
    """Service class for wallet and balance operations."""
    
    @staticmethod
    def get_wallet_balance(profile: Profile) -> Dict[str, Any]:
        """
        Get complete wallet balance information for a user.
        
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
        
        # Check sufficient balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            raise ValidationError(f"موجودی {currency_type} کافی نیست.")
        
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
        
        # Check sufficient frozen balance
        frozen_balance = WalletService.get_frozen_balance(profile, currency_type)
        if frozen_balance < amount:
            raise ValidationError(f"موجودی مسدود شده {currency_type} کافی نیست.")
        
        # Unfreeze the balance
        if currency_type == 'RIAL':
            profile.frozen_rial_balance -= amount
            profile.rial_balance += amount
        elif currency_type == 'GOLD':
            profile.frozen_gold_balance -= amount
            profile.gold_balance_grams += amount
        elif currency_type == 'COIN':
            profile.frozen_coin_balance -= amount
            profile.coin_balance += amount
        elif currency_type == 'DOLLAR':
            profile.frozen_dollar_balance -= amount
            profile.dollar_balance += amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        
        logger.info(
            f"Unfroze {amount} {currency_type} for user {profile.get_display_name()}"
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
            raise ValidationError(f"موجودی {currency_type} کافی نیست.")
        
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
        
        logger.info(
            f"Deducted {amount} {currency_type} from user {profile.get_display_name()}"
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
        
        logger.info(
            f"Added {amount} {currency_type} to user {profile.get_display_name()}"
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
        
        # Rial balance
        text += "💵 *موجودی ریالی:*\n"
        text += f"├─ آزاد: {balances['rial']['available']:,.0f} ریال\n"
        text += f"└─ مسدود شده: {balances['rial']['frozen']:,.0f} ریال\n\n"
        
        # Gold balance
        text += "🪙 *موجودی طلا:*\n"
        text += f"├─ آزاد: {balances['gold']['available']} گرم\n"
        text += f"└─ مسدود شده: {balances['gold']['frozen']} گرم\n\n"
        
        # Coin balance
        text += "🥇 *موجودی سکه:*\n"
        text += f"├─ آزاد: {balances['coin']['available']} عدد\n"
        text += f"└─ مسدود شده: {balances['coin']['frozen']} عدد\n\n"
        
        # Dollar balance
        text += "💵 *موجودی دلار:*\n"
        text += f"├─ آزاد: {balances['dollar']['available']} دلار\n"
        text += f"└─ مسدود شده: {balances['dollar']['frozen']} دلار\n\n"
        
        text += f"⏰ آخرین بروزرسانی: {profile.updated_at.strftime('%Y/%m/%d - %H:%M')}"
        
        return text
