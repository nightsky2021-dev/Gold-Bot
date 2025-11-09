"""Context data management for trading conversations."""

from typing import Optional, Dict, Any
from decimal import Decimal
from telegram.ext import ContextTypes
from trading.models import Order


class TradingContext:
    """Manages conversation context data for trading operations."""
    
    def __init__(self, context: ContextTypes.DEFAULT_TYPE):
        self.context = context
        self._data = context.user_data if context.user_data is not None else {}
    
    @property
    def last_message_id(self) -> Optional[int]:
        """Get the last message ID for editing."""
        return self._data.get('last_message_id')
    
    @last_message_id.setter
    def last_message_id(self, value: int):
        """Set the last message ID."""
        self._data['last_message_id'] = value
    
    # Property getters with validation
    @property
    def product_id(self) -> Optional[int]:
        return self._data.get('product_id')
    
    @product_id.setter
    def product_id(self, value: int):
        self._data['product_id'] = value
    
    @property
    def order_type(self) -> Optional[str]:
        return self._data.get('order_type')
    
    @order_type.setter
    def order_type(self, value: str):
        if value not in [Order.OrderType.BUY, Order.OrderType.SELL]:
            raise ValueError(f"Invalid order type: {value}")
        self._data['order_type'] = value
    
    @property
    def calculation_method(self) -> Optional[str]:
        return self._data.get('calculation_method')
    
    @calculation_method.setter
    def calculation_method(self, value: str):
        self._data['calculation_method'] = value
    
    @property
    def quantity_grams(self) -> Optional[Decimal]:
        val = self._data.get('quantity_grams')
        return Decimal(str(val)) if val else None
    
    @quantity_grams.setter
    def quantity_grams(self, value: Decimal):
        self._data['quantity_grams'] = value
    
    @property
    def price_per_gram(self) -> Optional[Decimal]:
        val = self._data.get('price_per_gram')
        return Decimal(str(val)) if val else None
    
    @price_per_gram.setter
    def price_per_gram(self, value: Decimal):
        self._data['price_per_gram'] = value
    
    @property
    def total_amount(self) -> Optional[Decimal]:
        val = self._data.get('total_amount')
        return Decimal(str(val)) if val else None
    
    @total_amount.setter
    def total_amount(self, value: Decimal):
        self._data['total_amount'] = value
    
    def get_price_timestamp(self, product_code: str) -> int:
        """Get price timestamp for a product."""
        return self._data.get(f'price_time_{product_code}', 0)
    
    def set_price_timestamp(self, product_code: str, timestamp: int):
        """Set price timestamp for a product."""
        self._data[f'price_time_{product_code}'] = timestamp
    
    def is_complete(self) -> bool:
        """Check if all required data is present."""
        return all([
            self.product_id,
            self.order_type,
            self.quantity_grams,
            self.price_per_gram,
            self.total_amount
        ])
    
    def clear(self):
        """Clear all trading context data."""
        self._data.clear()
    
    def to_dict(self) -> Dict[str, Any]:
        """Export context as dictionary."""
        return {
            'product_id': self.product_id,
            'order_type': self.order_type,
            'calculation_method': self.calculation_method,
            'quantity_grams': float(self.quantity_grams) if self.quantity_grams else None,
            'price_per_gram': float(self.price_per_gram) if self.price_per_gram else None,
            'total_amount': float(self.total_amount) if self.total_amount else None,
        }
