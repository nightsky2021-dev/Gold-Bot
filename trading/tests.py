"""
Tests for the trading app.

Tests cover:
- Product model functionality
- Order model functionality
- Trading services
- Admin actions
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from users.models import Profile
from .models import Product, Order
from .services import ProductService, OrderService, BalanceService


class ProductModelTest(TestCase):
    """Test Product model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.product = Product.objects.create(
            name='سکه بهار آزادی',
            buy_price=Decimal('65000000'),
            sell_price=Decimal('68000000'),
            is_active=True
        )
    
    def test_product_str(self):
        """Test string representation of product."""
        self.assertEqual(str(self.product), 'سکه بهار آزادی')
    
    def test_slug_auto_generation(self):
        """Test automatic slug generation."""
        self.assertIsNotNone(self.product.slug)
        self.assertTrue(len(self.product.slug) > 0)
    
    def test_get_price_spread(self):
        """Test price spread calculation."""
        spread = self.product.get_price_spread()
        self.assertEqual(spread, Decimal('3000000'))
    
    def test_get_price_spread_percentage(self):
        """Test price spread percentage calculation."""
        percentage = self.product.get_price_spread_percentage()
        expected = (Decimal('3000000') / Decimal('65000000')) * 100
        self.assertAlmostEqual(float(percentage), float(expected), places=2)


class OrderModelTest(TestCase):
    """Test Order model functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(
            user=self.user,
            telegram_id='123456789',
            phone_number='+1234567890',
            is_approved=True,
            rial_balance=Decimal('100000000'),
            gold_balance_grams=Decimal('20.0000')
        )
        self.product = Product.objects.create(
            name='طلای 18 عیار',
            buy_price=Decimal('2500000'),
            sell_price=Decimal('2600000'),
            is_active=True
        )
        self.order = Order.objects.create(
            profile=self.profile,
            product=self.product,
            order_type=Order.OrderType.BUY,
            quantity_grams=Decimal('5.0000'),
            price_per_gram=Decimal('2600000'),
            total_amount=Decimal('13000000'),
            status=Order.OrderStatus.PENDING
        )
    
    def test_order_str(self):
        """Test string representation of order."""
        order_str = str(self.order)
        self.assertIn('testuser', order_str)
        self.assertIn('خرید', order_str)
    
    def test_calculate_total(self):
        """Test total calculation."""
        total = self.order.calculate_total()
        expected = Decimal('5.0000') * Decimal('2600000')
        self.assertEqual(total, expected)
    
    def test_is_pending(self):
        """Test pending status check."""
        self.assertTrue(self.order.is_pending())
        
        self.order.status = Order.OrderStatus.COMPLETED
        self.assertFalse(self.order.is_pending())
    
    def test_can_be_cancelled(self):
        """Test cancellation eligibility."""
        self.assertTrue(self.order.can_be_cancelled())
        
        self.order.status = Order.OrderStatus.COMPLETED
        self.assertFalse(self.order.can_be_cancelled())


class ProductServiceTest(TestCase):
    """Test ProductService functionality."""
    
    def setUp(self):
        """Set up test data."""
        Product.objects.create(
            name='Product 1',
            buy_price=1000,
            sell_price=1100,
            is_active=True
        )
        Product.objects.create(
            name='Product 2',
            buy_price=2000,
            sell_price=2200,
            is_active=False
        )
    
    def test_get_active_products(self):
        """Test getting only active products."""
        products = ProductService.get_active_products()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, 'Product 1')
    
    def test_get_product_by_id(self):
        """Test getting product by ID."""
        product = Product.objects.first()
        retrieved = ProductService.get_product_by_id(product.id)
        self.assertEqual(retrieved.id, product.id)
        
        # Test inactive product
        inactive = Product.objects.get(is_active=False)
        retrieved_inactive = ProductService.get_product_by_id(inactive.id)
        self.assertIsNone(retrieved_inactive)
    
    def test_format_product_prices(self):
        """Test product price formatting."""
        product = Product.objects.first()
        formatted = ProductService.format_product_prices(product)
        
        self.assertIn(product.name, formatted)
        self.assertIn('1,000', formatted)
        self.assertIn('1,100', formatted)


class OrderServiceTest(TestCase):
    """Test OrderService functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(
            user=self.user,
            telegram_id='123456789',
            phone_number='+1234567890',
            is_approved=True,
            rial_balance=Decimal('100000000'),
            gold_balance_grams=Decimal('20.0000')
        )
        self.product = Product.objects.create(
            name='Test Product',
            buy_price=Decimal('1000000'),
            sell_price=Decimal('1100000'),
            is_active=True
        )
    
    def test_calculate_order_details_by_grams(self):
        """Test order calculation by grams."""
        quantity, price, total = OrderService.calculate_order_details(
            product=self.product,
            order_type=Order.OrderType.BUY,
            amount=Decimal('5.0000'),
            calculation_method='grams'
        )
        
        self.assertEqual(quantity, Decimal('5.0000'))
        self.assertEqual(price, self.product.sell_price)
        self.assertEqual(total, Decimal('5500000'))
    
    def test_calculate_order_details_by_rial(self):
        """Test order calculation by rial."""
        quantity, price, total = OrderService.calculate_order_details(
            product=self.product,
            order_type=Order.OrderType.BUY,
            amount=Decimal('5500000'),
            calculation_method='rial'
        )
        
        self.assertEqual(total, Decimal('5500000'))
        self.assertEqual(price, self.product.sell_price)
        self.assertEqual(quantity, Decimal('5.0000'))
    
    def test_calculate_order_details_invalid_amount(self):
        """Test order calculation with invalid amount."""
        with self.assertRaises(ValidationError):
            OrderService.calculate_order_details(
                product=self.product,
                order_type=Order.OrderType.BUY,
                amount=Decimal('-1'),
                calculation_method='grams'
            )
    
    def test_create_order(self):
        """Test order creation."""
        order = OrderService.create_order(
            profile=self.profile,
            product=self.product,
            order_type=Order.OrderType.BUY,
            quantity_grams=Decimal('5.0000'),
            price_per_gram=self.product.sell_price,
            total_amount=Decimal('5500000')
        )
        
        self.assertIsNotNone(order.id)
        self.assertEqual(order.status, Order.OrderStatus.PENDING)
        self.assertEqual(order.profile, self.profile)
        self.assertEqual(order.product, self.product)
    
    def test_create_order_unapproved_user(self):
        """Test order creation by unapproved user."""
        self.profile.is_approved = False
        self.profile.save()
        
        with self.assertRaises(ValidationError) as context:
            OrderService.create_order(
                profile=self.profile,
                product=self.product,
                order_type=Order.OrderType.BUY,
                quantity_grams=Decimal('5.0000'),
                price_per_gram=self.product.sell_price,
                total_amount=Decimal('5500000')
            )
        
        self.assertIn('تأیید', str(context.exception))
    
    def test_get_user_orders(self):
        """Test getting user orders."""
        # Create some orders
        for i in range(3):
            OrderService.create_order(
                profile=self.profile,
                product=self.product,
                order_type=Order.OrderType.BUY,
                quantity_grams=Decimal('1.0000'),
                price_per_gram=self.product.sell_price,
                total_amount=Decimal('1100000')
            )
        
        orders = OrderService.get_user_orders(self.profile)
        self.assertEqual(len(orders), 3)
        
        # Test with limit
        orders_limited = OrderService.get_user_orders(self.profile, limit=2)
        self.assertEqual(len(orders_limited), 2)


