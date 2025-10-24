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
    """محاسبه‌گر قیمت‌های نهایی با اعمال مارجین"""
    
    # مارجین‌ها و ضرایب
    GOLD_MARGIN = Decimal('300000')  # 30 هزار تومان = 300,000 ریال
    COIN_WEIGHT_GRAMS = Decimal('9.573')  # وزن سکه تمام به گرم
    COIN_MARGIN = Decimal('4500000')  # 450 هزار تومان = 4,500,000 ریال
    DOLLAR_MARGIN = Decimal('10000')  # 1 هزار تومان = 10,000 ریال
    
    @classmethod
    def calculate_gold_abshodeh_prices(cls, api_gold_price: Decimal) -> ProductPrices:
        """
        محاسبه قیمت طلای آبشده
        
        Args:
            api_gold_price: قیمت پایه از API (ریال به ازای هر گرم)
            
        Returns:
            ProductPrices با قیمت خرید و فروش
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
        محاسبه قیمت سکه تمام غیربانکی
        
        Args:
            api_gold_price: قیمت پایه طلا از API (ریال به ازای هر گرم)
            
        Returns:
            ProductPrices با قیمت خرید و فروش (به ازای هر سکه)
        """
        # محاسبه قیمت پایه سکه (وزن طلا × قیمت هر گرم)
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
        محاسبه قیمت دلار
        
        Args:
            api_dollar_buy: قیمت خرید دلار از API
            api_dollar_sell: قیمت فروش دلار از API
            
        Returns:
            ProductPrices با قیمت خرید و فروش
        """
        # قیمت خرید ما از مشتری = قیمت خرید API - مارجین
        buy_price = api_dollar_buy - cls.DOLLAR_MARGIN
        # قیمت فروش ما به مشتری = قیمت فروش API + مارجین
        sell_price = api_dollar_sell + cls.DOLLAR_MARGIN
        
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
        محاسبه تمام قیمت‌ها
        
        Args:
            api_gold_price: قیمت طلای آبشده از API (ریال/گرم)
            api_dollar_buy: قیمت خرید دلار از API
            api_dollar_sell: قیمت فروش دلار از API
            
        Returns:
            AllPrices یا None در صورت عدم دریافت قیمت‌ها
        """
        if not all([api_gold_price, api_dollar_buy, api_dollar_sell]):
            logger.error("برخی از قیمت‌های API دریافت نشد")
            return None
        
        # Type narrowing: اطمینان از اینکه مقادیر None نیستند
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

