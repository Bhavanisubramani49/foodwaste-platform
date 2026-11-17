# FoodWasteAI – AI-Powered Food Waste Management & Redistribution Platform

> **AI-Powered Surplus Identification, Demand Forecasting & NGO Redistribution Optimization Platform**  
> *Fully Integrated Multi-Tier System: Django 5 Web Application · PostgreSQL Database · FastAPI ML Microservice (Prophet / PyTorch LSTM / Scikit-learn)*

---

## 📌 Project Overview

**FoodWasteAI** is a production-ready, full-stack platform designed to eliminate commercial food waste by combining predictive artificial intelligence with a real-time community redistribution marketplace.

The platform continuously monitors perishable commercial inventory, projects category-level consumer demand, detects imminent spoilage risks, and autonomously matches surplus food packages to nearby verified NGOs, relief kitchens, and food shelters through a secure, PIN-verified custody pipeline.

---

## 🚀 Complete Platform Capabilities (Milestones 1 – 4)

### 1. Operations & Inventory Management (Milestone 1)
- **Role-Based Portals:** Multi-tenant interface tailored for Commercial Businesses, Verified NGOs, and System Administrators.
- **Full Inventory Lifecycle:** Complete CRUD operations tracking food category, quantity, unit, storage location, purchase date, and expiry window.
- **Dynamic Risk Classification:** Linear decay velocity and shelf-life tracking flagging batches into `Low`, `Medium`, `High`, and `Critical (< 24h)` urgency tiers.
- **RFC-Compliant CSV Bulk Import:** Fast ingestion of batch data with row-level validation and downloadable standard templates.

### 2. Predictive AI & Machine Learning Microservice (Milestone 2)
- **FastAPI Microservice (Port 8001):** High-throughput asynchronous prediction engine secured with `X-API-Key` authentication.
- **Category-Adaptive Demand Forecasting:** Dual time-series models (Meta Prophet & 2-Layer Deep PyTorch LSTM) trained on commercial transaction histories.
- **Food Spoilage Risk Classifier:** 87.3% accurate Random Forest model evaluating spoilage risk levels based on temperature, shelf-life, and demand.
- **Smart Replenishment Recommender:** Automated reorder quantity calculation factoring in vendor lead-time and safety stock buffers ($\beta = 0.20\text{--}0.30$).
- **Microsecond Circuit Breaker:** Django integration client seamlessly falls back to heuristic engines if the microservice is offline, guaranteeing zero UI downtime.

### 3. Surplus Food Redistribution & NGO Logistics (Milestone 3)
- **Real-Time Surplus Marketplace:** Split-view layout featuring active surplus lots, live 45-minute countdown timers, and simulated geographic mapping.
- **NGO Community Requirements Registry:** NGOs register nutritional needs with category, required volume, urgency tier, and neighborhood delivery constraints.
- **Multi-Criteria Smart Matching Engine:** Automated scoring (Category 40%, Quantity 30%, Urgency 20%, Location 10%) providing ranked match recommendations.
- **Atomic Concurrency Protection:** Thread-safe claim reservations powered by database row locking (`select_for_update`) preventing double-claims.
- **Verified Handoff & Security PIN:** Auto-generated `#RC-XXXX` collection codes validated upon driver arrival at the kitchen.
- **Live Environmental & ESG Impact Dashboard:** Real-time metrics calculating meals served ($2.22 \times \text{kg}$), $\text{CO}_2\text{e}$ emissions prevented ($2.5 \times \text{kg}$), and landfill space saved ($500 \text{ kg/m}^3$).

### 4. Quality Assurance, Optimization & Delivery (Milestone 4)
- **91 Automated Tests Passing (100%):** 60 Django unit/E2E tests and 31 FastAPI pytest scenarios.
- **High-Performance Query Latencies:** Under 50ms p50 response times across all primary views.
- **Comprehensive Technical Documentation:** 10 detailed technical documents located in `docs/`.

---

## 🛠️ Technology Stack

