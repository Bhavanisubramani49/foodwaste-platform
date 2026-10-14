from django.shortcuts import render
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response


def home(request):
    """
    Public Landing Page for FoodWasteAI.
    """
    context = {
        'brand_name': 'FoodWasteAI',
        'headline': 'Turn Surplus Food into Community Impact.',
        'subheadline': 'Intelligent inventory tracking, explainable AI waste prediction, and automated surplus redistribution connecting businesses with verified NGOs in real time.',
        'features': [
            {
                'title': 'Real-Time Inventory Tracking',
                'desc': 'Track batch lifecycles, shelf-life, and storage temperatures to catch near-expiry items early.',
                'icon': 'bi-box-seam',
                'badge': 'Core Engine'
            },
            {
                'title': 'AI Waste Prediction',
                'desc': 'Forecast surplus probabilities and quantify risk before food spoils using machine learning models.',
                'icon': 'bi-cpu',
                'badge': 'AI-Powered'
            },
            {
                'title': 'Surplus Marketplace',
                'desc': 'Broadcast non-expired excess batches instantly to pre-verified NGOs and community kitchens.',
                'icon': 'bi-shop',
                'badge': 'Smart Matching'
            },
            {
                'title': 'Impact & ESG Analytics',
                'desc': 'Track kilograms saved, meals provided, and estimated CO2 emission reductions with live analytics.',
                'icon': 'bi-graph-up-arrow',
                'badge': 'Analytics'
            },
        ],
        'steps': [
            {'num': '01', 'title': 'Track Inventory', 'desc': 'Log product batches, quantities, purchase dates, and expiry windows.'},
            {'num': '02', 'title': 'Identify Surplus', 'desc': 'AI flags items at risk of spoiling and recommends immediate donation quantity.'},
            {'num': '03', 'title': 'Redistribute Food', 'desc': 'Matched NGOs claim surplus, schedule prompt pickup, and verify meal handoff.'},
        ],
        'metrics': {
            'businesses_registered': 42,
            'ngos_partnered': 28,
            'kg_redistributed': 14850,
            'meals_supported': 37125,
            'co2_saved_kg': 26730
        }
    }
    return render(request, 'core/home.html', context)


def dashboard(request):
    """
    Business User Dashboard providing comprehensive KPI cards,
    interactive Chart.js visualisations, and recent activity monitoring.
    """
    # Baseline demonstration and operational dataset
    stats = {
        'total_items': 84,
        'total_stock_kg': 1420,
        'expiring_soon': 18,
        'high_risk_items': 7,
        'surplus_available_kg': 340,
        'pending_requests': 4,
        'completed_donations': 29,
        'waste_avoided_kg': 1150,
        'meals_provided': 2875,
    }

    recent_activities = [
        {
            'product': 'Fresh Artisanal Sourdough Bread',
            'category': 'Bakery',
            'quantity': '24 loaves',
            'expiry': 'Tomorrow (Oct 15)',
            'risk_level': 'Critical',
            'risk_badge': 'badge-risk-critical',
            'surplus_status': 'Listed in Marketplace',
            'donation_status': 'Pending NGO Claim',
            'action_label': 'Manage Claim'
        },
        {
            'product': 'Organic Greek Yogurt 500g',
            'category': 'Dairy',
            'quantity': '40 tubs',
            'expiry': 'In 2 days (Oct 16)',
            'risk_level': 'High',
            'risk_badge': 'badge-risk-high',
            'surplus_status': 'Listed in Marketplace',
            'donation_status': 'Claimed by City Shelter',
            'action_label': 'Schedule Pickup'
        },
        {
            'product': 'Farm Fresh Spinach & Greens',
            'category': 'Produce',
            'quantity': '15 kg',
            'expiry': 'In 3 days (Oct 17)',
            'risk_level': 'High',
            'risk_badge': 'badge-risk-high',
            'surplus_status': 'Eligible for Surplus',
            'donation_status': 'Unlisted',
            'action_label': 'List Surplus'
        },
        {
            'product': 'Cooked Rice & Vegetable Curry',
            'category': 'Prepared Meals',
            'quantity': '50 portions',
            'expiry': 'Today (Oct 14)',
            'risk_level': 'Critical',
            'risk_badge': 'badge-risk-critical',
            'surplus_status': 'Claimed',
            'donation_status': 'Scheduled (7:30 PM)',
            'action_label': 'View Transit'
        },
        {
            'product': 'Pasteurised Whole Milk 1L',
            'category': 'Dairy',
            'quantity': '35 bottles',
            'expiry': 'In 5 days (Oct 19)',
            'risk_level': 'Medium',
            'risk_badge': 'badge-risk-medium',
            'surplus_status': 'In Monitoring',
            'donation_status': 'Not Needed',
            'action_label': 'Monitor'
        },
        {
            'product': 'Organic Rolled Oats 1kg',
            'category': 'Dry Goods',
            'quantity': '120 packets',
            'expiry': 'In 45 days (Nov 28)',
            'risk_level': 'Low',
            'risk_badge': 'badge-risk-low',
            'surplus_status': 'Healthy Stock',
            'donation_status': 'Not Applicable',
            'action_label': 'View Stock'
        },
    ]

    context = {
        'stats': stats,
        'recent_activities': recent_activities,
        # Chart data payload for Chart.js
        'chart_categories_labels': ['Bakery', 'Dairy', 'Produce', 'Prepared Meals', 'Meat & Poultry', 'Dry Goods'],
        'chart_categories_data': [220, 310, 280, 190, 90, 330],
        'chart_expiry_labels': ['Today', 'Tomorrow', '+2 Days', '+3 Days', '+4 Days', '+5 Days', '+6 Days', '+7 Days'],
        'chart_expiry_data': [8, 14, 12, 9, 6, 4, 3, 2],
        'chart_risk_labels': ['Low Risk', 'Medium Risk', 'High Risk', 'Critical Risk'],
        'chart_risk_data': [45, 14, 7, 18],
        'chart_donations_labels': ['May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct'],
        'chart_donations_data': [140, 210, 180, 290, 320, 340],
    }
    return render(request, 'core/dashboard.html', context)


