"""
Service layer for the user transaction portal.

This module contains business logic for portal authentication,
profit/loss calculations, and data aggregation.
"""

import logging
import secrets
from typing import Optional, Dict, List, Tuple, Any
from decimal import Decimal
from datetime import datetime, timedelta
from django.db import transaction
from django.db.models import Sum, Q, Count, Avg, F, QuerySet
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.conf import settings

from .models import (
    Product, Order, Transaction, PortalAccessToken, WithdrawRequest
)
from users.models import Profile

logger = logging.getLogger('trading.portal')


class PortalTokenService:
    """Service for managing portal access tokens."""
    
    @staticmethod
    def get_token_validity_hours() -> int:
        """Get token validity hours from settings or use default."""
        return getattr(settings, 'PORTAL_TOKEN_EXPIRATION_HOURS', 24)
    
    @staticmethod
    def generate_token(profile: Profile, single_use: bool = False) -> PortalAccessToken:
        """
        Generate a new access token for user.
        
        Args:
            profile: User profile
            single_use: If True, token can only be used once
            
        Returns:
            PortalAccessToken instance
        """
        # Generate secure random token
        token_string = secrets.token_urlsafe(32)
        
        # Set expiration
        validity_hours = PortalTokenService.get_token_validity_hours()
        expires_at = timezone.now() + timedelta(hours=validity_hours)
        
        # Create token
        token = PortalAccessToken.objects.create(
            profile=profile,
            token=token_string,
            expires_at=expires_at,
            is_used=False
        )
        
        logger.info(
            f"Portal token generated for {profile.get_display_name()}: "
            f"{token_string[:8]}... (expires: {expires_at})"
        )
        
        return token
    
    @staticmethod
    def validate_token(token_string: str) -> Optional[Profile]:
        """
        Validate a token and return associated profile.
        
        Args:
            token_string: The token string to validate
            
        Returns:
            Profile if valid, None otherwise
        """
        try:
            token = PortalAccessToken.objects.select_related('profile').get(
                token=token_string
            )
            
            if token.is_valid():
                return token.profile
            else:
                logger.warning(f"Invalid or expired token attempted: {token_string[:8]}...")
                return None
                
        except PortalAccessToken.DoesNotExist:
            logger.warning(f"Non-existent token attempted: {token_string[:8]}...")
            return None
    
    @staticmethod
    def mark_token_used(
        token_string: str,
        ip_address: Optional[str] = None,
        user_agent: str = ""
    ) -> bool:
        """
        Mark a token as used.
        
        Args:
            token_string: The token string
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            True if successful, False otherwise
        """
        try:
            token = PortalAccessToken.objects.get(token=token_string)
            token.mark_as_used(ip_address, user_agent)
            logger.info(f"Token marked as used: {token_string[:8]}...")
            return True
        except PortalAccessToken.DoesNotExist:
            return False
    
    @staticmethod
    def cleanup_expired_tokens() -> int:
        """
        Delete expired tokens from database.
        
        Returns:
            Number of tokens deleted
        """
        count, _ = PortalAccessToken.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        
        if count > 0:
            logger.info(f"Cleaned up {count} expired portal tokens")
        
        return count


