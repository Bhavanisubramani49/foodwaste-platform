# FoodWasteAI – System Architecture

## 1. Architectural Overview

FoodWasteAI implements a decoupled, modern multi-tier architecture consisting of:
1. **Presentation & Application Layer (Django):** Handles server-side template rendering, user sessions, role-based access control (RBAC), and transaction-safe domain workflows.
2. **Predictive Microservice Layer (FastAPI):** Dedicated high-concurrency microservice executing ML inference for demand forecasting (Prophet, PyTorch LSTM), spoilage risk scoring, and automated reorder replenishment.
3. **Data & Storage Layer (PostgreSQL):** Stores relational business profiles, inventory batches, surplus lots, NGO requirements, and donation lifecycle states with full ACID transaction guarantees.
4. **Resilient Inter-Service Integration:** Standard-library HTTP integration client with an automated circuit-breaker pattern ensuring uninterrupted operation if the ML service is offline.

```
                              USER BROWSERS & CLIENTS
                         (Desktop, Tablet, Mobile Devices)
                                        │
                                        │ HTTPS / HTTP
                                        ▼
                     +---------------------------------------+
                     |         Django 5 Application          |
                     |             (Port 8000)               |
                     |                                       |
                     | - Template Engine (Bootstrap/Chart.js)|
                     | - Session Auth & RBAC (access.py)     |
                     | - Inventory & Surplus Logic           |
                     | - Smart Matching Engine (matching.py) |
                     | - Atomic Claims (select_for_update)   |
                     | - Impact Services (services.py)       |
                     | - ML Client (ml_client.py)            |
                     +-------------------+-------------------+
                                         │
                   +---------------------+---------------------+
                   │ Internal HTTP / API Key                   │ Django ORM / SQL
                   ▼                                           ▼
+------------------------------------+      +------------------------------------+
|        FastAPI ML Engine           |      |        PostgreSQL Database         |
|           (Port 8001)              |      |            (Port 5432)             |
|                                    |      |                                    |
| - POST /predict/demand (Prophet/   |      | - auth_user & core_userprofile     |
|   PyTorch LSTM)                    |      | - food_management_inventoryitem    |
| - POST /risk/score (Decay Velocity)|      | - food_management_surpluslisting   |
| - POST /reorder/recommend          |      | - food_management_ngorequirement   |
| - GET /health & /models/metrics    |      | - food_management_donationrequest  |
+------------------+-----------------+      +------------------------------------+
                   │
                   ▼
     +---------------------------+
     |   Trained Model Weights   |
     |                           |
     | - prophet_{category}.joblib|
     | - lstm_{category}.pt      |
     | - waste_level_model.joblib|
     | - metrics.json            |
     +---------------------------+
```

---

## 2. Core Subsystems

### 2.1 Django Application Layer (`food_management`)
- **`access.py`:** Role enforcement module (`role_required` decorator). Intercepts requests, validates user profile roles (`business`, `ngo`, `admin`), and redirects unauthenticated or unauthorized users safely.
- **`models.py`:** Contains core domain entities:
  - `InventoryItem`: Tracks batch shelf-life, quantity, storage location, purchase date, and expiry date.
  - `SurplusListing`: Represents commercial excess available for immediate community redistribution.
  - `NGORequirement`: Tracks verified NGO nutritional needs, quantity required, urgency tier, and location.
  - `DonationRequest`: Manages atomic claim allocations, pickup scheduling, and verification PINs.
- **`matching.py`:** Multi-criteria weighted algorithm executing four-factor scoring (Category 40%, Quantity 30%, Expiry Urgency 20%, Location 10%) to rank surplus lots against active NGO requirements.
- **`services.py`:** Computes environmental impact analytics, gamification points, community leaderboard rankings, and heuristic waste risks.
- **`ml_client.py`:** Production HTTP client interfacing with FastAPI. Incorporates an automatic circuit-breaker:
  - Default connection timeout: `1.5s`
  - Circuit cooldown window: `15.0s`
  - Fallback: Transparently switches to heuristic calculations if FastAPI is unreachable.

### 2.2 FastAPI Machine Learning Service (`ml-service`)
- **Framework:** FastAPI with Uvicorn ASGI runner.
- **Authentication:** `X-API-Key` header verification.
- **Background Worker:** APScheduler running scheduled multi-tenant inventory risk evaluations.
- **Predictive Pipelines:**
  - `ProphetForecaster`: Additive time-series model capturing weekly seasonality for demand prediction.
  - `LSTMForecaster`: PyTorch deep recurrent neural network (2 LSTM layers + dropout + dense linear head) for non-linear temporal forecasting.
  - `Optimizer`: Dynamic inventory replenishment logic computing safety stock and reorder quantities.

---

## 3. Data Flow Diagram: End-to-End Operational Lifecycle

```
[Commercial Business]                [FoodWasteAI Platform]                    [Verified NGO]
        │                                       │                                     │
        │ 1. Log Inventory Batch                │                                     │
        ├──────────────────────────────────────>│                                     │
        │                                       │ 2. Spoilage Prediction & Risk Alert │
        │                                       ├────────────────────────────────────>│
        │ 3. Post Surplus Listing               │                                     │
        ├──────────────────────────────────────>│                                     │
        │                                       │ 4. Smart Matching Engine            │
        │                                       │    Evaluates Compatibility (0-100%) │
        │                                       │                                     │
        │                                       │ 5. Notification & Match Display     │
        │                                       │────────────────────────────────────>│
        │                                       │                                     │
        │                                       │ 6. Submit Claim & Lock Allocation   │
        │                                       │<────────────────────────────────────┤
        │ 7. Review & Approve Claim             │                                     │
        ├──────────────────────────────────────>│ 8. Generate Pickup PIN (#RC-XXXX)   │
        │                                       │────────────────────────────────────>│
        │                                       │                                     │
        │                                       │ 9. Driver Arrives with PIN          │
        │ 10. Enter Driver PIN & Verify Handoff │<────────────────────────────────────┤
        ├──────────────────────────────────────>│                                     │
        │                                       │ 11. Complete Status: 'collected'    │
        │                                       │     Update Recovery Telemetry &     │
        │                                       │     Award Community Points          │
        ▼                                       ▼                                     ▼
```
