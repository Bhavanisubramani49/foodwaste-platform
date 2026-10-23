"""
Unit tests for Step 3: Waste Risk Scoring Engine.
Verifies formula correctness and all required edge cases.
"""

import pytest

from risk.risk_scorer import (
    calculate_waste_risk,
    compute_urgency_factor,
)


def test_edge_case_expired_items():
    # Expired yesterday, positive stock
    result = calculate_waste_risk(days_to_expiry=0, current_stock=25.0, forecast_demand=50.0)
    assert result.risk_score == 100.0
    assert result.risk_level == "Critical"
    assert result.surplus_qty == 25.0
    assert result.surplus_ratio == 1.0
    assert "expired" in result.action_recommendation.lower()

    # Expired 5 days ago
    res_neg = calculate_waste_risk(days_to_expiry=-5, current_stock=10.0, forecast_demand=0.0)
    assert res_neg.risk_score == 100.0
    assert res_neg.risk_level == "Critical"
    assert res_neg.surplus_qty == 10.0


def test_edge_case_zero_stock():
    # Zero stock regardless of days to expiry
    result = calculate_waste_risk(days_to_expiry=3, current_stock=0.0, forecast_demand=40.0)
    assert result.risk_score == 0.0
    assert result.risk_level == "Low"
    assert result.surplus_qty == 0.0
    assert result.surplus_ratio == 0.0

    # Negative stock (e.g. data anomaly) clipped to 0
    res_neg = calculate_waste_risk(days_to_expiry=1, current_stock=-10.0, forecast_demand=10.0)
    assert res_neg.risk_score == 0.0
    assert res_neg.risk_level == "Low"


def test_edge_case_zero_demand():
    # 50kg in stock, but 0 demand projected before 2-day expiry -> All will spoil
    result = calculate_waste_risk(days_to_expiry=2, current_stock=50.0, forecast_demand=0.0)
    assert result.surplus_qty == 50.0
    assert result.surplus_ratio == 1.0
    assert result.risk_score >= 85.0
    assert result.risk_level == "Critical"


def test_high_demand_low_risk():
    # 20kg in stock, 100kg demand over next 7 days -> Stock will sell out easily
    result = calculate_waste_risk(days_to_expiry=7, current_stock=20.0, forecast_demand=100.0)
    assert result.surplus_qty == 0.0
    assert result.surplus_ratio == 0.0
    assert result.risk_score < 25.0
    assert result.risk_level == "Low"


def test_moderate_surplus_medium_risk():
    # 50kg in stock, 35kg demand over 8 days -> 15kg surplus (30% surplus ratio)
    result = calculate_waste_risk(days_to_expiry=8, current_stock=50.0, forecast_demand=35.0)
    assert result.surplus_qty == 15.0
    assert result.risk_score >= 25.0
    assert result.risk_level in ["Medium", "High"]


def test_urgency_factor_monotonic_decay():
    u_0 = compute_urgency_factor(0)
    u_2 = compute_urgency_factor(2)
    u_5 = compute_urgency_factor(5)
    u_10 = compute_urgency_factor(10)
    u_30 = compute_urgency_factor(30)

    assert u_0 >= u_2 >= u_5 >= u_10 >= u_30
    assert u_0 == 1.00
    assert u_30 == 0.15


def test_result_dictionary_serialization():
    result = calculate_waste_risk(days_to_expiry=4, current_stock=40.0, forecast_demand=15.0)
    d = result.to_dict()

    expected_keys = {
        "risk_score",
        "risk_level",
        "surplus_qty",
        "surplus_ratio",
        "urgency_factor",
        "action_recommendation",
    }
    assert expected_keys.issubset(set(d.keys()))
    assert isinstance(d["risk_score"], float)
    assert d["risk_level"] in ["Low", "Medium", "High", "Critical"]
