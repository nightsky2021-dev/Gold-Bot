"""
Views for the user transaction portal.

Handles authentication, dashboard, transactions, P/L, and exports.
"""

import logging
import csv
import io
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpRequest
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import Product, Order
from .portal_services import (
    PortalTokenService,
    ProfitLossService,
    PortalDataService
)
from users.models import Profile

logger = logging.getLogger('trading.portal_views')


# ==================== Helper Functions ====================

def get_client_ip(request: HttpRequest) -> Optional[str]:
    """Extract client IP address from request."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def parse_date_filter(request: HttpRequest) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse date filter from request parameters."""
    date_from = None
    date_to = None
    
    date_range = request.GET.get('date_range', 'all')
    
    if date_range == 'today':
        date_from = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        date_to = timezone.now()
    elif date_range == '7d':
        date_from = timezone.now() - timedelta(days=7)
        date_to = timezone.now()
    elif date_range == '30d':
        date_from = timezone.now() - timedelta(days=30)
        date_to = timezone.now()
    elif date_range == '3m':
        date_from = timezone.now() - timedelta(days=90)
        date_to = timezone.now()
    elif date_range == '6m':
        date_from = timezone.now() - timedelta(days=180)
        date_to = timezone.now()
    elif date_range == '1y':
        date_from = timezone.now() - timedelta(days=365)
        date_to = timezone.now()
    elif date_range == 'custom':
        from_str = request.GET.get('date_from')
        to_str = request.GET.get('date_to')
        if from_str:
            try:
                date_from = datetime.fromisoformat(from_str)
            except ValueError:
                pass
        if to_str:
            try:
                date_to = datetime.fromisoformat(to_str)
            except ValueError:
                pass
    
    return date_from, date_to


# ==================== Authentication Views ====================

@csrf_exempt
@require_http_methods(["GET"])
def portal_auth(request: HttpRequest, token: str) -> HttpResponse:
    """
    Authenticate user with token and create session.
    
    URL: /portal/auth/<token>/
    """
    # Validate token
    profile = PortalTokenService.validate_token(token)
    
    if not profile:
        return render(request, 'portal/error.html', {
            'error_title': 'دسترسی غیرمجاز',
            'error_message': 'لینک دسترسی نامعتبر یا منقضی شده است. لطفاً از ربات تلگرام لینک جدید دریافت کنید.',
        })
    
    # Mark token as used (optional, comment out for reusable tokens)
    # ip_address = get_client_ip(request)
    # user_agent = request.META.get('HTTP_USER_AGENT', '')
    # PortalTokenService.mark_token_used(token, ip_address, user_agent)
    
    # Create session
    request.session['profile_id'] = profile.id
    request.session['authenticated_at'] = timezone.now().isoformat()
    request.session.set_expiry(3600)  # 1 hour
    
    logger.info(f"User authenticated via portal: {profile.get_display_name()}")
    
    # Redirect to dashboard
    return redirect('trading:portal_dashboard')


def require_portal_auth(view_func):
    """Decorator to require portal authentication."""
    def wrapper(request: HttpRequest, *args, **kwargs):
        profile_id = request.session.get('profile_id')
        
        if not profile_id:
            return render(request, 'portal/error.html', {
                'error_title': 'احراز هویت لازم است',
                'error_message': 'لطفاً از ربات تلگرام وارد شوید.',
            })
        
        try:
            profile = Profile.objects.select_related('user').get(id=profile_id)
            request.profile = profile
        except Profile.DoesNotExist:
            return render(request, 'portal/error.html', {
                'error_title': 'خطا',
                'error_message': 'کاربر یافت نشد.',
            })
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


@require_http_methods(["GET"])
@require_portal_auth
def portal_logout(request: HttpRequest) -> HttpResponse:
    """
    Logout and clear session.
    
    URL: /portal/logout/
    """
    request.session.flush()
    return render(request, 'portal/logged_out.html', {
        'message': 'شما با موفقیت خارج شدید.',
    })


