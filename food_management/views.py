import csv
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from io import StringIO
import json

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from core.models import UserProfile

from .access import get_or_create_user_profile, role_required
from .forms import (
    CSVImportForm,
    DonationRequestForm,
    InventoryForm,
    NGORequirementForm,
    SurplusListingForm,
    UserProfileForm,
    UserRegistrationForm,
)
from .matching import find_matches_for_listing, find_matches_for_ngo, score_match
from .ml_client import ml_client
from .models import DonationRequest, InventoryItem, NGORequirement, SurplusListing
from .services import (
    estimate_waste_risk,
    get_comprehensive_impact_analytics,
    get_gamification_summary,
    get_impact_summary,
    get_leaderboard,
)


def dashboard(request):
    """
    Primary Operations & AI Forecasting Dashboard.
    Routes NGOs directly to the NGO Command Center, and Businesses/Admins to the inventory & prediction engine.
    """
    if request.user.is_authenticated:
        profile = get_or_create_user_profile(request.user)
        if profile and profile.role == 'ngo':
            return ngo_dashboard(request)

    inventory = InventoryItem.objects.all().order_by('-created_at')
    recent_inventory = inventory[:5]
    total_inventory = inventory.count()
    near_expiry = inventory.filter(expiry_date__lte=date.today() + timedelta(days=7)).count()
    high_risk = inventory.filter(risk_level__in=['high', 'critical']).count()
    active_surplus = SurplusListing.objects.filter(status='available').count()
    donation_requests = DonationRequest.objects.count()
    collected_donations = DonationRequest.objects.filter(status='collected').count()
    recovered_quantity = DonationRequest.objects.filter(status='collected').aggregate(total=Sum('requested_quantity'))['total'] or 0
    prediction = estimate_waste_risk(inventory)
    gamification = get_gamification_summary(request.user)
    leaderboard = get_leaderboard(limit=5)

    # -------------------------------------------------------------
    # Milestone 2: AI Demand Forecasting & Spoilage Risk Integration
    # -------------------------------------------------------------
    supported_cats = {'dairy', 'bakery', 'produce', 'meat', 'packaged', 'beverages'}
    cat_counts = {}
    for item in inventory:
        cat_norm = (item.category or '').strip().lower()
        if cat_norm in supported_cats:
            cat_counts[cat_norm] = cat_counts.get(cat_norm, 0.0) + float(item.quantity or 0)

    dominant_category = max(cat_counts, key=cat_counts.get) if cat_counts else 'dairy'
    dominant_stock = cat_counts.get(dominant_category, 0.0)
    if dominant_stock <= 0:
        dominant_stock = sum(float(item.quantity or 0) for item in inventory) or 45.0

    # 1. Fetch AI Demand Forecast (FastAPI microservice or fallback)
    forecast_data = ml_client.predict_demand(category=dominant_category, horizon_days=7)
    if forecast_data and 'forecast' in forecast_data and len(forecast_data['forecast']) > 0:
        forecast_labels = []
        forecast_predicted = []
        forecast_lower = []
        forecast_upper = []
        for f in forecast_data['forecast']:
            try:
                dt = date.fromisoformat(f['date'])
                label = dt.strftime('%a (%d %b)')
            except Exception:
                label = str(f.get('date', ''))
            forecast_labels.append(label)
            forecast_predicted.append(round(float(f.get('predicted_demand', 0.0)), 1))
            forecast_lower.append(round(float(f.get('lower_bound', 0.0)), 1))
            forecast_upper.append(round(float(f.get('upper_bound', 0.0)), 1))
        is_live_model = True
        model_used = forecast_data.get('model_used', 'Prophet/LSTM')
    else:
        today = date.today()
        forecast_labels = [(today + timedelta(days=i)).strftime('%a (%d %b)') for i in range(1, 8)]
        base = max(15.0, round(dominant_stock * 0.25, 1))
        forecast_predicted = [round(base * (1.0 + 0.08 * (i % 4)), 1) for i in range(7)]
        forecast_lower = [round(val * 0.85, 1) for val in forecast_predicted]
        forecast_upper = [round(val * 1.15, 1) for val in forecast_predicted]
        is_live_model = False
        model_used = 'Fallback Heuristics'

    # 2. Real-time Inventory Spoilage Risk Calculation
    predicted_waste_kg = 0.0
    at_risk_names = []
    for item in inventory:
        risk_res = ml_client.calculate_inventory_risk(item)
        score = float(risk_res.get('risk_score', 0.0) or 0.0)
        surplus = float(risk_res.get('surplus_qty', 0.0) or 0.0)
        if score >= 60 or surplus > 0:
            qty = surplus if surplus > 0 else (float(item.quantity or 0) * 0.5)
            predicted_waste_kg += qty
            if item.name not in at_risk_names:
                at_risk_names.append(item.name)

    predicted_waste_kg = round(predicted_waste_kg, 1)
    if predicted_waste_kg == 0.0 and prediction.get('predicted_waste_kg', 0) > 0:
        predicted_waste_kg = prediction['predicted_waste_kg']

    if at_risk_names:
        sample_names = ', '.join(at_risk_names[:3])
        ai_mitigation_text = f'Fast-track {sample_names} (~{predicted_waste_kg} kg) to Surplus Marketplace or nearby NGOs before shelf-life expires.'
    elif total_inventory > 0:
        ai_mitigation_text = 'All inventory batches are within safe shelf-life thresholds. Regular monitoring recommended.'
    else:
        ai_mitigation_text = 'No active inventory recorded. Add stock items to activate real-time AI spoilage prediction.'

    # 3. Smart Replenishment Reorder Recommendation
    reorder_recommendation = ml_client.recommend_reorder(
        category=dominant_category,
        current_stock=dominant_stock,
        lead_time_days=2,
    )
    if not reorder_recommendation:
        reorder_recommendation = {
            'category': dominant_category,
            'recommended_order_qty': max(0.0, round(50.0 - dominant_stock, 1)) if dominant_stock < 50 else 0.0,
            'action': 'ORDER_RECOMMENDED' if dominant_stock < 50 else 'HOLD_NO_ORDER',
            'urgency': 'NORMAL' if dominant_stock < 50 else 'HOLD',
            'unit': 'kg',
            'reasoning': f'Current {dominant_category} stock ({dominant_stock:.1f} kg) evaluated via baseline replenishment rule.',
            'is_fallback': True,
        }

    context = {
        'total_inventory': total_inventory,
        'near_expiry': near_expiry,
        'high_risk': high_risk,
        'active_surplus': active_surplus,
        'donation_requests': donation_requests,
        'collected_donations': collected_donations,
        'recovered_quantity': recovered_quantity,
        'recent_inventory': recent_inventory,
        'prediction': prediction,
        'gamification': gamification,
        'leaderboard': leaderboard,
        'dominant_category': dominant_category,
        'predicted_waste_kg': predicted_waste_kg,
        'ai_mitigation_text': ai_mitigation_text,
        'is_live_model': is_live_model,
        'model_used': model_used,
        'reorder_recommendation': reorder_recommendation,
        'forecast_labels_json': json.dumps(forecast_labels),
        'forecast_predicted_json': json.dumps(forecast_predicted),
        'forecast_lower_json': json.dumps(forecast_lower),
        'forecast_upper_json': json.dumps(forecast_upper),
    }
    return render(request, 'food_management/dashboard.html', context)


