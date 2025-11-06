"""
Custom admin views for the trading app.

Provides dashboard and analytics views for admin interface.
"""

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from trading.models import Product, Order, Transaction, WithdrawRequest
from users.models import Profile, BankAccount


@staff_member_required
def admin_dashboard(request):
    """
    Custom admin dashboard with KPIs and analytics.
    
    Provides comprehensive overview of system statistics and recent activity.
    """
    
    # Date ranges for statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # ===== USER STATISTICS =====
    total_users = Profile.objects.count()
    approved_users = Profile.objects.filter(is_approved=True).count()
    pending_users = Profile.objects.filter(is_approved=False).count()
    new_users_this_week = Profile.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(week_ago, datetime.min.time()))
    ).count()
    new_users_this_month = Profile.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(month_ago, datetime.min.time()))
    ).count()
    
    # ===== ORDER STATISTICS =====
    total_orders = Order.objects.count()
    pending_orders = 0  # No pending orders with instant execution
    completed_orders = Order.objects.filter(status=Order.OrderStatus.COMPLETED).count()
    cancelled_orders = Order.objects.filter(status=Order.OrderStatus.CANCELLED).count()
    
    orders_this_week = Order.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(week_ago, datetime.min.time()))
    ).count()
    orders_this_month = Order.objects.filter(
        created_at__gte=timezone.make_aware(datetime.combine(month_ago, datetime.min.time()))
    ).count()
    
    # Order type breakdown
    buy_orders = Order.objects.filter(order_type=Order.OrderType.BUY).count()
    sell_orders = Order.objects.filter(order_type=Order.OrderType.SELL).count()
    
    # ===== TRANSACTION STATISTICS =====
    total_transactions = Transaction.objects.count()
    pending_transactions = Transaction.objects.filter(status='PENDING').count()
    completed_transactions = Transaction.objects.filter(status='COMPLETED').count()
    
    # Transaction type breakdown
    deposit_txns = Transaction.objects.filter(transaction_type='DEPOSIT').count()
    withdraw_txns = Transaction.objects.filter(transaction_type='WITHDRAW').count()
    
    # Total deposit and withdrawal amounts (RIAL only)
    total_deposits = Transaction.objects.filter(
        transaction_type='DEPOSIT',
        status='COMPLETED',
        currency='RIAL'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    total_withdrawals = Transaction.objects.filter(
        transaction_type='WITHDRAW',
        status='COMPLETED',
        currency='RIAL'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
    
    # ===== WITHDRAWAL REQUEST STATISTICS =====
    total_withdraw_requests = WithdrawRequest.objects.count()
    pending_withdraw_requests = WithdrawRequest.objects.filter(status='PENDING').count()
    processing_withdraw_requests = WithdrawRequest.objects.filter(status='PROCESSING').count()
    completed_withdraw_requests = WithdrawRequest.objects.filter(status='COMPLETED').count()
    
    # ===== FINANCIAL STATISTICS =====
    # Total revenue from completed orders (selling to customers)
    total_revenue = Order.objects.filter(
        status=Order.OrderStatus.COMPLETED,
        order_type=Order.OrderType.BUY  # User buys from us
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Total cost from completed orders (buying from customers)
    total_cost = Order.objects.filter(
        status=Order.OrderStatus.COMPLETED,
        order_type=Order.OrderType.SELL  # User sells to us
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # ===== PRODUCT STATISTICS =====
    active_products = Product.objects.filter(is_active=True).count()
    inactive_products = Product.objects.filter(is_active=False).count()
    
    # ===== RECENT ACTIVITY =====
    recent_orders = Order.objects.select_related('profile__user', 'product').order_by('-created_at')[:10]
    recent_transactions = Transaction.objects.select_related('profile__user').order_by('-created_at')[:10]
    recent_users = Profile.objects.select_related('user').order_by('-created_at')[:10]
    
    # ===== TOP USERS BY ORDER VALUE =====
    top_users = Profile.objects.annotate(
        total_order_value=Sum('orders__total_amount', filter=Q(orders__status=Order.OrderStatus.COMPLETED))
    ).filter(total_order_value__isnull=False).order_by('-total_order_value')[:10]
    
    # ===== ALERTS =====
    alerts = []
    
    if pending_orders > 0:
        alerts.append({
            'type': 'warning',
            'message': f'{pending_orders} سفارش در انتظار بررسی',
            'url': '/admin/trading/order/?status=PENDING'
        })
    
    if pending_transactions > 0:
        alerts.append({
            'type': 'info',
            'message': f'{pending_transactions} تراکنش در انتظار تأیید',
            'url': '/admin/trading/transaction/?status=PENDING'
        })
    
    if pending_withdraw_requests > 0:
        alerts.append({
            'type': 'warning',
            'message': f'{pending_withdraw_requests} درخواست برداشت در انتظار پردازش',
            'url': '/admin/trading/withdrawrequest/?status=PENDING'
        })
    
    if pending_users > 0:
        alerts.append({
            'type': 'info',
            'message': f'{pending_users} کاربر در انتظار تأیید',
            'url': '/admin/users/profile/?is_approved__exact=0'
        })
    
    context = {
        # User stats
        'total_users': total_users,
        'approved_users': approved_users,
        'pending_users': pending_users,
        'new_users_this_week': new_users_this_week,
        'new_users_this_month': new_users_this_month,
        
        # Order stats
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'orders_this_week': orders_this_week,
        'orders_this_month': orders_this_month,
        'buy_orders': buy_orders,
        'sell_orders': sell_orders,
        
        # Transaction stats
        'total_transactions': total_transactions,
        'pending_transactions': pending_transactions,
        'completed_transactions': completed_transactions,
        'deposit_txns': deposit_txns,
        'withdraw_txns': withdraw_txns,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        
        # Withdrawal request stats
        'total_withdraw_requests': total_withdraw_requests,
        'pending_withdraw_requests': pending_withdraw_requests,
        'processing_withdraw_requests': processing_withdraw_requests,
        'completed_withdraw_requests': completed_withdraw_requests,
        
        # Financial stats
        'total_revenue': total_revenue,
        'total_cost': total_cost,
        'net_profit': total_revenue - total_cost,
        
        # Product stats
        'active_products': active_products,
        'inactive_products': inactive_products,
        
        # Recent activity
        'recent_orders': recent_orders,
        'recent_transactions': recent_transactions,
        'recent_users': recent_users,
        'top_users': top_users,
        
        # Alerts
        'alerts': alerts,
        
        # Misc
        'title': 'داشبورد مدیریت',
        'site_title': 'پنل مدیریت طلا',
    }
    
    return render(request, 'admin/dashboard.html', context)
