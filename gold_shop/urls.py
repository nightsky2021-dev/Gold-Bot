"""
URL configuration for gold_shop project.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from trading.admin_views import admin_dashboard

urlpatterns = [
    path('', include('trading.urls')),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda request: HttpResponse(status=204)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Customize admin site headers
admin.site.site_header = "سامانه معاملات طلای آنلاین"
admin.site.site_title = "پنل مدیریت"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