# ==================== Dashboard View ====================

@require_http_methods(["GET"])
@require_portal_auth
def portal_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Main dashboard view.
    
    URL: /portal/dashboard/
    """
    profile = request.profile
    
    # Get dashboard data
    data = PortalDataService.get_dashboard_data(profile)
    
    context = {
        'profile': profile,
        'total_portfolio_value': data['total_portfolio_value'],
        'rial_balance': data['rial_balance'],
        'portfolio_items': data['portfolio_items'],
        'recent_orders': data['recent_orders'],
        'today_pl': data['today_pl'],
        'total_orders': data['total_orders'],
        'total_invested': data['total_invested'],
        'net_pl': data['net_pl'],
        'roi_percentage': data['roi_percentage'],
        'page_title': 'داشبورد',
    }
    
    return render(request, 'portal/dashboard.html', context)


# ==================== Transactions View ====================

@require_http_methods(["GET"])
@require_portal_auth
def portal_transactions(request: HttpRequest) -> HttpResponse:
    """
    Transactions list view with filtering.
    
    URL: /portal/transactions/
    """
    profile = request.profile
    
    # Get filters from request
    product_id = request.GET.get('product_id')
    transaction_type = request.GET.get('transaction_type')
    date_from, date_to = parse_date_filter(request)
    page = int(request.GET.get('page', 1))
    
    # Get filtered data
    data = PortalDataService.get_transactions_data(
        profile=profile,
        product_id=int(product_id) if product_id else None,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=20
    )
    
    # Get all products for filter dropdown
    products = Product.objects.filter(is_active=True).order_by('name')
    
    context = {
        'profile': profile,
        'orders': data['orders'],
        'total_count': data['total_count'],
        'page': data['page'],
        'total_pages': data['total_pages'],
        'has_next': data['has_next'],
        'has_prev': data['has_prev'],
        'products': products,
        'selected_product_id': product_id,
        'selected_transaction_type': transaction_type,
        'selected_date_range': request.GET.get('date_range', 'all'),
        'page_title': 'تراکنش‌ها',
    }
    
    return render(request, 'portal/transactions.html', context)


# ==================== Profit/Loss View ====================

@require_http_methods(["GET"])
@require_portal_auth
def portal_profitloss(request: HttpRequest) -> HttpResponse:
    """
    Profit/Loss analysis view.
    
    URL: /portal/profitloss/
    """
    profile = request.profile
    
    # Get date filters
    date_from, date_to = parse_date_filter(request)
    
    # Calculate portfolio P/L
    pl_data = ProfitLossService.calculate_portfolio_pl(
        profile=profile,
        date_from=date_from,
        date_to=date_to
    )
    
    context = {
        'profile': profile,
        'products': pl_data['products'],
        'total_invested': pl_data['total_invested'],
        'total_received': pl_data['total_received'],
        'current_portfolio_value': pl_data['current_portfolio_value'],
        'realized_pl': pl_data['realized_pl'],
        'unrealized_pl': pl_data['unrealized_pl'],
        'total_pl': pl_data['total_pl'],
        'roi_percentage': pl_data['roi_percentage'],
        'best_product': pl_data['best_product'],
        'worst_product': pl_data['worst_product'],
        'selected_date_range': request.GET.get('date_range', 'all'),
        'page_title': 'سود و زیان',
    }
    
    return render(request, 'portal/profitloss.html', context)


# ==================== Statement View ====================

@require_http_methods(["GET"])
@require_portal_auth
def portal_statement(request: HttpRequest) -> HttpResponse:
    """
    Account statement view.
    
    URL: /portal/statement/
    """
    profile = request.profile
    
    # Get statement data
    data = PortalDataService.get_account_statement(profile)
    
    context = {
        'profile': profile,
        'rial_balance': data['rial_balance'],
        'product_balances': data['product_balances'],
        'deposits': data['deposits'],
        'withdrawals': data['withdrawals'],
        'net_cash_flow': data['net_cash_flow'],
        'is_creditor': data['is_creditor'],
        'pending_deposits': data['pending_deposits'],
        'pending_withdrawals': data['pending_withdrawals'],
        'total_transactions': data['total_transactions'],
        'total_buy_orders': data['total_buy_orders'],
        'total_sell_orders': data['total_sell_orders'],
        'most_traded_product': data['most_traded_product'],
        'first_transaction_date': data['first_transaction_date'],
        'last_transaction_date': data['last_transaction_date'],
        'updated_at': data['updated_at'],
        'page_title': 'صورتحساب',
    }
    
    return render(request, 'portal/statement.html', context)


# ==================== Export Views ====================

@require_http_methods(["GET"])
@require_portal_auth
def export_transactions_csv(request: HttpRequest) -> HttpResponse:
    """
    Export transactions to CSV.
    
    URL: /portal/export/transactions/csv/
    """
    profile = request.profile
    
    # Get filters
    product_id = request.GET.get('product_id')
    transaction_type = request.GET.get('transaction_type')
    date_from, date_to = parse_date_filter(request)
    
    # Get data (no pagination for export)
    data = PortalDataService.get_transactions_data(
        profile=profile,
        product_id=int(product_id) if product_id else None,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        page=1,
        per_page=10000  # High limit for export
    )
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header with BOM for Persian characters
    output.write('\ufeff')
    
    # Headers
    writer.writerow([
        'شماره سفارش',
        'تاریخ',
        'نوع',
        'محصول',
        'مقدار',
        'قیمت واحد',
        'مبلغ کل',
        'وضعیت'
    ])
    
    # Write data
    for order in data['orders']:
        writer.writerow([
            order.id,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.get_order_type_display(),
            order.product.name,
            float(order.quantity_grams),
            float(order.price_per_gram),
            float(order.total_amount),
            order.get_status_display()
        ])
    
    # Create response
    response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
    filename = f'transactions_{profile.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    logger.info(f"CSV export generated for {profile.get_display_name()}: {data['total_count']} records")
    
    return response


@require_http_methods(["GET"])
@require_portal_auth
def export_transactions_pdf(request: HttpRequest) -> HttpResponse:
    """
    Export transactions to PDF.
    
    URL: /portal/export/transactions/pdf/
    """
    from django.template.loader import render_to_string
    from weasyprint import HTML
    
    profile = request.profile
    
    # Get filters
    product_id = request.GET.get('product_id')
    transaction_type = request.GET.get('transaction_type')
    date_from, date_to = parse_date_filter(request)
    
    # Get data
    data = PortalDataService.get_transactions_data(
        profile=profile,
        product_id=int(product_id) if product_id else None,
        transaction_type=transaction_type,
        date_from=date_from,
        date_to=date_to,
        page=1,
        per_page=1000  # Limit for PDF
    )
    
    # Render HTML template
    html_content = render_to_string('portal/exports/transactions_pdf.html', {
        'profile': profile,
        'orders': data['orders'],
        'total_count': data['total_count'],
        'date_from': date_from,
        'date_to': date_to,
        'generated_at': timezone.now(),
    })
    
    # Generate PDF
    pdf_file = HTML(string=html_content).write_pdf()
    
    # Create response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'transactions_{profile.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    logger.info(f"PDF export generated for {profile.get_display_name()}: {data['total_count']} records")
    
    return response


@require_http_methods(["GET"])
@require_portal_auth
def export_statement_pdf(request: HttpRequest) -> HttpResponse:
    """
    Export account statement to PDF.
    
    URL: /portal/export/statement/pdf/
    """
    from django.template.loader import render_to_string
    from weasyprint import HTML
    
    profile = request.profile
    
    # Get statement data
    data = PortalDataService.get_account_statement(profile)
    
    # Render HTML template
    html_content = render_to_string('portal/exports/statement_pdf.html', {
        'profile': profile,
        'rial_balance': data['rial_balance'],
        'product_balances': data['product_balances'],
        'deposits': data['deposits'],
        'withdrawals': data['withdrawals'],
        'net_cash_flow': data['net_cash_flow'],
        'is_creditor': data['is_creditor'],
        'total_transactions': data['total_transactions'],
        'total_buy_orders': data['total_buy_orders'],
        'total_sell_orders': data['total_sell_orders'],
        'generated_at': timezone.now(),
    })
    
    # Generate PDF
    pdf_file = HTML(string=html_content).write_pdf()
    
    # Create response
    response = HttpResponse(pdf_file, content_type='application/pdf')
    filename = f'statement_{profile.id}_{timezone.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    logger.info(f"Statement PDF export generated for {profile.get_display_name()}")
    
    return response


# ==================== API Endpoints (for AJAX requests) ====================

@require_http_methods(["GET"])
@require_portal_auth
def api_refresh_prices(request: HttpRequest) -> JsonResponse:
    """
    API endpoint to get latest prices.
    
    URL: /portal/api/prices/
    """
    products = Product.objects.filter(is_active=True)
    
    prices_data = []
    for product in products:
        prices_data.append({
            'id': product.id,
            'name': product.name,
            'buy_price': float(product.buy_price),
            'sell_price': float(product.sell_price),
            'updated_at': product.updated_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'prices': prices_data,
        'updated_at': timezone.now().isoformat(),
    })


# ==================== Invoice and Receipt Views ====================

@require_http_methods(["GET"])
@require_portal_auth
def portal_order_invoice(request: HttpRequest, order_id: int) -> HttpResponse:
    """
    Download invoice PDF for a specific order.
    
    URL: /portal/order/<order_id>/invoice/
    """
    profile = request.profile
    
    try:
        order = Order.objects.select_related('product', 'profile').get(
            id=order_id,
            profile=profile,
            status=Order.OrderStatus.COMPLETED
        )
    except Order.DoesNotExist:
        return render(request, 'portal/error.html', {
            'error_title': 'فاکتور یافت نشد',
            'error_message': 'سفارش مورد نظر یافت نشد یا تکمیل نشده است.',
        })
    
    # Generate invoice
    from .invoice_generator import InvoiceGenerator
    pdf_buffer = InvoiceGenerator.generate_order_invoice(order)
    filename = InvoiceGenerator.get_invoice_filename(order)
    
    # Log invoice download
    logger.info(f"Invoice downloaded by {profile.get_display_name()}: Order #{order.id}")
    
    # Return PDF response
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@require_http_methods(["GET"])
@require_portal_auth
def portal_receipt_view(request: HttpRequest, transaction_id: int) -> HttpResponse:
    """
    View receipt image for a specific transaction.
    
    URL: /portal/transaction/<transaction_id>/receipt/
    """
    profile = request.profile
    
    try:
        from .models import Transaction
        transaction = Transaction.objects.get(
            id=transaction_id,
            profile=profile
        )
    except Transaction.DoesNotExist:
        return render(request, 'portal/error.html', {
            'error_title': 'رسید یافت نشد',
            'error_message': 'تراکنش مورد نظر یافت نشد.',
        })
    
    if not transaction.receipt_image:
        return render(request, 'portal/error.html', {
            'error_title': 'رسید موجود نیست',
            'error_message': 'برای این تراکنش رسیدی آپلود نشده است.',
        })
    
    # Serve the image
    from django.http import FileResponse
    import os
    from django.conf import settings
    
    file_path = transaction.receipt_image.path
    if not os.path.exists(file_path):
        return render(request, 'portal/error.html', {
            'error_title': 'فایل یافت نشد',
            'error_message': 'فایل رسید در سرور یافت نشد.',
        })
    
    # Determine content type
    file_ext = os.path.splitext(file_path)[1].lower()
    content_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf',
    }
    content_type = content_types.get(file_ext, 'application/octet-stream')
    
    return FileResponse(
        open(file_path, 'rb'),
        content_type=content_type,
        filename=os.path.basename(file_path)
    )
