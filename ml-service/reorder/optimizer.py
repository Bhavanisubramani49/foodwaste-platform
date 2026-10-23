"""
Smart Reorder Optimizer for Perishable Inventory.

Determines optimal purchase quantities considering:
- Forecast demand over lead time + review period
- Dynamic safety stock (service level based)
- Current stock on hand
- Perishable shelf-life spoilage constraint
- Physical storage capacity limits
- Minimum Order Quantity (MOQ)

Provides comprehensive, human-readable reasoning with every recommendation.
"""

from __future__ import annotations

import math
from typing import Dict, Literal, NamedTuple, Optional

from data.generate_data import CATEGORY_PROFILES


ReorderStatus = Literal[
    "ORDER_RECOMMENDED",
    "SUFFICIENT_STOCK",
    "CAPACITY_CONSTRAINED",
    "SHELF_LIFE_CONSTRAINED",
]


class ReorderRecommendation(NamedTuple):
    recommended_order_qty: float
    status: ReorderStatus
    target_stock: float
    safety_stock: float
    current_stock: float
    storage_capacity: float
    capacity_utilized_pct: float
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            "recommended_order_qty": self.recommended_order_qty,
            "status": self.status,
            "target_stock": self.target_stock,
            "safety_stock": self.safety_stock,
            "current_stock": self.current_stock,
            "storage_capacity": self.storage_capacity,
            "capacity_utilized_pct": self.capacity_utilized_pct,
            "reasoning": self.reasoning,
        }


def calculate_safety_stock(
    daily_demand_mean: float,
    daily_demand_std: float,
    lead_time_days: int = 2,
    service_level_z: float = 1.65,  # 95% service level
) -> float:
    """
    Computes statistical safety stock:
    Safety Stock = Z * sqrt(Lead Time) * sigma_demand
    """
    if daily_demand_std <= 0.0:
        # Fallback to standard rule of thumb: 20% of lead time demand
        return round(0.20 * daily_demand_mean * lead_time_days, 2)

    ss = service_level_z * math.sqrt(max(1, lead_time_days)) * daily_demand_std
    return round(max(1.0, ss), 2)


def recommend_reorder(
    category: str,
    current_stock: float,
    forecast_lead_demand: float,
    lead_time_days: int = 2,
    storage_capacity: Optional[float] = None,
    safety_stock: Optional[float] = None,
    shelf_life_days: Optional[int] = None,
    min_order_qty: float = 0.0,
    daily_demand_std: float = 0.0,
) -> ReorderRecommendation:
    """
    Computes optimal replenishment order quantity and provides step-by-step reasoning.

    Parameters:
    - category: Product category (e.g. dairy, bakery, produce, meat, packaged, beverages)
    - current_stock: Units/kg currently in storage
    - forecast_lead_demand: Projected cumulative demand during lead time + review period
    - lead_time_days: Supplier delivery time in days (default: 2)
    - storage_capacity: Max physical storage capacity (default: category default * 5)
    - safety_stock: Explicit buffer stock (if None, statistically derived)
    - shelf_life_days: Max shelf life (default: extracted from category domain profile)
    - min_order_qty: Supplier minimum order threshold
    - daily_demand_std: Historical standard deviation of daily demand
    """
    cat_lower = category.lower()
    profile = CATEGORY_PROFILES.get(cat_lower, {
        "base_demand": 50.0,
        "shelf_life_days": 14,
        "unit": "kg",
    })

    stock = max(0.0, float(current_stock))
    demand = max(0.0, float(forecast_lead_demand))
    lead_days = max(1, int(lead_time_days))
    shelf_days = int(shelf_life_days) if shelf_life_days is not None else int(profile["shelf_life_days"])

    # Default storage capacity: 4x base daily demand
    if storage_capacity is None:
        capacity = round(profile["base_demand"] * 4.0, 1)
    else:
        capacity = max(10.0, float(storage_capacity))

    # Calculate safety stock if not explicitly supplied
    if safety_stock is None:
        mean_daily = demand / lead_days if lead_days > 0 else demand
        std_daily = daily_demand_std if daily_demand_std > 0 else (mean_daily * 0.20)
        ss = calculate_safety_stock(mean_daily, std_daily, lead_days)
    else:
        ss = max(0.0, float(safety_stock))

    # 1. Base Target Stock Level (Reorder Point policy)
    target_stock = round(demand + ss, 2)

    # 2. Raw Deficit / Ideal Order Quantity
    raw_needed = max(0.0, target_stock - stock)

    reasoning_steps = []
    status: ReorderStatus = "ORDER_RECOMMENDED"

    if raw_needed <= 0.0:
        status = "SUFFICIENT_STOCK"
        recommended_qty = 0.0
        reasoning_steps.append(
            f"Current inventory ({stock:.1f}) exceeds the target stock level ({target_stock:.1f} = "
            f"forecast demand {demand:.1f} + safety stock {ss:.1f}). No purchase required."
        )
    else:
        reasoning_steps.append(
            f"Deficit detected: target stock is {target_stock:.1f} (forecast demand {demand:.1f} + "
            f"safety stock {ss:.1f}) minus current stock {stock:.1f} = {raw_needed:.1f} required."
        )
        recommended_qty = raw_needed

        # 3. Perishable Shelf-Life Upper Bound Constraint
        # Never order more than what expected demand can clear within shelf life
        max_shelf_demand = (demand / lead_days) * shelf_days if lead_days > 0 else (demand * shelf_days)
        max_permissible_inventory = max(0.0, max_shelf_demand - stock)

        if recommended_qty > max_permissible_inventory:
            status = "SHELF_LIFE_CONSTRAINED"
            recommended_qty = round(max(0.0, max_permissible_inventory), 2)
            reasoning_steps.append(
                f"Shelf-life constraint applied: items expire in {shelf_days} days. "
                f"Capped order to {recommended_qty:.1f} to prevent surplus spoilage."
            )

        # 4. Storage Capacity Constraint
        available_space = max(0.0, capacity - stock)
        if recommended_qty > available_space:
            status = "CAPACITY_CONSTRAINED"
            recommended_qty = round(available_space, 2)
            reasoning_steps.append(
                f"Storage capacity ceiling reached: max storage is {capacity:.1f}, "
                f"available space is {available_space:.1f}. Order quantity adjusted down to {recommended_qty:.1f}."
            )

        # 5. Supplier Minimum Order Quantity (MOQ)
        if 0.0 < recommended_qty < min_order_qty:
            if stock + min_order_qty <= capacity:
                recommended_qty = min_order_qty
                reasoning_steps.append(f"Adjusted up to supplier minimum order quantity (MOQ: {min_order_qty:.1f}).")
            else:
                reasoning_steps.append(
                    f"Required quantity ({recommended_qty:.1f}) is below supplier MOQ ({min_order_qty:.1f}), "
                    "but increasing would exceed storage capacity. Recommend supplier waiver or alternative source."
                )

    projected_post_order_stock = stock + recommended_qty
    utilization_pct = round((projected_post_order_stock / capacity) * 100.0, 1) if capacity > 0 else 0.0

    final_reasoning = " ".join(reasoning_steps)

    return ReorderRecommendation(
        recommended_order_qty=round(recommended_qty, 2),
        status=status,
        target_stock=target_stock,
        safety_stock=ss,
        current_stock=stock,
        storage_capacity=capacity,
        capacity_utilized_pct=utilization_pct,
        reasoning=final_reasoning,
    )
