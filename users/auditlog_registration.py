"""
Auditlog registration for users app models.

Registers models for comprehensive audit trail tracking.
"""

from auditlog.registry import auditlog
from .models import Profile, BankAccount


# Register models for audit logging
auditlog.register(Profile, exclude_fields=['updated_at'])
auditlog.register(BankAccount, exclude_fields=['updated_at'])
