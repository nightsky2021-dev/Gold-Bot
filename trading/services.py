"""
لایه سرویس برای منطق تجاری مربوط به معاملات
"""
from typing import List, Optional, Tuple
from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Product, Order
from users.models import Profile


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
        total_amount: Decimal
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
            status=Order.OrderStatus.PENDING
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def create_sell_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal
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
