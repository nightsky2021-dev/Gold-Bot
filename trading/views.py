from django.shortcuts import render
from django.http import HttpResponse
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

