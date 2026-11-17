# FoodWasteAI – API Documentation

## 1. Overview & Authentication

FoodWasteAI provides two API interfaces:
1. **Django Platform Web Routes & JSON Endpoints (Port 8000)**
2. **FastAPI Machine Learning Microservice Endpoints (Port 8001)**

### Authentication Schemes
- **Django Endpoints:** Cookie-based session authentication with CSRF tokens on state-changing requests.
- **FastAPI Endpoints:** Header-based API key authentication via `X-API-Key`.
  ```http
  X-API-Key: dev-secret-key-food-waste-2026
  Content-Type: application/json
  ```

---

## 2. FastAPI Machine Learning Endpoints (Port 8001)

### 2.1 System Health
- **Endpoint:** `GET /health`
- **Authentication:** Public
- **Response:**
  ```json
  {
    "status": "healthy",
    "environment": "production",
    "version": "1.0.0",
    "timestamp": "2026-11-17T11:45:00.123456",
    "models_loaded": [
      "prophet_dairy.joblib",
      "lstm_produce.pt",
      "lstm_bakery.pt"
    ]
  }
  ```

### 2.2 Predict Future Demand
- **Endpoint:** `POST /predict/demand`
- **Authentication:** `X-API-Key`
- **Request Body:**
  ```json
  {
    "category": "dairy",
    "horizon_days": 7,
    "model_type": "best"
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "category": "dairy",
    "model_used": "prophet",
    "unit": "kg",
    "forecast": [
      {
        "date": "2026-11-18",
        "predicted_demand": 42.5,
        "lower_bound": 36.1,
        "upper_bound": 48.9
      },
      {
        "date": "2026-11-19",
        "predicted_demand": 44.8,
        "lower_bound": 38.0,
        "upper_bound": 51.2
      }
    ]
  }
  ```

### 2.3 Real-Time Spoilage Risk Scoring
- **Endpoint:** `POST /risk/score`
- **Authentication:** `X-API-Key`
- **Request Body:**
  ```json
  {
    "item_name": "Greek Yogurt 500g",
    "category": "dairy",
    "days_to_expiry": 2,
    "current_stock": 25.0,
    "forecast_demand": 10.0
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "item_name": "Greek Yogurt 500g",
    "category": "dairy",
    "risk_score": 75.0,
    "risk_level": "High",
    "surplus_qty": 15.0,
    "surplus_ratio": 0.6,
    "urgency_factor": 0.8,
    "action_recommendation": "Post 15.0 kg surplus immediately to nearby NGOs."
  }
  ```

### 2.4 Smart Replenishment Reorder Recommendation
- **Endpoint:** `POST /reorder/recommend`
- **Authentication:** `X-API-Key`
- **Request Body:**
  ```json
  {
    "category": "produce",
    "current_stock": 18.0,
    "lead_time_days": 2,
    "storage_capacity": 100.0
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "category": "produce",
    "recommended_order_qty": 32.5,
    "action": "ORDER_RECOMMENDED",
    "urgency": "NORMAL",
    "unit": "kg",
    "reasoning": "Current stock (18.0 kg) will be depleted within 1.4 days. Lead time is 2 days."
  }
  ```

---

## 3. Django Web Platform Routes (Port 8000)

| Path | Method | Access Role | Description |
|---|---|---|---|
| `/app/` | GET | Authenticated | Main Operations & AI Dashboard |
| `/app/accounts/login/` | GET, POST | Public | User authentication endpoint |
| `/app/accounts/register/` | GET, POST | Public | Account creation (business/ngo) |
| `/app/inventory/` | GET | Authenticated | Inventory listing & risk filters |
| `/app/inventory/add/` | GET, POST | Business, Admin | Manual inventory batch creation |
| `/app/inventory/<id>/edit/` | GET, POST | Business, Admin | Update existing inventory batch |
| `/app/inventory/<id>/delete/` | POST | Business, Admin | Delete inventory batch |
| `/app/inventory/import/` | GET, POST | Business, Admin | Bulk CSV batch upload |
| `/app/inventory/download-template/` | GET | Authenticated | Streams RFC-compliant CSV template |
| `/app/expiry-alerts/` | GET | Authenticated | Filtered view for critical batches |
| `/app/surplus/` | GET | Authenticated | Surplus food marketplace |
| `/app/surplus/add/` | GET, POST | Business, Admin | Post surplus package for donation |
| `/app/surplus/<id>/cancel/` | POST | Business, Admin | Cancel active surplus lot |
| `/app/ngo/` | GET | NGO, Admin | NGO Command Center & matches |
| `/app/ngo/requirements/` | GET | Authenticated | NGO requirements listing |
| `/app/ngo/requirements/add/` | GET, POST | NGO, Admin | Register community food need |
| `/app/ngo/requirements/<id>/status/` | POST | NGO, Admin | Update requirement (fulfilled/cancelled) |
| `/app/donations/` | GET | Authenticated | Donation allocation dispatch pipeline |
| `/app/donations/request/` | GET, POST | NGO, Admin | Claim surplus lot & receive PIN |
| `/app/donations/<id>/update/` | POST | Participants, Admin | Advance state machine & verify PIN |
| `/app/impact/` | GET | Authenticated | Real-time ESG environmental analytics |
| `/app/leaderboard/` | GET | Authenticated | Community gamification rankings |
| `/app/admin-panel/` | GET | Admin only | Administrative audit console |
| `/app/api/health/` | GET | Public | Health status JSON API |
