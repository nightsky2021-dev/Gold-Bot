"""
Service layer for trading app.

This module contains business logic for trading operations,
separated from models and views for better maintainability.
"""

import logging
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from .models import Product, Order, Transaction, WithdrawRequest
from users.models import Profile, BankAccount

if TYPE_CHECKING:
    from django.db.models import QuerySet

logger = logging.getLogger('trading')


class TradingService:
    """
    Facade service class that provides unified access to trading operations.
    This class delegates to specialized service classes for better organization.
    """
    
    @staticmethod
    def get_active_products() -> 'QuerySet[Product]':
        """Get all active products available for trading."""
        return ProductService.get_active_products()
    
    @staticmethod
    def update_all_prices() -> None:
        """Update all product prices from external sources."""
        # Import here to avoid circular imports
        from trading.management.commands.update_prices import Command
        command = Command()
        command.handle()
    
    @staticmethod
    def get_user_recent_orders(
        profile: Profile,
        limit: int = 10
    ) -> List[Order]:
        """Get user's recent orders."""
        return OrderService.get_user_orders(profile, limit=limit)
    
    @staticmethod
    def calculate_buy_details(
        product: Product,
        amount: Decimal,
        calculation_method: str = 'rial'
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate buy order details.
        
        Args:
            product: Product to buy
            amount: Amount in grams or rial (based on calculation_method)
            calculation_method: 'grams' or 'rial'
            
        Returns:
            Tuple of (quantity_grams, total_amount)
        """
        quantity_grams, price_per_gram, total_amount = OrderService.calculate_order_details(
            product=product,
            order_type=Order.OrderType.BUY,
            amount=amount,
            calculation_method=calculation_method
        )
        return quantity_grams, total_amount
    
    @staticmethod
    def calculate_sell_details(
        product: Product,
        amount: Decimal,
        calculation_method: str = 'grams'
    ) -> Tuple[Decimal, Decimal]:
        """
        Calculate sell order details.
        
        Args:
            product: Product to sell
            amount: Amount in grams or rial (based on calculation_method)
            calculation_method: 'grams' or 'rial'
            
        Returns:
            Tuple of (quantity_grams, total_amount)
        """
        quantity_grams, price_per_gram, total_amount = OrderService.calculate_order_details(
            product=product,
            order_type=Order.OrderType.SELL,
            amount=amount,
            calculation_method=calculation_method
        )
        return quantity_grams, total_amount
    
    @staticmethod
    def create_buy_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal
    ) -> Order:
        """
        Create a buy order.
        
        Args:
            profile: User profile
            product: Product to buy
            quantity_grams: Quantity in grams
            total_amount: Total amount in Rial
            
        Returns:
            Created Order instance
        """
        price_per_gram = product.sell_price
        return OrderService.create_order(
            profile=profile,
            product=product,
            order_type=Order.OrderType.BUY,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )
    
    @staticmethod
    def create_sell_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal
    ) -> Order:
        """
        Create a sell order.
        
        Args:
            profile: User profile
            product: Product to sell
            quantity_grams: Quantity in grams
            total_amount: Total amount in Rial
            
        Returns:
            Created Order instance
        """
        price_per_gram = product.buy_price
        return OrderService.create_order(
            profile=profile,
            product=product,
            order_type=Order.OrderType.SELL,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount
        )


class ProductService:
    """Service class for Product-related operations."""
    
    @staticmethod
    def get_active_products() -> 'QuerySet[Product]':
        """
        Get all active products available for trading.
        
        Returns:
            QuerySet of active Product instances, ordered by name.
        """
        return Product.objects.filter(is_active=True).order_by('name')
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """
        Get a product by its ID.
        
        Args:
            product_id: The ID of the product.
            
        Returns:
            Product instance if found and active, None otherwise.
        """
        try:
            return Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            logger.warning(f"Product with ID {product_id} not found or inactive")
            return None
    
    @staticmethod
    def get_product_by_slug(slug: str) -> Optional[Product]:
        """
        Get a product by its slug.
        
        Args:
            slug: The slug of the product.
            
        Returns:
            Product instance if found and active, None otherwise.
        """
        try:
            return Product.objects.get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            logger.warning(f"Product with slug '{slug}' not found or inactive")
            return None
    
    @staticmethod
    def format_product_prices(product: Product) -> str:
        """
        Format product prices for display.
        
        Args:
            product: Product instance.
            
        Returns:
            Formatted string with buy and sell prices.
        """
        return (
            f"📊 *{product.name}*\n"
            f"💰 قیمت خرید (شما به ما می‌فروشید): {product.buy_price:,} ریال\n"
            f"💵 قیمت فروش (شما از ما می‌خرید): {product.sell_price:,} ریال"
        )


class OrderService:
    """Service class for Order-related operations."""
    
    @staticmethod
    def calculate_order_details(
        product: Product,
        order_type: str,
        amount: Decimal,
        calculation_method: str = 'grams'
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """
        Calculate order details based on amount and calculation method.
        
        Args:
            product: The product being traded.
            order_type: 'BUY' or 'SELL'
            amount: Amount in grams or rial (based on calculation_method)
            calculation_method: 'grams' or 'rial'
            
        Returns:
            Tuple of (quantity_grams, price_per_gram, total_amount)
            
        Raises:
            ValidationError: If inputs are invalid.
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد.")
        
        # Determine price per gram based on order type
        if order_type == Order.OrderType.BUY:
            price_per_gram = product.sell_price  # User buys from us
        elif order_type == Order.OrderType.SELL:
            price_per_gram = product.buy_price  # User sells to us
        else:
            raise ValidationError("نوع سفارش نامعتبر است.")
        
        # Calculate based on method
        if calculation_method == 'grams':
            quantity_grams = amount
            total_amount = quantity_grams * price_per_gram
        elif calculation_method == 'rial':
            total_amount = amount
            quantity_grams = total_amount / price_per_gram
        else:
            raise ValidationError("روش محاسبه نامعتبر است.")
        
        # Round to appropriate decimal places
        quantity_grams = Decimal(str(round(float(quantity_grams), 4)))
        total_amount = Decimal(str(round(float(total_amount), 0)))
        
        return quantity_grams, price_per_gram, total_amount
    
    @staticmethod
    @transaction.atomic
    def create_order(
        profile: Profile,
        product: Product,
        order_type: str,
        quantity_grams: Decimal,
        price_per_gram: Decimal,
        total_amount: Decimal
    ) -> Order:
        """
        Create a new order (in PENDING status).
        
        Args:
            profile: User profile placing the order.
            product: Product being traded.
            order_type: 'BUY' or 'SELL'
            quantity_grams: Quantity in grams.
            price_per_gram: Price per gram at time of order.
            total_amount: Total amount in Rial.
            
        Returns:
            Created Order instance.
            
        Raises:
            ValidationError: If user cannot trade or inputs are invalid.
        """
        # Validate user can trade
        if not profile.can_trade():
            raise ValidationError(
                "حساب شما هنوز تأیید نشده است. "
                "لطفاً منتظر تأیید مدیر باشید."
            )
        
        # Validate product is active
        if not product.is_active:
            raise ValidationError("این محصول در حال حاضر غیرفعال است.")
        
        # Validate amounts
        if quantity_grams <= 0 or total_amount <= 0:
            raise ValidationError("مقادیر وارد شده نامعتبر است.")
        
        # For BUY orders, check if user has sufficient Rial balance
        # Note: We don't enforce this at order creation, only at completion
        # This allows users to order and then deposit
        
        # For SELL orders, check if user has sufficient gold balance
        # Again, not enforced at creation time
        
        # Create the order
        order = Order.objects.create(
            profile=profile,
            product=product,
            order_type=order_type,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount,
            status=Order.OrderStatus.PENDING
        )
        
        logger.info(
            f"Order {order.id} created: {order_type} "
            f"{quantity_grams}g of {product.name} "
            f"by user {profile.get_display_name()}"
        )
        
        return order
    
    @staticmethod
    def get_user_orders(
        profile: Profile,
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[Order]:
        """
        Get orders for a specific user.
        
        Args:
            profile: User profile.
            limit: Maximum number of orders to return (None for all).
            status: Filter by status (None for all statuses).
            
        Returns:
            List of Order instances.
        """
        queryset = profile.orders.all()
        
        if status:
            queryset = queryset.filter(status=status)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def format_order_for_display(order: Order, include_status: bool = True) -> str:
        """
        Format an order for display in Telegram.
        
        Args:
            order: Order instance.
            include_status: Whether to include order status.
            
        Returns:
            Formatted string.
        """
        order_type_emoji = "📈" if order.order_type == Order.OrderType.BUY else "📉"
        order_type_text = order.get_order_type_display()
        
        text = (
            f"{order_type_emoji} *سفارش #{order.id}*\n"
            f"📦 محصول: {order.product.name}\n"
            f"⚖️ مقدار: {order.quantity_grams} گرم\n"
            f"💰 قیمت هر گرم: {order.price_per_gram:,} ریال\n"
            f"💵 مبلغ کل: {order.total_amount:,} ریال\n"
            f"📅 تاریخ: {order.created_at.strftime('%Y/%m/%d %H:%M')}\n"
        )
        
        if include_status:
            status_emoji = {
                Order.OrderStatus.PENDING: "🕐",
                Order.OrderStatus.COMPLETED: "✅",
                Order.OrderStatus.CANCELLED: "❌",
            }
            emoji = status_emoji.get(order.status, "")
            text += f"{emoji} وضعیت: {order.get_status_display()}\n"
        
        return text
    
    @staticmethod
    def format_order_preview(
        product: Product,
        order_type: str,
        quantity_grams: Decimal,
        total_amount: Decimal
    ) -> str:
        """
        Format order preview before confirmation.
        
        Args:
            product: Product instance.
            order_type: 'BUY' or 'SELL'
            quantity_grams: Quantity in grams.
            total_amount: Total amount in Rial.
            
        Returns:
            Formatted preview string.
        """
        order_type_text = "خرید از ما" if order_type == Order.OrderType.BUY else "فروش به ما"
        order_type_emoji = "📈" if order_type == Order.OrderType.BUY else "📉"
        
        return (
            f"{order_type_emoji} *پیش‌فاکتور {order_type_text}*\n\n"
            f"📦 محصول: *{product.name}*\n"
            f"⚖️ مقدار: *{quantity_grams} گرم*\n"
            f"💵 مبلغ کل: *{total_amount:,} ریال*\n\n"
            f"آیا از ثبت این سفارش مطمئن هستید؟"
        )


class BalanceService:
    """Service class for balance-related operations."""
    
    @staticmethod
    def format_portfolio(profile: Profile) -> str:
        """
        Format user's portfolio for display.
        
        Args:
            profile: User profile.
            
        Returns:
            Formatted portfolio string.
        """
        return (
            f"📊 *پورتفولیوی شما:*\n\n"
            f"💰 *موجودی ریالی:* {profile.rial_balance:,} ریال\n"
            f"⚖️ *موجودی طلا:* {profile.gold_balance_grams} گرم"
        )
    
    @staticmethod
    @transaction.atomic
    def update_balance(
        profile: Profile,
        rial_change: Decimal = Decimal('0'),
        gold_change: Decimal = Decimal('0')
    ) -> None:
        """
        Update user's balance atomically.
        
        Args:
            profile: User profile.
            rial_change: Change in Rial balance (positive or negative).
            gold_change: Change in gold balance (positive or negative).
            
        Raises:
            ValidationError: If resulting balance would be negative.
        """
        new_rial = profile.rial_balance + rial_change
        new_gold = profile.gold_balance_grams + gold_change
        
        if new_rial < 0:
            raise ValidationError("موجودی ریالی کافی نیست.")
        
        if new_gold < 0:
            raise ValidationError("موجودی طلا کافی نیست.")
        
        profile.rial_balance = new_rial
        profile.gold_balance_grams = new_gold
        profile.save()
        
        logger.info(
            f"Balance updated for {profile.get_display_name()}: "
            f"Rial change: {rial_change}, Gold change: {gold_change}"
        )


class WalletService:
    """Service class for wallet and balance management."""
    
    @staticmethod
    def get_wallet_balance(profile: Profile) -> Dict[str, Decimal]:
        """
        Get complete wallet balance information.
        
        Args:
            profile: User profile
            
        Returns:
            Dictionary with all balance information
        """
        return {
            'rial': profile.rial_balance,
            'gold': profile.gold_balance_grams,
            'coin': profile.coin_balance,
            'dollar': profile.dollar_balance,
            'frozen_rial': profile.frozen_rial_balance,
            'frozen_gold': profile.frozen_gold_balance,
            'frozen_coin': profile.frozen_coin_balance,
            'frozen_dollar': profile.frozen_dollar_balance,
            'available_rial': profile.get_available_balance('RIAL'),
            'available_gold': profile.get_available_balance('GOLD'),
            'available_coin': profile.get_available_balance('COIN'),
            'available_dollar': profile.get_available_balance('DOLLAR'),
        }
    
    @staticmethod
    @transaction.atomic
    def freeze_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        Freeze balance for pending transaction.
        
        Args:
            profile: User profile
            currency_type: Currency type (RIAL, GOLD, COIN, DOLLAR)
            amount: Amount to freeze
            
        Raises:
            ValidationError: If insufficient balance
        """
        # Lock the profile row to prevent race conditions
        profile = Profile.objects.select_for_update().get(id=profile.id)
        
        if currency_type == 'RIAL':
            if profile.rial_balance < amount:
                raise ValidationError(f"موجودی ریالی کافی نیست. موجودی: {profile.rial_balance:,}")
            profile.rial_balance -= amount
            profile.frozen_rial_balance += amount
            profile.save(update_fields=['rial_balance', 'frozen_rial_balance'])
            
        elif currency_type == 'GOLD':
            if profile.gold_balance_grams < amount:
                raise ValidationError(f"موجودی طلا کافی نیست. موجودی: {profile.gold_balance_grams}")
            profile.gold_balance_grams -= amount
            profile.frozen_gold_balance += amount
            profile.save(update_fields=['gold_balance_grams', 'frozen_gold_balance'])
            
        elif currency_type == 'COIN':
            if profile.coin_balance < amount:
                raise ValidationError(f"موجودی سکه کافی نیست. موجودی: {profile.coin_balance}")
            profile.coin_balance -= amount
            profile.frozen_coin_balance += amount
            profile.save(update_fields=['coin_balance', 'frozen_coin_balance'])
            
        elif currency_type == 'DOLLAR':
            if profile.dollar_balance < amount:
                raise ValidationError(f"موجودی دلار کافی نیست. موجودی: {profile.dollar_balance}")
            profile.dollar_balance -= amount
            profile.frozen_dollar_balance += amount
            profile.save(update_fields=['dollar_balance', 'frozen_dollar_balance'])
        else:
            raise ValidationError(f"نوع ارز نامعتبر: {currency_type}")
        
        logger.info(
            f"Froze {amount} {currency_type} for {profile.get_display_name()}"
        )
    
    @staticmethod
    @transaction.atomic
    def unfreeze_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        Unfreeze balance (return to available balance).
        
        Args:
            profile: User profile
            currency_type: Currency type (RIAL, GOLD, COIN, DOLLAR)
            amount: Amount to unfreeze
            
        Raises:
            ValidationError: If insufficient frozen balance
        """
        # Lock the profile row
        profile = Profile.objects.select_for_update().get(id=profile.id)
        
        if currency_type == 'RIAL':
            if profile.frozen_rial_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_rial_balance -= amount
            profile.rial_balance += amount
            profile.save(update_fields=['rial_balance', 'frozen_rial_balance'])
            
        elif currency_type == 'GOLD':
            if profile.frozen_gold_balance < amount:
                raise ValidationError("موجودی طلای مسدود شده کافی نیست.")
            profile.frozen_gold_balance -= amount
            profile.gold_balance_grams += amount
            profile.save(update_fields=['gold_balance_grams', 'frozen_gold_balance'])
            
        elif currency_type == 'COIN':
            if profile.frozen_coin_balance < amount:
                raise ValidationError("موجودی سکه مسدود شده کافی نیست.")
            profile.frozen_coin_balance -= amount
            profile.coin_balance += amount
            profile.save(update_fields=['coin_balance', 'frozen_coin_balance'])
            
        elif currency_type == 'DOLLAR':
            if profile.frozen_dollar_balance < amount:
                raise ValidationError("موجودی دلار مسدود شده کافی نیست.")
            profile.frozen_dollar_balance -= amount
            profile.dollar_balance += amount
            profile.save(update_fields=['dollar_balance', 'frozen_dollar_balance'])
        else:
            raise ValidationError(f"نوع ارز نامعتبر: {currency_type}")
        
        logger.info(
            f"Unfroze {amount} {currency_type} for {profile.get_display_name()}"
        )
    
    @staticmethod
    @transaction.atomic
    def deduct_frozen_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        Deduct from frozen balance (for completed withdrawals).
        
        Args:
            profile: User profile
            currency_type: Currency type
            amount: Amount to deduct
            
        Raises:
            ValidationError: If insufficient frozen balance
        """
        # Lock the profile row
        profile = Profile.objects.select_for_update().get(id=profile.id)
        
        if currency_type == 'RIAL':
            if profile.frozen_rial_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_rial_balance -= amount
            profile.save(update_fields=['frozen_rial_balance'])
            
        elif currency_type == 'GOLD':
            if profile.frozen_gold_balance < amount:
                raise ValidationError("موجودی طلای مسدود شده کافی نیست.")
            profile.frozen_gold_balance -= amount
            profile.save(update_fields=['frozen_gold_balance'])
            
        elif currency_type == 'COIN':
            if profile.frozen_coin_balance < amount:
                raise ValidationError("موجودی سکه مسدود شده کافی نیست.")
            profile.frozen_coin_balance -= amount
            profile.save(update_fields=['frozen_coin_balance'])
            
        elif currency_type == 'DOLLAR':
            if profile.frozen_dollar_balance < amount:
                raise ValidationError("موجودی دلار مسدود شده کافی نیست.")
            profile.frozen_dollar_balance -= amount
            profile.save(update_fields=['frozen_dollar_balance'])
        else:
            raise ValidationError(f"نوع ارز نامعتبر: {currency_type}")
        
        logger.info(
            f"Deducted {amount} {currency_type} from frozen balance for {profile.get_display_name()}"
        )
    
    @staticmethod
    @transaction.atomic
    def add_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        Add to available balance.
        
        Args:
            profile: User profile
            currency_type: Currency type
            amount: Amount to add
        """
        # Lock the profile row
        profile = Profile.objects.select_for_update().get(id=profile.id)
        
        if currency_type == 'RIAL':
            profile.rial_balance += amount
            profile.save(update_fields=['rial_balance'])
            
        elif currency_type == 'GOLD':
            profile.gold_balance_grams += amount
            profile.save(update_fields=['gold_balance_grams'])
            
        elif currency_type == 'COIN':
            profile.coin_balance += amount
            profile.save(update_fields=['coin_balance'])
            
        elif currency_type == 'DOLLAR':
            profile.dollar_balance += amount
            profile.save(update_fields=['dollar_balance'])
        else:
            raise ValidationError(f"نوع ارز نامعتبر: {currency_type}")
        
        logger.info(
            f"Added {amount} {currency_type} to {profile.get_display_name()}'s balance"
        )
    
    @staticmethod
    def check_sufficient_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> bool:
        """
        Check if user has sufficient available balance.
        
        Args:
            profile: User profile
            currency_type: Currency type
            amount: Amount to check
            
        Returns:
            True if sufficient, False otherwise
        """
        available = profile.get_available_balance(currency_type)
        return available >= amount
    
    @staticmethod
    def format_wallet_display(profile: Profile) -> str:
        """
        Format wallet information for display.
        
        Args:
            profile: User profile
            
        Returns:
            Formatted string
        """
        balances = WalletService.get_wallet_balance(profile)
        
        return (
            f"💼 *کیف پول شما:*\n\n"
            f"💵 *موجودی ریالی:*\n"
            f"├─ آزاد: {balances['available_rial']:,} ریال\n"
            f"└─ مسدود شده: {balances['frozen_rial']:,} ریال\n\n"
            f"🪙 *موجودی طلا:*\n"
            f"├─ آزاد: {balances['available_gold']} گرم\n"
            f"└─ مسدود شده: {balances['frozen_gold']} گرم\n\n"
            f"🥇 *موجودی سکه:*\n"
            f"├─ آزاد: {balances['available_coin']} عدد\n"
            f"└─ مسدود شده: {balances['frozen_coin']} عدد\n\n"
            f"💵 *موجودی دلار:*\n"
            f"├─ آزاد: {balances['available_dollar']} دلار\n"
            f"└─ مسدود شده: {balances['frozen_dollar']} دلار\n\n"
            f"⏰ آخرین بروزرسانی: {timezone.now().strftime('%Y/%m/%d - %H:%M')}"
        )


class TransactionService:
    """Service class for transaction management."""
    
    @staticmethod
    def _get_current_balance(profile: Profile, currency_type: str) -> Decimal:
        """Get current balance for a currency type."""
        balance_map = {
            'RIAL': profile.rial_balance,
            'GOLD': profile.gold_balance_grams,
            'COIN': profile.coin_balance,
            'DOLLAR': profile.dollar_balance,
        }
        return balance_map.get(currency_type, Decimal('0'))
    
    @staticmethod
    @transaction.atomic
    def create_transaction(
        profile: Profile,
        transaction_type: str,
        currency_type: str,
        amount: Decimal,
        related_bank_account: Optional[BankAccount] = None,
        related_order: Optional[Order] = None,
        user_note: str = '',
        admin_note: str = '',
        receipt_image=None
    ) -> Transaction:
        """
        Create a new transaction record.
        
        Args:
            profile: User profile
            transaction_type: Type of transaction
            currency_type: Currency type
            amount: Transaction amount
            related_bank_account: Related bank account (optional)
            related_order: Related order (optional)
            user_note: User's note
            admin_note: Admin's note
            receipt_image: Receipt image (optional)
            
        Returns:
            Transaction instance
        """
        # Generate unique transaction number
        transaction_number = Transaction.generate_transaction_number()
        
        # Get balance before transaction
        balance_before = TransactionService._get_current_balance(profile, currency_type)
        
        # Calculate balance after (for display purposes, actual balance change happens elsewhere)
        if transaction_type in [Transaction.TransactionType.DEPOSIT, 
                               Transaction.TransactionType.TRANSFER_RECEIVE]:
            balance_after = balance_before + amount
        elif transaction_type in [Transaction.TransactionType.WITHDRAW,
                                 Transaction.TransactionType.TRANSFER_SEND]:
            balance_after = balance_before - amount
        elif transaction_type == Transaction.TransactionType.BUY:
            # For BUY, this depends on currency - if RIAL, it decreases; otherwise increases
            if currency_type == 'RIAL':
                balance_after = balance_before - amount
            else:
                balance_after = balance_before + amount
        elif transaction_type == Transaction.TransactionType.SELL:
            # For SELL, opposite of BUY
            if currency_type == 'RIAL':
                balance_after = balance_before + amount
            else:
                balance_after = balance_before - amount
        else:
            balance_after = balance_before
        
        # Create transaction
        txn = Transaction.objects.create(
            transaction_number=transaction_number,
            profile=profile,
            transaction_type=transaction_type,
            currency_type=currency_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_after,
            status=Transaction.TransactionStatus.PENDING,
            related_bank_account=related_bank_account,
            related_order=related_order,
            user_note=user_note,
            admin_note=admin_note,
            receipt_image=receipt_image
        )
        
        logger.info(
            f"Transaction {transaction_number} created: "
            f"{transaction_type} {amount} {currency_type} "
            f"for {profile.get_display_name()}"
        )
        
        return txn
    
    @staticmethod
    def get_user_transactions(
        profile: Profile,
        currency_type: Optional[str] = None,
        transaction_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = 20
    ) -> List[Transaction]:
        """
        Get user's transaction history.
        
        Args:
            profile: User profile
            currency_type: Filter by currency type
            transaction_type: Filter by transaction type
            status: Filter by status
            limit: Maximum number of transactions
            
        Returns:
            List of Transaction instances
        """
        queryset = profile.transactions.all()
        
        if currency_type:
            queryset = queryset.filter(currency_type=currency_type)
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    @transaction.atomic
    def complete_transaction(
        transaction_id: int,
        admin_user: Optional[User] = None,
        admin_note: str = ''
    ) -> Transaction:
        """
        Mark transaction as completed.
        
        Args:
            transaction_id: Transaction ID
            admin_user: Admin user completing the transaction
            admin_note: Admin's note
            
        Returns:
            Updated Transaction instance
        """
        txn = Transaction.objects.select_related('profile').get(id=transaction_id)
        
        if not txn.is_pending():
            raise ValidationError("فقط تراکنش‌های در حال انتظار قابل تکمیل هستند.")
        
        txn.status = Transaction.TransactionStatus.COMPLETED
        txn.completed_at = timezone.now()
        
        if admin_note:
            txn.admin_note = admin_note
        
        txn.save(update_fields=['status', 'completed_at', 'admin_note', 'updated_at'])
        
        logger.info(
            f"Transaction {txn.transaction_number} completed "
            f"by admin {admin_user.username if admin_user else 'system'}"
        )
        
        # TODO: Send notification to user
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def cancel_transaction(
        transaction_id: int,
        reason: str,
        admin_user: Optional[User] = None
    ) -> Transaction:
        """
        Cancel a transaction.
        
        Args:
            transaction_id: Transaction ID
            reason: Reason for cancellation
            admin_user: Admin user canceling the transaction
            
        Returns:
            Updated Transaction instance
        """
        txn = Transaction.objects.select_related('profile').get(id=transaction_id)
        
        if not txn.is_pending():
            raise ValidationError("فقط تراکنش‌های در حال انتظار قابل لغو هستند.")
        
        txn.status = Transaction.TransactionStatus.CANCELLED
        txn.admin_note = reason
        txn.save(update_fields=['status', 'admin_note', 'updated_at'])
        
        logger.info(
            f"Transaction {txn.transaction_number} cancelled "
            f"by admin {admin_user.username if admin_user else 'system'}. "
            f"Reason: {reason}"
        )
        
        # TODO: Send notification to user with reason
        
        return txn
    
    @staticmethod
    def format_transaction_for_display(txn: Transaction) -> str:
        """Format transaction for display in Telegram."""
        type_emoji = {
            Transaction.TransactionType.DEPOSIT: '🟢',
            Transaction.TransactionType.WITHDRAW: '🔴',
            Transaction.TransactionType.BUY: '📈',
            Transaction.TransactionType.SELL: '📉',
            Transaction.TransactionType.TRANSFER_SEND: '↗️',
            Transaction.TransactionType.TRANSFER_RECEIVE: '↙️',
        }
        
        status_emoji = {
            Transaction.TransactionStatus.PENDING: '⏳',
            Transaction.TransactionStatus.COMPLETED: '✅',
            Transaction.TransactionStatus.CANCELLED: '❌',
            Transaction.TransactionStatus.FAILED: '⚠️',
        }
        
        emoji = type_emoji.get(txn.transaction_type, '📝')
        status_icon = status_emoji.get(txn.status, '')
        
        text = (
            f"┌─────────────────────────\n"
            f"│ {emoji} {txn.get_transaction_type_display()}\n"
            f"│ 💰 مبلغ: {txn.amount} {txn.get_currency_type_display()}\n"
            f"│ 📅 {txn.created_at.strftime('%Y/%m/%d - %H:%M')}\n"
            f"│ {status_icon} {txn.get_status_display()}\n"
            f"│ 🔢 {txn.transaction_number}\n"
            f"└─────────────────────────\n"
        )
        
        return text


class DepositService:
    """Service class for deposit operations."""
    
    @staticmethod
    @transaction.atomic
    def create_deposit_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: Optional[int] = None,
        user_note: str = '',
        receipt_image=None
    ) -> Transaction:
        """
        Create a deposit request.
        
        Args:
            profile: User profile
            currency_type: Currency type
            amount: Deposit amount
            bank_account_id: Source bank account ID
            user_note: User's note
            receipt_image: Receipt image
            
        Returns:
            Transaction instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValidationError("مبلغ باید بزرگتر از صفر باشد.")
        
        # Get bank account if provided
        bank_account = None
        if bank_account_id:
            try:
                bank_account = BankAccount.objects.get(
                    id=bank_account_id,
                    profile=profile
                )
                if not bank_account.can_be_used_for_transaction():
                    raise ValidationError(
                        "این حساب بانکی تایید نشده یا غیرفعال است."
                    )
            except BankAccount.DoesNotExist:
                raise ValidationError("حساب بانکی یافت نشد.")
        
        # Create transaction
        txn = TransactionService.create_transaction(
            profile=profile,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            currency_type=currency_type,
            amount=amount,
            related_bank_account=bank_account,
            user_note=user_note,
            receipt_image=receipt_image
        )
        
        logger.info(
            f"Deposit request created: {txn.transaction_number} - "
            f"{amount} {currency_type} for {profile.get_display_name()}"
        )
        
        # TODO: Send notification to admin
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def approve_deposit(
        transaction_id: int,
        admin_user: User,
        admin_note: str = ''
    ) -> Transaction:
        """
        Approve a deposit request.
        
        Args:
            transaction_id: Transaction ID
            admin_user: Admin user approving the deposit
            admin_note: Admin's note
            
        Returns:
            Updated Transaction instance
        """
        txn = Transaction.objects.select_related('profile').get(id=transaction_id)
        
        if txn.transaction_type != Transaction.TransactionType.DEPOSIT:
            raise ValidationError("این تراکنش یک درخواست واریز نیست.")
        
        if not txn.is_pending():
            raise ValidationError("این تراکنش قبلاً پردازش شده است.")
        
        # Add balance to user
        WalletService.add_balance(
            profile=txn.profile,
            currency_type=txn.currency_type,
            amount=txn.amount
        )
        
        # Update transaction balance_after to reflect actual final balance
        txn.balance_after = TransactionService._get_current_balance(
            txn.profile, txn.currency_type
        )
        
        # Mark transaction as completed
        txn.status = Transaction.TransactionStatus.COMPLETED
        txn.completed_at = timezone.now()
        if admin_note:
            txn.admin_note = admin_note
        txn.save(update_fields=['status', 'completed_at', 'admin_note', 'balance_after', 'updated_at'])
        
        logger.info(
            f"Deposit approved: {txn.transaction_number} - "
            f"{txn.amount} {txn.currency_type} added to {txn.profile.get_display_name()}'s balance "
            f"by admin {admin_user.username}"
        )
        
        # TODO: Send notification to user
        
        return txn
    
    @staticmethod
    @transaction.atomic
    def reject_deposit(
        transaction_id: int,
        reason: str,
        admin_user: User
    ) -> Transaction:
        """
        Reject a deposit request.
        
        Args:
            transaction_id: Transaction ID
            reason: Reason for rejection
            admin_user: Admin user rejecting the deposit
            
        Returns:
            Updated Transaction instance
        """
        txn = Transaction.objects.select_related('profile').get(id=transaction_id)
        
        if txn.transaction_type != Transaction.TransactionType.DEPOSIT:
            raise ValidationError("این تراکنش یک درخواست واریز نیست.")
        
        if not txn.is_pending():
            raise ValidationError("این تراکنش قبلاً پردازش شده است.")
        
        # Cancel transaction
        txn = TransactionService.cancel_transaction(
            transaction_id=transaction_id,
            reason=reason,
            admin_user=admin_user
        )
        
        logger.info(
            f"Deposit rejected: {txn.transaction_number} by admin {admin_user.username}"
        )
        
        # TODO: Send notification to user with reason
        
        return txn


class WithdrawService:
    """Service class for withdrawal operations."""
    
    @staticmethod
    @transaction.atomic
    def create_withdraw_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: int,
        user_note: str = ''
    ) -> WithdrawRequest:
        """
        Create a withdrawal request.
        
        Args:
            profile: User profile
            currency_type: Currency type
            amount: Withdrawal amount
            bank_account_id: Destination bank account ID
            user_note: User's note
            
        Returns:
            WithdrawRequest instance
            
        Raises:
            ValidationError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValidationError("مبلغ باید بزرگتر از صفر باشد.")
        
        # Check sufficient balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            available = profile.get_available_balance(currency_type)
            raise ValidationError(
                f"موجودی کافی نیست. موجودی در دسترس: {available}"
            )
        
        # Get and validate bank account
        try:
            bank_account = BankAccount.objects.get(
                id=bank_account_id,
                profile=profile
            )
            if not bank_account.can_be_used_for_transaction():
                raise ValidationError(
                    "این حساب بانکی تایید نشده یا غیرفعال است."
                )
        except BankAccount.DoesNotExist:
            raise ValidationError("حساب بانکی یافت نشد.")
        
        # Freeze balance
        WalletService.freeze_balance(
            profile=profile,
            currency_type=currency_type,
            amount=amount
        )
        
        # Create transaction
        txn = TransactionService.create_transaction(
            profile=profile,
            transaction_type=Transaction.TransactionType.WITHDRAW,
            currency_type=currency_type,
            amount=amount,
            related_bank_account=bank_account,
            user_note=user_note
        )
        
        # Create withdraw request
        request_number = WithdrawRequest.generate_request_number()
        withdraw_request = WithdrawRequest.objects.create(
            request_number=request_number,
            profile=profile,
            bank_account=bank_account,
            currency_type=currency_type,
            amount=amount,
            status=WithdrawRequest.RequestStatus.PENDING,
            related_transaction=txn
        )
        
        logger.info(
            f"Withdraw request created: {request_number} - "
            f"{amount} {currency_type} for {profile.get_display_name()}"
        )
        
        # TODO: Send notification to admin
        
        return withdraw_request
    
    @staticmethod
    @transaction.atomic
    def approve_withdraw(
        withdraw_request_id: int,
        admin_user: User,
        admin_note: str = ''
    ) -> WithdrawRequest:
        """
        Approve a withdrawal request.
        
        Args:
            withdraw_request_id: WithdrawRequest ID
            admin_user: Admin user approving the withdrawal
            admin_note: Admin's note
            
        Returns:
            Updated WithdrawRequest instance
        """
        withdraw_request = WithdrawRequest.objects.select_related(
            'profile', 'related_transaction', 'bank_account'
        ).get(id=withdraw_request_id)
        
        if not withdraw_request.is_pending():
            raise ValidationError("این درخواست قبلاً پردازش شده است.")
        
        # Deduct from frozen balance
        WalletService.deduct_frozen_balance(
            profile=withdraw_request.profile,
            currency_type=withdraw_request.currency_type,
            amount=withdraw_request.amount
        )
        
        # Update withdraw request
        withdraw_request.status = WithdrawRequest.RequestStatus.COMPLETED
        withdraw_request.processed_at = timezone.now()
        withdraw_request.completed_at = timezone.now()
        if admin_note:
            withdraw_request.admin_note = admin_note
        withdraw_request.save(update_fields=[
            'status', 'processed_at', 'completed_at', 'admin_note'
        ])
        
        # Complete related transaction
        if withdraw_request.related_transaction:
            txn = withdraw_request.related_transaction
            txn.balance_after = TransactionService._get_current_balance(
                txn.profile, txn.currency_type
            )
            TransactionService.complete_transaction(
                transaction_id=txn.id,
                admin_user=admin_user,
                admin_note=admin_note
            )
        
        logger.info(
            f"Withdraw approved: {withdraw_request.request_number} - "
            f"{withdraw_request.amount} {withdraw_request.currency_type} "
            f"for {withdraw_request.profile.get_display_name()} "
            f"by admin {admin_user.username}"
        )
        
        # TODO: Send notification to user
        
        return withdraw_request
    
    @staticmethod
    @transaction.atomic
    def reject_withdraw(
        withdraw_request_id: int,
        reason: str,
        admin_user: User
    ) -> WithdrawRequest:
        """
        Reject a withdrawal request.
        
        Args:
            withdraw_request_id: WithdrawRequest ID
            reason: Reason for rejection
            admin_user: Admin user rejecting the withdrawal
            
        Returns:
            Updated WithdrawRequest instance
        """
        withdraw_request = WithdrawRequest.objects.select_related(
            'profile', 'related_transaction'
        ).get(id=withdraw_request_id)
        
        if not withdraw_request.is_pending():
            raise ValidationError("این درخواست قبلاً پردازش شده است.")
        
        # Unfreeze balance (return to available)
        WalletService.unfreeze_balance(
            profile=withdraw_request.profile,
            currency_type=withdraw_request.currency_type,
            amount=withdraw_request.amount
        )
        
        # Update withdraw request
        withdraw_request.status = WithdrawRequest.RequestStatus.REJECTED
        withdraw_request.processed_at = timezone.now()
        withdraw_request.admin_note = reason
        withdraw_request.save(update_fields=[
            'status', 'processed_at', 'admin_note'
        ])
        
        # Cancel related transaction
        if withdraw_request.related_transaction:
            TransactionService.cancel_transaction(
                transaction_id=withdraw_request.related_transaction.id,
                reason=reason,
                admin_user=admin_user
            )
        
        logger.info(
            f"Withdraw rejected: {withdraw_request.request_number} "
            f"by admin {admin_user.username}. Reason: {reason}"
        )
        
        # TODO: Send notification to user with reason
        
        return withdraw_request
