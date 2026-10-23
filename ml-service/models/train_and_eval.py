"""
Model Training, Evaluation, and Comparison Pipeline.

Compares:
1. Naive Baseline (Lag-7 Seasonal Persistence)
2. Meta Prophet Forecaster (Additive/Multiplicative Seasonality)
3. PyTorch LSTM Recurrent Network (Rolling Lookback)

Computes MAE, RMSE, and MAPE across all categories on an out-of-sample test horizon.
Saves:
- `models/metrics.json` (Structured benchmark metrics)
- `reports/forecast_comparison_<category>.png` (Comparative visualization)
- `models/saved/` (Trained model weights and artifacts)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple
import matplotlib
matplotlib.use("Agg")  # Non-interactive headless backend for server/CLI
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from data.generate_data import CATEGORY_PROFILES
from data.preprocess import (
    clean_transactions,
    fill_missing_days,
    handle_outliers,
    prepare_category_series,
    time_based_split,
)
from models.baseline_prophet import ProphetForecaster
from models.lstm_model import LSTMForecaster


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes MAE, RMSE, and MAPE metrics safely."""
    y_true = np.asarray(y_true, dtype=np.float64)
    y_pred = np.asarray(y_pred, dtype=np.float64)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))

    # Safe MAPE avoiding division by 0
    denom = np.maximum(np.abs(y_true), 1.0)
    mape = float(np.mean(np.abs(y_true - y_pred) / denom) * 100.0)

    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2),
    }


def naive_seasonal_baseline(train_series: np.ndarray, horizon: int, lag: int = 7) -> np.ndarray:
    """
    Predicts using seasonal lag (same day of previous week).
    """
    preds = []
    history = list(train_series)
    for _ in range(horizon):
        pred_val = history[-lag] if len(history) >= lag else history[-1]
        preds.append(pred_val)
        history.append(pred_val)
    return np.array(preds, dtype=np.float64)


