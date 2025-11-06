"""
Reporting Views for Trading System.

Provides API endpoints for generating and downloading reports.
These endpoints are used by the Telegram bot for user-facing reports.
"""

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal

from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.exceptions import PermissionDenied
import json

from users.models import Profile
from .models import Product
from .reporting import (
    TransactionReportService,
    CSVExportService,
    PDFExportService,
    BusinessReportService
)


def _get_profile_from_request(request) -> Optional[Profile]:
    """
    Extract profile from request.
    
    For bot requests, expects 'telegram_id' in POST/GET data.
    For authenticated requests, uses request.user.
    """
    telegram_id = request.POST.get('telegram_id') or request.GET.get('telegram_id')
    
    if telegram_id:
        try:
            return Profile.objects.get(telegram_id=telegram_id)
        except Profile.DoesNotExist:
            return None
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            return request.user.profile
        except Profile.DoesNotExist:
            return None
    
    return None


def _parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime object."""
    if not date_string:
        return None
    
    try:
        return datetime.strptime(date_string, '%Y-%m-%d')
    except ValueError:
        return None


def _get_date_range_from_preset(preset: str) -> tuple[Optional[datetime], Optional[datetime]]:
    """
    Get date range from preset string.
    
    Presets: 'last_7_days', 'last_30_days', 'this_month', 'last_month'
    """
    now = timezone.now()
    
    if preset == 'last_7_days':
        start_date = now - timedelta(days=7)
        return start_date, now
    
    elif preset == 'last_30_days':
        start_date = now - timedelta(days=30)
        return start_date, now
    
    elif preset == 'this_month':
        start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return start_date, now
    
    elif preset == 'last_month':
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = first_of_this_month - timedelta(days=1)
        start_date = last_month.replace(day=1)
        end_date = first_of_this_month - timedelta(seconds=1)
        return start_date, end_date
    
    return None, None


@csrf_exempt
@require_http_methods(["GET", "POST"])
def transaction_history_api(request):
    """
    API endpoint for fetching transaction history with filters.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range (last_7_days, last_30_days, this_month, last_month)
        - transaction_type: Filter by type (DEPOSIT, WITHDRAW, BUY, SELL)
        - status: Filter by status
        - limit: Number of records to return (default 50)
    
    Returns:
        JSON with transaction list and summary
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    transaction_type = request.POST.get('transaction_type') or request.GET.get('transaction_type')
    status = request.POST.get('status') or request.GET.get('status')
    limit = int(request.POST.get('limit') or request.GET.get('limit', 50))
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    # Get transactions
    transactions = TransactionReportService.filter_transactions(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        status=status
    )[:limit]
    
    # Get summary
    summary = TransactionReportService.get_summary_statistics(
        profile=profile,
        start_date=start_date,
        end_date=end_date
    )
    
    # Format transactions
    transaction_list = [
        {
            'id': txn.id,
            'date': txn.created_at.isoformat(),
            'type': txn.transaction_type,
            'type_display': txn.get_transaction_type_display(),
            'currency': txn.currency,
            'currency_display': txn.get_currency_display(),
            'amount': float(txn.amount),
            'status': txn.status,
            'status_display': txn.get_status_display(),
            'description': txn.description or ''
        }
        for txn in transactions
    ]
    
    return JsonResponse({
        'success': True,
        'transactions': transaction_list,
        'summary': summary,
        'filters': {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'transaction_type': transaction_type,
            'status': status
        }
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def order_history_api(request):
    """
    API endpoint for fetching order history with filters.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range (last_7_days, last_30_days, this_month, last_month)
        - order_type: Filter by type (BUY, SELL)
        - product_code: Filter by product code
        - status: Filter by status
        - limit: Number of records to return (default 50)
    
    Returns:
        JSON with order list and summary
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    order_type = request.POST.get('order_type') or request.GET.get('order_type')
    product_code = request.POST.get('product_code') or request.GET.get('product_code')
    status = request.POST.get('status') or request.GET.get('status')
    limit = int(request.POST.get('limit') or request.GET.get('limit', 50))
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    # Get product filter
    product = None
    if product_code:
        try:
            product = Product.objects.get(product_code=product_code)
        except Product.DoesNotExist:
            pass
    
    # Get orders
    orders = TransactionReportService.filter_orders(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        order_type=order_type,
        product=product,
        status=status
    )[:limit]
    
    # Get summary
    summary = TransactionReportService.get_summary_statistics(
        profile=profile,
        start_date=start_date,
        end_date=end_date
    )
    
    # Format orders
    order_list = [
        {
            'id': order.id,
            'date': order.created_at.isoformat(),
            'product': order.product.name,
            'product_code': order.product.product_code,
            'type': order.order_type,
            'type_display': order.get_order_type_display(),
            'quantity_grams': float(order.quantity_grams),
            'price_per_gram': float(order.price_per_gram),
            'total_amount': float(order.total_amount),
            'status': order.status,
            'status_display': order.get_status_display()
        }
        for order in orders
    ]
    
    return JsonResponse({
        'success': True,
        'orders': order_list,
        'summary': summary,
        'filters': {
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None,
            'order_type': order_type,
            'product_code': product_code,
            'status': status
        }
    })


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_transactions_csv(request):
    """
    Export user transactions to CSV.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range
        - transaction_type: Filter by type
    
    Returns:
        CSV file
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    transaction_type = request.POST.get('transaction_type') or request.GET.get('transaction_type')
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    return CSVExportService.export_transactions_csv(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_orders_csv(request):
    """
    Export user orders to CSV.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range
        - order_type: Filter by type
        - product_code: Filter by product
    
    Returns:
        CSV file
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    order_type = request.POST.get('order_type') or request.GET.get('order_type')
    product_code = request.POST.get('product_code') or request.GET.get('product_code')
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    # Get product filter
    product = None
    if product_code:
        try:
            product = Product.objects.get(product_code=product_code)
        except Product.DoesNotExist:
            pass
    
    return CSVExportService.export_orders_csv(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        order_type=order_type,
        product=product
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_transactions_pdf(request):
    """
    Export user transactions to PDF.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range
        - transaction_type: Filter by type
    
    Returns:
        PDF file
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    transaction_type = request.POST.get('transaction_type') or request.GET.get('transaction_type')
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    pdf_buffer = PDFExportService.export_transactions_pdf(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type
    )
    
    if not pdf_buffer:
        return JsonResponse({'error': 'PDF library not available'}, status=500)
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transactions_{profile.telegram_id}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    return response


@csrf_exempt
@require_http_methods(["GET", "POST"])
def export_orders_pdf(request):
    """
    Export user orders to PDF.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range
        - order_type: Filter by type
    
    Returns:
        PDF file
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    order_type = request.POST.get('order_type') or request.GET.get('order_type')
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    pdf_buffer = PDFExportService.export_orders_pdf(
        profile=profile,
        start_date=start_date,
        end_date=end_date,
        order_type=order_type
    )
    
    if not pdf_buffer:
        return JsonResponse({'error': 'PDF library not available'}, status=500)
    
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="orders_{profile.telegram_id}_{timezone.now().strftime("%Y%m%d")}.pdf"'
    return response


@csrf_exempt
@require_http_methods(["GET", "POST"])
def user_summary_api(request):
    """
    Get user trading summary for a given period.
    
    Parameters:
        - telegram_id: User's Telegram ID
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
        - date_preset: Preset range
    
    Returns:
        JSON with summary statistics
    """
    profile = _get_profile_from_request(request)
    if not profile:
        return JsonResponse({'error': 'Profile not found'}, status=404)
    
    # Get filters
    date_preset = request.POST.get('date_preset') or request.GET.get('date_preset')
    start_date_str = request.POST.get('start_date') or request.GET.get('start_date')
    end_date_str = request.POST.get('end_date') or request.GET.get('end_date')
    
    # Parse dates
    if date_preset:
        start_date, end_date = _get_date_range_from_preset(date_preset)
    else:
        start_date = _parse_date(start_date_str)
        end_date = _parse_date(end_date_str)
    
    summary = TransactionReportService.get_summary_statistics(
        profile=profile,
        start_date=start_date,
        end_date=end_date
    )
    
    return JsonResponse({
        'success': True,
        'summary': summary
    })