def inventory_list(request):
    """Placeholder view for Inventory Management module (Milestone 1)."""
    return render(request, 'core/inventory_list.html', {'title': 'Inventory Management'})


def expiry_alerts(request):
    """Placeholder view for Expiry Alerts & Monitoring module."""
    return render(request, 'core/expiry_alerts.html', {'title': 'Expiry Alerts & Thresholds'})


def waste_prediction(request):
    """Placeholder view for AI Waste Prediction Engine (Milestone 2)."""
    return render(request, 'core/waste_prediction.html', {'title': 'AI Waste-Risk Prediction'})


def marketplace(request):
    """Placeholder view for Surplus Food Marketplace (Milestone 3)."""
    return render(request, 'core/marketplace.html', {'title': 'Surplus Food Marketplace'})


def ngo_requirements(request):
    """Placeholder view for NGO Food Requirements module."""
    return render(request, 'core/ngo_requirements.html', {'title': 'NGO Food Requirements'})


def donation_requests(request):
    """Placeholder view for Donation Requests & Lifecycle."""
    return render(request, 'core/donation_requests.html', {'title': 'Donation Requests & Allocations'})


def pickup_schedule(request):
    """Placeholder view for Pickup Scheduling & Transit."""
    return render(request, 'core/pickup_schedule.html', {'title': 'Pickup Schedule & Logistics'})


def impact_analytics(request):
    """Placeholder view for Community Impact & ESG Analytics."""
    return render(request, 'core/impact_analytics.html', {'title': 'Community Impact & Sustainability Analytics'})


def leaderboard(request):
    """Placeholder view for Donor & NGO Leaderboard."""
    return render(request, 'core/leaderboard.html', {'title': 'Community Impact Leaderboard'})


def notifications(request):
    """Placeholder view for User Notifications Center."""
    return render(request, 'core/notifications.html', {'title': 'Notifications'})


def profile(request):
    """Placeholder view for Profile & Organization Settings."""
    return render(request, 'core/profile.html', {'title': 'Profile & Organization Settings'})


@api_view(['GET'])
def health_check(request):
    """
    Lightweight health check API endpoint verifying DRF functionality and DB connectivity.
    """
    from django.db import connection
    db_status = 'connected'
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1;')
    except Exception as e:
        db_status = f'disconnected: {str(e)}'

    return Response({
        'status': 'healthy',
        'platform': 'FoodWasteAI',
        'version': '2.0.0',
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'database_status': db_status,
        'rest_framework': 'active',
        'theme': 'Orange + Sky Blue',
    })
