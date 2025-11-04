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

logger = logging.getLogger('trading')


class TradingService:
    """Service class for trading-related operations like price updates."""
    
    @staticmethod
    def update_all_prices() -> bool:
        """
        Update all product prices from the API.
        
        Fetches current prices from the configured price provider,
        calculates final prices with margins, and updates all products.
        
        Returns:
            bool: True if prices were updated successfully, False otherwise.
        """
        from .price_providers import get_active_provider
        from .price_calculator import PriceCalculator
        
        try:
            # Get price provider
            provider = get_active_provider()
            logger.info("Fetching prices from API...")
            
            # Fetch API prices
            api_prices = provider.get_all_prices()
            api_gold_price = api_prices.get('gold')
            api_dollar_buy = api_prices.get('dollar_buy')
            api_dollar_sell = api_prices.get('dollar_sell')
            
            # Validate that we got all prices
            if not all([api_gold_price, api_dollar_buy, api_dollar_sell]):
                logger.error("Failed to fetch all required prices from API")
                return False
            
            # Calculate final prices with margins
            all_prices = PriceCalculator.calculate_all_prices(
                api_gold_price,
                api_dollar_buy,
                api_dollar_sell
            )
            
            if not all_prices:
                logger.error("Failed to calculate prices")
                return False
            
            # Update products
            updated_count = 0
            
            # Update gold product
            try:
                gold = Product.objects.get(product_code=Product.PRODUCT_CODE_GOLD)
                gold.buy_price = all_prices.gold_abshodeh.buy_price
                gold.sell_price = all_prices.gold_abshodeh.sell_price
                gold.save()
                logger.info(f"Updated gold prices: Buy={gold.buy_price}, Sell={gold.sell_price}")
                updated_count += 1
            except Product.DoesNotExist:
                logger.warning("Gold product not found in database")
            
            # Update coin product
            try:
                coin = Product.objects.get(product_code=Product.PRODUCT_CODE_COIN)
                coin.buy_price = all_prices.coin_full.buy_price
                coin.sell_price = all_prices.coin_full.sell_price
                coin.save()
                logger.info(f"Updated coin prices: Buy={coin.buy_price}, Sell={coin.sell_price}")
                updated_count += 1
            except Product.DoesNotExist:
                logger.warning("Coin product not found in database")
            
            # Update dollar product
            try:
                dollar = Product.objects.get(product_code=Product.PRODUCT_CODE_DOLLAR)
                dollar.buy_price = all_prices.dollar.buy_price
                dollar.sell_price = all_prices.dollar.sell_price
                dollar.save()
                logger.info(f"Updated dollar prices: Buy={dollar.buy_price}, Sell={dollar.sell_price}")
                updated_count += 1
            except Product.DoesNotExist:
                logger.warning("Dollar product not found in database")
            
            logger.info(f"Successfully updated {updated_count} products")
            return updated_count > 0
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}", exc_info=True)
            return False


