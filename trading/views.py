from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
import django

def home(request):
    """Home page view"""
    context = {
        'django_version': django.get_version()
    }
    return render(request, 'trading/home.html', context)

def api_status(request):
    """API status endpoint"""
    return HttpResponse("API is running", status=200)


@staff_member_required
def admin_order_invoice(request, order_id):
    """
    Admin-only invoice download endpoint.
    
    URL: /admin/order/<order_id>/invoice/
    """
    from .models import Order
    from .invoice_generator import InvoiceGenerator
    
    order = get_object_or_404(Order, id=order_id)
    
    # Only allow download for completed orders
    if order.status != Order.OrderStatus.COMPLETED:
        raise Http404("Invoice can only be generated for completed orders.")
    
    # Generate invoice
    pdf_buffer = InvoiceGenerator.generate_order_invoice(order)
    filename = InvoiceGenerator.get_invoice_filename(order)
    
    # Log invoice download
    import logging
    logger = logging.getLogger('trading.admin')
    logger.info(f"Invoice downloaded by admin {request.user.username}: Order #{order.id}")
    
    # Return PDF response
    response = HttpResponse(pdf_buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

