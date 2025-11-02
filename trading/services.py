"""
Service layer for trading app.

This module contains business logic for trading operations,
separated from models and views for better maintainability.
"""

import logging
from typing import List, Optional, Tuple
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import Product, Order
from users.models import Profile

logger = logging.getLogger('trading')


class ProductService:
    """Service class for Product-related operations."""
    
    @staticmethod
    def get_active_products() -> List[Product]:
        """
        Get all active products available for trading.
        
        Returns:
            List of active Product instances, ordered by name.
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


class TransactionService:
    """Service class for Transaction-related operations."""
    
    @staticmethod
    @transaction.atomic
    def create_deposit(
        profile: 'Profile',
        currency: str,
        amount: Decimal,
        bank_account: 'BankAccount' = None,
        receipt_image = None,
        description: str = ""
    ) -> 'Transaction':
        """
        Create a deposit transaction.
        
        Args:
            profile: User profile
            currency: Currency type ('RIAL', 'GOLD', etc.)
            amount: Amount to deposit
            bank_account: Bank account used (optional)
            receipt_image: Receipt image file (optional)
            description: Additional description
            
        Returns:
            Created Transaction instance
        """
        from .models import Transaction
        
        transaction_obj = Transaction.objects.create(
            profile=profile,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            currency=currency,
            amount=amount,
            bank_account=bank_account,
            receipt_image=receipt_image,
            description=description,
            status=Transaction.TransactionStatus.PENDING
        )
        
        logger.info(
            f"Deposit transaction {transaction_obj.id} created: "
            f"{amount} {currency} by {profile.get_display_name()}"
        )
        
        return transaction_obj
    
    @staticmethod
    def get_user_transactions(
        profile: 'Profile',
        limit: Optional[int] = None,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List['Transaction']:
        """
        Get transactions for a specific user.
        
        Args:
            profile: User profile
            limit: Maximum number of transactions (None for all)
            status: Filter by status (None for all)
            transaction_type: Filter by type (None for all)
            
        Returns:
            List of Transaction instances
        """
        from .models import Transaction
        
        queryset = profile.transactions.all()
        
        if status:
            queryset = queryset.filter(status=status)
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def format_transaction_for_display(transaction: 'Transaction') -> str:
        """
        Format transaction for display in Telegram.
        
        Args:
            transaction: Transaction instance
            
        Returns:
            Formatted string
        """
        type_emoji = {
            'DEPOSIT': '📥',
            'WITHDRAW': '📤',
            'BUY': '📈',
            'SELL': '📉',
            'ADJUSTMENT': '⚙️'
        }
        
        status_emoji = {
            'PENDING': '⏳',
            'COMPLETED': '✅',
            'CANCELLED': '❌',
            'REJECTED': '🚫'
        }
        
        emoji = type_emoji.get(transaction.transaction_type, '💳')
        status_icon = status_emoji.get(transaction.status, '')
        
        text = (
            f"{emoji} *تراکنش #{transaction.id}*\n"
            f"نوع: {transaction.get_transaction_type_display()}\n"
            f"ارز: {transaction.get_currency_display_name()}\n"
            f"مقدار: {transaction.amount:,.2f}\n"
            f"وضعیت: {status_icon} {transaction.get_status_display()}\n"
            f"تاریخ: {transaction.created_at.strftime('%Y/%m/%d %H:%M')}\n"
        )
        
        if transaction.description:
            text += f"توضیحات: {transaction.description}\n"
        
        return text


class WithdrawalService:
    """Service class for withdrawal-related operations."""
    
    @staticmethod
    @transaction.atomic
    def create_withdraw_request(
        profile: 'Profile',
        currency: str,
        amount: Decimal,
        bank_account: 'BankAccount'
    ) -> 'WithdrawRequest':
        """
        Create a withdrawal request and freeze balance.
        
        Args:
            profile: User profile
            currency: Currency type
            amount: Amount to withdraw
            bank_account: Destination bank account
            
        Returns:
            Created WithdrawRequest instance
            
        Raises:
            ValidationError: If insufficient balance or bank account not verified
        """
        from .models import WithdrawRequest
        from users.services import WalletService
        
        # Validate bank account
        if not bank_account.is_verified:
            raise ValidationError("حساب بانکی تأیید نشده است.")
        
        if bank_account.profile != profile:
            raise ValidationError("این حساب بانکی متعلق به شما نیست.")
        
        # Freeze balance
        try:
            WalletService.freeze_balance(profile, currency, float(amount))
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Create withdraw request
        withdraw_request = WithdrawRequest.objects.create(
            profile=profile,
            currency=currency,
            amount=amount,
            bank_account=bank_account,
            status=WithdrawRequest.WithdrawStatus.PENDING
        )
        
        logger.info(
            f"Withdraw request {withdraw_request.id} created: "
            f"{amount} {currency} by {profile.get_display_name()}"
        )
        
        return withdraw_request
    
    @staticmethod
    def get_user_withdraw_requests(
        profile: 'Profile',
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> List['WithdrawRequest']:
        """
        Get withdrawal requests for a specific user.
        
        Args:
            profile: User profile
            limit: Maximum number of requests (None for all)
            status: Filter by status (None for all)
            
        Returns:
            List of WithdrawRequest instances
        """
        from .models import WithdrawRequest
        
        queryset = profile.withdraw_requests.all()
        
        if status:
            queryset = queryset.filter(status=status)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def format_withdraw_request_for_display(request: 'WithdrawRequest') -> str:
        """
        Format withdrawal request for display.
        
        Args:
            request: WithdrawRequest instance
            
        Returns:
            Formatted string
        """
        status_emoji = {
            'PENDING': '⏳',
            'PROCESSING': '🔄',
            'COMPLETED': '✅',
            'CANCELLED': '❌',
            'REJECTED': '🚫'
        }
        
        status_icon = status_emoji.get(request.status, '')
        
        text = (
            f"📤 *درخواست برداشت #{request.id}*\n"
            f"ارز: {request.get_currency_display()}\n"
            f"مقدار: {request.amount:,.2f}\n"
            f"بانک: {request.bank_account.bank_name}\n"
            f"شماره حساب: {request.bank_account.get_masked_account_number()}\n"
            f"وضعیت: {status_icon} {request.get_status_display()}\n"
            f"تاریخ: {request.created_at.strftime('%Y/%m/%d %H:%M')}\n"
        )
        
        if request.rejection_reason:
            text += f"\nدلیل رد: {request.rejection_reason}\n"
        
        return text


class BankAccountService:
    """Service class for bank account operations."""
    
    @staticmethod
    @transaction.atomic
    def create_bank_account(
        profile: 'Profile',
        bank_name: str,
        account_holder_name: str,
        account_number: str,
        iban: str = "",
        account_type: str = "SAVINGS"
    ) -> 'BankAccount':
        """
        Create a new bank account for user.
        
        Args:
            profile: User profile
            bank_name: Name of the bank
            account_holder_name: Name of account holder
            account_number: 16-digit account number
            iban: IBAN number (optional)
            account_type: Type of account (SAVINGS or CURRENT)
            
        Returns:
            Created BankAccount instance
            
        Raises:
            ValidationError: If account number is invalid or duplicate
        """
        from users.models import BankAccount
        
        # Validate account number
        if not account_number.isdigit() or len(account_number) != 16:
            raise ValidationError("شماره حساب باید دقیقاً 16 رقم باشد.")
        
        # Check for duplicate
        if BankAccount.objects.filter(
            profile=profile,
            account_number=account_number
        ).exists():
            raise ValidationError("این حساب بانکی قبلاً ثبت شده است.")
        
        # Create bank account
        bank_account = BankAccount.objects.create(
            profile=profile,
            bank_name=bank_name,
            account_holder_name=account_holder_name,
            account_number=account_number,
            iban=iban,
            account_type=account_type,
            is_verified=False  # Must be verified by admin
        )
        
        logger.info(
            f"Bank account {bank_account.id} created for {profile.get_display_name()}: "
            f"{bank_name} - {account_number[-4:]}"
        )
        
        return bank_account
    
    @staticmethod
    def get_user_bank_accounts(
        profile: 'Profile',
        verified_only: bool = False
    ) -> List['BankAccount']:
        """
        Get bank accounts for a user.
        
        Args:
            profile: User profile
            verified_only: Only return verified accounts
            
        Returns:
            List of BankAccount instances
        """
        from users.models import BankAccount
        
        queryset = profile.bank_accounts.all()
        
        if verified_only:
            queryset = queryset.filter(is_verified=True)
        
        return list(queryset)
    
    @staticmethod
    def format_bank_account_for_display(bank_account: 'BankAccount') -> str:
        """
        Format bank account for display.
        
        Args:
            bank_account: BankAccount instance
            
        Returns:
            Formatted string
        """
        status_icon = '✅' if bank_account.is_verified else '⏳'
        status_text = 'تأیید شده' if bank_account.is_verified else 'در انتظار تأیید'
        
        text = (
            f"🏦 *{bank_account.bank_name}*\n"
            f"صاحب حساب: {bank_account.account_holder_name}\n"
            f"شماره حساب: {bank_account.get_masked_account_number()}\n"
            f"نوع حساب: {bank_account.get_account_type_display()}\n"
            f"وضعیت: {status_icon} {status_text}\n"
        )
        
        return text
