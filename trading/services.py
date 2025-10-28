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

from .models import Product, Order, Transaction, WithdrawRequest
from users.models import Profile, BankAccount
from users.wallet_services import WalletService

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
    """Service class for transaction operations."""
    
    @staticmethod
    @transaction.atomic
    def create_transaction(
        profile: Profile,
        transaction_type: str,
        currency_type: str,
        amount: Decimal,
        **kwargs
    ) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            profile: User profile.
            transaction_type: Type of transaction.
            currency_type: Type of currency.
            amount: Transaction amount.
            **kwargs: Additional fields (related_bank_account, related_order, etc.).
            
        Returns:
            Created Transaction instance.
        """
        # Get current balance
        balance_before = WalletService.get_available_balance(profile, currency_type)
        
        # Create transaction
        transaction_obj = Transaction.objects.create(
            profile=profile,
            transaction_type=transaction_type,
            currency_type=currency_type,
            amount=amount,
            balance_before=balance_before,
            balance_after=balance_before,  # Will be updated when completed
            **kwargs
        )
        
        logger.info(
            f"Transaction {transaction_obj.transaction_number} created: "
            f"{transaction_type} {amount} {currency_type} for {profile.get_display_name()}"
        )
        
        return transaction_obj
    
    @staticmethod
    def get_user_transactions(
        profile: Profile,
        currency_type: Optional[str] = None,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List[Transaction]:
        """
        Get user's transactions with filtering.
        
        Args:
            profile: User profile.
            currency_type: Filter by currency type.
            limit: Maximum number of transactions to return.
            status: Filter by status.
            
        Returns:
            List of Transaction instances.
        """
        queryset = profile.transactions.all()
        
        if currency_type:
            queryset = queryset.filter(currency_type=currency_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset[:limit])
    
    @staticmethod
    @transaction.atomic
    def complete_transaction(transaction_id: int, admin_user=None) -> Transaction:
        """
        Complete a transaction.
        
        Args:
            transaction_id: ID of the transaction.
            admin_user: Admin user completing the transaction.
            
        Returns:
            Updated Transaction instance.
        """
        transaction_obj = Transaction.objects.get(id=transaction_id)
        
        if not transaction_obj.is_pending():
            raise ValidationError("تراکنش در وضعیت نامناسب برای تکمیل است.")
        
        # Update balance based on transaction type
        if transaction_obj.transaction_type in ['DEPOSIT', 'SELL', 'TRANSFER_RECEIVE']:
            WalletService.add_balance(
                transaction_obj.profile,
                transaction_obj.currency_type,
                transaction_obj.amount
            )
        elif transaction_obj.transaction_type in ['WITHDRAW', 'BUY', 'TRANSFER_SEND']:
            WalletService.deduct_balance(
                transaction_obj.profile,
                transaction_obj.currency_type,
                transaction_obj.amount
            )
        
        # Update transaction
        transaction_obj.status = Transaction.TransactionStatus.COMPLETED
        transaction_obj.completed_at = timezone.now()
        transaction_obj.balance_after = WalletService.get_available_balance(
            transaction_obj.profile,
            transaction_obj.currency_type
        )
        transaction_obj.save()
        
        logger.info(
            f"Transaction {transaction_obj.transaction_number} completed by {admin_user}"
        )
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def cancel_transaction(transaction_id: int, reason: str, admin_user=None) -> Transaction:
        """
        Cancel a transaction.
        
        Args:
            transaction_id: ID of the transaction.
            reason: Reason for cancellation.
            admin_user: Admin user cancelling the transaction.
            
        Returns:
            Updated Transaction instance.
        """
        transaction_obj = Transaction.objects.get(id=transaction_id)
        
        if not transaction_obj.can_be_cancelled():
            raise ValidationError("تراکنش قابل لغو نیست.")
        
        # If it's a withdraw transaction, unfreeze the balance
        if transaction_obj.transaction_type == 'WITHDRAW':
            WalletService.unfreeze_balance(
                transaction_obj.profile,
                transaction_obj.currency_type,
                transaction_obj.amount
            )
        
        # Update transaction
        transaction_obj.status = Transaction.TransactionStatus.CANCELLED
        transaction_obj.admin_note = reason
        transaction_obj.save()
        
        logger.info(
            f"Transaction {transaction_obj.transaction_number} cancelled: {reason}"
        )
        
        return transaction_obj
    
    @staticmethod
    def format_transaction_for_display(transaction_obj: Transaction) -> str:
        """
        Format transaction for display in Telegram.
        
        Args:
            transaction_obj: Transaction instance.
            
        Returns:
            Formatted string.
        """
        status_emoji = {
            Transaction.TransactionStatus.PENDING: "🕐",
            Transaction.TransactionStatus.COMPLETED: "✅",
            Transaction.TransactionStatus.CANCELLED: "❌",
            Transaction.TransactionStatus.FAILED: "⚠️",
        }
        
        type_emoji = {
            Transaction.TransactionType.DEPOSIT: "💰",
            Transaction.TransactionType.WITHDRAW: "💸",
            Transaction.TransactionType.BUY: "📈",
            Transaction.TransactionType.SELL: "📉",
            Transaction.TransactionType.TRANSFER_SEND: "📤",
            Transaction.TransactionType.TRANSFER_RECEIVE: "📥",
        }
        
        emoji = type_emoji.get(transaction_obj.transaction_type, "💳")
        status_icon = status_emoji.get(transaction_obj.status, "")
        
        text = f"┌─────────────────────────\n"
        text += f"│ {emoji} {transaction_obj.get_transaction_type_display()}\n"
        text += f"│ 💰 مبلغ: {transaction_obj.amount:,.4f} {transaction_obj.get_currency_type_display()}\n"
        text += f"│ 📅 {transaction_obj.created_at.strftime('%Y/%m/%d - %H:%M')}\n"
        text += f"│ {status_icon} {transaction_obj.get_status_display()}\n"
        text += f"│ 🔢 {transaction_obj.transaction_number}\n"
        text += f"└─────────────────────────"
        
        return text


class DepositService:
    """Service class for deposit operations."""
    
    @staticmethod
    @transaction.atomic
    def create_deposit_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: int,
        receipt_image=None
    ) -> Transaction:
        """
        Create a deposit request.
        
        Args:
            profile: User profile.
            currency_type: Type of currency to deposit.
            amount: Amount to deposit.
            bank_account_id: ID of source bank account.
            receipt_image: Optional receipt image.
            
        Returns:
            Created Transaction instance.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Validate bank account
        try:
            bank_account = BankAccount.objects.get(
                id=bank_account_id,
                profile=profile,
                is_verified=True,
                is_active=True
            )
        except BankAccount.DoesNotExist:
            raise ValidationError("حساب بانکی تایید شده یافت نشد.")
        
        # Create transaction
        transaction_obj = TransactionService.create_transaction(
            profile=profile,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            currency_type=currency_type,
            amount=amount,
            related_bank_account=bank_account,
            user_note=f"واریز از حساب {bank_account.bank_name}"
        )
        
        # TODO: Send notification to admin
        
        return transaction_obj
    
    @staticmethod
    @transaction.atomic
    def approve_deposit(transaction_id: int, admin_user) -> Transaction:
        """
        Approve a deposit request.
        
        Args:
            transaction_id: ID of the deposit transaction.
            admin_user: Admin user approving the deposit.
            
        Returns:
            Updated Transaction instance.
        """
        return TransactionService.complete_transaction(transaction_id, admin_user)
    
    @staticmethod
    def reject_deposit(transaction_id: int, reason: str, admin_user) -> Transaction:
        """
        Reject a deposit request.
        
        Args:
            transaction_id: ID of the deposit transaction.
            reason: Reason for rejection.
            admin_user: Admin user rejecting the deposit.
            
        Returns:
            Updated Transaction instance.
        """
        return TransactionService.cancel_transaction(transaction_id, reason, admin_user)


