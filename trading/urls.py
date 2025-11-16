from django.urls import path
from . import views, views_reporting, portal_views

app_name = 'trading'

urlpatterns = [
    path('', views.home, name='home'),
    path('api/status/', views.api_status, name='api_status'),
    
    # Admin invoice endpoint
    path('admin/order/<int:order_id>/invoice/', views.admin_order_invoice, name='admin_order_invoice'),
    
    # Reporting endpoints
    path('api/reports/transactions/', views_reporting.transaction_history_api, name='transaction_history_api'),
    path('api/reports/orders/', views_reporting.order_history_api, name='order_history_api'),
    path('api/reports/summary/', views_reporting.user_summary_api, name='user_summary_api'),
    
    # Export endpoints
    path('api/export/transactions/csv/', views_reporting.export_transactions_csv, name='export_transactions_csv'),
    path('api/export/transactions/pdf/', views_reporting.export_transactions_pdf, name='export_transactions_pdf'),
    path('api/export/orders/csv/', views_reporting.export_orders_csv, name='export_orders_csv'),
    path('api/export/orders/pdf/', views_reporting.export_orders_pdf, name='export_orders_pdf'),
    
    # User Transaction Portal
    path('portal/auth/<str:token>/', portal_views.portal_auth, name='portal_auth'),
    path('portal/logout/', portal_views.portal_logout, name='portal_logout'),
    path('portal/dashboard/', portal_views.portal_dashboard, name='portal_dashboard'),
    path('portal/transactions/', portal_views.portal_transactions, name='portal_transactions'),
    path('portal/profitloss/', portal_views.portal_profitloss, name='portal_profitloss'),
    path('portal/statement/', portal_views.portal_statement, name='portal_statement'),
    
    # Portal export endpoints
    path('portal/export/transactions/csv/', portal_views.export_transactions_csv, name='portal_export_transactions_csv'),
    path('portal/export/transactions/pdf/', portal_views.export_transactions_pdf, name='portal_export_transactions_pdf'),
    path('portal/export/statement/pdf/', portal_views.export_statement_pdf, name='portal_export_statement_pdf'),
    
    # Portal API endpoints
    path('portal/api/prices/', portal_views.api_refresh_prices, name='portal_api_prices'),
    
    # Invoice and Receipt endpoints
    path('portal/order/<int:order_id>/invoice/', portal_views.portal_order_invoice, name='portal_order_invoice'),
    path('portal/transaction/<int:transaction_id>/receipt/', portal_views.portal_receipt_view, name='portal_receipt_view'),
]
