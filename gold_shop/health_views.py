"""
Health check and monitoring views for Gold Shop application.

These endpoints can be used by monitoring tools, load balancers,
and orchestration platforms to check application health.
"""

import logging
from typing import Dict, Any

from django.http import JsonResponse
from django.db import connection
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET", "HEAD"])
def health_check(request) -> JsonResponse:
    """
    Basic health check endpoint.
    
    Returns 200 if application is running.
    Used for basic liveness probes.
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'gold_shop',
    })


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request) -> JsonResponse:
    """
    Readiness check endpoint.
    
    Checks if application is ready to serve requests.
    Tests database connectivity and other critical services.
    """
    checks = {}
    overall_status = 'ready'
    status_code = 200
    
    # Check database connectivity
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        checks['database'] = 'connected'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        overall_status = 'not_ready'
        status_code = 503
        logger.error(f"Database health check failed: {str(e)}")
    
    # Check if bot token is configured
    if settings.TELEGRAM_BOT_TOKEN:
        checks['telegram_bot_token'] = 'configured'
    else:
        checks['telegram_bot_token'] = 'not_configured'
        if overall_status == 'ready':
            overall_status = 'degraded'
    
    return JsonResponse({
        'status': overall_status,
        'checks': checks,
    }, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def metrics(request) -> JsonResponse:
    """
    Application metrics endpoint.
    
    Returns basic application metrics.
    Can be extended to include more detailed metrics.
    """
    from users.models import Profile
    from trading.models import Product, Order
    
    try:
        metrics_data: Dict[str, Any] = {
            'users': {
                'total': Profile.objects.count(),
                'approved': Profile.objects.filter(is_approved=True).count(),
                'pending': Profile.objects.filter(is_approved=False).count(),
            },
            'products': {
                'total': Product.objects.count(),
                'active': Product.objects.filter(is_active=True).count(),
            },
            'orders': {
                'total': Order.objects.count(),
                'pending': Order.objects.filter(status='PENDING').count(),
                'completed': Order.objects.filter(status='COMPLETED').count(),
                'cancelled': Order.objects.filter(status='CANCELLED').count(),
            },
        }
        
        return JsonResponse({
            'status': 'success',
            'metrics': metrics_data,
        })
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'error': 'Failed to collect metrics',
        }, status=500)
