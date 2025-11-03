"""Message formatters for trading operations."""

from decimal import Decimal
from trading.models import Product, Order
from users.models import Profile


class TradeMessageFormatter:
    """Formats messages for trading operations."""
    
    @staticmethod
    def format_product_list_item(product: Product, order_type: str) -> str:
        """Format single product for list display."""
        price = product.sell_price if order_type == Order.OrderType.BUY else product.buy_price
        action = "خرید" if order_type == Order.OrderType.BUY else "فروش"
        
        return f"{product.name} - {price:,} ریال ({action})"
    
    @staticmethod
    def format_order_summary(
        product: Product,
        order_type: str,
        quantity: Decimal,
        price_per_unit: Decimal,
        total: Decimal,
        unit: str
    ) -> str:
        """Format order summary for confirmation."""
        action_emoji = "🟢" if order_type == Order.OrderType.BUY else "🔴"
        action_text = "خرید" if order_type == Order.OrderType.BUY else "فروش"
        
        return (
            f"{action_emoji} *پیش‌فاکتور {action_text}*\n"
            f"{'═' * 30}\n\n"
            f"📦 *محصول:* {product.name}\n"
            f"💎 *قیمت واحد:* {price_per_unit:,} ریال\n"
            f"⚖️ *مقدار:* {quantity} {unit}\n"
            f"💵 *مبلغ کل:* {total:,} ریال\n\n"
            f"{'═' * 30}\n"
        )
    
    @staticmethod
    def format_balance_change(
        current_rial: Decimal,
        final_rial: Decimal,
        current_product: Decimal,
        final_product: Decimal,
        product_name: str,
        unit: str
    ) -> str:
        """Format balance change preview."""
        rial_change = final_rial - current_rial
        product_change = final_product - current_product
        
        rial_sign = "+" if rial_change >= 0 else ""
        product_sign = "+" if product_change >= 0 else ""
        
        return (
            f"💼 *تغییرات موجودی:*\n\n"
            f"💰 *ریال:*\n"
            f"   فعلی: {current_rial:,} ریال\n"
            f"   تغییر: {rial_sign}{rial_change:,} ریال\n"
            f"   نهایی: {final_rial:,} ریال\n\n"
            f"📦 *{product_name}:*\n"
            f"   فعلی: {current_product} {unit}\n"
            f"   تغییر: {product_sign}{product_change} {unit}\n"
            f"   نهایی: {final_product} {unit}\n"
        )
    
    @staticmethod
    def format_success_message(
        order_id: int,
        order_type: str,
        product_name: str,
        quantity: Decimal,
        total: Decimal,
        unit: str
    ) -> str:
        """Format success message after order completion."""
        action_emoji = "✅" if order_type == Order.OrderType.BUY else "✅"
        action_text = "خرید" if order_type == Order.OrderType.BUY else "فروش"
        
        return (
            f"{action_emoji} *{action_text} با موفقیت انجام شد!*\n\n"
            f"🧾 *شماره سفارش:* #{order_id}\n"
            f"📦 *محصول:* {product_name}\n"
            f"⚖️ *مقدار:* {quantity} {unit}\n"
            f"💵 *مبلغ:* {total:,} ریال\n\n"
            f"از {'خرید' if order_type == Order.OrderType.BUY else 'همراهی'} شما متشکریم! 🙏"
        )
