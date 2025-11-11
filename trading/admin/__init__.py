"""
Django admin configuration for trading app.

This package provides modular admin interfaces for:
- Products (gold, coins, etc.)
- Orders (buy/sell transactions)
- Transactions (deposits, withdrawals)
- Withdrawal Requests
- Price History
- Business Reporting Dashboard

Each admin class is in its own module for better maintainability.
"""

from django.contrib import admin

from .product_admin import ProductAdmin
from .order_admin import OrderAdmin
from .transaction_admin import TransactionAdmin
from .withdraw_admin import WithdrawRequestAdmin
from .pricehistory_admin import PriceHistoryAdmin
from .reporting_admin import BusinessReportingAdmin

from ..models import (
    Product,
    Order,
    Transaction,
    WithdrawRequest,
    PriceHistory
)


# Register admin classes
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Transaction, TransactionAdmin)
admin.site.register(WithdrawRequest, WithdrawRequestAdmin)
admin.site.register(PriceHistory, PriceHistoryAdmin)

# Note: BusinessReportingAdmin is not registered as it's a custom dashboard
# that needs to be accessed via a custom URL pattern


__all__ = [
    'ProductAdmin',
    'OrderAdmin',
    'TransactionAdmin',
    'WithdrawRequestAdmin',
    'PriceHistoryAdmin',
    'BusinessReportingAdmin',
]