class ProfitLossService:
    """Service for calculating profit/loss metrics."""
    
    @staticmethod
    def calculate_product_pl(
        profile: Profile,
        product: Product,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate profit/loss for a specific product.
        
        Args:
            profile: User profile
            product: Product to analyze
            date_from: Start date for filtering (optional)
            date_to: End date for filtering (optional)
            
        Returns:
            Dictionary with P/L metrics
        """
        # Build queryset with filters
        orders_qs = Order.objects.filter(
            profile=profile,
            product=product,
            status=Order.OrderStatus.COMPLETED
        )
        
        if date_from:
            orders_qs = orders_qs.filter(created_at__gte=date_from)
        if date_to:
            orders_qs = orders_qs.filter(created_at__lte=date_to)
        
        # Aggregate buy orders
        buy_orders = orders_qs.filter(order_type=Order.OrderType.BUY).aggregate(
            total_quantity=Sum('quantity_grams'),
            total_amount=Sum('total_amount'),
            count=Count('id'),
            avg_price=Avg('price_per_gram')
        )
        
        # Aggregate sell orders
        sell_orders = orders_qs.filter(order_type=Order.OrderType.SELL).aggregate(
            total_quantity=Sum('quantity_grams'),
            total_amount=Sum('total_amount'),
            count=Count('id'),
            avg_price=Avg('price_per_gram')
        )
        
        # Calculate metrics
        total_bought = buy_orders['total_quantity'] or Decimal('0')
        total_sold = sell_orders['total_quantity'] or Decimal('0')
        amount_invested = buy_orders['total_amount'] or Decimal('0')
        amount_received = sell_orders['total_amount'] or Decimal('0')
        avg_buy_price = buy_orders['avg_price'] or Decimal('0')
        avg_sell_price = sell_orders['avg_price'] or Decimal('0')
        
        # Current holdings
        from trading.services import OrderService
        current_holdings = OrderService.get_product_balance(profile, product)
        
        # Realized P/L (from completed sells)
        realized_pl = amount_received - (total_sold * avg_buy_price if total_sold > 0 else Decimal('0'))
        
        # Unrealized P/L (from current holdings)
        current_price = product.sell_price  # Current market price
        unrealized_pl = (current_holdings * current_price) - (current_holdings * avg_buy_price if current_holdings > 0 else Decimal('0'))
        
        # Total P/L
        total_pl = realized_pl + unrealized_pl
        
        # ROI percentage
        roi_percentage = (total_pl / amount_invested * 100) if amount_invested > 0 else Decimal('0')
        
        return {
            'product': product,
            'total_bought': total_bought,
            'total_sold': total_sold,
            'current_holdings': current_holdings,
            'amount_invested': amount_invested,
            'amount_received': amount_received,
            'avg_buy_price': avg_buy_price,
            'avg_sell_price': avg_sell_price,
            'current_market_price': current_price,
            'realized_pl': realized_pl,
            'unrealized_pl': unrealized_pl,
            'total_pl': total_pl,
            'roi_percentage': roi_percentage,
            'buy_count': buy_orders['count'] or 0,
            'sell_count': sell_orders['count'] or 0,
        }
    
    @staticmethod
    def calculate_portfolio_pl(
        profile: Profile,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Calculate overall portfolio profit/loss.
        
        Args:
            profile: User profile
            date_from: Start date for filtering (optional)
            date_to: End date for filtering (optional)
            
        Returns:
            Dictionary with portfolio-level metrics
        """
        # Get all products user has traded
        orders_qs = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        )
        
        if date_from:
            orders_qs = orders_qs.filter(created_at__gte=date_from)
        if date_to:
            orders_qs = orders_qs.filter(created_at__lte=date_to)
        
        traded_products = Product.objects.filter(
            orders__in=orders_qs
        ).distinct()
        
        # Calculate P/L for each product
        product_pl_list = []
        total_invested = Decimal('0')
        total_received = Decimal('0')
        total_realized_pl = Decimal('0')
        total_unrealized_pl = Decimal('0')
        
        for product in traded_products:
            pl = ProfitLossService.calculate_product_pl(
                profile, product, date_from, date_to
            )
            product_pl_list.append(pl)
            total_invested += pl['amount_invested']
            total_received += pl['amount_received']
            total_realized_pl += pl['realized_pl']
            total_unrealized_pl += pl['unrealized_pl']
        
        total_pl = total_realized_pl + total_unrealized_pl
        roi_percentage = (total_pl / total_invested * 100) if total_invested > 0 else Decimal('0')
        
        # Find best and worst performing products
        best_product = max(product_pl_list, key=lambda x: x['total_pl']) if product_pl_list else None
        worst_product = min(product_pl_list, key=lambda x: x['total_pl']) if product_pl_list else None
        
        # Current portfolio value
        current_portfolio_value = sum([
            pl['current_holdings'] * pl['current_market_price']
            for pl in product_pl_list
        ])
        
        return {
            'products': product_pl_list,
            'total_invested': total_invested,
            'total_received': total_received,
            'current_portfolio_value': current_portfolio_value,
            'realized_pl': total_realized_pl,
            'unrealized_pl': total_unrealized_pl,
            'total_pl': total_pl,
            'roi_percentage': roi_percentage,
            'best_product': best_product,
            'worst_product': worst_product,
            'total_products_traded': len(product_pl_list),
        }


