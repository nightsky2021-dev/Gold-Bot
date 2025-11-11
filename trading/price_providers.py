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


class AnigoldPriceProvider(PriceProvider):
    """ارائه‌دهنده قیمت از API Anigold"""
    
    BASE_URL = "http://api.anigoldbot.ir/store/prices/"
    
    def __init__(self, api_key: str, timeout: int = 10, max_retries: int = 3):
        """
        Args:
            api_key: کلید API سرویس Anigold
            timeout: زمان انتظار برای پاسخ (ثانیه)
            max_retries: تعداد تلاش‌های مجدد
        """
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self._cached_prices = None
    
    def _fetch_all_prices(self) -> Optional[Dict[str, Decimal]]:
        """
        دریافت تمام قیمت‌ها از API Anigold
        
        Returns:
            دیکشنری حاوی قیمت‌ها یا None در صورت خطا
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                headers = {
                    'apikey': self.api_key,
                    'Content-Type': 'application/json'
                }
                
                response = requests.post(
                    self.BASE_URL,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check if API returned success
                if isinstance(data, dict) and not data.get('IsSuccess', True):
                    logger.error(f"Anigold API returned error: {data.get('Message')}")
                    return None
                
                # Anigold returns array of price objects
                if isinstance(data, list):
                    # Convert from array format to dict mapping
                    data = self._convert_anigold_response(data)
                elif isinstance(data, dict) and 'Prices' in data:
                    data = self._convert_anigold_response(data['Prices'])
                
                # Extract prices from response
                prices = {}
                for key, value in data.items():
                    if key != 'status' and value is not None and value != '':
                        try:
                            # Skip non-numeric values
                            if isinstance(value, bool) or value in ['true', 'false', True, False]:
                                continue
                            
                            # Convert to Decimal, handle different formats
                            price_str = str(value).replace(',', '').strip()
                            
                            # Skip empty or non-numeric strings
                            if not price_str or not any(c.isdigit() for c in price_str):
                                logger.debug(f"Skipping non-numeric value for {key}: {value}")
                                continue
                            
                            prices[key] = Decimal(price_str)
                            logger.debug(f"Successfully parsed {key}: {value} -> {prices[key]}")
                        except (ValueError, TypeError, Exception) as e:
                            logger.warning(f"Could not parse price for {key}: {value} (type: {type(value).__name__}) - {e}")
                            continue
                
                self._cached_prices = prices
                logger.info(f"Successfully fetched {len(prices)} prices from Anigold API")
                return prices
                
            except requests.exceptions.RequestException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    logger.warning(f"تلاش {attempt + 1} برای دریافت قیمت‌ها از Anigold ناموفق بود. تلاش مجدد...")
                    continue
                else:
                    logger.error(f"خطا در دریافت قیمت‌ها از Anigold API پس از {self.max_retries} تلاش: {e}")
                    return None
            except Exception as e:
                logger.error(f"خطا در پردازش پاسخ Anigold API: {e}", exc_info=True)
                return None
        
        return None
    
    def _convert_anigold_response(self, prices_array: list) -> Dict[str, Decimal]:
        """
        Convert Anigold API response from array format to dict mapping.
        
        Anigold returns: [{"fa_slug": "دلار آمریکا", "price": "75000", ...}, ...]
        We need: {"dollar_usa": Decimal("750000"), ...}
        
        IMPORTANT: Anigold API returns prices in TOMANS, so we multiply by 10 to convert to RIALS.
        """
        result = {}
        
        # Mapping from Anigold fa_slug to our product codes
        # Based on actual API response
        slug_mapping = {
            # Currencies
            'دلار آمریکا': 'dollar_usa',
            'یورو': 'euro',
            'لیر ترکیه': 'lira_turkey',
            'یوان چین': 'yuan_china',
            'پوند انگلیس': 'pound_uk',
            'درهم امارات': 'dirham_uae',
            # Coins - Using سکه 86 (Emami coin) variants
            'سکه 86': 'coin_full',
            'نیم سکه 86': 'coin_half',
            'ربع سکه 86': 'coin_quarter',
            # Gold - Using گرم 24 عیار (24 karat per gram)
            'گرم 24 عیار': 'gold_abshodeh',
        }
        
        for item in prices_array:
            if not isinstance(item, dict):
                continue
                
            fa_slug = item.get('fa_slug', '')
            price_value = item.get('price') or item.get('buyprice')
            
            if fa_slug in slug_mapping and price_value:
                product_code = slug_mapping[fa_slug]
                try:
                    price_str = str(price_value).replace(',', '').strip()
                    # Convert from Tomans to Rials (multiply by 10)
                    price_tomans = Decimal(price_str)
                    price_rials = price_tomans * Decimal('10')
                    result[product_code] = price_rials
                    logger.debug(f"Mapped {fa_slug} -> {product_code}: {price_tomans:,.0f} Tomans = {price_rials:,.0f} Rials")
                except Exception as e:
                    logger.warning(f"Could not parse price for {fa_slug}: {price_value} - {e}")
        
        return result
    
    def get_price(self, product_code: str) -> Optional[Decimal]:
        """دریافت قیمت برای یک محصول خاص"""
        if not self._cached_prices:
            self._fetch_all_prices()
        
        if self._cached_prices:
            return self._cached_prices.get(product_code)
        return None
    
    def get_gold_price(self) -> Optional[Decimal]:
        """دریافت قیمت طلای آبشده"""
        return self.get_price('gold_abshodeh')
    
    def get_dollar_buy_price(self) -> Optional[Decimal]:
        """دریافت قیمت خرید دلار - Anigold فقط یک قیمت دارد"""
        return self.get_price('dollar_usa')
    
    def get_dollar_sell_price(self) -> Optional[Decimal]:
        """دریافت قیمت فروش دلار - Anigold فقط یک قیمت دارد"""
        return self.get_price('dollar_usa')


# تابع کمکی برای دریافت provider فعال
def get_active_provider() -> PriceProvider:
    """
    دریافت ارائه‌دهنده قیمت فعال
    
    این تابع بر اساس تنظیمات PRICE_PROVIDER_TYPE provider مناسب را برمی‌گرداند
    
    Raises:
        ImproperlyConfigured: If API key is not set in settings
    """
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured
    
    provider_type = getattr(settings, 'PRICE_PROVIDER_TYPE', 'anigold').lower()
    
    if provider_type == 'anigold':
        api_key = getattr(settings, 'ANIGOLD_API_KEY', None)
        if not api_key:
            raise ImproperlyConfigured(
                'ANIGOLD_API_KEY is not set in Django settings. '
                'Please set it in your settings.py or environment variables.'
            )
        return AnigoldPriceProvider(api_key)
    
    elif provider_type == 'navasan':
        api_key = getattr(settings, 'NAVASAN_API_KEY', None)
        if not api_key:
            raise ImproperlyConfigured(
                'NAVASAN_API_KEY is not set in Django settings. '
                'Please set it in your settings.py or environment variables.'
            )
        return NavasanPriceProvider(api_key)
    
    else:
        raise ImproperlyConfigured(
            f'Unknown PRICE_PROVIDER_TYPE: {provider_type}. '
            'Supported types: "anigold", "navasan"'
        )

