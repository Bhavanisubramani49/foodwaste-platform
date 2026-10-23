"""
Unit tests for Step 2: Forecasting models (Prophet, PyTorch LSTM, metrics).
"""

from datetime import date, timedelta
import numpy as np
import pandas as pd
import pytest

from models.baseline_prophet import ProphetForecaster
from models.lstm_model import LSTMForecaster
from models.train_and_eval import compute_metrics, naive_seasonal_baseline


def test_compute_metrics():
    y_true = np.array([10.0, 20.0, 30.0])
    y_pred = np.array([12.0, 18.0, 33.0])

    metrics = compute_metrics(y_true, y_pred)
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics

    # MAE should be (2 + 2 + 3) / 3 = 2.33
    assert abs(metrics["mae"] - 2.33) < 0.1
    # Check MAPE is calculated
    assert metrics["mape"] > 0.0


def test_naive_seasonal_baseline():
    # 14 days of repeating weekly pattern
    pattern = [10, 12, 14, 16, 18, 25, 22] * 2
    preds = naive_seasonal_baseline(np.array(pattern), horizon=7, lag=7)
    assert len(preds) == 7
    # Should equal the last 7 values
    np.testing.assert_array_equal(preds, pattern[-7:])


def test_lstm_forecaster_train_and_predict():
    # Generate 60 days of synthetic sine demand
    t = np.linspace(0, 4 * np.pi, 60)
    series = 40.0 + 10.0 * np.sin(t) + np.random.normal(0, 1, 60)

    forecaster = LSTMForecaster(category="bakery", lookback=10, hidden_dim=16, lr=0.01)
    forecaster.fit(series, epochs=10, batch_size=8, verbose=False)

    horizon = 7
    predictions = forecaster.predict(series, horizon=horizon)

    assert isinstance(predictions, np.ndarray)
    assert len(predictions) == horizon
    # Demand must be non-negative
    assert (predictions >= 0.0).all()


def test_prophet_forecaster_train_and_predict():
    # Create minimal 40-day time series
    start = date(2026, 1, 1)
    dates = [start + timedelta(days=i) for i in range(40)]
    df = pd.DataFrame({
        "ds": pd.to_datetime(dates),
        "y": [30.0 + (i % 7) * 4.0 for i in range(40)],
    })

    forecaster = ProphetForecaster(category="dairy", weekly_seasonality=True, yearly_seasonality=False)
    forecaster.fit(df)

    forecast_df = forecaster.predict(horizon=7)
    assert len(forecast_df) == 7
    for col in ["ds", "yhat", "yhat_lower", "yhat_upper"]:
        assert col in forecast_df.columns
    assert (forecast_df["yhat"] >= 0.0).all()