@role_required('ngo', 'admin')
def ngo_dashboard(request):
    """
    Dedicated Command Center for NGOs, food banks, and relief kitchens.
    Displays matched surplus lots, active collection dispatches with PINs, and community requirements.
    """
    today = date.today()
    my_requests = DonationRequest.objects.filter(
        Q(ngo_user=request.user) | Q(ngo_name__iexact=getattr(getattr(request.user, 'profile', None), 'organization_name', '') or request.user.username)
    ).select_related('listing').order_by('-created_at')

    active_pickups = my_requests.filter(status__in=['requested', 'approved', 'scheduled'])
    completed_pickups = my_requests.filter(status='collected')
    total_received_kg = float(completed_pickups.aggregate(total=Sum('requested_quantity'))['total'] or 0.0)
    meals_served = int(round(total_received_kg * 2.22))
    gamification = get_gamification_summary(request.user)

    my_requirements = NGORequirement.objects.filter(
        Q(ngo_user=request.user) | Q(ngo_name__iexact=getattr(getattr(request.user, 'profile', None), 'organization_name', '') or request.user.username)
    ).order_by('-created_at')

    smart_matches = []
    seen_listings = set()
    for req in my_requirements.filter(status__in=['open', 'partially_fulfilled']):
        matches = find_matches_for_ngo(req, min_score=40)
        for m in matches:
            if m['listing'].pk not in seen_listings:
                seen_listings.add(m['listing'].pk)
                smart_matches.append(m)
                if len(smart_matches) >= 6:
                    break
        if len(smart_matches) >= 6:
            break

    if not smart_matches:
        fallback_listings = SurplusListing.objects.filter(
            status='available',
            expiry_date__gte=today,
        ).order_by('expiry_date')[:6]
        for l in fallback_listings:
            if l.remaining_quantity > 0:
                smart_matches.append({
                    'listing': l,
                    'score': 75,
                    'tier': 'Available Lot',
                    'reasons': [f"Available in marketplace ({l.remaining_quantity} {l.unit})"],
                    'available_qty': l.remaining_quantity,
                })

    context = {
        'active_pickups': active_pickups,
        'completed_pickups': completed_pickups,
        'total_received_kg': round(total_received_kg, 1),
        'meals_served': meals_served,
        'gamification': gamification,
        'my_requirements': my_requirements[:5],
        'smart_matches': smart_matches[:6],
    }
    return render(request, 'food_management/ngo_dashboard.html', context)


