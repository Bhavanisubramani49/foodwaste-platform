"""
Unit tests for Step 4: Smart Reorder Recommendation Engine.
"""

import pytest

from reorder.optimizer import (
    calculate_safety_stock,
    recommend_reorder,
)


def test_safety_stock_calculation():
    # Mean daily demand = 50, std = 10, lead time = 4 days
    # Z = 1.65 => 1.65 * sqrt(4) * 10 = 1.65 * 2 * 10 = 33.0
    ss = calculate_safety_stock(daily_demand_mean=50.0, daily_demand_std=10.0, lead_time_days=4)
    assert abs(ss - 33.0) < 0.1


def test_sufficient_stock_no_reorder():
    # Current stock 100 exceeds demand 40 + safety stock 10
    rec = recommend_reorder(
        category="dairy",
        current_stock=100.0,
        forecast_lead_demand=40.0,
        safety_stock=10.0,
        storage_capacity=200.0,
    )
    assert rec.status == "SUFFICIENT_STOCK"
    assert rec.recommended_order_qty == 0.0
    assert "no purchase required" in rec.reasoning.lower()


def test_standard_reorder_recommended():
    # Demand = 60, Safety stock = 15, Target = 75. Current stock = 25.
    # Deficit = 50. Within capacity (200) and shelf life.
    rec = recommend_reorder(
        category="dairy",
        current_stock=25.0,
        forecast_lead_demand=60.0,
        safety_stock=15.0,
        storage_capacity=200.0,
        shelf_life_days=14,
    )
    assert rec.status == "ORDER_RECOMMENDED"
    assert rec.recommended_order_qty == 50.0
    assert rec.target_stock == 75.0
    assert "deficit detected" in rec.reasoning.lower()


def test_storage_capacity_constraint():
    # Deficit = 80, but remaining space in storage is only 30 (capacity 100 - stock 70)
    rec = recommend_reorder(
        category="beverages",
        current_stock=70.0,
        forecast_lead_demand=120.0,
        safety_stock=30.0,
        storage_capacity=100.0,
    )
    assert rec.status == "CAPACITY_CONSTRAINED"
    assert rec.recommended_order_qty == 30.0  # Capped at 100 - 70
    assert "capacity ceiling reached" in rec.reasoning.lower()


def test_shelf_life_constraint_prevents_spoilage():
    # Bakery item with 2-day shelf life, lead time = 2 days, demand = 20/day
    # Even if target stock is huge, we cannot stock more than what can be sold before expiry
    rec = recommend_reorder(
        category="bakery",
        current_stock=10.0,
        forecast_lead_demand=40.0,
        lead_time_days=2,
        safety_stock=50.0,  # Unrealistic huge safety stock
        storage_capacity=300.0,
        shelf_life_days=2,
    )
    assert rec.status == "SHELF_LIFE_CONSTRAINED"
    # Max shelf demand is 40. Current stock is 10. Max order is 30.
    assert rec.recommended_order_qty <= 30.0
    assert "shelf-life constraint applied" in rec.reasoning.lower()


def test_minimum_order_quantity_bump():
    # Needed is 15, but supplier MOQ is 25
    rec = recommend_reorder(
        category="packaged",
        current_stock=20.0,
        forecast_lead_demand=30.0,
        safety_stock=5.0,
        storage_capacity=200.0,
        min_order_qty=25.0,
    )
    assert rec.recommended_order_qty == 25.0
    assert "moq" in rec.reasoning.lower()


def test_recommendation_dict_serialization():
    rec = recommend_reorder(
        category="produce",
        current_stock=20.0,
        forecast_lead_demand=50.0,
        safety_stock=10.0,
    )
    d = rec.to_dict()
    assert "recommended_order_qty" in d
    assert "status" in d
    assert "reasoning" in d
    assert isinstance(d["reasoning"], str)
