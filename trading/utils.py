"""
Utility functions for the trading app.

Contains helper functions for Persian number formatting,
user tier calculations, and other common operations.
"""

from decimal import Decimal
from typing import Optional
from django.utils.safestring import mark_safe


# Persian/Farsi digit mapping
PERSIAN_DIGITS = {
    '0': '۰',
    '1': '۱',
    '2': '۲',
    '3': '۳',
    '4': '۴',
    '5': '۵',
    '6': '۶',
    '7': '۷',
    '8': '۸',
    '9': '۹',
}


def to_persian_numbers(text: str) -> str:
    """
    Convert English/Arabic numerals to Persian/Farsi numerals.
    
    Args:
        text: String containing numbers to convert
        
    Returns:
        String with Persian numerals
        
    Example:
        >>> to_persian_numbers("1234")
        "۱۲۳۴"
        >>> to_persian_numbers("Price: 100,000 Rial")
        "Price: ۱۰۰,۰۰۰ Rial"
    """
    if not text:
        return text
    
    result = str(text)
    for eng, per in PERSIAN_DIGITS.items():
        result = result.replace(eng, per)
    
    return result


def format_price_persian(amount: Decimal, include_currency: bool = True) -> str:
    """
    Format a price with thousand separators and optional Persian numerals.
    
    Args:
        amount: Price amount to format
        include_currency: Whether to include 'ریال' suffix
        
    Returns:
        Formatted price string
        
    Example:
        >>> format_price_persian(Decimal('1000000'))
        "۱,۰۰۰,۰۰۰ ریال"
    """
    formatted = f"{amount:,.0f}"
    persian_formatted = to_persian_numbers(formatted)
    
    if include_currency:
        return f"{persian_formatted} ریال"
    
    return persian_formatted


def format_quantity_persian(quantity: Decimal, unit: str = 'گرم') -> str:
    """
    Format a quantity with Persian numerals and unit.
    
    Args:
        quantity: Quantity to format
        unit: Unit of measurement (default: 'گرم')
        
    Returns:
        Formatted quantity string
        
    Example:
        >>> format_quantity_persian(Decimal('10.5'))
        "۱۰.۵ گرم"
    """
    formatted = f"{quantity}"
    persian_formatted = to_persian_numbers(formatted)
    
    return f"{persian_formatted} {unit}"


def get_user_tier(total_trade_volume: Decimal) -> dict:
    """
    Calculate user tier based on total trade volume.
    
    Tier Structure:
    - Bronze: 0-10M Rial
    - Silver: 10-50M Rial
    - Gold: 50-200M Rial
    - Platinum: 200M+ Rial
    
    Args:
        total_trade_volume: Total trade volume in Rial
        
    Returns:
        Dictionary with tier info:
        {
            'tier': 'GOLD',
            'tier_display': 'طلایی',
            'color': '#FFD700',
            'emoji': '🥇',
            'min_volume': Decimal('50000000'),
            'max_volume': Decimal('200000000'),
            'next_tier': 'PLATINUM',
            'progress_to_next': Decimal('0.25')  # 25% progress to next tier
        }
    """
    tiers = {
        'BRONZE': {
            'tier': 'BRONZE',
            'tier_display': 'برنزی',
            'color': '#CD7F32',
            'emoji': '🥉',
            'min_volume': Decimal('0'),
            'max_volume': Decimal('10000000'),
            'next_tier': 'SILVER',
            'benefits': [
                'دسترسی به معاملات پایه',
                'پشتیبانی استاندارد'
            ]
        },
        'SILVER': {
            'tier': 'SILVER',
            'tier_display': 'نقره‌ای',
            'color': '#C0C0C0',
            'emoji': '🥈',
            'min_volume': Decimal('10000000'),
            'max_volume': Decimal('50000000'),
            'next_tier': 'GOLD',
            'benefits': [
                'کاهش ۵٪ مارجین',
                'پشتیبانی اولویت‌دار',
                'دسترسی به تحلیل‌های بازار'
            ]
        },
        'GOLD': {
            'tier': 'GOLD',
            'tier_display': 'طلایی',
            'color': '#FFD700',
            'emoji': '🥇',
            'min_volume': Decimal('50000000'),
            'max_volume': Decimal('200000000'),
            'next_tier': 'PLATINUM',
            'benefits': [
                'کاهش ۱۰٪ مارجین',
                'پشتیبانی اختصاصی',
                'دسترسی زودهنگام به محصولات جدید',
                'تحلیل‌های پیشرفته بازار'
            ]
        },
        'PLATINUM': {
            'tier': 'PLATINUM',
            'tier_display': 'پلاتینیوم',
            'color': '#E5E4E2',
            'emoji': '💎',
            'min_volume': Decimal('200000000'),
            'max_volume': None,
            'next_tier': None,
            'benefits': [
                'کاهش ۱۵٪ مارجین',
                'مدیر حساب اختصاصی',
                'خدمات VIP',
                'دسترسی به معاملات عمده با قیمت ویژه',
                'مشاوره سرمایه‌گذاری رایگان'
            ]
        }
    }
    
    # Determine tier
    current_tier = None
    for tier_name, tier_data in tiers.items():
        if tier_data['max_volume'] is None:
            # Platinum (no upper limit)
            if total_trade_volume >= tier_data['min_volume']:
                current_tier = tier_data
                break
        else:
            if tier_data['min_volume'] <= total_trade_volume < tier_data['max_volume']:
                current_tier = tier_data
                break
    
    if current_tier is None:
        current_tier = tiers['BRONZE']
    
    # Calculate progress to next tier
    progress_to_next = Decimal('0')
    if current_tier['next_tier']:
        next_tier_data = tiers[current_tier['next_tier']]
        tier_range = next_tier_data['min_volume'] - current_tier['min_volume']
        user_progress = total_trade_volume - current_tier['min_volume']
        if tier_range > 0:
            progress_to_next = (user_progress / tier_range) * 100
            progress_to_next = min(progress_to_next, Decimal('100'))
    else:
        progress_to_next = Decimal('100')  # Max tier reached
    
    result = current_tier.copy()
    result['progress_to_next'] = progress_to_next
    result['total_trade_volume'] = total_trade_volume
    
    return result


