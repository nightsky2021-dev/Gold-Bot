"""
توابع کمکی برای ربات تلگرام
"""
from decimal import Decimal, InvalidOperation
from typing import Optional, Tuple
from django.utils import timezone
from datetime import datetime


def format_number(number: Decimal, decimal_places: int = 0) -> str:
    """فرمت کردن اعداد با جداکننده هزارگان"""
    if decimal_places == 0:
        return f"{int(number):,}"
    else:
        return f"{float(number):,.{decimal_places}f}"


def parse_decimal(text: str) -> Optional[Decimal]:
    """تبدیل متن به Decimal"""
    try:
        # حذف کاما و فاصله
        text = text.replace(',', '').replace(' ', '').strip()
        return Decimal(text)
    except (InvalidOperation, ValueError):
        return None


def format_datetime(dt: datetime) -> str:
    """فرمت کردن تاریخ و زمان به فارسی"""
    # تبدیل به timezone تهران
    local_dt = timezone.localtime(dt)
    return local_dt.strftime('%Y/%m/%d %H:%M')


def validate_amount(amount: Decimal, min_amount: Decimal = Decimal('0.0001')) -> Tuple[bool, str]:
    """
    اعتبارسنجی مقدار
    
    Returns:
        Tuple[bool, str]: (معتبر است؟, پیام خطا)
    """
    if amount <= 0:
        return False, "❌ مقدار باید بیشتر از صفر باشد."
    
    if amount < min_amount:
        return False, f"❌ حداقل مقدار {format_number(min_amount, 4)} است."
    
    return True, ""


def escape_markdown(text: str) -> str:
    """Escape کردن کاراکترهای خاص Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text
