from django.shortcuts import render
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home(request):
    """
    Renders the platform landing page to verify that Django,
    the template engine, and static assets are working properly.
    """
    context = {
        'project_name': 'AI-Powered Food Waste Management Platform',
        'tagline': 'Surplus Identification & Redistribution Optimization',
        'status': 'Foundation Ready',
        'debug_mode': settings.DEBUG,
        'db_engine': settings.DATABASES['default']['ENGINE'].split('.')[-1],
        'modules': [
            {
                'name': 'Core Foundation & Configuration',
                'status': 'Completed',
                'description': 'Django 5, DRF, PostgreSQL configuration, templates, and static assets structure.'
            },
            {
                'name': 'User Authentication & Roles',
                'status': 'Upcoming',
                'description': 'Role-based access for Restaurants/Businesses, NGOs, and Admins.'
            },
            {
                'name': 'Food Inventory & Surplus Tracking',
                'status': 'Upcoming',
                'description': 'Expiry date tracking, surplus batch registration, and threshold alerts.'
            },
            {
                'name': 'NGO Matching & Donation Coordination',
                'status': 'Upcoming',
                'description': 'Surplus broadcast, NGO claim workflows, pickup scheduling, and verification.'
            },
            {
                'name': 'AI-Powered Waste Prediction',
                'status': 'Upcoming',
                'description': 'Machine learning models for surplus forecasting and demand estimation.'
            },
        ]
    }
    return render(request, 'core/home.html', context)


@api_view(['GET'])
def health_check(request):
    """
    Lightweight health check API endpoint verifying DRF functionality.
    """
    return Response({
        'status': 'healthy',
        'platform': 'AI-Powered Food Waste Management Platform',
        'version': '1.0.0',
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'rest_framework': 'active',
    })
