"""
URL configuration for gold_shop project.
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path, include

urlpatterns = [
    path('', include('trading.urls')),
    path('admin/', admin.site.urls),
    path('favicon.ico', lambda request: HttpResponse(status=204)),
]

# Customize admin site headers
admin.site.site_header = "سامانه معاملات طلای آنلاین"
admin.site.site_title = "پنل مدیریت"
admin.site.index_title = "خوش آمدید به پنل مدیریت"