class PortalDataService:
    """Service for aggregating portal dashboard data."""
    
    @staticmethod
    def get_dashboard_data(profile: Profile) -> Dict[str, Any]:
        """
        Get dashboard overview data.
        
        Args:
            profile: User profile
            
        Returns:
            Dictionary with dashboard metrics
        """
        # Total portfolio value
        from trading.services import OrderService
        
        # Get all products with balances
        all_products = Product.objects.filter(is_active=True)
        portfolio_items = []
        total_portfolio_value = Decimal('0')
        
        for product in all_products:
            balance = OrderService.get_product_balance(profile, product)
            if balance > 0:
                value = balance * product.sell_price
                portfolio_items.append({
                    'product': product,
                    'balance': balance,
                    'unit': OrderService.get_product_unit(product),
                    'current_price': product.sell_price,
                    'value': value
                })
                total_portfolio_value += value
        
        # Add Rial balance
        total_portfolio_value += profile.rial_balance
        
        # Recent transactions (last 5)
        recent_orders = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).select_related('product').order_by('-created_at')[:5]
        
        # Today's P/L
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_pl = ProfitLossService.calculate_portfolio_pl(
            profile,
            date_from=today_start
        )
        
        # Total statistics
        total_orders = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).count()
        
        # Calculate total invested (all buy orders)
        total_invested = Order.objects.filter(
            profile=profile,
            order_type=Order.OrderType.BUY,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Overall P/L
        overall_pl = ProfitLossService.calculate_portfolio_pl(profile)
        
        # Get wallet balances using WalletService for consistency
        from users.services import WalletService
        wallet_balances = WalletService.get_wallet_balance(profile)
        
        # Safely extract rial balance with fallback
        rial_balance_data = wallet_balances.get('rial')
        if not rial_balance_data:
            # Fallback: construct from profile fields if not in wallet_balances
            logger.warning(f"Rial balance not found in wallet_balances for profile {profile.id}, using fallback")
            rial_balance_data = {
                'total': profile.rial_balance + profile.frozen_rial_balance,
                'available': profile.rial_balance,
                'frozen': profile.frozen_rial_balance
            }
        
        return {
            'profile': profile,
            'total_portfolio_value': total_portfolio_value,
            'rial_balance': rial_balance_data,
            'wallet_balances': wallet_balances,
            'portfolio_items': portfolio_items,
            'recent_orders': recent_orders,
            'today_pl': today_pl['total_pl'],
            'total_orders': total_orders,
            'total_invested': total_invested,
            'net_pl': overall_pl['total_pl'],
            'roi_percentage': overall_pl['roi_percentage'],
        }
    
    @staticmethod
    def get_transactions_data(
        profile: Profile,
        product_id: Optional[int] = None,
        transaction_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict[str, Any]:
        """
        Get filtered transaction list.
        
        Args:
            profile: User profile
            product_id: Filter by product ID
            transaction_type: Filter by type (BUY/SELL)
            date_from: Start date
            date_to: End date
            page: Page number
            per_page: Items per page
            
        Returns:
            Dictionary with transactions and pagination info
        """
        # Build queryset
        orders_qs = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).select_related('product').order_by('-created_at')
        
        # Apply filters
        if product_id:
            orders_qs = orders_qs.filter(product_id=product_id)
        
        if transaction_type:
            orders_qs = orders_qs.filter(order_type=transaction_type)
        
        if date_from:
            orders_qs = orders_qs.filter(created_at__gte=date_from)
        
        if date_to:
            orders_qs = orders_qs.filter(created_at__lte=date_to)
        
        # Total count
        total_count = orders_qs.count()
        
        # Pagination
        start = (page - 1) * per_page
        end = start + per_page
        orders = orders_qs[start:end]
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return {
            'orders': orders,
            'total_count': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
        }
    
    @staticmethod
    def get_account_statement(profile: Profile) -> Dict[str, Any]:
        """
        Get account statement with balances and pending items.
        
        Args:
            profile: User profile
            
        Returns:
            Dictionary with statement data
        """
        from trading.services import OrderService
        
        # Current balances
        all_products = Product.objects.filter(is_active=True)
        balances = []
        
        for product in all_products:
            balance = OrderService.get_product_balance(profile, product)
            if balance > 0:
                balances.append({
                    'product': product,
                    'balance': balance,
                    'unit': OrderService.get_product_unit(product),
                    'current_price': product.sell_price,
                    'value_in_rial': balance * product.sell_price
                })
        
        # Rial balance - use WalletService for consistency
        from users.services import WalletService
        wallet_balances = WalletService.get_wallet_balance(profile)
        rial_balance = wallet_balances.get('rial', {
            'available': profile.get_available_rial_balance(),
            'frozen': profile.frozen_rial_balance,
            'total': profile.rial_balance + profile.frozen_rial_balance
        })
        
        # Total deposits and withdrawals
        deposits = Transaction.objects.filter(
            profile=profile,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            status=Transaction.TransactionStatus.COMPLETED,
            currency=Transaction.CurrencyType.RIAL
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        withdrawals = Transaction.objects.filter(
            profile=profile,
            transaction_type=Transaction.TransactionType.WITHDRAW,
            status=Transaction.TransactionStatus.COMPLETED,
            currency=Transaction.CurrencyType.RIAL
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        net_cash_flow = deposits - withdrawals
        
        # Pending items
        pending_deposits = Transaction.objects.filter(
            profile=profile,
            status=Transaction.TransactionStatus.PENDING,
            transaction_type=Transaction.TransactionType.DEPOSIT
        )
        
        pending_withdrawals = WithdrawRequest.objects.filter(
            profile=profile,
            status__in=[
                WithdrawRequest.WithdrawStatus.PENDING,
                WithdrawRequest.WithdrawStatus.PROCESSING
            ]
        )
        
        # Transaction statistics
        total_transactions = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).count()
        
        total_buy_orders = Order.objects.filter(
            profile=profile,
            order_type=Order.OrderType.BUY,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        total_sell_orders = Order.objects.filter(
            profile=profile,
            order_type=Order.OrderType.SELL,
            status=Order.OrderStatus.COMPLETED
        ).aggregate(
            count=Count('id'),
            total=Sum('total_amount')
        )
        
        # Most traded product
        most_traded = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).values('product__name').annotate(
            count=Count('id')
        ).order_by('-count').first()
        
        # First and last transaction dates
        first_order = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).order_by('created_at').first()
        
        last_order = Order.objects.filter(
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        ).order_by('-created_at').first()
        
        return {
            'profile': profile,
            'rial_balance': rial_balance,
            'product_balances': balances,
            'deposits': deposits,
            'withdrawals': withdrawals,
            'net_cash_flow': net_cash_flow,
            'is_creditor': net_cash_flow > 0,
            'pending_deposits': pending_deposits,
            'pending_withdrawals': pending_withdrawals,
            'total_transactions': total_transactions,
            'total_buy_orders': total_buy_orders,
            'total_sell_orders': total_sell_orders,
            'most_traded_product': most_traded['product__name'] if most_traded else 'ندارد',
            'first_transaction_date': first_order.created_at if first_order else None,
            'last_transaction_date': last_order.created_at if last_order else None,
            'updated_at': timezone.now(),
        }
