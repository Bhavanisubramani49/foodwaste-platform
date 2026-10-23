"""
Prophet Forecasting Baseline for Category Food Demand.

Implements daily, weekly, and yearly seasonality decomposition
with prediction intervals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from prophet import Prophet


class ProphetForecaster:
    """
    Wrapper for Facebook/Meta Prophet model tuned for perishable inventory demand.
    """

    def __init__(
        self,
        category: str,
        weekly_seasonality: bool = True,
        yearly_seasonality: bool = True,
        changepoint_prior_scale: float = 0.05,
    ):
        self.category = category.lower()
        self.weekly_seasonality = weekly_seasonality
        self.yearly_seasonality = yearly_seasonality
        self.changepoint_prior_scale = changepoint_prior_scale
        self.model: Optional[Prophet] = None

    def fit(self, train_df: pd.DataFrame) -> ProphetForecaster:
        """
        Fits Prophet on a dataframe containing ['ds', 'y'].
        """
        df = train_df[["ds", "y"]].copy()
        df["ds"] = pd.to_datetime(df["ds"])
        df["y"] = df["y"].astype(float)

        self.model = Prophet(
            weekly_seasonality=self.weekly_seasonality,
            yearly_seasonality=self.yearly_seasonality,
            daily_seasonality=False,
            changepoint_prior_scale=self.changepoint_prior_scale,
            interval_width=0.90,
        )
        # Suppress cmdstanpy verbose logs
        self.model.fit(df)
        return self

    def predict(self, horizon: int = 14) -> pd.DataFrame:
        """
        Generates forecast for the next `horizon` days.
        Returns DataFrame with ['ds', 'yhat', 'yhat_lower', 'yhat_upper'].
        """
        if self.model is None:
            raise RuntimeError(f"Prophet model for '{self.category}' has not been trained yet.")

        future = self.model.make_future_dataframe(periods=horizon, freq="D", include_history=False)
        forecast = self.model.predict(future)

        # Enforce non-negative demand bounds
        forecast["yhat"] = forecast["yhat"].clip(lower=0.0)
        forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0.0)
        forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0.0)

        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    def predict_dates(self, target_dates: pd.DatetimeIndex | pd.Series) -> pd.DataFrame:
        """
        Predicts on specific target dates (used for test evaluation).
        """
        if self.model is None:
            raise RuntimeError(f"Prophet model for '{self.category}' has not been trained yet.")

        future = pd.DataFrame({"ds": pd.to_datetime(target_dates)})
        forecast = self.model.predict(future)
        forecast["yhat"] = forecast["yhat"].clip(lower=0.0)
        forecast["yhat_lower"] = forecast["yhat_lower"].clip(lower=0.0)
        forecast["yhat_upper"] = forecast["yhat_upper"].clip(lower=0.0)
        return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]]

    def save(self, filepath: str | Path) -> None:
        """Saves model to disk using joblib."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)

    @staticmethod
    def load(filepath: str | Path) -> ProphetForecaster:
        """Loads a saved ProphetForecaster instance."""
        return joblib.load(filepath)
