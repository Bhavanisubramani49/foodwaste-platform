from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List

from django.db.models import Count, F, Sum
from django.db.models.functions import TruncMonth

from core.models import UserProfile
from .models import DonationRequest, InventoryItem, NGORequirement, SurplusListing


def estimate_waste_risk(items):
    if not items:
        return {
            'avg_risk': 0,
            'high_risk_count': 0,
            'predicted_waste_kg': 0.0,
            'recommended_action': 'Add inventory records to start forecasting.',
        }

    total = 0
    high_risk_count = 0
    total_surplus_kg = 0.0
    for item in items:
        score = item.calculate_waste_risk_score()
        total += score
        if score >= 70:
            high_risk_count += 1
            total_surplus_kg += float(item.quantity or 0) * 0.8
        elif score >= 50:
            total_surplus_kg += float(item.quantity or 0) * 0.4

    avg_risk = round(total / len(items), 1)
    if avg_risk >= 70:
        recommendation = 'Prioritize immediate redistribution or marketplace posting for high-risk stock.'
    elif avg_risk >= 40:
        recommendation = 'Review purchase plans and schedule stock rotation.'
    else:
        recommendation = 'Inventory is stable; continue routine monitoring.'

    return {
        'avg_risk': avg_risk,
        'high_risk_count': high_risk_count,
        'predicted_waste_kg': round(total_surplus_kg, 1),
        'recommended_action': recommendation,
    }


def get_gamification_summary(user):
    if not user or not user.is_authenticated:
        return {
            'points': 0,
            'streak_days': 0,
            'level': 1,
            'next_badge': 'Starter',
            'badges': [],
        }

    profile, _ = UserProfile.objects.get_or_create(user=user)
    level = max(1, int(profile.level or 1))
    points = int(profile.points or 0)
    badges = profile.badges or []
    next_badge = 'Bronze' if points < 100 else 'Silver' if points < 250 else 'Gold'
    return {
        'points': points,
        'streak_days': int(profile.streak_days or 0),
        'level': level,
        'next_badge': next_badge,
        'badges': badges,
    }


def get_leaderboard(limit=5, anonymize=False):
    profiles = UserProfile.objects.select_related('user').order_by('-points', '-streak_days', 'user__username')[:limit]
    leaderboard = []
    for profile in profiles:
        leaderboard.append({
            'rank': len(leaderboard) + 1,
            'name': 'Anonymous' if anonymize else (profile.organization_name or profile.user.username),
            'points': int(profile.points or 0),
            'level': max(1, int(profile.level or 1)),
            'role': profile.get_role_display(),
        })
    return leaderboard


def get_impact_summary() -> Dict[str, Any]:
    """
    Returns baseline impact metrics based on database records of collected food donations.
    """
    collected = DonationRequest.objects.filter(status='collected')
    total_recovered = float(collected.aggregate(total=Sum('requested_quantity'))['total'] or 0.0)
    return {
        'collected_count': collected.count(),
        'total_recovered': round(total_recovered, 1),
    }


def get_comprehensive_impact_analytics() -> Dict[str, Any]:
    """
    Calculates detailed food waste diversion metrics directly from database records.
    Documented Assumptions & Scientific Benchmarks:
    1. Meals Provided: 1 meal = 0.45 kg of edible food (standard FAO / USDA / Feeding America benchmark: ~2.22 meals per kg).
    2. CO2e Avoidance: 1 kg of food waste diverted from landfill prevents 2.5 kg of CO2 equivalent emissions
       (preventing anaerobic methane release; EPA WARM & FAO Food Wastage Footprint methodology).
    3. Landfill Space Saved: Organic municipal waste density averages ~500 kg/m^3 (1 m^3 saved per 500 kg diverted).
    4. Economic Valuation: Average wholesale nutritional value is ₹120 ($1.45) per kg of edible food rescued.
    """
    collected_requests = DonationRequest.objects.filter(status='collected').select_related('listing')
    active_requests = DonationRequest.objects.filter(status__in=['requested', 'approved', 'scheduled'])

    total_recovered_kg = float(collected_requests.aggregate(total=Sum('requested_quantity'))['total'] or 0.0)
    scheduled_kg = float(active_requests.aggregate(total=Sum('requested_quantity'))['total'] or 0.0)

    # Calculate actual or estimated uncollected inventory waste
    expired_inventory_items = InventoryItem.objects.filter(expiry_date__lt=date.today())
    total_expired_kg = float(expired_inventory_items.aggregate(total=Sum('quantity'))['total'] or 0.0)

    total_food_managed_kg = total_recovered_kg + total_expired_kg
    if total_food_managed_kg > 0:
        diversion_rate = round((total_recovered_kg / total_food_managed_kg) * 100, 1)
    else:
        diversion_rate = 100.0 if total_recovered_kg > 0 else 0.0

    # Conversions
    meals_served = int(round(total_recovered_kg * 2.22))
    co2_prevented_kg = round(total_recovered_kg * 2.5, 1)
    co2_prevented_tonnes = round(co2_prevented_kg / 1000.0, 3)
    landfill_m3_saved = round(total_recovered_kg / 500.0, 2)
    economic_value_inr = round(total_recovered_kg * 120.0, 2)

    # Category breakdown of diverted food
    category_counts = {}
    for req in collected_requests:
        cat = (getattr(req.listing, 'category', None) or 'Uncategorized').strip().capitalize()
        qty = float(req.requested_quantity or 0.0)
        category_counts[cat] = category_counts.get(cat, 0.0) + qty

    sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
    category_breakdown = [{'category': cat, 'quantity_kg': round(qty, 1)} for cat, qty in sorted_categories]

    # Partner counts
    participating_businesses = SurplusListing.objects.values('business').distinct().count()
    participating_ngos = collected_requests.values('ngo_name').distinct().count()

    return {
        'total_recovered_kg': round(total_recovered_kg, 1),
        'scheduled_kg': round(scheduled_kg, 1),
        'total_expired_kg': round(total_expired_kg, 1),
        'diversion_rate': diversion_rate,
        'meals_served': meals_served,
        'co2_prevented_kg': co2_prevented_kg,
        'co2_prevented_tonnes': co2_prevented_tonnes,
        'landfill_m3_saved': landfill_m3_saved,
        'economic_value_inr': economic_value_inr,
        'completed_collections_count': collected_requests.count(),
        'active_allocations_count': active_requests.count(),
        'participating_businesses': max(1, participating_businesses),
        'participating_ngos': max(1, participating_ngos),
        'category_breakdown': category_breakdown,
        'methodology_assumptions': [
            '1 kg of recovered food provides ~2.22 nutritious meal portions (USDA / Feeding America standard of 0.45 kg/meal).',
            '1 kg of food diverted from landfills avoids 2.5 kg of CO2 equivalent emissions by preventing anaerobic decomposition into methane (EPA WARM & FAO models).',
            'Landfill volume saved is based on typical compacted organic municipal solid waste density of 500 kg/m³.',
            'Economic value is estimated using an average edible wholesale recovery valuation of ₹120 per kg.',
        ],
    }
