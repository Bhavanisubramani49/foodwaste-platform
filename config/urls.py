"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Wire root URL '/' to core application
    path('', include('core.urls')),
    # Wire dashboard and app modules to food_management
    path('app/', include('food_management.urls')),
]
