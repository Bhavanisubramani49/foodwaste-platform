"""
Waste Risk Scoring Engine for Perishable Inventory.

Combines:
- Days to Expiry (D)
- Current Stock (S)
- Forecast Demand over Remaining Shelf-Life (F)

Outputs:
- Numerical waste risk score in [0.0, 100.0]
- Qualitative classification label: Low, Medium, High, Critical
- Quantified surplus amount (expected unsold quantity)
- Actionable operational recommendation

Mathematical Formulation:
--------------------------
1. Edge Cases:
   - If S <= 0:
       Score = 0.0, Label = "Low"
       (No physical inventory exists; zero waste risk)
   - If D <= 0 and S > 0:
       Score = 100.0, Label = "Critical"
       (Product has expired; 100% of stock is spoiled)

2. Surplus Stock & Surplus Ratio:
   S_surplus = max(0.0, S - F)
   R_surplus = S_surplus / S    (Proportion of stock projected to spoil)

3. Time Urgency Factor U(D):
   Non-linear step decay modeling proximity to expiry:
   - D <= 0:  U = 1.00
   - 1 <= D <= 2:  U = 0.90
   - 3 <= D <= 5:  U = 0.75
   - 6 <= D <= 10: U = 0.55
   - 11 <= D <= 20: U = 0.35
   - D > 20: U = 0.15

4. Composite Score Calculation:
   Score = min(100.0, max(0.0,
       (0.65 * R_surplus + 0.35 * U(D) * (1.0 if R_surplus > 0 else 0.30)) * 100.0
   ))

5. Risk Thresholds:
   - Critical: Score >= 75.0 (or D <= 0)
   - High:     50.0 <= Score < 75.0
   - Medium:   25.0 <= Score < 50.0
   - Low:      Score < 25.0
"""

from __future__ import annotations

from typing import Dict, Literal, NamedTuple


RiskLevel = Literal["Low", "Medium", "High", "Critical"]


class WasteRiskResult(NamedTuple):
    risk_score: float
    risk_level: RiskLevel
    surplus_qty: float
    surplus_ratio: float
    urgency_factor: float
    action_recommendation: str

    def to_dict(self) -> Dict:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "surplus_qty": self.surplus_qty,
            "surplus_ratio": self.surplus_ratio,
            "urgency_factor": self.urgency_factor,
            "action_recommendation": self.action_recommendation,
        }


def compute_urgency_factor(days_to_expiry: int) -> float:
    """Returns non-linear time urgency factor U(D) in [0.15, 1.00]."""
    if days_to_expiry <= 0:
        return 1.00
    elif days_to_expiry <= 2:
        return 0.90
    elif days_to_expiry <= 5:
        return 0.75
    elif days_to_expiry <= 10:
        return 0.55
    elif days_to_expiry <= 20:
        return 0.35
    else:
        return 0.15


def calculate_waste_risk(
    days_to_expiry: int,
    current_stock: float,
    forecast_demand: float,
    category: str | None = None,
) -> WasteRiskResult:
    """
    Computes calibrated waste risk score (0-100) and actionable diagnosis.

    Parameters:
    - days_to_expiry: Days remaining until expiration date
    - current_stock: Quantity currently in stock (kg, units, etc.)
    - forecast_demand: Cumulative forecasted demand over the remaining days
    - category: Optional category context for customized messaging
    """
    stock = max(0.0, float(current_stock))
    demand = max(0.0, float(forecast_demand))
    d_days = int(days_to_expiry)

    # -------------------------------------------------------------------------
    # Edge Case 1: Zero or Negative Stock
    # -------------------------------------------------------------------------
    if stock <= 0.0:
        return WasteRiskResult(
            risk_score=0.0,
            risk_level="Low",
            surplus_qty=0.0,
            surplus_ratio=0.0,
            urgency_factor=compute_urgency_factor(d_days),
            action_recommendation="Inventory exhausted; no waste risk. Consider restocking if demand persists.",
        )

    # -------------------------------------------------------------------------
    # Edge Case 2: Already Expired Items
    # -------------------------------------------------------------------------
    if d_days <= 0:
        return WasteRiskResult(
            risk_score=100.0,
            risk_level="Critical",
            surplus_qty=round(stock, 2),
            surplus_ratio=1.0,
            urgency_factor=1.00,
            action_recommendation="Item has expired! Remove from circulation immediately. Evaluate for composting or bio-energy.",
        )

    # -------------------------------------------------------------------------
    # General Case: Surplus & Urgency
    # -------------------------------------------------------------------------
    surplus_qty = max(0.0, stock - demand)
    surplus_ratio = surplus_qty / stock if stock > 0 else 0.0
    urgency = compute_urgency_factor(d_days)

    # Weighting:
    # If there is expected surplus (stock exceeds forecast demand):
    #   Surplus severity (65%) + Time urgency (35%)
    # If demand exceeds stock (no surplus expected):
    #   Minimal baseline residual risk scaled down by 0.30
    if surplus_ratio > 0.0:
        raw_score = (0.65 * surplus_ratio + 0.35 * urgency) * 100.0
    else:
        # Stock will be completely sold if forecast holds true.
        # Slight residual risk accounts for unexpected demand variations when expiry is very near.
        raw_score = 0.35 * urgency * 0.30 * 100.0

    score = round(min(100.0, max(0.0, raw_score)), 1)

    # Classify Risk Level
    if score >= 75.0 or d_days <= 1:
        risk_level: RiskLevel = "Critical"
    elif score >= 50.0:
        risk_level = "High"
    elif score >= 25.0:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Actionable operational recommendations
    if risk_level == "Critical":
        action = (
            f"Urgent: {surplus_qty:.1f} units expected to spoil in {d_days}d. "
            "Post immediate surplus listing for NGO donation or apply a 70%+ flash discount."
        )
    elif risk_level == "High":
        action = (
            f"High waste risk: Projected {surplus_qty:.1f} surplus units. "
            "Schedule NGO pickup or offer a 30-50% promotional markdown."
        )
    elif risk_level == "Medium":
        action = (
            f"Moderate risk: Potential minor surplus ({surplus_qty:.1f} units). "
            "Prioritize first-in-first-out (FIFO) rotation and monitor sales pace."
        )
    else:
        action = "Low risk: Projected demand safely absorbs inventory before expiration. Maintain standard monitoring."

    return WasteRiskResult(
        risk_score=score,
        risk_level=risk_level,
        surplus_qty=round(surplus_qty, 2),
        surplus_ratio=round(surplus_ratio, 3),
        urgency_factor=round(urgency, 2),
        action_recommendation=action,
    )