def impact_dashboard(request):
    """
    Renders live impact analytics calculated from database records.
    """
    impact_data = get_comprehensive_impact_analytics()
    return render(request, 'food_management/impact.html', {'impact': impact_data})


def ngo_requirements_list(request):
    """
    Lists NGO registered community food needs and shows matching surplus lots for each.
    """
    requirements = NGORequirement.objects.all().order_by('-created_at')
    requirement_data = []
    for req in requirements:
        matches = find_matches_for_ngo(req, min_score=40)
        requirement_data.append({
            'requirement': req,
            'matches': matches[:5],
        })
    return render(request, 'food_management/ngo_requirements.html', {'requirement_data': requirement_data})


@role_required('ngo', 'admin')
def ngo_requirement_create(request):
    """
    Allows NGOs to register a new food need with quantity, category, and urgency.
    """
    if request.method == 'POST':
        form = NGORequirementForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.ngo_user = request.user
            if hasattr(request.user, 'profile') and request.user.profile.organization_name:
                req.ngo_name = request.user.profile.organization_name
            else:
                req.ngo_name = request.user.username
            req.save()
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.points += 15
            profile.level = max(1, profile.points // 100 + 1)
            profile.save()
            messages.success(request, f"Food need for '{req.category}' registered! Smart matching engine activated.")
            return redirect('ngo_requirements_list')
    else:
        form = NGORequirementForm()
    return render(request, 'food_management/ngo_requirement_form.html', {'form': form})


@role_required('ngo', 'admin')
def ngo_requirement_toggle_status(request, req_id):
    """
    Allows NGOs to close, fulfill, or cancel an active community food requirement.
    """
    req = get_object_or_404(NGORequirement, pk=req_id)
    is_admin = request.user.is_superuser or request.user.is_staff or (
        hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
    )
    if not is_admin and req.ngo_user and req.ngo_user != request.user:
        messages.error(request, 'Permission denied: You can only update your own food requirements.')
        return redirect('ngo_requirements_list')

    if request.method == 'POST':
        new_status = request.POST.get('status', 'cancelled')
        if new_status in dict(NGORequirement.STATUS_CHOICES):
            req.status = new_status
            req.save()
            messages.success(request, f"Requirement updated to '{req.get_status_display()}'.")
    return redirect('ngo_requirements_list')


def surplus_list(request):
    """
    Displays active surplus listings with live timers and filters.
    """
    today = date.today()
    listings = SurplusListing.objects.filter(status='available', expiry_date__gte=today).order_by('expiry_date')
    q = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    if q:
        listings = listings.filter(
            Q(food_name__icontains=q)
            | Q(pickup_location__icontains=q)
            | Q(category__icontains=q)
        )
    if category:
        listings = listings.filter(category__iexact=category)

    categories = (
        SurplusListing.objects.filter(status='available', expiry_date__gte=today)
        .values_list('category', flat=True)
        .distinct()
    )

    return render(request, 'food_management/surplus_list.html', {
        'listings': listings,
        'categories': categories,
        'selected_category': category,
        'query': q,
    })


@role_required('business', 'admin')
def surplus_listing_create(request):
    """
    Allows businesses to list surplus inventory for donation redistribution.
    """
    if request.method == 'POST':
        form = SurplusListingForm(request.POST)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.business = request.user
            listing.save()
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.points += 20
            profile.level = max(1, profile.points // 100 + 1)
            profile.badges = list(profile.badges or [])
            if 'Food Rescuer' not in profile.badges:
                profile.badges.append('Food Rescuer')
            profile.save()
            messages.success(request, f"Surplus lot '{listing.food_name}' posted to Marketplace!")
            return redirect('surplus_list')
    else:
        form = SurplusListingForm()
    return render(request, 'food_management/surplus_form.html', {'form': form})


@role_required('business', 'admin')
def surplus_listing_cancel(request, listing_id):
    """
    Cancels an active surplus lot and revokes pending allocations.
    """
    listing = get_object_or_404(SurplusListing, pk=listing_id)
    if not request.user.is_superuser and listing.business and listing.business != request.user:
        messages.error(request, 'Permission denied: You can only cancel your own surplus listings.')
        return redirect('surplus_list')

    if request.method == 'POST':
        if listing.status == 'collected':
            messages.error(request, 'Cannot cancel a surplus listing that has already been collected.')
            return redirect('surplus_list')

        listing.status = 'cancelled'
        listing.save()
        listing.requests.filter(status__in=['requested', 'approved', 'scheduled']).update(
            status='cancelled',
            cancellation_reason='Surplus lot cancelled by donor.',
        )
        messages.info(request, f"Surplus lot '{listing.food_name}' has been cancelled.")
    return redirect('surplus_list')


def donation_requests(request):
    """
    Tracks donation allocations across requested, approved, scheduled, collected, and cancelled states.
    """
    requests = DonationRequest.objects.select_related('listing').all().order_by('-created_at')
    status_filter = request.GET.get('status', '').strip()
    if status_filter:
        requests = requests.filter(status=status_filter)
    return render(request, 'food_management/donation_requests.html', {'requests': requests, 'status_filter': status_filter})


@role_required('ngo', 'business', 'admin')
def donation_request_create(request):
    """
    Enables NGOs to claim available surplus food with concurrency safety and PIN generation.
    """
    prefill_listing_id = request.GET.get('listing')
    initial = {}
    if prefill_listing_id:
        try:
            listing_obj = SurplusListing.objects.get(pk=prefill_listing_id)
            initial['listing'] = listing_obj
            initial['requested_quantity'] = listing_obj.remaining_quantity
        except SurplusListing.DoesNotExist:
            pass

    if request.method == 'POST':
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                listing = SurplusListing.objects.select_for_update().get(pk=form.cleaned_data['listing'].pk)
                requested_qty = form.cleaned_data['requested_quantity']
                remaining = listing.remaining_quantity

                if listing.is_expired():
                    messages.error(request, 'This surplus lot has expired and can no longer be claimed.')
                    return render(request, 'food_management/donation_form.html', {'form': form})

                if listing.status in ['cancelled', 'collected']:
                    messages.error(request, f'This surplus lot is {listing.status} and cannot be claimed.')
                    return render(request, 'food_management/donation_form.html', {'form': form})

                if requested_qty > remaining:
                    messages.error(request, f'Cannot claim {requested_qty} {listing.unit}. Only {remaining} {listing.unit} remaining.')
                    return render(request, 'food_management/donation_form.html', {'form': form})

                donation = form.save(commit=False)
                donation.ngo_user = request.user
                if hasattr(request.user, 'profile') and request.user.profile.organization_name:
                    donation.ngo_name = request.user.profile.organization_name
                donation.save()

                if listing.remaining_quantity <= 0:
                    listing.status = 'reserved'
                    listing.save()

                messages.success(
                    request,
                    f"Allocation request confirmed! Your collection PIN is {donation.pickup_code}. Present this code at pickup.",
                )
                return redirect('donation_requests')
    else:
        form = DonationRequestForm(initial=initial)
    return render(request, 'food_management/donation_form.html', {'form': form})


@role_required('ngo', 'business', 'admin')
def donation_status_update(request, request_id):
    """
    Safely transitions donation allocations through their lifecycle states.
    Awards gamification points and updates recovery metrics upon confirmed collection.
    """
    if request.method == 'POST':
        with transaction.atomic():
            donation = get_object_or_404(DonationRequest.objects.select_for_update(), pk=request_id)
            listing = SurplusListing.objects.select_for_update().get(pk=donation.listing.pk)
            next_status = request.POST.get('status')

            is_admin = request.user.is_superuser or request.user.is_staff or (
                hasattr(request.user, 'profile') and request.user.profile.role == 'admin'
            )
            is_donor = (listing.business and listing.business == request.user)
            is_claimant = (donation.ngo_user and donation.ngo_user == request.user)

            if not (is_admin or is_donor or is_claimant):
                messages.error(request, 'Permission denied: You do not have permission to manage this donation allocation.')
                return redirect('donation_requests')

            if next_status in dict(DonationRequest.STATUS_CHOICES):
                if not donation.can_transition_to(next_status) and not is_admin:
                    messages.error(request, f"Invalid status transition from '{donation.get_status_display()}' to '{next_status.capitalize()}'.")
                    return redirect('donation_requests')

                # Role-specific transition permissions: Only donor or admin can approve
                if next_status == 'approved' and not (is_donor or is_admin):
                    messages.error(request, 'Only the donor business or an administrator can approve donation requests.')
                    return redirect('donation_requests')

                # PIN verification when confirming collection
                if next_status == 'collected':
                    verification_pin = request.POST.get('verification_pin', '').strip().upper()
                    if verification_pin and verification_pin != donation.pickup_code.strip().upper():
                        messages.error(request, f"Verification failed: PIN '{verification_pin}' does not match the pickup PIN.")
                        return redirect('donation_requests')

                donation.status = next_status

                if next_status == 'collected':
                    donation.completed_at = timezone.now()
                    if listing.remaining_quantity <= 0:
                        listing.status = 'collected'
                        listing.save()

                    if listing.business:
                        bus_prof, _ = UserProfile.objects.get_or_create(user=listing.business)
                        bus_prof.points += 30
                        bus_prof.streak_days += 1
                        bus_prof.level = max(1, bus_prof.points // 100 + 1)
                        bus_prof.save()

                    if donation.ngo_user:
                        ngo_prof, _ = UserProfile.objects.get_or_create(user=donation.ngo_user)
                        ngo_prof.points += 25
                        ngo_prof.level = max(1, ngo_prof.points // 100 + 1)
                        badges = list(ngo_prof.badges or [])
                        if 'Impact Hero' not in badges:
                            badges.append('Impact Hero')
                        ngo_prof.badges = badges
                        ngo_prof.save()

                elif next_status == 'cancelled':
                    donation.cancellation_reason = request.POST.get('reason', 'Cancelled by participant')
                    if listing.status in ['reserved', 'collected']:
                        listing.status = 'available'
                        listing.save()

                donation.save()
                messages.success(request, f"Donation request marked as '{donation.get_status_display()}'.")
    return redirect('donation_requests')


@role_required('admin')
def admin_dashboard(request):
    inventory = InventoryItem.objects.all()
    recent_requests = DonationRequest.objects.select_related('listing').order_by('-created_at')[:5]

    search_user = request.GET.get('search_user', '').strip()
    active_tab = request.GET.get('tab', 'restaurants')

    business_profiles = UserProfile.objects.filter(role='business').select_related('user').order_by('-created_at')
    ngo_profiles = UserProfile.objects.filter(role='ngo').select_related('user').order_by('-created_at')

    if search_user:
        business_profiles = business_profiles.filter(
            Q(user__username__icontains=search_user)
            | Q(organization_name__icontains=search_user)
            | Q(user__email__icontains=search_user)
            | Q(phone_number__icontains=search_user)
        )
        ngo_profiles = ngo_profiles.filter(
            Q(user__username__icontains=search_user)
            | Q(organization_name__icontains=search_user)
            | Q(user__email__icontains=search_user)
            | Q(phone_number__icontains=search_user)
        )

    total_businesses = UserProfile.objects.filter(role='business').count()
    total_ngos = UserProfile.objects.filter(role='ngo').count()
    total_users = User.objects.filter(is_superuser=False).count()
    suspended_users = User.objects.filter(is_active=False).count()

    summary = {
        'total_inventory': inventory.count(),
        'near_expiry': inventory.filter(expiry_date__lte=date.today() + timedelta(days=7)).count(),
        'high_risk': inventory.filter(risk_level__in=['high', 'critical']).count(),
        'active_surplus': SurplusListing.objects.filter(status='available').count(),
        'donation_requests': DonationRequest.objects.count(),
    }
    context = {
        'summary': summary,
        'inventory_count': summary['total_inventory'],
        'surplus_count': summary['active_surplus'],
        'donation_count': summary['donation_requests'],
        'recent_requests': recent_requests,
        'leaderboard': get_leaderboard(limit=5),
        'business_profiles': business_profiles,
        'ngo_profiles': ngo_profiles,
        'search_user': search_user,
        'active_tab': active_tab,
        'total_businesses': total_businesses,
        'total_ngos': total_ngos,
        'total_users': total_users,
        'suspended_users': suspended_users,
    }
    return render(request, 'food_management/admin_dashboard.html', context)


@role_required('admin')
def admin_user_toggle_status(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        if target_user == request.user:
            messages.error(request, 'You cannot suspend your own administrative account.')
            return redirect('admin_dashboard')

        if target_user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Permission denied: Cannot modify a superuser account.')
            return redirect('admin_dashboard')

        target_user.is_active = not target_user.is_active
        target_user.save()

        status_text = 'reactivated' if target_user.is_active else 'suspended / deactivated due to malpractice'
        messages.success(request, f"User account '{target_user.username}' has been {status_text}.")
    return redirect('admin_dashboard')


@role_required('admin')
def admin_user_delete(request, user_id):
    if request.method == 'POST':
        target_user = get_object_or_404(User, pk=user_id)
        if target_user == request.user:
            messages.error(request, 'You cannot delete your own administrative account.')
            return redirect('admin_dashboard')

        if target_user.is_superuser and not request.user.is_superuser:
            messages.error(request, 'Permission denied: Cannot delete a superuser account.')
            return redirect('admin_dashboard')

        username = target_user.username
        target_user.delete()
        messages.success(request, f"User account '{username}' has been permanently removed due to malpractice / policy violation.")
    return redirect('admin_dashboard')


def inventory_list(request):
    items = InventoryItem.objects.all().order_by('expiry_date')
    query = request.GET.get('q', '').strip()
    risk = request.GET.get('risk', '').strip()

    if query:
        items = items.filter(
            Q(name__icontains=query)
            | Q(category__icontains=query)
            | Q(storage_location__icontains=query)
        )
    if risk:
        items = items.filter(risk_level=risk)

    return render(
        request,
        'food_management/inventory_list.html',
        {'items': items, 'query': query, 'risk': risk},
    )


def expiry_alerts(request):
    """
    Dedicated view for inventory items approaching expiry or flagged with critical/high risk.
    """
    today = date.today()
    threshold = today + timedelta(days=7)
    items = InventoryItem.objects.filter(
        Q(expiry_date__lte=threshold) | Q(risk_level__in=['critical', 'high'])
    ).order_by('expiry_date')
    return render(
        request,
        'food_management/inventory_list.html',
        {'items': items, 'risk': 'critical'},
    )


@role_required('business', 'admin')
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.points += 10
            profile.level = max(1, profile.points // 100 + 1)
            profile.streak_days += 1
            profile.badges = list(profile.badges or [])
            if 'Inventory Keeper' not in profile.badges:
                profile.badges.append('Inventory Keeper')
            profile.save()
            return redirect('inventory_list')
    else:
        form = InventoryForm()
    return render(request, 'food_management/inventory_form.html', {'form': form})


@role_required('business', 'admin')
def inventory_update(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inventory item updated.')
            return redirect('inventory_list')
    else:
        form = InventoryForm(instance=item)
    return render(request, 'food_management/inventory_form.html', {'form': form, 'editing': True})


@role_required('business', 'admin')
def inventory_delete(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Inventory item removed successfully.')
    return redirect('inventory_list')


@role_required('business', 'admin')
def inventory_import(request):
    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            file = request.FILES['csv_file']
            text = file.read().decode('utf-8-sig')
            reader = csv.DictReader(StringIO(text))
            created = 0
            for row in reader:
                if not row or not row.get('name'):
                    continue
                try:
                    quantity = Decimal(row.get('quantity', 0))
                except (InvalidOperation, TypeError, ValueError):
                    continue

                purchase_value = row.get('purchase_date')
                expiry_value = row.get('expiry_date')
                try:
                    purchase_date = date.fromisoformat(purchase_value) if purchase_value else date.today()
                    expiry_date_value = date.fromisoformat(expiry_value) if expiry_value else date.today()
                except ValueError:
                    continue

                InventoryItem.objects.create(
                    name=row.get('name', '').strip(),
                    category=row.get('category', 'Uncategorized').strip() or 'Uncategorized',
                    quantity=quantity,
                    unit=row.get('unit', 'kg').strip() or 'kg',
                    purchase_date=purchase_date,
                    expiry_date=expiry_date_value,
                    storage_location=row.get('storage_location', 'Main storage').strip() or 'Main storage',
                    notes=row.get('notes', ''),
                )
                created += 1

            messages.success(request, f'Imported {created} inventory item(s).')
            return redirect('inventory_list')
    else:
        form = CSVImportForm()
    return render(request, 'food_management/inventory_import.html', {'form': form})


def leaderboard(request):
    entries = get_leaderboard(limit=10)
    return render(request, 'food_management/leaderboard.html', {'leaderboard': entries})


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            get_or_create_user_profile(user)
            login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('admin_dashboard' if get_or_create_user_profile(user).role == 'admin' else 'dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'food_management/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            get_or_create_user_profile(user)
            login(request, user)
            messages.success(request, 'Welcome back!')
            default_target = 'admin_dashboard' if get_or_create_user_profile(user).role == 'admin' else 'dashboard'
            return redirect(request.GET.get('next') or default_target)
    else:
        form = AuthenticationForm()
    return render(request, 'food_management/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('dashboard')


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile_obj)
    return render(request, 'food_management/profile.html', {'form': form, 'profile': profile_obj})


def download_csv_template(request):
    """
    Streams a pre-formatted RFC-compliant CSV template for inventory bulk import.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory_import_template.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'name', 'category', 'quantity', 'unit', 'purchase_date', 'expiry_date', 'storage_location', 'notes'
    ])
    today = date.today().strftime('%Y-%m-%d')
    exp_3d = (date.today() + timedelta(days=3)).strftime('%Y-%m-%d')
    exp_7d = (date.today() + timedelta(days=7)).strftime('%Y-%m-%d')
    writer.writerow(['Greek Yogurt 500g', 'Dairy', '40.0', 'tubs', today, exp_3d, 'Walk-in Refrigerator', 'Keep at 2-4 C'])
    writer.writerow(['Artisanal Sourdough Bread', 'Bakery', '24.0', 'loaves', today, exp_3d, 'Bakery Rack A', 'Daily fresh bake'])
    writer.writerow(['Fresh Spinach Leaves', 'Produce', '15.5', 'kg', today, exp_7d, 'Produce Chiller', 'Grade A'])
    return response