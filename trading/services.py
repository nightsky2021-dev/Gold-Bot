"""
Business logic services for trading app
"""
from typing import List, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Product, Order
from users.models import Profile


def get_active_products() -> List[Product]:
    """
    دریافت لیست محصولات فعال
    
    Returns:
        List[Product]: لیست محصولات فعال
    """
    return list(Product.objects.filter(is_active=True).order_by('name'))


def get_product_by_id(product_id: int) -> Optional[Product]:
    """
    دریافت محصول بر اساس شناسه
    
    Args:
        product_id: شناسه محصول
    
    Returns:
        Product یا None
    """
    try:
        return Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return None


def calculate_buy_order(
    product: Product,
    amount_type: str,
    amount_value: Decimal
) -> dict:
    """
    محاسبه جزئیات سفارش خرید (مشتری از ما می‌خرد)
    
    Args:
        product: محصول
        amount_type: نوع محاسبه ('rial' یا 'gram')
        amount_value: مقدار (ریال یا گرم)
    
    Returns:
        dict: جزئیات محاسبه شده
    """
    if amount_type == 'rial':
        # محاسبه بر اساس ریال
        total_rial = Decimal(amount_value)
        quantity_grams = total_rial / product.sell_price
    else:  # gram
        # محاسبه بر اساس گرم
        quantity_grams = Decimal(amount_value)
        total_rial = quantity_grams * product.sell_price
    
    return {
        'product': product,
        'quantity_grams': quantity_grams,
        'price_per_gram': product.sell_price,
        'total_amount': total_rial,
        'order_type': Order.OrderType.BUY
    }


def calculate_sell_order(
    product: Product,
    amount_type: str,
    amount_value: Decimal
) -> dict:
    """
    محاسبه جزئیات سفارش فروش (مشتری به ما می‌فروشد)
    
    Args:
        product: محصول
        amount_type: نوع محاسبه ('rial' یا 'gram')
        amount_value: مقدار (ریال یا گرم)
    
    Returns:
        dict: جزئیات محاسبه شده
    """
    if amount_type == 'rial':
        # محاسبه بر اساس ریال
        total_rial = Decimal(amount_value)
        quantity_grams = total_rial / product.buy_price
    else:  # gram
        # محاسبه بر اساس گرم
        quantity_grams = Decimal(amount_value)
        total_rial = quantity_grams * product.buy_price
    
    return {
        'product': product,
        'quantity_grams': quantity_grams,
        'price_per_gram': product.buy_price,
        'total_amount': total_rial,
        'order_type': Order.OrderType.SELL
    }


def create_order(
    profile: Profile,
    product: Product,
    order_type: str,
    quantity_grams: Decimal,
    price_per_gram: Decimal,
    total_amount: Decimal
) -> Order:
    """
    ایجاد سفارش جدید با وضعیت PENDING
    
    Args:
        profile: پروفایل کاربر
        product: محصول
        order_type: نوع سفارش ('BUY' یا 'SELL')
        quantity_grams: مقدار به گرم
        price_per_gram: قیمت هر گرم
        total_amount: مبلغ کل
    
    Returns:
        Order: سفارش ایجاد شده
    """
    order = Order.objects.create(
        profile=profile,
        product=product,
        order_type=order_type,
        quantity_grams=quantity_grams,
        price_per_gram=price_per_gram,
        total_amount=total_amount,
        status=Order.OrderStatus.PENDING
    )
    
    return order


def process_order(order: Order) -> Order:
    """
    پردازش سفارش و به‌روزرسانی موجودی کاربر
    این تابع توسط ادمین برای تایید سفارشات فراخوانی می‌شود
    
    Args:
        order: سفارش
    
    Returns:
        Order: سفارش پردازش شده
    
    Raises:
        ValueError: در صورت عدم کفایت موجودی
    """
    from users.services import update_user_balance
    
    if order.status != Order.OrderStatus.PENDING:
        raise ValueError("فقط سفارشات در حالت PENDING قابل پردازش هستند.")
    
    with transaction.atomic():
        profile = Profile.objects.select_for_update().get(id=order.profile.id)
        
        if order.order_type == Order.OrderType.BUY:
            # مشتری از ما می‌خرد: ریال کم می‌شود، طلا زیاد می‌شود
            rial_change = -order.total_amount
            gold_change = order.quantity_grams
        else:  # SELL
            # مشتری به ما می‌فروشد: طلا کم می‌شود، ریال زیاد می‌شود
            rial_change = order.total_amount
            gold_change = -order.quantity_grams
        
        # به‌روزرسانی موجودی (این تابع خطا می‌دهد اگر موجودی کافی نباشد)
        update_user_balance(profile, rial_change=rial_change, gold_change=gold_change)
        
        # تغییر وضعیت سفارش به تکمیل شده
        order.status = Order.OrderStatus.COMPLETED
        order.save(update_fields=['status'])
    
    return order


def get_user_orders(profile: Profile, limit: int = 5) -> List[Order]:
    """
    دریافت تاریخچه سفارشات کاربر
    
    Args:
        profile: پروفایل کاربر
        limit: تعداد سفارشات برگشتی
    
    Returns:
        List[Order]: لیست سفارشات
    """
    return list(
        Order.objects
        .filter(profile=profile)
        .select_related('product')
        .order_by('-created_at')[:limit]
    )


def get_price_list() -> str:
    """
    دریافت لیست قیمت‌های محصولات فعال به صورت فرمت شده
    
    Returns:
        str: متن فرمت شده قیمت‌ها
    """
    products = get_active_products()
    
    if not products:
        return "در حال حاضر محصولی برای نمایش وجود ندارد."
    
    lines = ["📊 *قیمت‌های لحظه‌ای طلا*\n"]
    
    for product in products:
        lines.append(f"🔸 *{product.name}*")
        lines.append(f"   💰 خرید از ما: `{product.get_formatted_sell_price()}` ریال")
        lines.append(f"   💵 فروش به ما: `{product.get_formatted_buy_price()}` ریال")
        lines.append("")
    
    lines.append(f"_آخرین به‌روزرسانی: {timezone.now().strftime('%Y-%m-%d %H:%M')}_")
    
    return "\n".join(lines)