def get_tier_badge_html(tier_info: dict) -> str:
    """
    Generate HTML badge for user tier display.
    
    Args:
        tier_info: Tier information dictionary from get_user_tier()
        
    Returns:
        HTML string for tier badge
    """
    return mark_safe(
        f'<span style="background: linear-gradient(135deg, {tier_info["color"]}, '
        f'{tier_info["color"]}CC); color: #000; padding: 5px 12px; '
        f'border-radius: 15px; font-weight: bold; font-size: 12px; '
        f'display: inline-block; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">'
        f'{tier_info["emoji"]} {tier_info["tier_display"]}'
        f'</span>'
    )


def format_percentage_change(current: Decimal, previous: Decimal) -> tuple[str, str]:
    """
    Calculate and format percentage change between two values.
    
    Args:
        current: Current value
        previous: Previous value
        
    Returns:
        Tuple of (percentage_string, trend_indicator)
        
    Example:
        >>> format_percentage_change(Decimal('110'), Decimal('100'))
        ('+10.0%', '📈')
        >>> format_percentage_change(Decimal('90'), Decimal('100'))
        ('-10.0%', '📉')
    """
    if previous == 0:
        return ('—', '')
    
    change = ((current - previous) / previous) * 100
    
    if change > 0:
        return (f'+{change:.1f}%', '📈')
    elif change < 0:
        return (f'{change:.1f}%', '📉')
    else:
        return ('0%', '➡️')


def get_trend_color(value: Decimal, threshold_positive: Decimal = Decimal('0')) -> str:
    """
    Get color code based on value trend.
    
    Args:
        value: Value to evaluate
        threshold_positive: Threshold above which value is considered positive
        
    Returns:
        Color code (green for positive, red for negative, gray for neutral)
    """
    if value > threshold_positive:
        return '#28a745'  # Green
    elif value < threshold_positive:
        return '#dc3545'  # Red
    else:
        return '#6c757d'  # Gray


def format_time_ago(dt) -> str:
    """
    Format a datetime as 'time ago' in Persian.
    
    Args:
        dt: datetime object
        
    Returns:
        Formatted time ago string in Persian
        
    Example:
        "۵ دقیقه پیش"
        "۲ ساعت پیش"
        "۳ روز پیش"
    """
    from django.utils import timezone
    
    now = timezone.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'هم‌اکنون'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{to_persian_numbers(str(minutes))} دقیقه پیش'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{to_persian_numbers(str(hours))} ساعت پیش'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{to_persian_numbers(str(days))} روز پیش'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{to_persian_numbers(str(weeks))} هفته پیش'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{to_persian_numbers(str(months))} ماه پیش'
    else:
        years = int(seconds / 31536000)
        return f'{to_persian_numbers(str(years))} سال پیش'


def calculate_margin_percentage(buy_margin: Decimal, sell_margin: Decimal, base_price: Decimal) -> dict:
    """
    Calculate margin percentages for display.
    
    Args:
        buy_margin: Buy margin in Rial
        sell_margin: Sell margin in Rial
        base_price: Base price from API
        
    Returns:
        Dictionary with margin percentages and profit margin
    """
    if base_price == 0:
        return {
            'buy_margin_pct': Decimal('0'),
            'sell_margin_pct': Decimal('0'),
            'profit_margin_pct': Decimal('0')
        }
    
    buy_margin_pct = (buy_margin / base_price) * 100
    sell_margin_pct = (sell_margin / base_price) * 100
    profit_margin_pct = ((buy_margin + sell_margin) / base_price) * 100
    
    return {
        'buy_margin_pct': buy_margin_pct.quantize(Decimal('0.01')),
        'sell_margin_pct': sell_margin_pct.quantize(Decimal('0.01')),
        'profit_margin_pct': profit_margin_pct.quantize(Decimal('0.01'))
    }


def get_performance_indicator(current: Decimal, target: Decimal) -> dict:
    """
    Get performance indicator comparing current value to target.
    
    Args:
        current: Current value
        target: Target value
        
    Returns:
        Dictionary with performance info
    """
    if target == 0:
        performance_pct = Decimal('100')
    else:
        performance_pct = (current / target) * 100
    
    if performance_pct >= 100:
        status = 'excellent'
        color = '#28a745'
        emoji = '🎉'
    elif performance_pct >= 75:
        status = 'good'
        color = '#20c997'
        emoji = '✅'
    elif performance_pct >= 50:
        status = 'fair'
        color = '#ffc107'
        emoji = '⚠️'
    else:
        status = 'poor'
        color = '#dc3545'
        emoji = '❌'
    
    return {
        'performance_pct': performance_pct.quantize(Decimal('0.1')),
        'status': status,
        'color': color,
        'emoji': emoji
    }
