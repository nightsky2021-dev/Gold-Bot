"""
سرویس محاسبه قیمت‌های نهایی با اعمال مارجین و فرمول‌ها
"""
from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProductPrices:
    """کلاس داده برای نگهداری قیمت‌های خرید و فروش یک محصول"""
    buy_price: Decimal  # قیمت خرید ما از مشتری
    sell_price: Decimal  # قیمت فروش ما به مشتری
    
    def __str__(self):
        return f"خرید: {self.buy_price:,} | فروش: {self.sell_price:,}"


@dataclass
class AllPrices:
    """کلاس داده برای نگهداری تمام قیمت‌ها"""
    gold_abshodeh: ProductPrices  # طلای آبشده (هر گرم)
    coin_full: ProductPrices  # سکه تمام غیربانکی (هر سکه)
    dollar: ProductPrices  # دلار (هر دلار)


class PriceCalculator:
    """
    محاسبه‌گر قیمت‌های نهایی با اعمال مارجین
    
    Note: این کلاس به صورت deprecated است. 
    اکنون محاسبات قیمت مستقیماً توسط Product model انجام می‌شود.
    این متدها فقط برای سازگاری با کد قدیمی نگه داشته شده‌اند.
    """
    
    # Default margins (برای سازگاری با کد قدیمی)
    GOLD_MARGIN = Decimal('300000')
    COIN_WEIGHT_GRAMS = Decimal('8.133')  
    COIN_MARGIN = Decimal('4500000')
    DOLLAR_MARGIN = Decimal('10000')
    
    @classmethod
    def calculate_product_prices(cls, product, api_base_price: Decimal) -> ProductPrices:
        """
        محاسبه قیمت محصول با استفاده از تنظیمات خود محصول
        
        این متد جدید است و از تنظیمات margin و weight که در Product ذخیره شده استفاده می‌کند.
        
        Args:
            product: شیء Product که شامل تنظیمات margin و weight است
            api_base_price: قیمت پایه از API (ریال به ازای هر گرم)
            
        Returns:
            ProductPrices با قیمت خرید و فروش محاسبه شده
        """
        # محاسبه قیمت پایه با احتساب وزن
        adjusted_base = api_base_price * product.weight_grams
        
        # محاسبه قیمت‌های نهایی با اعمال مارجین‌ها
        buy_price = (adjusted_base - product.buy_margin).quantize(Decimal('1'))
        sell_price = (adjusted_base + product.sell_margin).quantize(Decimal('1'))
        
        return ProductPrices(
            buy_price=buy_price,
            sell_price=sell_price
        )
    
    # متدهای زیر برای سازگاری با کد قدیمی نگه داشته شده‌اند (Deprecated)
    
    @classmethod
    def calculate_gold_abshodeh_prices(cls, api_gold_price: Decimal) -> ProductPrices:
        """
        [DEPRECATED] از Product.calculate_prices_from_base() استفاده کنید
        
        محاسبه قیمت طلای آبشده
        """
        buy_price = api_gold_price - cls.GOLD_MARGIN
        sell_price = api_gold_price + cls.GOLD_MARGIN
        
        return ProductPrices(
            buy_price=buy_price.quantize(Decimal('1')),
            sell_price=sell_price.quantize(Decimal('1'))
        )
    
    @classmethod
    def calculate_coin_full_prices(cls, api_gold_price: Decimal) -> ProductPrices:
        """
        [DEPRECATED] از Product.calculate_prices_from_base() استفاده کنید
        
        محاسبه قیمت سکه تمام غیربانکی
        """
        base_coin_price = api_gold_price * cls.COIN_WEIGHT_GRAMS
        
        buy_price = base_coin_price - cls.COIN_MARGIN
        sell_price = base_coin_price + cls.COIN_MARGIN
        
        return ProductPrices(
            buy_price=buy_price.quantize(Decimal('1')),
            sell_price=sell_price.quantize(Decimal('1'))
        )
    
    @classmethod
    def calculate_dollar_prices(cls, api_dollar_buy: Decimal, api_dollar_sell: Decimal) -> ProductPrices:
        """
        [DEPRECATED] از Product.calculate_prices_from_base() استفاده کنید
        
        محاسبه قیمت دلار
        """
        # برای دلار، میانگین قیمت خرید و فروش API را به عنوان پایه استفاده می‌کنیم
        api_avg = (api_dollar_buy + api_dollar_sell) / 2
        
        buy_price = api_avg - cls.DOLLAR_MARGIN
        sell_price = api_avg + cls.DOLLAR_MARGIN
        
        return ProductPrices(
            buy_price=buy_price.quantize(Decimal('1')),
            sell_price=sell_price.quantize(Decimal('1'))
        )
    
    @classmethod
    def calculate_all_prices(
        cls,
        api_gold_price: Optional[Decimal],
        api_dollar_buy: Optional[Decimal],
        api_dollar_sell: Optional[Decimal]
    ) -> Optional[AllPrices]:
        """
        [DEPRECATED] این متد برای سازگاری با کد قدیمی نگه داشته شده است
        
        محاسبه تمام قیمت‌ها
        """
        if not all([api_gold_price, api_dollar_buy, api_dollar_sell]):
            logger.error("برخی از قیمت‌های API دریافت نشد")
            return None
        
        # Type narrowing
        assert api_gold_price is not None
        assert api_dollar_buy is not None
        assert api_dollar_sell is not None
        
        try:
            gold_prices = cls.calculate_gold_abshodeh_prices(api_gold_price)
            coin_prices = cls.calculate_coin_full_prices(api_gold_price)
            dollar_prices = cls.calculate_dollar_prices(api_dollar_buy, api_dollar_sell)
            
            return AllPrices(
                gold_abshodeh=gold_prices,
                coin_full=coin_prices,
                dollar=dollar_prices
            )
        except Exception as e:
            logger.error(f"خطا در محاسبه قیمت‌ها: {e}")
            return None

