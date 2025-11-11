"""
Shared mixins and base classes for admin interfaces.

These mixins provide common functionality used across multiple admin classes.
"""

from typing import Any, Optional
from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html
from decimal import Decimal


class ReadOnlyAdminMixin:
    """
    Mixin to make an admin interface read-only.
    
    Useful for audit trails and historical data that shouldn't be modified.
    """
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Disable adding new records."""
        return False
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Allow viewing but not changing records."""
        return True
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Disable deleting records."""
        return False


class SuperuserOnlyMixin:
    """
    Mixin to restrict admin access to superusers only.
    
    Provides fine-grained permission control for sensitive operations.
    """
    
    def has_add_permission(self, request: HttpRequest) -> bool:
        """Only superusers can add records."""
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def has_change_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Only superusers can change records."""
        return bool(request.user and getattr(request.user, 'is_superuser', False))
    
    def has_delete_permission(self, request: HttpRequest, obj: Any = None) -> bool:
        """Only superusers can delete records."""
        return bool(request.user and getattr(request.user, 'is_superuser', False))


class FormattingMixin:
    """
    Mixin providing common formatting methods for admin displays.
    
    Includes methods for formatting prices, quantities, badges, etc.
    """
    
    @staticmethod
    def format_currency(amount: Decimal, currency: str = 'ریال', decimal_places: int = 0) -> str:
        """
        Format currency amount with thousand separators.
        
        Args:
            amount: The amount to format
            currency: Currency symbol/name
            decimal_places: Number of decimal places to show
            
        Returns:
            Formatted string with currency
        """
        format_str = f"{{:,.{decimal_places}f}}"
        return f"{format_str.format(float(amount))} {currency}"
    
    @staticmethod
    def format_badge(text: str, color: str, bg_color: Optional[str] = None) -> str:
        """
        Format text as a colored badge.
        
        Args:
            text: Badge text
            color: Text color
            bg_color: Background color (defaults to transparent)
            
        Returns:
            HTML formatted badge
        """
        style = f"color: {color}; padding: 5px 10px; border-radius: 12px; font-weight: bold;"
        if bg_color:
            style += f" background-color: {bg_color};"
        
        return format_html(
            '<span class="badge" style="{}">{}</span>',
            style,
            text
        )
    
    @staticmethod
    def format_success_badge(text: str) -> str:
        """Format text as a success badge (green)."""
        return format_html(
            '<span class="badge badge-success" style="background-color: #28a745; color: white; padding: 5px 10px; border-radius: 12px;">{}</span>',
            text
        )
    
    @staticmethod
    def format_warning_badge(text: str) -> str:
        """Format text as a warning badge (yellow)."""
        return format_html(
            '<span class="badge badge-warning" style="background-color: #ffc107; color: black; padding: 5px 10px; border-radius: 12px;">{}</span>',
            text
        )
    
    @staticmethod
    def format_danger_badge(text: str) -> str:
        """Format text as a danger badge (red)."""
        return format_html(
            '<span class="badge badge-danger" style="background-color: #dc3545; color: white; padding: 5px 10px; border-radius: 12px;">{}</span>',
            text
        )
    
    @staticmethod
    def format_info_badge(text: str) -> str:
        """Format text as an info badge (blue)."""
        return format_html(
            '<span class="badge badge-info" style="background-color: #17a2b8; color: white; padding: 5px 10px; border-radius: 12px;">{}</span>',
            text
        )
    
    @staticmethod
    def format_secondary_badge(text: str) -> str:
        """Format text as a secondary badge (gray)."""
        return format_html(
            '<span class="badge badge-secondary" style="background-color: #6c757d; color: white; padding: 5px 10px; border-radius: 12px;">{}</span>',
            text
        )


class UserDisplayMixin:
    """
    Mixin for displaying user information in admin interfaces.
    
    Provides consistent user display across all admin classes.
    """
    
    def get_user_display(self, obj: Any) -> str:
        """
        Display user information with proper formatting.
        
        Args:
            obj: Object with a 'profile' attribute
            
        Returns:
            Formatted user display name
        """
        if hasattr(obj, 'profile') and obj.profile:
            return obj.profile.get_display_name()
        return '—'
    
    # Set common properties for the method
    get_user_display.short_description = 'کاربر'  # type: ignore
    get_user_display.admin_order_field = 'profile__user__first_name'  # type: ignore


__all__ = [
    'ReadOnlyAdminMixin',
    'SuperuserOnlyMixin',
    'FormattingMixin',
    'UserDisplayMixin',
]

