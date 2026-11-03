"""
Smart Matching Engine for Surplus Food Redistribution (Milestone 3).

Matches available surplus listings with registered NGO food requirements using:
- Food category compatibility (40 pts)
- Quantity fulfillment ratio (30 pts)
- Expiry date vs urgency alignment (20 pts)
- Geographical location compatibility (10 pts)
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from .models import NGORequirement, SurplusListing


def score_match(listing: SurplusListing, requirement: NGORequirement) -> Dict[str, Any]:
    """
    Evaluates compatibility between a SurplusListing and an NGORequirement.
    Returns match score (0-100), classification tier, and reasoning factors.
    """
    reasons = []

    # Disqualification: Expired surplus, cancelled/collected lot, zero stock, or closed requirement
    if listing.is_expired():
        return {
            'score': 0,
            'tier': 'Ineligible',
            'reasons': ['Surplus lot has already passed its expiry date.'],
            'eligible': False,
        }

    if listing.status in ['cancelled', 'collected']:
        return {
            'score': 0,
            'tier': 'Ineligible',
            'reasons': [f'Surplus lot is {listing.status}.'],
            'eligible': False,
        }

    if requirement.status in ['fulfilled', 'cancelled']:
        return {
            'score': 0,
            'tier': 'Ineligible',
            'reasons': [f'Requirement is already {requirement.status}.'],
            'eligible': False,
        }

    avail_qty = float(listing.remaining_quantity)
    if avail_qty <= 0:
        return {
            'score': 0,
            'tier': 'Ineligible',
            'reasons': ['Surplus lot has no remaining unallocated stock.'],
            'eligible': False,
        }

    # 1. Category Compatibility (Max 40 pts)
    cat_listing = (listing.category or '').strip().lower()
    cat_req = (requirement.category or '').strip().lower()

    if cat_listing == cat_req:
        category_score = 40
        reasons.append(f"Direct category match: '{listing.category}'")
    elif cat_listing in cat_req or cat_req in cat_listing:
        category_score = 25
        reasons.append(f"Related category overlap: '{listing.category}' ~ '{requirement.category}'")
    else:
        # Cross-category mismatch severely drops compatibility
        category_score = 5
        reasons.append(f"Category mismatch: '{listing.category}' vs requested '{requirement.category}'")

    # 2. Quantity Fulfillment Ratio (Max 30 pts)
    needed_qty = float(requirement.unfulfilled_quantity or requirement.quantity_needed or 1.0)
    if avail_qty >= needed_qty:
        quantity_score = 30
        reasons.append(f"100% quantity fulfillment ({avail_qty} {listing.unit} available >= {needed_qty} needed)")
    else:
        ratio = avail_qty / needed_qty
        quantity_score = max(5, int(30 * ratio))
        reasons.append(f"Partial fulfillment: {avail_qty} {listing.unit} covers {int(ratio * 100)}% of {needed_qty} needed")

    # 3. Expiry Date & Urgency Alignment (Max 20 pts)
    days_left = (listing.expiry_date - date.today()).days
    urgency = requirement.urgency

    if urgency == 'urgent' and days_left <= 2:
        expiry_score = 20
        reasons.append(f"Perfect urgent match: expires in {days_left}d, immediate redistribution needed")
    elif urgency in ['medium', 'urgent'] and days_left >= 1:
        expiry_score = 20
        reasons.append(f"Safe consumption window: {days_left} day(s) before expiry")
    elif urgency == 'low' and days_left >= 4:
        expiry_score = 20
        reasons.append(f"Adequate shelf-life buffer ({days_left} days)")
    elif days_left >= 1:
        expiry_score = 15
        reasons.append(f"Valid shelf-life ({days_left} days left)")
    else:
        expiry_score = 5
        reasons.append("Borderline expiry window (expires today)")

    # 4. Location Proximity (Max 10 pts)
    loc_listing = (listing.pickup_location or '').strip().lower()
    loc_req = (requirement.location or '').strip().lower()

    if not loc_req or not loc_listing:
        location_score = 8
        reasons.append("Location flexible / not restricted")
    else:
        words_listing = set(loc_listing.replace(',', ' ').split())
        words_req = set(loc_req.replace(',', ' ').split())
        common_words = words_listing.intersection(words_req)
        if common_words:
            location_score = 10
            reasons.append(f"Co-located / proximity match in '{', '.join(common_words)}'")
        else:
            location_score = 6
            reasons.append(f"Nearby regional handoff ({listing.pickup_location})")

    total_score = min(100, category_score + quantity_score + expiry_score + location_score)

    if total_score >= 80:
        tier = 'Excellent Match'
    elif total_score >= 60:
        tier = 'Strong Match'
    elif total_score >= 40:
        tier = 'Moderate Match'
    else:
        tier = 'Low Compatibility'

    return {
        'score': total_score,
        'tier': tier,
        'reasons': reasons,
        'eligible': total_score >= 40,
        'category_score': category_score,
        'quantity_score': quantity_score,
        'expiry_score': expiry_score,
        'location_score': location_score,
    }


def find_matches_for_ngo(requirement: NGORequirement, min_score: int = 40) -> List[Dict[str, Any]]:
    """
    Finds and ranks all available SurplusListings compatible with an NGORequirement.
    """
    active_listings = SurplusListing.objects.filter(
        status='available',
        expiry_date__gte=date.today(),
    ).select_related('business').order_by('expiry_date')

    matches = []
    for listing in active_listings:
        if listing.remaining_quantity <= 0:
            continue
        eval_result = score_match(listing, requirement)
        if eval_result['score'] >= min_score:
            matches.append({
                'listing': listing,
                'requirement': requirement,
                'score': eval_result['score'],
                'tier': eval_result['tier'],
                'reasons': eval_result['reasons'],
                'available_qty': listing.remaining_quantity,
            })

    matches.sort(key=lambda m: m['score'], reverse=True)
    return matches


def find_matches_for_listing(listing: SurplusListing, min_score: int = 40) -> List[Dict[str, Any]]:
    """
    Finds and ranks all active NGORequirements compatible with a SurplusListing.
    """
    if listing.is_expired() or listing.remaining_quantity <= 0:
        return []

    active_requirements = NGORequirement.objects.filter(
        status__in=['open', 'partially_fulfilled']
    ).select_related('ngo_user').order_by('-created_at')

    matches = []
    for req in active_requirements:
        eval_result = score_match(listing, req)
        if eval_result['score'] >= min_score:
            matches.append({
                'listing': listing,
                'requirement': req,
                'score': eval_result['score'],
                'tier': eval_result['tier'],
                'reasons': eval_result['reasons'],
                'needed_qty': req.unfulfilled_quantity,
            })

    matches.sort(key=lambda m: m['score'], reverse=True)
    return matches