def train_and_evaluate_all(
    data_path: str | Path = "data/daily_transactions.csv",
    business_id: str = "biz_001",
    val_days: int = 30,
    test_days: int = 14,
    models_dir: str | Path = "models/saved",
    reports_dir: str | Path = "reports",
    metrics_path: str | Path = "models/metrics.json",
    categories: List[str] | None = None,
) -> Dict[str, Dict]:
    """
    Executes end-to-end training and evaluation for each category.
    """
    data_file = Path(data_path)
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found at {data_file}. Please run data generator first.")

    models_path = Path(models_dir)
    reports_path = Path(reports_dir)
    models_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading data from {data_file}...")
    raw_df = pd.read_csv(data_file)
    df = clean_transactions(raw_df)
    df = fill_missing_days(df)
    df = handle_outliers(df, columns=["sales_qty"])

    if categories is None:
        categories = list(CATEGORY_PROFILES.keys())

    all_metrics: Dict[str, Dict] = {}

    for cat in categories:
        print(f"\n==================================================")
        print(f"  Training and Evaluating Category: '{cat.upper()}'")
        print(f"==================================================")

        series_df = prepare_category_series(df, category=cat, business_id=business_id)
        train_df, val_df, test_df = time_based_split(series_df, val_days=val_days, test_days=test_days)

        train_val_df = pd.concat([train_df, val_df], ignore_index=True)
        y_test = test_df["y"].values
        horizon = len(y_test)

        # ----------------------------------------------------
        # 1. Naive Seasonal Baseline (Lag 7)
        # ----------------------------------------------------
        naive_preds = naive_seasonal_baseline(train_val_df["y"].values, horizon=horizon, lag=7)
        naive_metrics = compute_metrics(y_test, naive_preds)
        print(f" [Naive Baseline] MAE: {naive_metrics['mae']}, RMSE: {naive_metrics['rmse']}, MAPE: {naive_metrics['mape']}%")

        # ----------------------------------------------------
        # 2. Meta Prophet Baseline
        # ----------------------------------------------------
        prophet_forecaster = ProphetForecaster(category=cat)
        prophet_forecaster.fit(train_val_df)
        prophet_forecast_df = prophet_forecaster.predict_dates(test_df["ds"])
        prophet_preds = prophet_forecast_df["yhat"].values
        prophet_metrics = compute_metrics(y_test, prophet_preds)
        print(f" [Prophet Model ] MAE: {prophet_metrics['mae']}, RMSE: {prophet_metrics['rmse']}, MAPE: {prophet_metrics['mape']}%")

        prophet_model_file = models_path / f"prophet_{cat}.joblib"
        prophet_forecaster.save(prophet_model_file)

        # ----------------------------------------------------
        # 3. PyTorch LSTM Model
        # ----------------------------------------------------
        lstm_forecaster = LSTMForecaster(category=cat, lookback=14, hidden_dim=40, lr=0.005)
        lstm_forecaster.fit(train_val_df["y"].values, epochs=25, batch_size=16, verbose=False)
        lstm_preds = lstm_forecaster.predict(train_val_df["y"].values, horizon=horizon)
        lstm_metrics = compute_metrics(y_test, lstm_preds)
        print(f" [PyTorch LSTM  ] MAE: {lstm_metrics['mae']}, RMSE: {lstm_metrics['rmse']}, MAPE: {lstm_metrics['mape']}%")

        lstm_model_file = models_path / f"lstm_{cat}.pt"
        lstm_forecaster.save(lstm_model_file)

        # ----------------------------------------------------
        # 4. Generate Comparative Plot
        # ----------------------------------------------------
        plt.figure(figsize=(10, 4.5))
        dates = pd.to_datetime(test_df["ds"]).dt.strftime("%b %d")
        x_indices = np.arange(len(dates))

        plt.plot(x_indices, y_test, label="Actual Demand", color="#111827", linewidth=2.2, marker="o")
        plt.plot(x_indices, naive_preds, label="Naive (Lag-7)", color="#9CA3AF", linestyle="--", linewidth=1.5)
        plt.plot(x_indices, prophet_preds, label=f"Prophet (MAPE: {prophet_metrics['mape']}%)", color="#2563EB", linewidth=1.8)
        plt.plot(x_indices, lstm_preds, label=f"PyTorch LSTM (MAPE: {lstm_metrics['mape']}%)", color="#10B981", linewidth=1.8)

        plt.title(f"Demand Forecast vs Actual on Test Horizon: {cat.capitalize()}", fontsize=12, fontweight="bold")
        plt.xlabel("Test Date", fontsize=10)
        plt.ylabel(f"Demand Quantity ({CATEGORY_PROFILES.get(cat, {}).get('unit', 'qty')})", fontsize=10)
        plt.xticks(x_indices, dates, rotation=45)
        plt.grid(True, linestyle=":", alpha=0.6)
        plt.legend(frameon=True, loc="upper right")
        plt.tight_layout()

        plot_path = reports_path / f"forecast_comparison_{cat}.png"
        plt.savefig(plot_path, dpi=150)
        plt.close()

        all_metrics[cat] = {
            "test_days": horizon,
            "unit": CATEGORY_PROFILES.get(cat, {}).get("unit", "qty"),
            "models": {
                "naive": naive_metrics,
                "prophet": prophet_metrics,
                "lstm": lstm_metrics,
            },
            "best_model": "prophet" if prophet_metrics["rmse"] <= lstm_metrics["rmse"] else "lstm",
        }

    # Save summary metrics to json
    metrics_file = Path(metrics_path)
    metrics_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_file, "w", encoding="utf-8") as f:
        json.dump(all_metrics, f, indent=2)

    print(f"\n[OK] Metrics saved to: {metrics_file}")
    print(f"[OK] Forecast comparison plots saved to: {reports_path}")
    print(f"[OK] Trained models saved to: {models_path}")
    return all_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train and evaluate food demand forecasting models.")
    parser.add_argument("--data", type=str, default="data/daily_transactions.csv")
    parser.add_argument("--business-id", type=str, default="biz_001")
    parser.add_argument("--categories", type=str, default=None, help="Comma-separated category list")
    parser.add_argument("--test-days", type=int, default=14)

    args = parser.parse_args()
    selected_cats = [c.strip() for c in args.categories.split(",")] if args.categories else None

    train_and_evaluate_all(
        data_path=args.data,
        business_id=args.business_id,
        test_days=args.test_days,
        categories=selected_cats,
    )
