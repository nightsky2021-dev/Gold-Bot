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
    
    def __init__(self, api_key: str, timeout: int = 5, max_retries: int = 3):
        """
        Args:
            api_key: کلید API سرویس نواسان
            timeout: زمان انتظار برای پاسخ (ثانیه)
            max_retries: تعداد تلاش‌های مجدد
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _fetch_price(self, item: str) -> Optional[Decimal]:
        """
        دریافت قیمت برای یک آیتم خاص با قابلیت تلاش مجدد
        
        Args:
            item: نوع آیتم (abshodeh, usd_buy, usd_sell)
            
        Returns:
            قیمت به صورت Decimal یا None در صورت خطا
        """
        last_error = None
        
        for attempt in range(self.max_retries):
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
                    item_data = data[item]
                    
                    # Check if the response is a nested object (new format)
                    if isinstance(item_data, dict) and 'value' in item_data:
                        price_str = str(item_data['value']).replace(',', '')
                    # Or if it's a simple value (old format)
                    else:
                        price_str = str(item_data).replace(',', '')
                    
                    return Decimal(price_str)
                
                logger.warning(f"آیتم {item} در پاسخ API یافت نشد: {data}")
                return None
                
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"تلاش {attempt + 1} برای دریافت قیمت {item} ناموفق بود. تلاش مجدد...")
                    continue
                else:
                    logger.error(f"خطا در دریافت قیمت {item} از API پس از {self.max_retries} تلاش: {e}")
                    return None
            except (ValueError, KeyError, Exception) as e:
                logger.error(f"خطا در پردازش پاسخ API برای {item}: {e}")
                return None
        
        return None
    
    def get_gold_price(self) -> Optional[Decimal]:
        """دریافت قیمت طلای آبشده (مثقال)"""
        price_per_mesghal = self._fetch_price('abshodeh')
        if price_per_mesghal:
            # API returns value in thousands of tomans
            # Convert: thousands of tomans -> tomans -> rials
            price_per_mesghal_rials = price_per_mesghal * Decimal('10000')
            # تبدیل از مثقال به گرم (1 مثقال = 4.608 گرم)
            return price_per_mesghal_rials / Decimal('4.608')
        return None
    
    def get_dollar_buy_price(self) -> Optional[Decimal]:
        """دریافت قیمت خرید دلار"""
        price_tomans = self._fetch_price('usd_buy')
        if price_tomans:
            # API returns value in tomans, convert to rials
            return price_tomans * Decimal('10')
        return None
    
    def get_dollar_sell_price(self) -> Optional[Decimal]:
        """دریافت قیمت فروش دلار"""
        price_tomans = self._fetch_price('usd_sell')
        if price_tomans:
            # API returns value in tomans, convert to rials
            return price_tomans * Decimal('10')
        return None


# تابع کمکی برای دریافت provider فعال
def get_active_provider() -> PriceProvider:
    """
    دریافت ارائه‌دهنده قیمت فعال
    
    این تابع را می‌توانید سفارشی‌سازی کنید تا provider مورد نظر را برگرداند
    
    Raises:
        ImproperlyConfigured: If NAVASAN_API_KEY is not set in settings
    """
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured
    
    api_key = getattr(settings, 'NAVASAN_API_KEY', None)
    if not api_key:
        raise ImproperlyConfigured(
            'NAVASAN_API_KEY is not set in Django settings. '
            'Please set it in your settings.py or environment variables.'
        )
    return NavasanPriceProvider(api_key)

