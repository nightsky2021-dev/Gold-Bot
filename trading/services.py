"""
لایه سرویس برای منطق تجاری مربوط به معاملات
"""
from typing import List, Optional, Tuple, cast
from decimal import Decimal, ROUND_HALF_UP
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from .models import Product, Order
from users.models import Profile
from .price_providers import get_active_provider
from .price_calculator import PriceCalculator
import logging

logger = logging.getLogger(__name__)


# Constants for validation
MIN_GRAM_AMOUNT = Decimal('0.0001')  # حداقل مقدار به گرم
MIN_RIAL_AMOUNT = Decimal('10000')  # حداقل مقدار به ریال (1000 تومان)


class TradingService:
    """سرویس مدیریت معاملات"""
    
    @staticmethod
    def _validate_amount(amount: Decimal, amount_type: str) -> None:
        """
        اعتبارسنجی مقدار ورودی
        
        Args:
            amount: مقدار برای اعتبارسنجی
            amount_type: نوع مقدار ('rial' یا 'gram')
            
        Raises:
            ValidationError: در صورت نامعتبر بودن مقدار
        """
        if amount <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد")
        
        if amount_type == 'gram':
            if amount < MIN_GRAM_AMOUNT:
                raise ValidationError(
                    f"حداقل مقدار برای خرید {MIN_GRAM_AMOUNT} گرم است"
                )
        elif amount_type == 'rial':
            if amount < MIN_RIAL_AMOUNT:
                raise ValidationError(
                    f"حداقل مقدار برای خرید {MIN_RIAL_AMOUNT:,} ریال است"
                )
        else:
            raise ValidationError(f"نوع مقدار نامعتبر است: {amount_type}")
    
    @staticmethod
    def _validate_product_price(price: Decimal, price_type: str) -> None:
        """
        اعتبارسنجی قیمت محصول
        
        Args:
            price: قیمت برای بررسی
            price_type: نوع قیمت (برای پیام خطا)
            
        Raises:
            ValidationError: در صورت نامعتبر بودن قیمت
        """
        if price <= 0:
            raise ValidationError(
                f"قیمت {price_type} محصول نامعتبر است. لطفاً با پشتیبانی تماس بگیرید."
            )
    
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
            
        Raises:
            ValidationError: در صورت نامعتبر بودن ورودی‌ها
        """
        # اعتبارسنجی مقدار
        TradingService._validate_amount(amount, amount_type)
        
        # اعتبارسنجی قیمت محصول
        TradingService._validate_product_price(product.sell_price, "فروش")  # pyright: ignore
        
        # محاسبه
        if amount_type == 'gram':
            quantity_grams = amount
            # استفاده از quantize برای گرد کردن صحیح
            total_amount = (amount * product.sell_price).quantize(  # pyright: ignore
                Decimal('1'), rounding=ROUND_HALF_UP
            )
        else:  # rial
            total_amount = amount
            # تقسیم با دقت بالا و گرد کردن به 4 رقم اعشار
            quantity_grams = (amount / product.sell_price).quantize(  # pyright: ignore
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
        
        # اعتبارسنجی نتایج
        if quantity_grams < MIN_GRAM_AMOUNT:
            raise ValidationError(
                f"مقدار محاسبه شده ({quantity_grams} گرم) کمتر از حداقل مجاز است"
            )
        
        logger.debug(
            f"محاسبه خرید - محصول: {product.name}, "
            f"نوع: {amount_type}, مقدار: {amount}, "
            f"نتیجه: {quantity_grams} گرم = {total_amount:,} ریال"
        )
        
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
            
        Raises:
            ValidationError: در صورت نامعتبر بودن ورودی‌ها
        """
        # اعتبارسنجی مقدار
        TradingService._validate_amount(amount, amount_type)
        
        # اعتبارسنجی قیمت محصول
        TradingService._validate_product_price(product.buy_price, "خرید")  # pyright: ignore
        
        # محاسبه
        if amount_type == 'gram':
            quantity_grams = amount
            # استفاده از quantize برای گرد کردن صحیح
            total_amount = (amount * product.buy_price).quantize(  # pyright: ignore
                Decimal('1'), rounding=ROUND_HALF_UP
            )
        else:  # rial
            total_amount = amount
            # تقسیم با دقت بالا و گرد کردن به 4 رقم اعشار
            quantity_grams = (amount / product.buy_price).quantize(  # pyright: ignore
                Decimal('0.0001'), rounding=ROUND_HALF_UP
            )
        
        # اعتبارسنجی نتایج
        if quantity_grams < MIN_GRAM_AMOUNT:
            raise ValidationError(
                f"مقدار محاسبه شده ({quantity_grams} گرم) کمتر از حداقل مجاز است"
            )
        
        logger.debug(
            f"محاسبه فروش - محصول: {product.name}, "
            f"نوع: {amount_type}, مقدار: {amount}, "
            f"نتیجه: {quantity_grams} گرم = {total_amount:,} ریال"
        )
        
        return quantity_grams, total_amount
    
    @staticmethod
    @transaction.atomic
    def create_buy_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal,
        invoice_number: Optional[str] = None
    ) -> Order:
        """
        ایجاد سفارش خرید (مشتری از ما می‌خرد)
        
        Args:
            profile: پروفایل کاربر
            product: محصول
            quantity_grams: مقدار به گرم
            total_amount: مبلغ کل
            invoice_number: شماره فاکتور (اختیاری)
            
        Returns:
            Order: سفارش ایجاد شده
            
        Raises:
            ValidationError: در صورت عدم کفایت موجودی یا نامعتبر بودن ورودی
        """
        # اعتبارسنجی ورودی‌ها
        if quantity_grams <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد")
        
        if total_amount <= 0:
            raise ValidationError("مبلغ باید بزرگتر از صفر باشد")
        
        if not product.is_active:
            raise ValidationError(f"محصول {product.name} در حال حاضر غیرفعال است")
        
        # بررسی موجودی ریالی
        if profile.rial_balance < total_amount:
            shortage = total_amount - cast(Decimal, profile.rial_balance)
            raise ValidationError(
                f"موجودی ریالی شما کافی نیست.\n"
                f"موجودی فعلی: {profile.rial_balance:,} ریال\n"
                f"مورد نیاز: {total_amount:,} ریال\n"
                f"کمبود: {shortage:,} ریال"
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
        
        logger.info(
            f"سفارش خرید ایجاد شد - کاربر: {cast(User, profile.user).get_full_name()}, "
            f"محصول: {product.name}, مقدار: {quantity_grams} گرم, "
            f"مبلغ: {total_amount:,} ریال, شماره سفارش: {order.id}"
        )
        
        return order
    
    @staticmethod
    @transaction.atomic
    def create_sell_order(
        profile: Profile,
        product: Product,
        quantity_grams: Decimal,
        total_amount: Decimal,
        invoice_number: Optional[str] = None
    ) -> Order:
        """
        ایجاد سفارش فروش (مشتری به ما می‌فروشد)
        
        Args:
            profile: پروفایل کاربر
            product: محصول
            quantity_grams: مقدار به گرم
            total_amount: مبلغ کل
            invoice_number: شماره فاکتور (اختیاری)
            
        Returns:
            Order: سفارش ایجاد شده
            
        Raises:
            ValidationError: در صورت عدم کفایت موجودی یا نامعتبر بودن ورودی
        """
        # اعتبارسنجی ورودی‌ها
        if quantity_grams <= 0:
            raise ValidationError("مقدار باید بزرگتر از صفر باشد")
        
        if total_amount <= 0:
            raise ValidationError("مبلغ باید بزرگتر از صفر باشد")
        
        if not product.is_active:
            raise ValidationError(f"محصول {product.name} در حال حاضر غیرفعال است")
        
        # بررسی موجودی طلا
        if profile.gold_balance_grams < quantity_grams:
            shortage = quantity_grams - cast(Decimal, profile.gold_balance_grams)
            raise ValidationError(
                f"موجودی طلای شما کافی نیست.\n"
                f"موجودی فعلی: {profile.gold_balance_grams} گرم\n"
                f"مورد نیاز: {quantity_grams} گرم\n"
                f"کمبود: {shortage} گرم"
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
        
        logger.info(
            f"سفارش فروش ایجاد شد - کاربر: {cast(User, profile.user).get_full_name()}, "
            f"محصول: {product.name}, مقدار: {quantity_grams} گرم, "
            f"مبلغ: {total_amount:,} ریال, شماره سفارش: {order.id}"
        )
        
        return order
    
    @staticmethod
    def get_user_recent_orders(profile: Profile, limit: int = 5) -> List[Order]:
        """
        دریافت آخرین سفارشات کاربر
        
        Args:
            profile: پروفایل کاربر
            limit: حداکثر تعداد سفارشات برای بازگشت (پیش‌فرض: 5)
            
        Returns:
            List[Order]: لیست سفارشات
        """
        if limit <= 0:
            logger.warning(f"limit نامعتبر دریافت شد: {limit}، استفاده از مقدار پیش‌فرض 5")
            limit = 5
        
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
            logger.info("شروع به‌روزرسانی قیمت‌ها از API...")
            
            # دریافت قیمت‌ها از API
            provider = get_active_provider()
            
            # دریافت قیمت‌ها با مدیریت خطا برای هر کدام
            api_gold = provider.get_gold_price()
            if not api_gold:
                logger.error("دریافت قیمت طلا از API ناموفق بود")
                return False
            
            api_dollar_buy = provider.get_dollar_buy_price()
            if not api_dollar_buy:
                logger.error("دریافت قیمت خرید دلار از API ناموفق بود")
                return False
            
            api_dollar_sell = provider.get_dollar_sell_price()
            if not api_dollar_sell:
                logger.error("دریافت قیمت فروش دلار از API ناموفق بود")
                return False
            
            logger.info(
                f"قیمت‌های API دریافت شد - طلا: {api_gold:,}, "
                f"دلار خرید: {api_dollar_buy:,}, دلار فروش: {api_dollar_sell:,}"
            )
            
            # محاسبه قیمت‌های نهایی
            all_prices = PriceCalculator.calculate_all_prices(
                api_gold, api_dollar_buy, api_dollar_sell
            )
            
            if not all_prices:
                logger.error("محاسبه قیمت‌ها ناموفق بود")
                return False
            
            # شمارنده محصولات به‌روز شده
            updated_count = 0
            
            # به‌روزرسانی محصولات
            # طلای آبشده
            try:
                gold_product = Product.get_by_code(Product.PRODUCT_CODE_GOLD)
                
                # اعتبارسنجی قیمت‌ها
                if all_prices.gold_abshodeh.buy_price <= 0 or all_prices.gold_abshodeh.sell_price <= 0:
                    logger.error("قیمت‌های محاسبه شده برای طلای آبشده نامعتبر است")
                else:
                    old_buy = gold_product.buy_price
                    old_sell = gold_product.sell_price
                    
                    gold_product.buy_price = all_prices.gold_abshodeh.buy_price  # pyright: ignore
                    gold_product.sell_price = all_prices.gold_abshodeh.sell_price  # pyright: ignore
                    gold_product.save()
                    updated_count += 1
                    
                    logger.info(
                        f"قیمت طلای آبشده به‌روز شد - "
                        f"خرید: {old_buy:,} -> {all_prices.gold_abshodeh.buy_price:,}, "
                        f"فروش: {old_sell:,} -> {all_prices.gold_abshodeh.sell_price:,}"
                    )
            except Product.DoesNotExist:
                logger.warning(
                    f"محصول طلای آبشده با کد {Product.PRODUCT_CODE_GOLD} یافت نشد. "
                    "لطفاً محصول را در پنل ادمین ایجاد کنید."
                )
            
            # سکه تمام
            try:
                coin_product = Product.get_by_code(Product.PRODUCT_CODE_COIN)
                
                # اعتبارسنجی قیمت‌ها
                if all_prices.coin_full.buy_price <= 0 or all_prices.coin_full.sell_price <= 0:
                    logger.error("قیمت‌های محاسبه شده برای سکه تمام نامعتبر است")
                else:
                    old_buy = coin_product.buy_price
                    old_sell = coin_product.sell_price
                    
                    coin_product.buy_price = all_prices.coin_full.buy_price  # pyright: ignore
                    coin_product.sell_price = all_prices.coin_full.sell_price  # pyright: ignore
                    coin_product.save()
                    updated_count += 1
                    
                    logger.info(
                        f"قیمت سکه تمام به‌روز شد - "
                        f"خرید: {old_buy:,} -> {all_prices.coin_full.buy_price:,}, "
                        f"فروش: {old_sell:,} -> {all_prices.coin_full.sell_price:,}"
                    )
            except Product.DoesNotExist:
                logger.warning(
                    f"محصول سکه تمام با کد {Product.PRODUCT_CODE_COIN} یافت نشد. "
                    "لطفاً محصول را در پنل ادمین ایجاد کنید."
                )
            
            # دلار
            try:
                dollar_product = Product.get_by_code(Product.PRODUCT_CODE_DOLLAR)
                
                # اعتبارسنجی قیمت‌ها
                if all_prices.dollar.buy_price <= 0 or all_prices.dollar.sell_price <= 0:
                    logger.error("قیمت‌های محاسبه شده برای دلار نامعتبر است")
                else:
                    old_buy = dollar_product.buy_price
                    old_sell = dollar_product.sell_price
                    
                    dollar_product.buy_price = all_prices.dollar.buy_price  # pyright: ignore
                    dollar_product.sell_price = all_prices.dollar.sell_price  # pyright: ignore
                    dollar_product.save()
                    updated_count += 1
                    
                    logger.info(
                        f"قیمت دلار به‌روز شد - "
                        f"خرید: {old_buy:,} -> {all_prices.dollar.buy_price:,}, "
                        f"فروش: {old_sell:,} -> {all_prices.dollar.sell_price:,}"
                    )
            except Product.DoesNotExist:
                logger.warning(
                    f"محصول دلار با کد {Product.PRODUCT_CODE_DOLLAR} یافت نشد. "
                    "لطفاً محصول را در پنل ادمین ایجاد کنید."
                )
            
            if updated_count > 0:
                logger.info(
                    f"به‌روزرسانی قیمت‌ها با موفقیت انجام شد. "
                    f"تعداد محصولات به‌روز شده: {updated_count}"
                )
                return True
            else:
                logger.warning("هیچ محصولی به‌روز نشد. لطفاً محصولات را در پنل ادمین بررسی کنید.")
                return False
            
        except Exception as e:
            logger.error(f"خطای غیرمنتظره در به‌روزرسانی قیمت‌ها: {e}", exc_info=True)
            return False

