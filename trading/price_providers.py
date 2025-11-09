"""
ماژول ارائه‌دهندگان قیمت (Price Providers)
این ماژول به صورت ماژولار طراحی شده تا تعویض API آسان باشد
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal, InvalidOperation
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


class AnigoldPriceProvider(PriceProvider):
    """ارائه‌دهنده قیمت از API Anigold"""
    
    BASE_URL = "http://api.anigoldbot.ir/store/prices/"
    
    # Mapping of product codes to API field names
    PRODUCT_MAPPING = {
        'dollar_usa': 'dollar',
        'euro': 'price_eur',
        'lira_turkey': 'price_try',
        'yuan_china': 'price_cny',
        'pound_uk': 'price_gbp',
        'dirham_uae': 'price_aed',
        'coin_full': 'sekeh_tamam_under86',
        'coin_half': 'nim_sekeh_under86',
        'coin_quarter': 'rob_sekeh_under86',
        'gold_abshodeh': 'geram18',
    }
    
    def __init__(self, api_key: str, timeout: int = 5, max_retries: int = 3):
        """
        Args:
            api_key: کلید API سرویس Anigold
            timeout: زمان انتظار برای پاسخ (ثانیه)
            max_retries: تعداد تلاش‌های مجدد
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
    
    def _fetch_all_prices(self) -> Optional[Dict[str, Decimal]]:
        """
        دریافت تمام قیمت‌ها از API با قابلیت تلاش مجدد
        
        Returns:
            دیکشنری قیمت‌ها یا None در صورت خطا
        """
        for attempt in range(self.max_retries):
            try:
                # Try with JSON body containing apikey
                payload = {
                    'apikey': self.api_key
                }
                
                response = requests.post(
                    self.BASE_URL,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check if API response has the expected format
                if isinstance(data, dict):
                    # New API format: {'IsSuccess': bool, 'Message': str, 'Prices': [...]}
                    if not data.get('IsSuccess', False):
                        logger.error(f"خطای API Anigold: {data.get('Message', 'خطای نامشخص')}")
                        return None
                    
                    # Get prices list from response
                    prices_list = data.get('Prices', [])
                    if not isinstance(prices_list, list):
                        logger.error(f"فرمت نامعتبر در پاسخ API: Prices باید لیست باشد")
                        return None
                    
                    data = prices_list  # Continue with the prices list
                elif not isinstance(data, list):
                    logger.error(f"خطا در پردازش پاسخ API: انتظار می‌رفت لیست یا dict باشد، اما یافت شد: {type(data).__name__}")
                    logger.error(f"محتوای پاسخ: {data}")
                    return None
                
                # Parse prices from response
                prices = {}
                for item in data:
                    if not isinstance(item, dict):
                        logger.warning(f"آیتم نامعتبر در پاسخ API (انتظار dict، یافت شد {type(item).__name__}): {item}")
                        continue
                    
                    en_slug = item.get('en_slug')
                    price = item.get('price')
                    
                    if en_slug and price:
                        try:
                            # Convert price to Decimal (price is in Tomans)
                            price_tomans = Decimal(str(price).replace(',', ''))
                            # Convert Tomans to Rials
                            prices[en_slug] = price_tomans * Decimal('10')
                        except (ValueError, InvalidOperation) as e:
                            logger.warning(f"خطا در تبدیل قیمت برای {en_slug}: {price} - {e}")
                            continue
                
                logger.info(f"دریافت {len(prices)} قیمت از API Anigold")
                return prices
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"تلاش {attempt + 1} برای دریافت قیمت‌ها ناموفق بود. تلاش مجدد...")
                    continue
                else:
                    logger.error(f"خطا در دریافت قیمت‌ها از API پس از {self.max_retries} تلاش: {e}")
                    return None
            except (ValueError, KeyError, Exception) as e:
                logger.error(f"خطا در پردازش پاسخ API: {e}")
                return None
        
        return None
    
    def get_price(self, product_code: str) -> Optional[Decimal]:
        """
        دریافت قیمت یک محصول خاص
        
        Args:
            product_code: کد محصول (مثل 'dollar_usa', 'euro', 'gold_abshodeh')
            
        Returns:
            قیمت به صورت Decimal یا None در صورت خطا
        """
        prices = self._fetch_all_prices()
        if not prices:
            return None
        
        # Get API field name from product code
        api_field = self.PRODUCT_MAPPING.get(product_code)
        if not api_field:
            logger.warning(f"کد محصول نامعتبر: {product_code}")
            return None
        
        return prices.get(api_field)
    
    def get_gold_price(self) -> Optional[Decimal]:
        """دریافت قیمت طلای آبشده (هر گرم - ریال)"""
        return self.get_price('gold_abshodeh')
    
    def get_dollar_buy_price(self) -> Optional[Decimal]:
        """دریافت قیمت خرید دلار (برای سازگاری با interface قدیمی)"""
        return self.get_price('dollar_usa')
    
    def get_dollar_sell_price(self) -> Optional[Decimal]:
        """دریافت قیمت فروش دلار (برای سازگاری با interface قدیمی)"""
        return self.get_price('dollar_usa')


# تابع کمکی برای دریافت provider فعال
def get_active_provider() -> PriceProvider:
    """
    دریافت ارائه‌دهنده قیمت فعال
    
    این تابع را می‌توانید سفارشی‌سازی کنید تا provider مورد نظر را برگرداند
    از متغیر PRICE_PROVIDER_TYPE در settings برای انتخاب provider استفاده می‌شود.
    """
    from django.conf import settings
    
    provider_type = getattr(settings, 'PRICE_PROVIDER_TYPE', 'anigold')
    
    if provider_type == 'anigold':
        api_key = getattr(settings, 'ANIGOLD_API_KEY', '1a233fab-04d1-47b2-b732-813d93795c43')
        return AnigoldPriceProvider(api_key)
    elif provider_type == 'navasan':
        api_key = getattr(settings, 'NAVASAN_API_KEY', 'freeTET7c1g57cU7kPnjQa4KAMP7BWaS')
        return NavasanPriceProvider(api_key)
    else:
        # Default to Anigold
        api_key = getattr(settings, 'ANIGOLD_API_KEY', '1a233fab-04d1-47b2-b732-813d93795c43')
        return AnigoldPriceProvider(api_key)

