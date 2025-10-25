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


class WalletService:
    """Service class for wallet operations."""
    
    @staticmethod
    def get_wallet_balance(profile: Profile) -> dict:
        """
        دریافت موجودی‌های کامل کاربر
        
        Args:
            profile: پروفایل کاربر
        
        Returns:
            Dict شامل موجودی‌های آزاد و مسدود شده
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
            'available_rial': profile.rial_balance - profile.frozen_rial_balance,
            'available_gold': profile.gold_balance_grams - profile.frozen_gold_balance,
            'available_coin': profile.coin_balance - profile.frozen_coin_balance,
            'available_dollar': profile.dollar_balance - profile.frozen_dollar_balance,
        }
    
    @staticmethod
    @transaction.atomic
    def freeze_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        مسدود کردن موجودی برای تراکنش
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز (RIAL, GOLD, COIN, DOLLAR)
            amount: مقدار
        
        Raises:
            ValidationError: اگر موجودی کافی نباشد
        """
        # Lock the row
        profile = Profile.objects.select_for_update().get(pk=profile.pk)
        
        if currency_type == 'RIAL':
            if profile.rial_balance < amount:
                raise ValidationError("موجودی ریالی کافی نیست.")
            profile.rial_balance -= amount
            profile.frozen_rial_balance += amount
        elif currency_type == 'GOLD':
            if profile.gold_balance_grams < amount:
                raise ValidationError("موجودی طلا کافی نیست.")
            profile.gold_balance_grams -= amount
            profile.frozen_gold_balance += amount
        elif currency_type == 'COIN':
            if profile.coin_balance < amount:
                raise ValidationError("موجودی سکه کافی نیست.")
            profile.coin_balance -= amount
            profile.frozen_coin_balance += amount
        elif currency_type == 'DOLLAR':
            if profile.dollar_balance < amount:
                raise ValidationError("موجودی دلار کافی نیست.")
            profile.dollar_balance -= amount
            profile.frozen_dollar_balance += amount
        else:
            raise ValidationError("نوع ارز نامعتبر است.")
        
        profile.save()
        logger.info(f"Froze {amount} {currency_type} for {profile.get_display_name()}")
    
    @staticmethod
    @transaction.atomic
    def unfreeze_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        آزاد کردن موجودی مسدود شده
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
        """
        profile = Profile.objects.select_for_update().get(pk=profile.pk)
        
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
        
        profile.save()
        logger.info(f"Unfroze {amount} {currency_type} for {profile.get_display_name()}")
    
    @staticmethod
    @transaction.atomic
    def deduct_frozen_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        کسر از موجودی مسدود شده (برای تکمیل تراکنش)
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
        """
        profile = Profile.objects.select_for_update().get(pk=profile.pk)
        
        if currency_type == 'RIAL':
            if profile.frozen_rial_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_rial_balance -= amount
        elif currency_type == 'GOLD':
            if profile.frozen_gold_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_gold_balance -= amount
        elif currency_type == 'COIN':
            if profile.frozen_coin_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_coin_balance -= amount
        elif currency_type == 'DOLLAR':
            if profile.frozen_dollar_balance < amount:
                raise ValidationError("موجودی مسدود شده کافی نیست.")
            profile.frozen_dollar_balance -= amount
        
        profile.save()
        logger.info(f"Deducted {amount} {currency_type} from frozen balance for {profile.get_display_name()}")
    
    @staticmethod
    @transaction.atomic
    def add_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> None:
        """
        افزودن موجودی
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
        """
        profile = Profile.objects.select_for_update().get(pk=profile.pk)
        
        if currency_type == 'RIAL':
            profile.rial_balance += amount
        elif currency_type == 'GOLD':
            profile.gold_balance_grams += amount
        elif currency_type == 'COIN':
            profile.coin_balance += amount
        elif currency_type == 'DOLLAR':
            profile.dollar_balance += amount
        
        profile.save()
        logger.info(f"Added {amount} {currency_type} to {profile.get_display_name()}")
    
    @staticmethod
    def check_sufficient_balance(
        profile: Profile,
        currency_type: str,
        amount: Decimal
    ) -> bool:
        """
        بررسی کفایت موجودی
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
        
        Returns:
            Boolean
        """
        if currency_type == 'RIAL':
            return (profile.rial_balance - profile.frozen_rial_balance) >= amount
        elif currency_type == 'GOLD':
            return (profile.gold_balance_grams - profile.frozen_gold_balance) >= amount
        elif currency_type == 'COIN':
            return (profile.coin_balance - profile.frozen_coin_balance) >= amount
        elif currency_type == 'DOLLAR':
            return (profile.dollar_balance - profile.frozen_dollar_balance) >= amount
        
        return False
    
    @staticmethod
    def format_wallet_display(profile: Profile) -> str:
        """
        فرمت کردن موجودی‌ها برای نمایش
        
        Args:
            profile: پروفایل کاربر
        
        Returns:
            متن فرمت شده
        """
        balances = WalletService.get_wallet_balance(profile)
        
        text = "💼 *کیف پول شما:*\n\n"
        
        text += f"💵 *موجودی ریالی:*\n"
        text += f"├─ آزاد: {balances['available_rial']:,} ریال\n"
        text += f"└─ مسدود شده: {balances['frozen_rial']:,} ریال\n\n"
        
        text += f"🪙 *موجودی طلا:*\n"
        text += f"├─ آزاد: {balances['available_gold']} گرم\n"
        text += f"└─ مسدود شده: {balances['frozen_gold']} گرم\n\n"
        
        text += f"🥇 *موجودی سکه:*\n"
        text += f"├─ آزاد: {balances['available_coin']} عدد\n"
        text += f"└─ مسدود شده: {balances['frozen_coin']} عدد\n\n"
        
        text += f"💵 *موجودی دلار:*\n"
        text += f"├─ آزاد: {balances['available_dollar']} دلار\n"
        text += f"└─ مسدود شده: {balances['frozen_dollar']} دلار\n"
        
        return text


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
    ) -> 'Transaction':
        """
        ایجاد تراکنش جدید
        
        Args:
            profile: پروفایل کاربر
            transaction_type: نوع تراکنش
            currency_type: نوع ارز
            amount: مقدار
            **kwargs: سایر فیلدها
        
        Returns:
            Transaction instance
        """
        from .models import Transaction
        
        # Get current balance
        balance_before = profile.get_available_balance(currency_type)
        
        # Generate transaction number
        transaction_number = Transaction.generate_transaction_number()
        
        # Calculate balance after (for display only, actual update happens later)
        if transaction_type in ['DEPOSIT', 'TRANSFER_RECEIVE', 'SELL']:
            balance_after = balance_before + amount
        elif transaction_type in ['WITHDRAW', 'TRANSFER_SEND', 'BUY']:
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
            status='PENDING',
            **kwargs
        )
        
        logger.info(f"Created transaction {txn.transaction_number} for {profile.get_display_name()}")
        
        return txn
    
    @staticmethod
    def get_user_transactions(
        profile: Profile,
        currency_type: Optional[str] = None,
        limit: int = 20,
        status: Optional[str] = None
    ) -> List['Transaction']:
        """
        دریافت تاریخچه تراکنش‌های کاربر
        
        Args:
            profile: پروفایل کاربر
            currency_type: فیلتر بر اساس نوع ارز
            limit: تعداد تراکنش‌ها
            status: فیلتر بر اساس وضعیت
        
        Returns:
            لیست تراکنش‌ها
        """
        from .models import Transaction
        
        queryset = Transaction.objects.filter(profile=profile)
        
        if currency_type:
            queryset = queryset.filter(currency_type=currency_type)
        
        if status:
            queryset = queryset.filter(status=status)
        
        return list(queryset.order_by('-created_at')[:limit])
    
    @staticmethod
    @transaction.atomic
    def complete_transaction(
        transaction_id: int,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        تکمیل تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import Transaction
        
        try:
            txn = Transaction.objects.select_related('profile').get(id=transaction_id)
            
            if txn.status != 'PENDING':
                return False, "این تراکنش قبلاً پردازش شده است."
            
            # Update transaction status
            txn.status = 'COMPLETED'
            txn.completed_at = timezone.now()
            txn.save()
            
            logger.info(f"Completed transaction {txn.transaction_number}")
            
            return True, "تراکنش با موفقیت تکمیل شد."
        except Transaction.DoesNotExist:
            return False, "تراکنش یافت نشد."
    
    @staticmethod
    @transaction.atomic
    def cancel_transaction(
        transaction_id: int,
        reason: str,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        لغو تراکنش
        
        Args:
            transaction_id: شناسه تراکنش
            reason: دلیل لغو
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import Transaction
        
        try:
            txn = Transaction.objects.get(id=transaction_id)
            
            if txn.status != 'PENDING':
                return False, "فقط تراکنش‌های در انتظار قابل لغو هستند."
            
            txn.status = 'CANCELLED'
            txn.admin_note = reason
            txn.save()
            
            logger.info(f"Cancelled transaction {txn.transaction_number}: {reason}")
            
            return True, "تراکنش لغو شد."
        except Transaction.DoesNotExist:
            return False, "تراکنش یافت نشد."


class DepositService:
    """Service class for deposit operations."""
    
    @staticmethod
    @transaction.atomic
    def create_deposit_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: Optional[int] = None,
        user_note: str = ""
    ) -> Tuple['Transaction', str]:
        """
        ایجاد درخواست واریز
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
            bank_account_id: شناسه حساب بانکی (اختیاری)
            user_note: یادداشت کاربر
        
        Returns:
            Tuple[Transaction, str]: تراکنش و پیام
        """
        # Create transaction
        txn = TransactionService.create_transaction(
            profile=profile,
            transaction_type='DEPOSIT',
            currency_type=currency_type,
            amount=amount,
            user_note=user_note
        )
        
        if bank_account_id:
            from users.models import BankAccount
            bank_account = BankAccount.objects.get(id=bank_account_id)
            txn.related_bank_account = bank_account
            txn.save()
        
        logger.info(f"Created deposit request: {txn.transaction_number}")
        
        return txn, "درخواست واریز با موفقیت ثبت شد و در انتظار تایید ادمین است."
    
    @staticmethod
    @transaction.atomic
    def approve_deposit(
        transaction_id: int,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        تایید واریز توسط ادمین
        
        Args:
            transaction_id: شناسه تراکنش
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import Transaction
        
        try:
            txn = Transaction.objects.select_related('profile').get(id=transaction_id)
            
            if txn.transaction_type != 'DEPOSIT':
                return False, "این تراکنش یک درخواست واریز نیست."
            
            if txn.status != 'PENDING':
                return False, "این تراکنش قبلاً پردازش شده است."
            
            # Add balance to user
            WalletService.add_balance(txn.profile, txn.currency_type, txn.amount)
            
            # Complete transaction
            txn.status = 'COMPLETED'
            txn.completed_at = timezone.now()
            txn.save()
            
            logger.info(f"Approved deposit {txn.transaction_number}")
            
            return True, "واریز تایید شد و به حساب کاربر اضافه گردید."
        except Transaction.DoesNotExist:
            return False, "تراکنش یافت نشد."
    
    @staticmethod
    @transaction.atomic
    def reject_deposit(
        transaction_id: int,
        reason: str,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        رد واریز
        
        Args:
            transaction_id: شناسه تراکنش
            reason: دلیل رد
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        return TransactionService.cancel_transaction(transaction_id, reason, admin_user)


class WithdrawService:
    """Service class for withdraw operations."""
    
    @staticmethod
    @transaction.atomic
    def create_withdraw_request(
        profile: Profile,
        currency_type: str,
        amount: Decimal,
        bank_account_id: int
    ) -> Tuple['WithdrawRequest', str]:
        """
        ایجاد درخواست برداشت
        
        Args:
            profile: پروفایل کاربر
            currency_type: نوع ارز
            amount: مقدار
            bank_account_id: شناسه حساب بانکی مقصد
        
        Returns:
            Tuple[WithdrawRequest, str]: درخواست برداشت و پیام
        """
        from .models import WithdrawRequest
        from users.models import BankAccount
        
        # Check balance
        if not WalletService.check_sufficient_balance(profile, currency_type, amount):
            raise ValidationError("موجودی کافی نیست.")
        
        # Check bank account
        bank_account = BankAccount.objects.get(id=bank_account_id, profile=profile)
        if not bank_account.can_be_used_for_transactions():
            raise ValidationError("این حساب بانکی تایید نشده یا غیرفعال است.")
        
        # Freeze balance
        WalletService.freeze_balance(profile, currency_type, amount)
        
        # Create transaction
        txn = TransactionService.create_transaction(
            profile=profile,
            transaction_type='WITHDRAW',
            currency_type=currency_type,
            amount=amount,
            related_bank_account_id=bank_account_id
        )
        
        # Create withdraw request
        request_number = WithdrawRequest.generate_request_number()
        withdraw_request = WithdrawRequest.objects.create(
            request_number=request_number,
            profile=profile,
            bank_account=bank_account,
            currency_type=currency_type,
            amount=amount,
            status='PENDING',
            related_transaction=txn
        )
        
        logger.info(f"Created withdraw request: {request_number}")
        
        return withdraw_request, "درخواست برداشت ثبت شد و موجودی مسدود گردید. در انتظار تایید ادمین."
    
    @staticmethod
    @transaction.atomic
    def approve_withdraw(
        withdraw_request_id: int,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        تایید برداشت
        
        Args:
            withdraw_request_id: شناسه درخواست برداشت
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import WithdrawRequest
        
        try:
            withdraw_request = WithdrawRequest.objects.select_related('profile', 'related_transaction').get(
                id=withdraw_request_id
            )
            
            if withdraw_request.status != 'PENDING':
                return False, "این درخواست قبلاً پردازش شده است."
            
            # Deduct from frozen balance
            WalletService.deduct_frozen_balance(
                withdraw_request.profile,
                withdraw_request.currency_type,
                withdraw_request.amount
            )
            
            # Update withdraw request
            withdraw_request.status = 'COMPLETED'
            withdraw_request.processed_at = timezone.now()
            withdraw_request.completed_at = timezone.now()
            withdraw_request.save()
            
            # Complete transaction
            if withdraw_request.related_transaction:
                withdraw_request.related_transaction.status = 'COMPLETED'
                withdraw_request.related_transaction.completed_at = timezone.now()
                withdraw_request.related_transaction.save()
            
            logger.info(f"Approved withdraw request: {withdraw_request.request_number}")
            
            return True, "درخواست برداشت تایید شد."
        except WithdrawRequest.DoesNotExist:
            return False, "درخواست برداشت یافت نشد."
    
    @staticmethod
    @transaction.atomic
    def reject_withdraw(
        withdraw_request_id: int,
        reason: str,
        admin_user: Optional[User] = None
    ) -> Tuple[bool, str]:
        """
        رد برداشت
        
        Args:
            withdraw_request_id: شناسه درخواست برداشت
            reason: دلیل رد
            admin_user: کاربر ادمین
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import WithdrawRequest
        
        try:
            withdraw_request = WithdrawRequest.objects.select_related('profile', 'related_transaction').get(
                id=withdraw_request_id
            )
            
            if withdraw_request.status != 'PENDING':
                return False, "این درخواست قبلاً پردازش شده است."
            
            # Unfreeze balance
            WalletService.unfreeze_balance(
                withdraw_request.profile,
                withdraw_request.currency_type,
                withdraw_request.amount
            )
            
            # Update withdraw request
            withdraw_request.status = 'REJECTED'
            withdraw_request.admin_note = reason
            withdraw_request.processed_at = timezone.now()
            withdraw_request.save()
            
            # Cancel transaction
            if withdraw_request.related_transaction:
                withdraw_request.related_transaction.status = 'CANCELLED'
                withdraw_request.related_transaction.admin_note = reason
                withdraw_request.related_transaction.save()
            
            logger.info(f"Rejected withdraw request: {withdraw_request.request_number} - {reason}")
            
            return True, "درخواست برداشت رد شد و موجودی آزاد گردید."
        except WithdrawRequest.DoesNotExist:
            return False, "درخواست برداشت یافت نشد."


class TransferService:
    """Service class for transfer operations."""
    
    @staticmethod
    def search_user_by_phone(phone_number: str) -> Optional[Profile]:
        """
        جستجوی کاربر بر اساس شماره تلفن
        
        Args:
            phone_number: شماره تلفن
        
        Returns:
            Profile یا None
        """
        try:
            profile = Profile.objects.get(phone_number=phone_number, is_approved=True)
            return profile
        except Profile.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def create_transfer_request(
        sender_profile: Profile,
        receiver_phone: str,
        currency_type: str,
        amount: Decimal,
        description: str = ""
    ) -> Tuple['TransferRequest', str]:
        """
        ایجاد درخواست انتقال وجه
        
        Args:
            sender_profile: پروفایل فرستنده
            receiver_phone: شماره تلفن گیرنده
            currency_type: نوع ارز
            amount: مقدار
            description: توضیحات
        
        Returns:
            Tuple[TransferRequest, str]: درخواست انتقال و پیام
        """
        from .models import TransferRequest
        
        # Find receiver
        receiver_profile = TransferService.search_user_by_phone(receiver_phone)
        if not receiver_profile:
            raise ValidationError("کاربری با این شماره تلفن یافت نشد.")
        
        # Check not sending to self
        if sender_profile.id == receiver_profile.id:
            raise ValidationError("نمی‌توانید به خودتان وجه منتقل کنید.")
        
        # Check balance
        if not WalletService.check_sufficient_balance(sender_profile, currency_type, amount):
            raise ValidationError("موجودی کافی نیست.")
        
        # Freeze sender's balance
        WalletService.freeze_balance(sender_profile, currency_type, amount)
        
        # Create sender transaction
        sender_txn = TransactionService.create_transaction(
            profile=sender_profile,
            transaction_type='TRANSFER_SEND',
            currency_type=currency_type,
            amount=amount,
            related_user=receiver_profile,
            user_note=description
        )
        
        # Create receiver transaction
        receiver_txn = TransactionService.create_transaction(
            profile=receiver_profile,
            transaction_type='TRANSFER_RECEIVE',
            currency_type=currency_type,
            amount=amount,
            related_user=sender_profile,
            user_note=description
        )
        
        # Create transfer request
        request_number = TransferRequest.generate_request_number()
        transfer_request = TransferRequest.objects.create(
            request_number=request_number,
            sender_profile=sender_profile,
            receiver_profile=receiver_profile,
            receiver_phone=receiver_phone,
            currency_type=currency_type,
            amount=amount,
            status='PENDING',
            sender_transaction=sender_txn,
            receiver_transaction=receiver_txn,
            description=description
        )
        
        # Auto-complete transfer (no admin approval needed for transfers)
        success, message = TransferService.complete_transfer(transfer_request.id)
        
        if not success:
            raise ValidationError(message)
        
        logger.info(f"Created and completed transfer request: {request_number}")
        
        return transfer_request, "انتقال وجه با موفقیت انجام شد."
    
    @staticmethod
    @transaction.atomic
    def complete_transfer(transfer_request_id: int) -> Tuple[bool, str]:
        """
        تکمیل انتقال
        
        Args:
            transfer_request_id: شناسه درخواست انتقال
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import TransferRequest
        
        try:
            transfer_request = TransferRequest.objects.select_related(
                'sender_profile', 'receiver_profile', 'sender_transaction', 'receiver_transaction'
            ).get(id=transfer_request_id)
            
            if transfer_request.status != 'PENDING':
                return False, "این انتقال قبلاً پردازش شده است."
            
            # Deduct from sender's frozen balance
            WalletService.deduct_frozen_balance(
                transfer_request.sender_profile,
                transfer_request.currency_type,
                transfer_request.amount
            )
            
            # Add to receiver's balance
            WalletService.add_balance(
                transfer_request.receiver_profile,
                transfer_request.currency_type,
                transfer_request.amount
            )
            
            # Complete transfer request
            transfer_request.status = 'COMPLETED'
            transfer_request.completed_at = timezone.now()
            transfer_request.save()
            
            # Complete transactions
            if transfer_request.sender_transaction:
                transfer_request.sender_transaction.status = 'COMPLETED'
                transfer_request.sender_transaction.completed_at = timezone.now()
                transfer_request.sender_transaction.save()
            
            if transfer_request.receiver_transaction:
                transfer_request.receiver_transaction.status = 'COMPLETED'
                transfer_request.receiver_transaction.completed_at = timezone.now()
                transfer_request.receiver_transaction.save()
            
            logger.info(f"Completed transfer request: {transfer_request.request_number}")
            
            return True, "انتقال وجه با موفقیت انجام شد."
        except TransferRequest.DoesNotExist:
            return False, "درخواست انتقال یافت نشد."
    
    @staticmethod
    @transaction.atomic
    def cancel_transfer(
        transfer_request_id: int,
        reason: str
    ) -> Tuple[bool, str]:
        """
        لغو انتقال
        
        Args:
            transfer_request_id: شناسه درخواست انتقال
            reason: دلیل لغو
        
        Returns:
            Tuple[bool, str]: موفقیت و پیام
        """
        from .models import TransferRequest
        
        try:
            transfer_request = TransferRequest.objects.select_related(
                'sender_profile', 'sender_transaction', 'receiver_transaction'
            ).get(id=transfer_request_id)
            
            if transfer_request.status != 'PENDING':
                return False, "فقط انتقال‌های در انتظار قابل لغو هستند."
            
            # Unfreeze sender's balance
            WalletService.unfreeze_balance(
                transfer_request.sender_profile,
                transfer_request.currency_type,
                transfer_request.amount
            )
            
            # Cancel transfer request
            transfer_request.status = 'CANCELLED'
            transfer_request.save()
            
            # Cancel transactions
            if transfer_request.sender_transaction:
                transfer_request.sender_transaction.status = 'CANCELLED'
                transfer_request.sender_transaction.admin_note = reason
                transfer_request.sender_transaction.save()
            
            if transfer_request.receiver_transaction:
                transfer_request.receiver_transaction.status = 'CANCELLED'
                transfer_request.receiver_transaction.admin_note = reason
                transfer_request.receiver_transaction.save()
            
            logger.info(f"Cancelled transfer request: {transfer_request.request_number} - {reason}")
            
            return True, "انتقال لغو شد."
        except TransferRequest.DoesNotExist:
            return False, "درخواست انتقال یافت نشد."
