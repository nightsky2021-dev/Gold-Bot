"""
ماژول ارائه‌دهندگان قیمت (Price Providers)
این ماژول به صورت ماژولار طراحی شده تا تعویض API آسان باشد
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal
import requests  # pyright: ignore[reportMissingModuleSource]
import logging

logger = logging.getLogger(__name__)


class PriceProvider(ABC):
    """کلاس پایه برای ارائه‌دهندگان قیمت"""
    
    @abstractmethod
    def get_gold_price(self) -> Optional[Decimal]:
        """دریافت قیمت طلای آبشده (ریال به ازای هر گرم)"""
        pass
    
    @abstractmethod
    def get_dollar_buy_price(self) -> Optional[Decimal]:
        """دریافت قیمت خرید دلار"""
        pass
    
    @abstractmethod
    def get_dollar_sell_price(self) -> Optional[Decimal]:
        """دریافت قیمت فروش دلار"""
        pass
    
    def get_all_prices(self) -> Dict[str, Optional[Decimal]]:
        """دریافت تمام قیمت‌ها"""
        return {
            'gold': self.get_gold_price(),
            'dollar_buy': self.get_dollar_buy_price(),
            'dollar_sell': self.get_dollar_sell_price(),
        }


class NavasanPriceProvider(PriceProvider):
    """ارائه‌دهنده قیمت از API Navasan"""
    
    BASE_URL = "http://api.navasan.tech/latest/"
    
    def __init__(self, api_key: str):
        """
        Args:
            api_key: کلید API سرویس نواسان
        """
        self.api_key = api_key
        self.timeout = 10  # ثانیه
    
    def _fetch_price(self, item: str) -> Optional[Decimal]:
        """
        دریافت قیمت برای یک آیتم خاص
        
        Args:
            item: نوع آیتم (abshodeh, usd_buy, usd_sell)
            
        Returns:
            قیمت به صورت Decimal یا None در صورت خطا
        """
        try:
            params = {
                'api_key': self.api_key,
                'item': item
            }
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # استخراج قیمت از پاسخ JSON
            if item in data:
                price_str = str(data[item]).replace(',', '')
                return Decimal(price_str)
            
            logger.warning(f"آیتم {item} در پاسخ API یافت نشد: {data}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"خطا در دریافت قیمت {item} از API: {e}")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"خطا در پردازش پاسخ API برای {item}: {e}")
            return None
    
    def get_gold_price(self) -> Optional[Decimal]:
        """دریافت قیمت طلای آبشده (مثقال)"""
        price_per_mesghal = self._fetch_price('abshodeh')
        if price_per_mesghal:
            # تبدیل از مثقال به گرم (1 مثقال = 4.608 گرم)
            return price_per_mesghal / Decimal('4.608')
        return None
    
    def get_dollar_buy_price(self) -> Optional[Decimal]:
        """دریافت قیمت خرید دلار"""
        return self._fetch_price('usd_buy')
    
    def get_dollar_sell_price(self) -> Optional[Decimal]:
        """دریافت قیمت فروش دلار"""
        return self._fetch_price('usd_sell')


# تابع کمکی برای دریافت provider فعال
def get_active_provider() -> PriceProvider:
    """
    دریافت ارائه‌دهنده قیمت فعال
    
    این تابع را می‌توانید سفارشی‌سازی کنید تا provider مورد نظر را برگرداند
    """
    from django.conf import settings
    
    api_key = getattr(settings, 'NAVASAN_API_KEY', 'freeTET7c1g57cU7kPnjQa4KAMP7BWaS')
    return NavasanPriceProvider(api_key)

