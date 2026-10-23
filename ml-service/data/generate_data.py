"""
Synthetic Data Generator for Food Waste Management Platform.

Generates:
1. Daily transaction time-series (sales, purchases, waste) per product category
   with seasonality, trends, holiday/weekend spikes, and category shelf lives.
2. Active inventory snapshot matching Milestone 1's InventoryItem schema
   for seamless real-data compatibility and DB import.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

# Categories and their domain-specific characteristics
CATEGORY_PROFILES: Dict[str, Dict] = {
    "dairy": {
        "base_demand": 45.0,
        "shelf_life_days": 10,
        "unit": "kg",
        "volatility": 0.18,
        "weekend_boost": 1.25,
        "spoilage_rate": 0.08,
        "sample_items": ["Whole Milk 1L", "Greek Yogurt", "Cheddar Cheese", "Butter 250g", "Paneer"],
        "storage": "Cold Room A (4°C)",
    },
    "bakery": {
        "base_demand": 60.0,
        "shelf_life_days": 3,
        "unit": "kg",
        "volatility": 0.25,
        "weekend_boost": 1.40,
        "spoilage_rate": 0.14,
        "sample_items": ["Sourdough Loaf", "Butter Croissant", "Whole Wheat Bread", "Baguette", "Muffins 4-pk"],
        "storage": "Bakery Rack 1",
    },
    "produce": {
        "base_demand": 80.0,
        "shelf_life_days": 7,
        "unit": "kg",
        "volatility": 0.22,
        "weekend_boost": 1.35,
        "spoilage_rate": 0.12,
        "sample_items": ["Tomatoes", "Bananas", "Spinach Bunch", "Bell Peppers", "Apples Gala"],
        "storage": "Produce Cooler B",
    },
    "meat": {
        "base_demand": 35.0,
        "shelf_life_days": 5,
        "unit": "kg",
        "volatility": 0.20,
        "weekend_boost": 1.50,
        "spoilage_rate": 0.07,
        "sample_items": ["Chicken Breast", "Minced Beef", "Pork Chops", "Salmon Fillet", "Lamb Stew Cut"],
        "storage": "Deep Freezer / Chiller (-2°C)",
    },
    "packaged": {
        "base_demand": 50.0,
        "shelf_life_days": 180,
        "unit": "units",
        "volatility": 0.12,
        "weekend_boost": 1.15,
        "spoilage_rate": 0.02,
        "sample_items": ["Pasta Penne 500g", "Canned Tomatoes", "Basmati Rice 1kg", "Olive Oil 500ml", "Cereal Flakes"],
        "storage": "Dry Storage Shelf C",
    },
    "beverages": {
        "base_demand": 40.0,
        "shelf_life_days": 90,
        "unit": "litres",
        "volatility": 0.15,
        "weekend_boost": 1.30,
        "spoilage_rate": 0.03,
        "sample_items": ["Orange Juice 1L", "Sparkling Water 6-pk", "Cold Brew Coffee", "Green Tea 500ml", "Lemonade"],
        "storage": "Beverage Display Aisle",
    },
}

# Major annual holidays (month, day) with their demand multiplier
KNOWN_HOLIDAYS = {
    (1, 1): 1.6,   # New Year's Day
    (2, 14): 1.3,  # Valentine's
    (4, 15): 1.4,  # Spring Holiday / Good Friday
    (5, 1): 1.2,   # Labour Day
    (7, 4): 1.5,   # Summer celebration
    (8, 15): 1.35, # Independence Day
    (10, 31): 1.4, # Halloween / Festival
    (11, 26): 1.6, # Thanksgiving / Autumn festival
    (12, 24): 1.8, # Christmas Eve
    (12, 25): 1.7, # Christmas Day
    (12, 31): 1.85 # New Year's Eve
}


def _get_holiday_multiplier(dt: date) -> float:
    """Returns demand spike multiplier if the date matches a known holiday."""
    return KNOWN_HOLIDAYS.get((dt.month, dt.day), 1.0)


def generate_synthetic_transactions(
    days: int = 365,
    businesses: List[str] | None = None,
    seed: int = 42,
    end_date: date | None = None,
) -> pd.DataFrame:
    """
    Generates realistic daily transaction records across businesses and categories.

    Includes:
    - Weekly seasonality (weekend surges)
    - Trend (gradual business growth over time)
    - Holiday spikes
    - Gaussian noise
    - Realistic purchase and waste dynamics based on category shelf life
    """
    if businesses is None:
        businesses = ["biz_001", "biz_002", "biz_003"]
    if end_date is None:
        end_date = date.today()

    rng = np.random.default_rng(seed)
    start_date = end_date - timedelta(days=days - 1)
    date_range = [start_date + timedelta(days=i) for i in range(days)]

    records = []

    for biz_idx, biz_id in enumerate(businesses):
        # Slightly vary business scale
        biz_scale = 0.85 + (biz_idx * 0.20)

        for category, profile in CATEGORY_PROFILES.items():
            base = profile["base_demand"] * biz_scale
            unit = profile["unit"]
            volatility = profile["volatility"]
            weekend_boost = profile["weekend_boost"]
            spoilage_rate = profile["spoilage_rate"]

            # Initialize a virtual inventory buffer to realistically simulate purchases and spoilage
            virtual_inventory = base * 2.5

            for step, dt in enumerate(date_range):
                # 1. Day of week effect: Sat=5, Sun=6 get boost; Friday gets slight boost
                weekday = dt.weekday()
                if weekday in (4, 5, 6):
                    day_effect = weekend_boost if weekday in (5, 6) else (1.0 + (weekend_boost - 1.0) * 0.5)
                elif weekday == 0:
                    day_effect = 0.90  # Monday slow-down
                else:
                    day_effect = 1.0

                # 2. Long-term trend: gentle growth curve (up to +12% over 1 year)
                trend_factor = 1.0 + (0.12 * (step / max(days, 1)))

                # 3. Holiday effect
                holiday_factor = _get_holiday_multiplier(dt)

                # 4. Seasonal variation (annual sine cycle)
                day_of_year = dt.timetuple().tm_yday
                seasonal_factor = 1.0 + 0.08 * np.sin(2 * np.pi * day_of_year / 365.25)

                # Combined expected demand
                expected_sales = base * day_effect * trend_factor * holiday_factor * seasonal_factor

                # Add noise
                noise = rng.normal(0, volatility * base)
                actual_sales = max(0.0, round(expected_sales + noise, 2))

                # Periodic restocking: replenishment orders triggered when inventory dips
                # Supermarkets typically order in batches 2-3 times a week for fresh goods, weekly for dry goods
                needs_restock = (virtual_inventory < actual_sales * 1.5) or (weekday in (1, 4))
                if needs_restock:
                    target_safety_stock = base * (3.0 if profile["shelf_life_days"] > 7 else 1.8)
                    purchase_qty = max(0.0, round(target_safety_stock - virtual_inventory + actual_sales + rng.normal(0, base * 0.1), 2))
                else:
                    purchase_qty = 0.0

                virtual_inventory += purchase_qty

                # Actual sales fulfilled cannot exceed available inventory
                sales_qty = min(virtual_inventory, actual_sales)
                virtual_inventory = max(0.0, virtual_inventory - sales_qty)

                # Waste generation based on shelf life and remaining stock
                # Shorter shelf life = higher probability of leftover stock expiring
                waste_chance = spoilage_rate * (1.3 if weekday == 6 else 1.0)
                if virtual_inventory > 0 and rng.random() < 0.35:
                    waste_qty = round(float(rng.uniform(0.02, waste_chance) * virtual_inventory), 2)
                    virtual_inventory = max(0.0, virtual_inventory - waste_qty)
                else:
                    waste_qty = 0.0

                records.append({
                    "date": dt.isoformat(),
                    "business_id": biz_id,
                    "category": category,
                    "sales_qty": round(sales_qty, 2),
                    "purchase_qty": round(purchase_qty, 2),
                    "waste_qty": round(waste_qty, 2),
                    "unit": unit,
                })

    df = pd.DataFrame(records)
    return df


def generate_inventory_snapshot(
    businesses: List[str] | None = None,
    seed: int = 42,
    as_of_date: date | None = None,
) -> pd.DataFrame:
    """
    Generates an active inventory snapshot matching Milestone 1 InventoryItem schema:
    [name, category, quantity, unit, purchase_date, expiry_date, storage_location, risk_level, notes]
    """
    if businesses is None:
        businesses = ["biz_001", "biz_002", "biz_003"]
    if as_of_date is None:
        as_of_date = date.today()

    rng = np.random.default_rng(seed)
    inventory_records = []

    for biz_id in businesses:
        for category, profile in CATEGORY_PROFILES.items():
            sample_items = profile["sample_items"]
            shelf_life = profile["shelf_life_days"]
            unit = profile["unit"]
            storage = profile["storage"]

            for item_name in sample_items:
                # Decide how many days ago this batch was purchased
                # Mix of fresh, mid-life, near-expiry, and a few expired items for testing edge cases
                status_roll = rng.random()
                if status_roll < 0.10:
                    # Near expired or already expired (-1 to +2 days from today)
                    expiry_offset = int(rng.integers(-1, 3))
                    purchase_offset = -(shelf_life - expiry_offset)
                elif status_roll < 0.35:
                    # Urgent / High risk: 3 to 6 days until expiry
                    expiry_offset = int(rng.integers(3, min(7, shelf_life + 2)))
                    purchase_offset = -(shelf_life - expiry_offset)
                elif status_roll < 0.70:
                    # Medium risk / Mid-life
                    expiry_offset = int(rng.integers(7, max(8, int(shelf_life * 0.7))))
                    purchase_offset = -(shelf_life - expiry_offset)
                else:
                    # Fresh batch
                    expiry_offset = int(rng.integers(int(shelf_life * 0.6), shelf_life + 5))
                    purchase_offset = int(rng.integers(-3, 1))

                # Normalize dates
                purchase_date = as_of_date + timedelta(days=purchase_offset)
                expiry_date = as_of_date + timedelta(days=expiry_offset)
                if expiry_date < purchase_date:
                    expiry_date = purchase_date + timedelta(days=max(1, shelf_life))

                # Quantity in stock
                base_qty = profile["base_demand"] * 0.4
                quantity = round(float(rng.uniform(base_qty * 0.3, base_qty * 1.8)), 2)

                # Milestone 1 compatible risk_level label assignment
                days_left = (expiry_date - as_of_date).days
                if days_left <= 3:
                    risk_level = "critical"
                elif days_left <= 7:
                    risk_level = "high"
                elif days_left <= 30:
                    risk_level = "medium"
                else:
                    risk_level = "low"

                inventory_records.append({
                    "name": f"{item_name} ({biz_id})",
                    "category": category,
                    "quantity": quantity,
                    "unit": unit,
                    "purchase_date": purchase_date.isoformat(),
                    "expiry_date": expiry_date.isoformat(),
                    "storage_location": storage,
                    "risk_level": risk_level,
                    "notes": f"Batch generated for {biz_id}. Shelf life: {shelf_life}d. Storage: {storage}.",
                })

    return pd.DataFrame(inventory_records)


def save_synthetic_data(
    output_dir: str | Path,
    days: int = 365,
    businesses: List[str] | None = None,
    seed: int = 42,
) -> Tuple[Path, Path]:
    """Saves both daily transactions and inventory snapshot CSVs to the specified directory."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    tx_df = generate_synthetic_transactions(days=days, businesses=businesses, seed=seed)
    inv_df = generate_inventory_snapshot(businesses=businesses, seed=seed)

    tx_file = out_path / "daily_transactions.csv"
    inv_file = out_path / "inventory_snapshot.csv"

    tx_df.to_csv(tx_file, index=False)
    inv_df.to_csv(inv_file, index=False)

    return tx_file, inv_file


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate realistic synthetic food transaction and inventory data.")
    parser.add_argument("--days", type=int, default=365, help="Number of historical days to simulate (default: 365)")
    parser.add_argument("--businesses", type=str, default="biz_001,biz_002,biz_003", help="Comma-separated business IDs")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility (default: 42)")
    parser.add_argument("--output-dir", type=str, default="data", help="Output directory for CSV files")

    args = parser.parse_args()
    biz_list = [b.strip() for b in args.businesses.split(",") if b.strip()]

    script_dir = Path(__file__).resolve().parent
    target_dir = (script_dir / ".." / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)

    print(f"Generating synthetic datasets ({args.days} days, businesses={biz_list}, seed={args.seed})...")
    tx_p, inv_p = save_synthetic_data(output_dir=target_dir, days=args.days, businesses=biz_list, seed=args.seed)
    print(f"[OK] Daily transactions saved to: {tx_p}")
    print(f"[OK] Inventory snapshot saved to: {inv_p}")
