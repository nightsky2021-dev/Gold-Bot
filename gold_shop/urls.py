"""
URL configuration for gold_shop project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
]

# Customize admin site
admin.site.site_header = "پنل مدیریت فروشگاه طلا"
admin.site.site_title = "مدیریت فروشگاه طلا"
admin.site.index_title = "خوش آمدید به پنل مدیریت"