| Tier | Technologies |
|---|---|
| **Web Platform** | Python 3.13, Django 5.x, Django Templates, Bootstrap 5.3.3, Chart.js 4.4.2 |
| **Relational Database** | PostgreSQL 16 (`foodwaste_db`) / SQLite (test fallback) |
| **ML Microservice** | FastAPI, Uvicorn, Pydantic, APScheduler |
| **Forecasting Models** | Meta Prophet, PyTorch LSTM (Deep Recurrent Neural Network) |
| **Classification Models**| Scikit-learn Random Forest Classifier |
| **Data Processing** | Pandas, NumPy, Joblib |

---

## 📁 Repository Structure

```text
foodwaste_platform_v2/
├── config/                     # Core Django project configuration & database settings
├── core/                       # UserProfile, authentication, and gamification models
├── docs/                       # Complete Milestone 4 Technical Documentation Suite
│   ├── PROJECT_OVERVIEW.md     # Executive summary & platform capabilities
│   ├── SYSTEM_ARCHITECTURE.md  # System diagrams, data flow & microservice integration
│   ├── DATABASE_DESIGN.md      # Normalized database schemas, ER diagrams & locking
│   ├── API_DOCUMENTATION.md    # RESTful & microservice endpoint reference
│   ├── ML_MODEL_EVALUATION.md  # Detailed metrics (MAE, RMSE, MAPE, Accuracy, F1)
│   ├── TESTING_REPORT.md       # Quality assurance report covering all 91 test cases
│   ├── SECURITY_REVIEW.md      # RBAC, CSRF, input validation & vulnerability audit
│   ├── DEPLOYMENT_GUIDE.md     # Installation, database setup & startup instructions
│   ├── USER_GUIDE.md           # Operational manual for Businesses, NGOs, and Admins
│   └── KNOWN_LIMITATIONS.md    # Boundary conditions, edge cases & future roadmap
├── food_management/            # Primary application: Inventory, Surplus, NGOs, Claims, Impact
│   ├── models.py               # InventoryItem, SurplusListing, NGORequirement, DonationRequest
│   ├── views.py                # Dashboard, CRUD views, state machine handlers, analytics
│   ├── matching.py             # Smart Matching Engine algorithm (100-pt scoring)
│   ├── ml_client.py            # HTTP microservice client with automated circuit-breaker
│   ├── services.py             # Scientific impact calculations & gamification rankings
│   └── templates/              # Production-grade Bootstrap 5 / Chart.js templates
├── ml-service/                 # FastAPI Predictive ML Microservice (Port 8001)
│   ├── api/                    # FastAPI routers, schemas, and background scheduler
│   ├── models/                 # Prophet and PyTorch LSTM model definitions and saved weights
│   ├── reorder/                # Inventory replenishment optimization engine
│   ├── risk/                   # Real-time spoilage risk scoring algorithms
│   └── tests/                  # Pytest automated test suite (31 tests)
├── ml_service/                 # Scikit-learn Random Forest food waste classification pipeline
├── static/                     # Design tokens, custom CSS stylesheet, and JavaScript
├── manage.py                   # Django CLI management executable
└── requirements.txt            # Python dependencies
```

---

## ⚡ Quick Start Guide

### 1. Configure Environment
```bash
cp .env.example .env
```

### 2. Apply Database Migrations
```bash
python manage.py migrate
```

### 3. Start FastAPI Machine Learning Microservice (Port 8001)
```bash
cd ml-service
uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
```

### 4. Start Django Web Platform (Port 8000)
```bash
python manage.py runserver 127.0.0.1:8000
```
Open **`http://127.0.0.1:8000/app/`** in your browser.

---

## 🧪 Running Automated Tests

```bash
# Run all 60 Django Unit & End-to-End Tests
python manage.py test --noinput

# Run all 31 FastAPI Microservice Tests
cd ml-service
pytest
```

---

## 📖 Complete Documentation
For in-depth architectural diagrams, database specifications, API schemas, model evaluations, and guides, refer to the files in the [`docs/`](docs/) directory.
