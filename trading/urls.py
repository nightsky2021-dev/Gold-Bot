from django.urls import path
from . import views, views_reporting

app_name = 'trading'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/status/', views.api_status, name='api_status'),
    
    # Reporting endpoints
    path('api/reports/transactions/', views_reporting.transaction_history_api, name='transaction_history_api'),
    path('api/reports/orders/', views_reporting.order_history_api, name='order_history_api'),
    path('api/reports/summary/', views_reporting.user_summary_api, name='user_summary_api'),
    
    # Export endpoints
    path('api/export/transactions/csv/', views_reporting.export_transactions_csv, name='export_transactions_csv'),
    path('api/export/transactions/pdf/', views_reporting.export_transactions_pdf, name='export_transactions_pdf'),
    path('api/export/orders/csv/', views_reporting.export_orders_csv, name='export_orders_csv'),
    path('api/export/orders/pdf/', views_reporting.export_orders_pdf, name='export_orders_pdf'),
]