class ProductService:
    """Service class for Product-related operations."""
    
    @staticmethod
    def get_active_products() -> List[Product]:
        """
        Get all active products available for trading.
        
        Returns:
            List of active Product instances, ordered by name.
        """
        return list(Product.objects.filter(is_active=True).order_by('name'))
    
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
    @transaction.atomic
    def execute_instant_order(
        profile: Profile,
        product: Product,
        order_type: str,
        amount: Decimal,
        calculation_method: str = 'grams'
    ) -> Order:
        """
        Execute an order instantly with atomic transaction.
        
        This is the new primary function for all trades. It combines validation,
        order creation, and balance updates into a single atomic operation.
        
        Args:
            profile: User profile placing the order.
            product: Product being traded.
            order_type: 'BUY' or 'SELL'
            amount: Amount in grams or rial (based on calculation_method)
            calculation_method: 'grams' or 'rial'
            
        Returns:
            Created and completed Order instance.
            
        Raises:
            ValidationError: If user cannot trade, insufficient balance, or inputs are invalid.
        """
        # 1. Validate user can trade
        if not profile.can_trade():
            raise ValidationError(
                "حساب شما هنوز تأیید نشده است. "
                "لطفاً منتظر تأیید مدیر باشید."
            )
        
        # 2. Validate product is active
        if not product.is_active:
            raise ValidationError("این محصول در حال حاضر غیرفعال است.")
        
        # 3. Fetch latest real-time price and calculate order details
        quantity_grams, price_per_gram, total_amount = OrderService.calculate_order_details(
            product=product,
            order_type=order_type,
            amount=amount,
            calculation_method=calculation_method
        )
        
        # 4. Validate balances
        if order_type == Order.OrderType.BUY:
            is_valid, error_msg = OrderService.validate_buy_balance(
                profile=profile,
                total_amount=total_amount
            )
            if not is_valid:
                # Create REJECTED order for audit trail
                order = Order.objects.create(
                    profile=profile,
                    product=product,
                    order_type=order_type,
                    quantity_grams=quantity_grams,
                    price_per_gram=price_per_gram,
                    total_amount=total_amount,
                    status=Order.OrderStatus.REJECTED,
                    notes=f"Rejected: {error_msg}"
                )
                raise ValidationError(error_msg)
        
        elif order_type == Order.OrderType.SELL:
            is_valid, error_msg = OrderService.validate_sell_balance(
                profile=profile,
                product=product,
                quantity_grams=quantity_grams
            )
            if not is_valid:
                # Create REJECTED order for audit trail
                order = Order.objects.create(
                    profile=profile,
                    product=product,
                    order_type=order_type,
                    quantity_grams=quantity_grams,
                    price_per_gram=price_per_gram,
                    total_amount=total_amount,
                    status=Order.OrderStatus.REJECTED,
                    notes=f"Rejected: {error_msg}"
                )
                raise ValidationError(error_msg)
        
        # 5. Execute balance updates
        if order_type == Order.OrderType.BUY:
            # Buy: Deduct Rial, Add Product
            profile.rial_balance -= total_amount
            
            # Add Product based on currency type
            currency_type = OrderService.get_product_currency_type(product)
            if currency_type == 'GOLD':
                profile.gold_balance_grams += quantity_grams
            elif currency_type == 'COIN':
                profile.coin_balance += quantity_grams
            elif currency_type == 'DOLLAR':
                profile.dollar_balance += quantity_grams
        
        elif order_type == Order.OrderType.SELL:
            # Sell: Deduct Product, Add Rial
            currency_type = OrderService.get_product_currency_type(product)
            if currency_type == 'GOLD':
                profile.gold_balance_grams -= quantity_grams
            elif currency_type == 'COIN':
                profile.coin_balance -= quantity_grams
            elif currency_type == 'DOLLAR':
                profile.dollar_balance -= quantity_grams
            
            # Add Rial
            profile.rial_balance += total_amount
        
        # 6. Save updated profile
        profile.save()
        
        # 7. Create order with COMPLETED status
        order = Order.objects.create(
            profile=profile,
            product=product,
            order_type=order_type,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount,
            status=Order.OrderStatus.COMPLETED,
            completed_at=timezone.now()
        )
        
        # 8. Create corresponding Transaction record for audit trail
        from trading.models import Transaction
        
        # Determine currency for transaction
        currency_type = OrderService.get_product_currency_type(product)
        transaction_type = Transaction.TransactionType.BUY if order_type == Order.OrderType.BUY else Transaction.TransactionType.SELL
        
        Transaction.objects.create(
            profile=profile,
            transaction_type=transaction_type,
            currency=currency_type,
            amount=quantity_grams,
            status=Transaction.TransactionStatus.COMPLETED,
            related_order=order,
            description=f"{'خرید' if order_type == Order.OrderType.BUY else 'فروش'} {quantity_grams} {OrderService.get_product_unit(product)} {product.name}",
            completed_at=timezone.now()
        )
        
        logger.info(
            f"Instant order {order.id} executed: {order_type} "
            f"{quantity_grams}g of {product.name} "
            f"by user {profile.get_display_name()}"
        )
        
        return order
    
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
        DEPRECATED: Use execute_instant_order() instead.
        
        Create a new order (in PENDING status).
        This function is deprecated in favor of instant execution.
        
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
        
        # Create the order with COMPLETED status (instant execution model)
        order = Order.objects.create(
            profile=profile,
            product=product,
            order_type=order_type,
            quantity_grams=quantity_grams,
            price_per_gram=price_per_gram,
            total_amount=total_amount,
            status=Order.OrderStatus.COMPLETED,
            completed_at=timezone.now()
        )
        
        logger.info(
            f"Order {order.id} created: {order_type} "  # type: ignore[attr-defined]
            f"{quantity_grams}g of {product.name} "
            f"by user {profile.get_display_name()}"
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def complete_order(
        order: Order,
        execute_immediately: bool = True
    ) -> Order:
        """
        DEPRECATED: Use execute_instant_order() instead.
        
        Complete an order and update balances.
        This function is deprecated in favor of instant execution.
        
        Args:
            order: Order instance to complete.
            execute_immediately: If True, execute balance changes immediately.
                                If False, just mark as completed (for admin processing).
            
        Returns:
            Updated Order instance.
            
        Raises:
            ValidationError: If balance is insufficient or order is invalid.
        """
        if order.status == Order.OrderStatus.COMPLETED:
            raise ValidationError("این سفارش قبلاً تکمیل شده است.")
        
        if order.status == Order.OrderStatus.CANCELLED:
            raise ValidationError("این سفارش لغو شده است.")
        
        if execute_immediately:
            # Validate and execute balance changes
            if order.order_type == Order.OrderType.BUY:
                # Buy: Deduct Rial, Add Product
                if not order.profile.has_sufficient_rial_balance(order.total_amount):
                    raise ValidationError(
                        f"موجودی ریالی کافی نیست. "
                        f"مورد نیاز: {order.total_amount:,} ریال"
                    )
                
                # Deduct Rial
                order.profile.rial_balance -= order.total_amount
                
                # Add Product
                currency_type = OrderService.get_product_currency_type(order.product)
                if currency_type == 'GOLD':
                    order.profile.gold_balance_grams += order.quantity_grams
                elif currency_type == 'COIN':
                    order.profile.coin_balance += order.quantity_grams
                elif currency_type == 'DOLLAR':
                    order.profile.dollar_balance += order.quantity_grams
                
            elif order.order_type == Order.OrderType.SELL:
                # Sell: Deduct Product, Add Rial
                currency_type = OrderService.get_product_currency_type(order.product)
                current_balance = OrderService.get_product_balance(order.profile, order.product)
                
                if current_balance < order.quantity_grams:
                    raise ValidationError(
                        f"موجودی {order.product.name} کافی نیست. "
                        f"مورد نیاز: {order.quantity_grams}"
                    )
                
                # Deduct Product
                if currency_type == 'GOLD':
                    order.profile.gold_balance_grams -= order.quantity_grams
                elif currency_type == 'COIN':
                    order.profile.coin_balance -= order.quantity_grams
                elif currency_type == 'DOLLAR':
                    order.profile.dollar_balance -= order.quantity_grams
                
                # Add Rial
                order.profile.rial_balance += order.total_amount
            
            # Save profile with updated balances
            order.profile.save()
        
        # Mark order as completed
        order.status = Order.OrderStatus.COMPLETED
        order.save()
        
        logger.info(
            f"Order {order.id} completed: {order.order_type} "  # type: ignore[attr-defined]
            f"{order.quantity_grams}g of {order.product.name} "
            f"by user {order.profile.get_display_name()}"
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
        # Use select_related to prefetch related product to avoid N+1 queries
        queryset = profile.orders.select_related('product').all()  # type: ignore[attr-defined]
        
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
        order_type_text = order.get_order_type_display()  # type: ignore[attr-defined]
        
        text = (
            f"{order_type_emoji} *سفارش #{order.id}*\n"  # type: ignore[attr-defined]
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
            text += f"{emoji} وضعیت: {order.get_status_display()}\n"  # type: ignore[attr-defined]
        
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
    
    @staticmethod
    def format_order_invoice(
        profile: Profile,
        product: Product,
        order_type: str,
        quantity_grams: Decimal,
        price_per_gram: Decimal,
        total_amount: Decimal
    ) -> str:
        """
        Format detailed order invoice with balance information.
        
        Args:
            profile: User profile.
            product: Product instance.
            order_type: 'BUY' or 'SELL'
            quantity_grams: Quantity in grams.
            price_per_gram: Price per gram.
            total_amount: Total amount in Rial.
            
        Returns:
            Formatted invoice string with balance details.
        """
        order_type_text = "خرید" if order_type == Order.OrderType.BUY else "فروش"
        order_type_emoji = "📈" if order_type == Order.OrderType.BUY else "📉"
        
        # Get product currency type
        product_currency = OrderService.get_product_currency_type(product)
        
        # Get current balances
        current_rial = profile.rial_balance
        current_product_balance = OrderService.get_product_balance(profile, product)
        
        # Calculate final balances
        if order_type == Order.OrderType.BUY:
            final_rial = current_rial - total_amount
            final_product_balance = current_product_balance + quantity_grams
            payment_text = f"💳 *پرداخت:* {total_amount:,} ریال"
            receive_text = f"📥 *دریافت:* {quantity_grams} {OrderService.get_product_unit(product)}"
        else:  # SELL
            final_rial = current_rial + total_amount
            final_product_balance = current_product_balance - quantity_grams
            payment_text = f"📤 *تحویل:* {quantity_grams} {OrderService.get_product_unit(product)}"
            receive_text = f"💰 *دریافت:* {total_amount:,} ریال"
        
        invoice = (
            f"🧾 *فاکتور {order_type_text}*\n"
            f"{'═' * 25}\n\n"
            f"📦 *محصول:* {product.name}\n"
            f"💎 *قیمت هر {OrderService.get_product_unit(product)}:* {price_per_gram:,} ریال\n"
            f"⚖️ *مقدار:* {quantity_grams} {OrderService.get_product_unit(product)}\n"
            f"💵 *مبلغ کل:* {total_amount:,} ریال\n\n"
            f"{payment_text}\n"
            f"{receive_text}\n\n"
            f"{'─' * 25}\n"
            f"💼 *موجودی‌ها:*\n\n"
            f"*ریال:*\n"
            f"  • فعلی: {current_rial:,} ریال\n"
            f"  • پس از معامله: {final_rial:,} ریال\n\n"
            f"*{product.name}:*\n"
            f"  • فعلی: {current_product_balance} {OrderService.get_product_unit(product)}\n"
            f"  • پس از معامله: {final_product_balance} {OrderService.get_product_unit(product)}\n"
            f"{'═' * 25}\n\n"
            f"آیا از انجام این معامله مطمئن هستید؟"
        )
        
        return invoice
    
    @staticmethod
    def get_product_currency_type(product: Product) -> str:
        """
        Get currency type for a product based on product code.
        
        Args:
            product: Product instance.
            
        Returns:
            Currency type string ('RIAL', 'GOLD', 'COIN', 'DOLLAR').
        """
        from bot.constants import PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR
        
        if product.product_code == PRODUCT_GOLD:
            return 'GOLD'
        elif product.product_code == PRODUCT_COIN:
            return 'COIN'
        elif product.product_code == PRODUCT_DOLLAR:
            return 'DOLLAR'
        else:
            return 'GOLD'  # Default to GOLD
    
    @staticmethod
    def get_product_balance(profile: Profile, product: Product) -> Decimal:
        """
        Get user's balance for a specific product.
        
        Args:
            profile: User profile.
            product: Product instance.
            
        Returns:
            Balance amount for the product.
        """
        currency_type = OrderService.get_product_currency_type(product)
        
        if currency_type == 'GOLD':
            return profile.gold_balance_grams
        elif currency_type == 'COIN':
            return profile.coin_balance
        elif currency_type == 'DOLLAR':
            return profile.dollar_balance
        else:
            return Decimal('0')
    
    @staticmethod
    def get_product_unit(product: Product) -> str:
        """
        Get unit text for a product.
        
        Args:
            product: Product instance.
            
        Returns:
            Unit text in Persian.
        """
        from bot.constants import PRODUCT_GOLD, PRODUCT_COIN, PRODUCT_DOLLAR
        
        if product.product_code == PRODUCT_GOLD:
            return 'گرم'
        elif product.product_code == PRODUCT_COIN:
            return 'عدد'
        elif product.product_code == PRODUCT_DOLLAR:
            return 'دلار'
        else:
            return 'گرم'
    
    @staticmethod
    def validate_buy_balance(
        profile: Profile,
        total_amount: Decimal
    ) -> tuple[bool, str]:
        """
        Validate if user has sufficient Rial balance for buying.
        
        Args:
            profile: User profile.
            total_amount: Total amount in Rial required.
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not profile.has_sufficient_rial_balance(total_amount):
            error_msg = (
                f"❌ *موجودی ریالی کافی نیست!*\n\n"
                f"💼 موجودی فعلی: {profile.rial_balance:,} ریال\n"
                f"💰 مورد نیاز: {total_amount:,} ریال\n"
                f"⚠️ کمبود: {(total_amount - profile.rial_balance):,} ریال\n\n"
                f"لطفاً ابتدا کیف پول خود را شارژ کنید."
            )
            return False, error_msg
        return True, ""
    
    @staticmethod
    def validate_sell_balance(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal
    ) -> tuple[bool, str]:
        """
        Validate if user has sufficient product balance for selling.
        
        Args:
            profile: User profile.
            product: Product instance.
            quantity_grams: Quantity to sell.
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        currency_type = OrderService.get_product_currency_type(product)
        current_balance = OrderService.get_product_balance(profile, product)
        unit = OrderService.get_product_unit(product)
        
        if current_balance < quantity_grams:
            error_msg = (
                f"❌ *موجودی {product.name} کافی نیست!*\n\n"
                f"💼 موجودی فعلی: {current_balance} {unit}\n"
                f"📤 مورد نیاز: {quantity_grams} {unit}\n"
                f"⚠️ کمبود: {(quantity_grams - current_balance)} {unit}\n\n"
                f"شما نمی‌توانید بیشتر از موجودی خود بفروشید."
            )
            return False, error_msg
        return True, ""


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
        profile: Profile,
        currency: str,
        amount: Decimal,
        bank_account: Optional[BankAccount] = None,
        receipt_image = None,
        description: str = ""
    ) -> Transaction:
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
            f"Deposit transaction {transaction_obj.id} created: "  # type: ignore[attr-defined]
            f"{amount} {currency} by {profile.get_display_name()}"
        )
        
        return transaction_obj
    
    @staticmethod
    def get_user_transactions(
        profile: Profile,
        limit: Optional[int] = None,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> List[Transaction]:
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
        queryset = profile.transactions.all()  # type: ignore[attr-defined]
        
        if status:
            queryset = queryset.filter(status=status)
        
        if transaction_type:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def format_transaction_for_display(transaction: Transaction) -> str:
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
            f"{emoji} *تراکنش #{transaction.id}*\n"  # type: ignore[attr-defined]
            f"نوع: {transaction.get_transaction_type_display()}\n"  # type: ignore[attr-defined]
            f"ارز: {transaction.get_currency_display_name()}\n"
            f"مقدار: {transaction.amount:,.2f}\n"
            f"وضعیت: {status_icon} {transaction.get_status_display()}\n"  # type: ignore[attr-defined]
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
        profile: Profile,
        currency: str,
        amount: Decimal,
        bank_account: BankAccount
    ) -> WithdrawRequest:
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
        from users.services import WalletService
        
        # Validate bank account
        if not bank_account.is_verified:
            raise ValidationError("حساب بانکی تأیید نشده است.")
        
        if bank_account.profile != profile:
            raise ValidationError("این حساب بانکی متعلق به شما نیست.")
        
        # Freeze balance
        try:
            WalletService.freeze_balance(profile, currency, amount)
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
            f"Withdraw request {withdraw_request.id} created: "  # type: ignore[attr-defined]
            f"{amount} {currency} by {profile.get_display_name()}"
        )
        
        return withdraw_request
    
    @staticmethod
    def get_user_withdraw_requests(
        profile: Profile,
        limit: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[WithdrawRequest]:
        """
        Get withdrawal requests for a specific user.
        
        Args:
            profile: User profile
            limit: Maximum number of requests (None for all)
            status: Filter by status (None for all)
            
        Returns:
            List of WithdrawRequest instances
        """
        queryset = profile.withdraw_requests.all()  # type: ignore[attr-defined]
        
        if status:
            queryset = queryset.filter(status=status)
        
        if limit:
            queryset = queryset[:limit]
        
        return list(queryset)
    
    @staticmethod
    def format_withdraw_request_for_display(request: WithdrawRequest) -> str:
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
            f"📤 *درخواست برداشت #{request.id}*\n"  # type: ignore[attr-defined]
            f"ارز: {request.get_currency_display()}\n"  # type: ignore[attr-defined]
            f"مقدار: {request.amount:,.2f}\n"
            f"بانک: {request.bank_account.bank_name}\n"
            f"شماره حساب: {request.bank_account.get_masked_account_number()}\n"
            f"وضعیت: {status_icon} {request.get_status_display()}\n"  # type: ignore[attr-defined]
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
        profile: Profile,
        bank_name: str,
        account_holder_name: str,
        account_number: str,
        iban: str = "",
        account_type: str = "SAVINGS"
    ) -> BankAccount:
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
            f"Bank account {bank_account.id} created for {profile.get_display_name()}: "  # type: ignore[attr-defined]
            f"{bank_name} - {account_number[-4:]}"
        )
        
        return bank_account
    
    @staticmethod
    def get_user_bank_accounts(
        profile: Profile,
        verified_only: bool = False
    ) -> List[BankAccount]:
        """
        Get bank accounts for a user.
        
        Args:
            profile: User profile
            verified_only: Only return verified accounts
            
        Returns:
            List of BankAccount instances
        """
        queryset = profile.bank_accounts.all()  # type: ignore[attr-defined]
        
        if verified_only:
            queryset = queryset.filter(is_verified=True)
        
        return list(queryset)
    
    @staticmethod
    def format_bank_account_for_display(bank_account: BankAccount) -> str:
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
            f"نوع حساب: {bank_account.get_account_type_display()}\n"  # type: ignore[attr-defined]
            f"وضعیت: {status_icon} {status_text}\n"
        )
        
        return text
