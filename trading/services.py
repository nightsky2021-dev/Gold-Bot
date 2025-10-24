"""
لایه سرویس برای منطق تجاری مربوط به معاملات
"""
from typing import List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Product, Order
from users.models import Profile
from .price_providers import get_active_provider
from .price_calculator import PriceCalculator
import logging

logger = logging.getLogger(__name__)


class TradingService:
    """سرویس مدیریت معاملات"""
    
    @staticmethod
    def get_active_products() -> List[Product]:
        """دریافت لیست محصولات فعال"""
        return Product.get_active_products()
    
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        """دریافت محصول براساس شناسه"""
        try:
            return Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return None
    
    @staticmethod
    def calculate_buy_details(
        product: Product,
        amount_type: str,
        amount: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        محاسبه جزئیات خرید
        
        Args:
            product: محصول مورد نظر
            amount_type: نوع مقدار ('rial' یا 'gram')
            amount: مقدار
            
        Returns:
            Tuple[Decimal, Decimal]: (مقدار به گرم, مبلغ کل)
        """
        if amount_type == 'gram':
            quantity_grams = amount
            total_amount = amount * product.sell_price
        else:  # rial
            total_amount = amount
            quantity_grams = amount / product.sell_price
        
        return quantity_grams, total_amount
    
    @staticmethod
    def calculate_sell_details(
        product: Product,
        amount_type: str,
        amount: Decimal
    ) -> Tuple[Decimal, Decimal]:
        """
        محاسبه جزئیات فروش
        
        Args:
            product: محصول مورد نظر
            amount_type: نوع مقدار ('rial' یا 'gram')
            amount: مقدار
            
        Returns:
            Tuple[Decimal, Decimal]: (مقدار به گرم, مبلغ کل)
        """
        if amount_type == 'gram':
            quantity_grams = amount
            total_amount = amount * product.buy_price
        else:  # rial
            total_amount = amount
            quantity_grams = amount / product.buy_price
        
        return quantity_grams, total_amount
    
    @staticmethod
    @transaction.atomic
    def create_buy_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal,
        invoice_number: str = None
    ) -> Order:
        """
        ایجاد سفارش خرید (مشتری از ما می‌خرد)
        
        Args:
            profile: پروفایل کاربر
            product: محصول
            quantity_grams: مقدار به گرم
            total_amount: مبلغ کل
            
        Returns:
            Order: سفارش ایجاد شده
            
        Raises:
            ValidationError: در صورت عدم کفایت موجودی
        """
        # بررسی موجودی ریالی
        if profile.rial_balance < total_amount:
            raise ValidationError(
                f"موجودی ریالی شما کافی نیست. موجودی فعلی: {profile.rial_balance:,} ریال"
            )
        
        # ایجاد سفارش
        order = Order.objects.create(
            profile=profile,
            product=product,
            order_type=Order.OrderType.BUY,
            quantity_grams=quantity_grams,
            price_per_gram=product.sell_price,
            total_amount=total_amount,
            invoice_number=invoice_number,
            status=Order.OrderStatus.PENDING
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def create_sell_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal,
        invoice_number: str = None
    ) -> Order:
        """
        ایجاد سفارش فروش (مشتری به ما می‌فروشد)
        
        Args:
            profile: پروفایل کاربر
            product: محصول
            quantity_grams: مقدار به گرم
            total_amount: مبلغ کل
            
        Returns:
            Order: سفارش ایجاد شده
            
        Raises:
            ValidationError: در صورت عدم کفایت موجودی
        """
        # بررسی موجودی طلا
        if profile.gold_balance_grams < quantity_grams:
            raise ValidationError(
                f"موجودی طلای شما کافی نیست. موجودی فعلی: {profile.gold_balance_grams} گرم"
            )
        
        # ایجاد سفارش
        order = Order.objects.create(
            profile=profile,
            product=product,
            order_type=Order.OrderType.SELL,
            quantity_grams=quantity_grams,
            price_per_gram=product.buy_price,
            total_amount=total_amount,
            invoice_number=invoice_number,
            status=Order.OrderStatus.PENDING
        )
        
        return order
    
    @staticmethod
    def get_user_recent_orders(profile: Profile, limit: int = 5) -> List[Order]:
        """دریافت آخرین سفارشات کاربر"""
        return list(
            Order.objects.filter(profile=profile)
            .select_related('product')
            .order_by('-created_at')[:limit]
        )
    
    @staticmethod
    @transaction.atomic
    def update_all_prices() -> bool:
        """
        به‌روزرسانی تمام قیمت‌های محصولات از API
        
        Returns:
            bool: True در صورت موفقیت، False در صورت خطا
        """
        try:
            # دریافت قیمت‌ها از API
            provider = get_active_provider()
            api_gold = provider.get_gold_price()
            api_dollar_buy = provider.get_dollar_buy_price()
            api_dollar_sell = provider.get_dollar_sell_price()
            
            if not all([api_gold, api_dollar_buy, api_dollar_sell]):
                logger.error("دریافت قیمت‌ها از API ناموفق بود")
                return False
            
            # محاسبه قیمت‌های نهایی
            all_prices = PriceCalculator.calculate_all_prices(
                api_gold, api_dollar_buy, api_dollar_sell
            )
            
            if not all_prices:
                logger.error("محاسبه قیمت‌ها ناموفق بود")
                return False
            
            # به‌روزرسانی محصولات
            # طلای آبشده
            try:
                gold_product = Product.get_by_code(Product.PRODUCT_CODE_GOLD)
                gold_product.buy_price = all_prices.gold_abshodeh.buy_price
                gold_product.sell_price = all_prices.gold_abshodeh.sell_price
                gold_product.save()
                logger.info(f"قیمت طلای آبشده به‌روز شد: {all_prices.gold_abshodeh}")
            except Product.DoesNotExist:
                logger.warning(f"محصول طلای آبشده با کد {Product.PRODUCT_CODE_GOLD} یافت نشد")
            
            # سکه تمام
            try:
                coin_product = Product.get_by_code(Product.PRODUCT_CODE_COIN)
                coin_product.buy_price = all_prices.coin_full.buy_price
                coin_product.sell_price = all_prices.coin_full.sell_price
                coin_product.save()
                logger.info(f"قیمت سکه تمام به‌روز شد: {all_prices.coin_full}")
            except Product.DoesNotExist:
                logger.warning(f"محصول سکه تمام با کد {Product.PRODUCT_CODE_COIN} یافت نشد")
            
            # دلار
            try:
                dollar_product = Product.get_by_code(Product.PRODUCT_CODE_DOLLAR)
                dollar_product.buy_price = all_prices.dollar.buy_price
                dollar_product.sell_price = all_prices.dollar.sell_price
                dollar_product.save()
                logger.info(f"قیمت دلار به‌روز شد: {all_prices.dollar}")
            except Product.DoesNotExist:
                logger.warning(f"محصول دلار با کد {Product.PRODUCT_CODE_DOLLAR} یافت نشد")
            
            logger.info("به‌روزرسانی قیمت‌ها با موفقیت انجام شد")
            return True
            
        except Exception as e:
            logger.error(f"خطا در به‌روزرسانی قیمت‌ها: {e}")
            return False

