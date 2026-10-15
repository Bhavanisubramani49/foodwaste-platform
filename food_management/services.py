from __future__ import annotations

from datetime import date

from django.db.models import Sum

from core.models import UserProfile

from .models import DonationRequest, InventoryItem


def estimate_waste_risk(items):
    if not items:
        return {
            'avg_risk': 0,
            'high_risk_count': 0,
            'recommended_action': 'Add inventory records to start forecasting.',
        }

    total = 0
    high_risk_count = 0
    for item in items:
        score = item.calculate_waste_risk_score()
        total += score
        if score >= 70:
            high_risk_count += 1

    avg_risk = round(total / len(items), 1)
    if avg_risk >= 70:
        recommendation = 'Prioritize redistribution or discounting for high-risk stock.'
    elif avg_risk >= 40:
        recommendation = 'Review purchase plans and schedule stock rotation.'
    else:
        recommendation = 'Inventory is stable; continue routine monitoring.'

    return {
        'avg_risk': avg_risk,
        'high_risk_count': high_risk_count,
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


def get_impact_summary():
    collected = DonationRequest.objects.filter(status='collected')
    total_recovered = collected.aggregate(total=Sum('requested_quantity'))['total'] or 0
    return {
        'collected_count': collected.count(),
        'total_recovered': total_recovered,
    }
