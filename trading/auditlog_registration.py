"""
Auditlog registration for trading app models.

Registers models for comprehensive audit trail tracking.
"""

from auditlog.registry import auditlog
from .models import Product, Order, Transaction, WithdrawRequest


# Register models for audit logging
auditlog.register(Product, exclude_fields=['updated_at'])
auditlog.register(Order, exclude_fields=['updated_at'])
auditlog.register(Transaction, exclude_fields=['updated_at'])
auditlog.register(WithdrawRequest, exclude_fields=['updated_at'])