class BalanceServiceTest(TestCase):
    """Test BalanceService functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(username='testuser')
        self.profile = Profile.objects.create(
            user=self.user,
            telegram_id='123456789',
            phone_number='+1234567890',
            rial_balance=Decimal('10000000'),
            gold_balance_grams=Decimal('5.0000')
        )
    
    def test_format_portfolio(self):
        """Test portfolio formatting."""
        formatted = BalanceService.format_portfolio(self.profile)
        
        self.assertIn('پورتفولیو', formatted)
        self.assertIn('10,000,000', formatted)
        self.assertIn('5.0000', formatted)
    
    def test_update_balance(self):
        """Test balance update."""
        BalanceService.update_balance(
            profile=self.profile,
            rial_change=Decimal('1000000'),
            gold_change=Decimal('2.0000')
        )
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.rial_balance, Decimal('11000000'))
        self.assertEqual(self.profile.gold_balance_grams, Decimal('7.0000'))
    
    def test_update_balance_negative_result(self):
        """Test balance update with negative result."""
        with self.assertRaises(ValidationError):
            BalanceService.update_balance(
                profile=self.profile,
                rial_change=Decimal('-20000000')
            )
        
        with self.assertRaises(ValidationError):
            BalanceService.update_balance(
                profile=self.profile,
                gold_change=Decimal('-10.0000')
            )
