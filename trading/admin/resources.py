"""
Import/Export resources for trading models.

These resources define how data is imported and exported for each model.
They use the django-import-export library for Excel/CSV operations.
"""

from typing import Any
from import_export import resources, fields  # type: ignore[import-untyped]

from ..models import Product, Order, Transaction, WithdrawRequest


class ProductResource(resources.ModelResource):
    """
    Resource for importing/exporting Product data.
    
    Includes calculated fields like price spread for export.
    """
    
    price_spread = fields.Field(
        column_name='اختلاف قیمت',
        readonly=True
    )
    
    def dehydrate_price_spread(self, product: Product) -> float:
        """Calculate price spread for export."""
        return float(product.get_price_spread())
    
    class Meta:
        model = Product
        fields = (
            'id',
            'product_code',
            'name',
            'slug',
            'buy_price',
            'sell_price',
            'price_spread',
            'is_active',
            'updated_at',
            'created_at'
        )
        export_order = fields


class OrderResource(resources.ModelResource):
    """
    Resource for importing/exporting Order data.
    
    Includes user and product names for better readability in exports.
    """
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    product_name = fields.Field(
        column_name='نام محصول',
        attribute='product__name',
        readonly=True
    )
    
    class Meta:
        model = Order
        fields = (
            'id',
            'user_name',
            'product_name',
            'order_type',
            'quantity_grams',
            'price_per_gram',
            'total_amount',
            'status',
            'created_at',
            'completed_at'
        )
        export_order = fields


class TransactionResource(resources.ModelResource):
    """
    Resource for importing/exporting Transaction data.
    
    Includes user information for better tracking.
    """
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    class Meta:
        model = Transaction
        fields = (
            'id',
            'user_name',
            'transaction_type',
            'currency',
            'amount',
            'status',
            'description',
            'created_at',
            'completed_at'
        )
        export_order = fields


class WithdrawRequestResource(resources.ModelResource):
    """
    Resource for importing/exporting WithdrawRequest data.
    
    Includes user information and rejection reasons.
    """
    
    user_name = fields.Field(
        column_name='نام کاربر',
        attribute='profile__user',
        readonly=True
    )
    
    class Meta:
        model = WithdrawRequest
        fields = (
            'id',
            'user_name',
            'currency',
            'amount',
            'status',
            'rejection_reason',
            'created_at',
            'completed_at'
        )
        export_order = fields


__all__ = [
    'ProductResource',
    'OrderResource',
    'TransactionResource',
    'WithdrawRequestResource',
]

