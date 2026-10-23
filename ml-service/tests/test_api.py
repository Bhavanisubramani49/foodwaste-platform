"""
Integration tests for FastAPI ML Service endpoints.
"""

from fastapi.testclient import TestClient
import pytest

from api.config import settings
from api.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-API-Key": settings.API_KEY}


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "models_loaded" in data


def test_api_key_authentication_enforcement():
    # Missing API Key
    resp_missing = client.post("/predict/demand", json={"category": "dairy", "horizon_days": 7})
    assert resp_missing.status_code == 401
    assert "Missing 'X-API-Key'" in resp_missing.json()["detail"]

    # Invalid API Key
    resp_invalid = client.post(
        "/predict/demand",
        headers={"X-API-Key": "wrong-key"},
        json={"category": "dairy", "horizon_days": 7},
    )
    assert resp_invalid.status_code == 401
    assert "Invalid API Key" in resp_invalid.json()["detail"]


def test_predict_demand_endpoint():
    payload = {
        "category": "dairy",
        "horizon_days": 7,
        "model_type": "prophet",
    }
    response = client.post("/predict/demand", headers=AUTH_HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "dairy"
    assert data["horizon_days"] == 7
    assert len(data["forecast"]) == 7
    assert data["total_projected_demand"] > 0


def test_risk_score_endpoint():
    # Normal item
    payload = {
        "item_name": "Greek Yogurt",
        "category": "dairy",
        "days_to_expiry": 3,
        "current_stock": 40.0,
        "forecast_demand": 10.0,
    }
    response = client.post("/risk/score", headers=AUTH_HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["item_name"] == "Greek Yogurt"
    assert data["risk_score"] > 50.0
    assert data["risk_level"] in ["High", "Critical"]
    assert data["surplus_qty"] == 30.0

    # Expired item edge case
    expired_payload = {
        "days_to_expiry": -1,
        "current_stock": 20.0,
        "forecast_demand": 5.0,
    }
    exp_resp = client.post("/risk/score", headers=AUTH_HEADERS, json=expired_payload)
    assert exp_resp.status_code == 200
    exp_data = exp_resp.json()
    assert exp_data["risk_score"] == 100.0
    assert exp_data["risk_level"] == "Critical"


def test_batch_risk_endpoint():
    response = client.get("/risk/batch/biz_001", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["business_id"] == "biz_001"
    assert "total_items" in data
    assert "average_risk_score" in data
    assert isinstance(data["items"], list)


def test_reorder_recommend_endpoint():
    payload = {
        "category": "dairy",
        "current_stock": 15.0,
        "forecast_lead_demand": 50.0,
        "lead_time_days": 2,
        "storage_capacity": 150.0,
        "safety_stock": 10.0,
    }
    response = client.post("/reorder/recommend", headers=AUTH_HEADERS, json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == "dairy"
    assert data["recommended_order_qty"] == 45.0  # (50 + 10) - 15 = 45
    assert data["status"] == "ORDER_RECOMMENDED"
    assert "reasoning" in data


def test_models_metrics_endpoint():
    response = client.get("/models/metrics", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    # Should include evaluated categories
    for cat in ["dairy", "bakery", "produce", "meat", "packaged", "beverages"]:
        assert cat in data
        assert "models" in data[cat]
        assert "naive" in data[cat]["models"]
