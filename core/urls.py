from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Primary Navigation
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('expiry-alerts/', views.expiry_alerts, name='expiry_alerts'),
    path('waste-prediction/', views.waste_prediction, name='waste_prediction'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('ngo-requirements/', views.ngo_requirements, name='ngo_requirements'),
    path('donation-requests/', views.donation_requests, name='donation_requests'),
    path('pickup-schedule/', views.pickup_schedule, name='pickup_schedule'),
    path('analytics/', views.impact_analytics, name='impact_analytics'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('notifications/', views.notifications, name='notifications'),
    path('profile/', views.profile, name='profile'),

    # APIs
    path('api/health/', views.health_check, name='health_check'),
]