class WithdrawService:
    """Service class for withdrawal operations."""
    
    @staticmethod
    @transaction.atomic
    def create_withdraw_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: int
    ) -> WithdrawRequest:
        """
        Create a withdrawal request.
        
        Args:
            profile: User profile.
            currency_type: Type of currency to withdraw.
            amount: Amount to withdraw.
            bank_account_id: ID of destination bank account.
            
        Returns:
            Created WithdrawRequest instance.
            
        Raises:
            ValidationError: If validation fails.
        """
        # Validate bank account
        try:
            bank_account = BankAccount.objects.get(
                id=bank_account_id,
                profile=profile,
                is_verified=True,
                is_active=True
            )
        except BankAccount.DoesNotExist:
            raise ValidationError("حساب بانکی تایید شده یافت نشد.")
        
        # Check sufficient balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            raise ValidationError(f"موجودی {currency_type} کافی نیست.")
        
        # Freeze the balance
        WalletService.freeze_balance(profile, currency_type, amount)
        
        # Create withdraw request
        withdraw_request = WithdrawRequest.objects.create(
            profile=profile,
            bank_account=bank_account,
            currency_type=currency_type,
            amount=amount
        )
        
        # Create related transaction
        transaction_obj = TransactionService.create_transaction(
            profile=profile,
            transaction_type=Transaction.TransactionType.WITHDRAW,
            currency_type=currency_type,
            amount=amount,
            related_bank_account=bank_account
        )
        
        # Link transaction to withdraw request
        withdraw_request.related_transaction = transaction_obj
        withdraw_request.save()
        
        # TODO: Send notification to admin
        
        return withdraw_request
    
    @staticmethod
    @transaction.atomic
    def approve_withdraw(withdraw_request_id: int, admin_user) -> WithdrawRequest:
        """
        Approve a withdrawal request.
        
        Args:
            withdraw_request_id: ID of the withdraw request.
            admin_user: Admin user approving the withdrawal.
            
        Returns:
            Updated WithdrawRequest instance.
        """
        withdraw_request = WithdrawRequest.objects.get(id=withdraw_request_id)
        
        if not withdraw_request.can_be_approved():
            raise ValidationError("درخواست قابل تایید نیست.")
        
        # Complete the transaction (this will deduct from frozen balance)
        TransactionService.complete_transaction(
            withdraw_request.related_transaction.id,
            admin_user
        )
        
        # Update withdraw request
        withdraw_request.status = WithdrawRequest.WithdrawStatus.COMPLETED
        withdraw_request.processed_at = timezone.now()
        withdraw_request.completed_at = timezone.now()
        withdraw_request.save()
        
        # TODO: Send notification to user
        
        return withdraw_request
    
    @staticmethod
    @transaction.atomic
    def reject_withdraw(withdraw_request_id: int, reason: str, admin_user) -> WithdrawRequest:
        """
        Reject a withdrawal request.
        
        Args:
            withdraw_request_id: ID of the withdraw request.
            reason: Reason for rejection.
            admin_user: Admin user rejecting the withdrawal.
            
        Returns:
            Updated WithdrawRequest instance.
        """
        withdraw_request = WithdrawRequest.objects.get(id=withdraw_request_id)
        
        if not withdraw_request.can_be_rejected():
            raise ValidationError("درخواست قابل رد نیست.")
        
        # Unfreeze the balance
        WalletService.unfreeze_balance(
            withdraw_request.profile,
            withdraw_request.currency_type,
            withdraw_request.amount
        )
        
        # Cancel the transaction
        TransactionService.cancel_transaction(
            withdraw_request.related_transaction.id,
            reason,
            admin_user
        )
        
        # Update withdraw request
        withdraw_request.status = WithdrawRequest.WithdrawStatus.REJECTED
        withdraw_request.processed_at = timezone.now()
        withdraw_request.admin_note = reason
        withdraw_request.save()
        
        # TODO: Send notification to user
        
        return withdraw_request
