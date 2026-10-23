"""
PyTorch LSTM Demand Forecaster for Category Food Demand.

Implements a configurable LSTM sequence model trained on rolling sliding windows.
Features:
- Configurable lookback window and horizon
- Normalized input scaling (MinMaxScaler)
- Multi-step recursive rollout for arbitrary prediction horizons
- Fast CPU-optimized execution
- Native PyTorch checkpointing + scaler serialization
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import joblib
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import DataLoader, TensorDataset

from data.preprocess import create_sliding_windows


class _LSTMNet(nn.Module):
    """Internal PyTorch recurrent architecture."""

    def __init__(
        self,
        input_size: int = 1,
        hidden_dim: int = 40,
        num_layers: int = 1,
        output_dim: int = 1,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc = nn.Linear(hidden_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, input_size)
        out, _ = self.lstm(x)
        # Take the output of the last time step
        last_out = out[:, -1, :]
        pred = self.fc(last_out)
        return pred


class LSTMForecaster:
    """
    High-level PyTorch LSTM forecaster with auto-scaling and rollout forecasting.
    """

    def __init__(
        self,
        category: str,
        lookback: int = 14,
        hidden_dim: int = 40,
        num_layers: int = 1,
        lr: float = 0.005,
    ):
        self.category = category.lower()
        self.lookback = lookback
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lr = lr

        self.scaler = MinMaxScaler(feature_range=(0.0, 1.0))
        self.model: Optional[_LSTMNet] = None
        self.device = torch.device("cpu")  # Designed to run fast locally on CPU

    def fit(
        self,
        train_values: np.ndarray,
        epochs: int = 25,
        batch_size: int = 16,
        verbose: bool = False,
    ) -> LSTMForecaster:
        """
        Trains the LSTM model on 1D series of historical values.
        """
        values = np.asarray(train_values, dtype=np.float32).reshape(-1, 1)
        scaled_values = self.scaler.fit_transform(values).flatten()

        X, y = create_sliding_windows(scaled_values, lookback=self.lookback, horizon=1)
        if len(X) == 0:
            raise ValueError(f"Insufficient historical data ({len(values)} points) for lookback={self.lookback}")

        X_tensor = torch.tensor(X, dtype=torch.float32, device=self.device)
        y_tensor = torch.tensor(y, dtype=torch.float32, device=self.device)

        dataset = TensorDataset(X_tensor, y_tensor)
        loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

        self.model = _LSTMNet(
            input_size=1,
            hidden_dim=self.hidden_dim,
            num_layers=self.num_layers,
            output_dim=1,
        ).to(self.device)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion = nn.MSELoss()

        self.model.train()
        for epoch in range(epochs):
            total_loss = 0.0
            for batch_x, batch_y in loader:
                optimizer.zero_grad()
                preds = self.model(batch_x)
                loss = criterion(preds, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

            if verbose and (epoch + 1) % 5 == 0:
                print(f"[{self.category}] Epoch {epoch+1}/{epochs} - Loss: {total_loss / len(loader):.5f}")

        return self

    def predict(self, recent_history: np.ndarray, horizon: int = 14) -> np.ndarray:
        """
        Multi-step recursive rollout forecasting:
        Uses the last `lookback` observations, predicts step t+1, rolls window forward,
        and repeats up to `horizon` steps.
        """
        if self.model is None:
            raise RuntimeError(f"LSTM model for '{self.category}' has not been trained yet.")

        history = np.asarray(recent_history, dtype=np.float32).flatten()
        if len(history) < self.lookback:
            raise ValueError(f"Recent history must have at least {self.lookback} points, got {len(history)}")

        # Use the most recent lookback elements
        curr_window = history[-self.lookback :].reshape(-1, 1)
        scaled_window = self.scaler.transform(curr_window).flatten().tolist()

        self.model.eval()
        predictions_scaled = []

        with torch.no_grad():
            for _ in range(horizon):
                x_input = np.array(scaled_window[-self.lookback :], dtype=np.float32).reshape(1, self.lookback, 1)
                x_tensor = torch.tensor(x_input, dtype=torch.float32, device=self.device)
                pred_scaled = self.model(x_tensor).cpu().numpy()[0, 0]

                predictions_scaled.append(pred_scaled)
                scaled_window.append(pred_scaled)

        # Invert scaling
        pred_scaled_arr = np.array(predictions_scaled).reshape(-1, 1)
        raw_preds = self.scaler.inverse_transform(pred_scaled_arr).flatten()

        # Enforce non-negative demand
        return np.clip(raw_preds, a_min=0.0, a_max=None)

    def save(self, filepath: str | Path) -> None:
        """Saves model weights and scaler to disk."""
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "category": self.category,
            "lookback": self.lookback,
            "hidden_dim": self.hidden_dim,
            "num_layers": self.num_layers,
            "lr": self.lr,
            "state_dict": self.model.state_dict() if self.model else None,
            "scaler": self.scaler,
        }
        torch.save(payload, path)

    @classmethod
    def load(cls, filepath: str | Path) -> LSTMForecaster:
        """Loads a saved LSTMForecaster from disk."""
        path = Path(filepath)
        payload = torch.load(path, map_location="cpu", weights_only=False)

        instance = cls(
            category=payload["category"],
            lookback=payload["lookback"],
            hidden_dim=payload["hidden_dim"],
            num_layers=payload["num_layers"],
            lr=payload["lr"],
        )
        instance.scaler = payload["scaler"]

        if payload["state_dict"] is not None:
            instance.model = _LSTMNet(
                input_size=1,
                hidden_dim=instance.hidden_dim,
                num_layers=instance.num_layers,
                output_dim=1,
            )
            instance.model.load_state_dict(payload["state_dict"])
            instance.model.eval()

        return instance
