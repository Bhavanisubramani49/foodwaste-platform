# FoodWasteAI – Deployment & Operation Guide

## 1. System Requirements

### Hardware Prerequisites
- **CPU:** Dual-core 2.0 GHz or higher (Quad-core recommended for LSTM training).
- **RAM:** Minimum 4 GB RAM (8 GB recommended for Prophet & PyTorch model caching).
- **Disk:** 5 GB free storage.

### Software Prerequisites
- **Operating System:** Windows 10/11, Ubuntu 22.04 LTS+, or macOS 13+.
- **Python:** Python 3.10 to 3.13.
- **Database:** PostgreSQL 14+ (or local SQLite for zero-config evaluation).

---

## 2. Environment Configuration

1. Clone or navigate to the project directory:
   ```bash
   cd C:\Users\Karunya\Downloads\foodwaste_platform_v2
   ```

2. Copy the example environment template:
   ```bash
   cp .env.example .env
   ```

3. Configure your local `.env` file (adjust database credentials as appropriate):
   ```ini
   # Django Core Settings
   DEBUG=True
   SECRET_KEY=local-dev-secret-key-foodwasteai-2026-change-in-prod
   ALLOWED_HOSTS=localhost,127.0.0.1

   # PostgreSQL Database Configuration
   DB_NAME=foodwaste_db
   DB_USER=postgres
   DB_PASSWORD=your_postgres_password
   DB_HOST=localhost
   DB_PORT=5432

   # ML Microservice Integration
   ML_SERVICE_URL=http://127.0.0.1:8001
   ML_SERVICE_API_KEY=dev-secret-key-food-waste-2026
   ML_SERVICE_TIMEOUT=1.5
   ```

---

## 3. Database Initialization

1. Ensure the PostgreSQL service is active and the target database exists:
   ```sql
   CREATE DATABASE foodwaste_db;
   ```

2. Apply Django database migrations:
   ```bash
   python manage.py migrate
   ```

3. Create an initial administrative superuser:
   ```bash
   python manage.py createsuperuser
   ```

---

## 4. Starting the Services

FoodWasteAI runs as two integrated microservices:
- **Port 8000:** Django Web Platform & Operations Portal
- **Port 8001:** FastAPI Predictive ML Microservice

### Terminal 1: Start FastAPI ML Microservice (Port 8001)
```bash
cd C:\Users\Karunya\Downloads\foodwaste_platform_v2\ml-service
uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
```
*Verify running:* Open `http://127.0.0.1:8001/health` in your browser.

### Terminal 2: Start Django Web Platform (Port 8000)
```bash
cd C:\Users\Karunya\Downloads\foodwaste_platform_v2
python manage.py runserver 127.0.0.1:8000
```
*Verify running:* Open `http://127.0.0.1:8000/app/` in your browser.

---

## 5. Running the Automated Test Suites

### Execute Complete Django Test Suite (60 tests)
```bash
python manage.py test --noinput
```

### Execute Dedicated End-to-End Workflow Suite (16 tests)
```bash
python manage.py test food_management.test_e2e_platform --noinput
```

### Execute FastAPI Pytest Suite (31 tests)
```bash
cd ml-service
pytest
```

---

## 6. End-to-End Demonstration Script

Follow these steps to demonstrate the complete platform workflow:

1. **Business Inventory Logging:**
   - Log into `/app/accounts/login/` with a business account (e.g. `bistro_owner`).
   - Navigate to `/app/inventory/add/` and log a fresh batch (e.g. `Paneer Curry, 20 kg, Expiry: +2 days`).
   - Observe the batch appearing on the Dashboard with risk level badges.
2. **AI Waste Prediction & Reorder Recommendation:**
   - View `/app/` to observe predicted waste volume (~kg) and confidence corridors.
   - Inspect the AI Reorder card recommending replenishment order quantities based on lead-time demand.
3. **Surplus Marketplace Creation:**
   - Click `+ Post Surplus Lot` on the dashboard or navigate to `/app/surplus/add/`.
   - Post an available surplus package (e.g. `20 kg, Available Today`).
   - View `/app/surplus/` to see the live split-view map and countdown clock.
4. **NGO Demand Registration:**
   - Log in as an NGO user (e.g. `shelter_ngo`).
   - Navigate to `/app/ngo/requirements/add/` and register community need (`Cooked Meals, 20 kg, Urgent`).
5. **Smart Matching & Claiming:**
   - Navigate to `/app/ngo/` (NGO Command Center) to view top compatible allocations.
   - Click `Claim Lot` $\to$ Confirm claim for 20 kg.
   - Receive the unique pickup verification code (e.g. `#RC-4821`).
6. **Physical Collection & PIN Handoff:**
   - Log back in as the donor business and navigate to `/app/donations/`.
   - Select status `Collected` and enter driver's PIN `RC-4821`.
   - System confirms verified handoff, marks status `Collected`, and awards gamification points.
7. **Environmental Impact Verification:**
   - Navigate to `/app/impact/` to observe real-time updated environmental metrics: meals served ($+44$), $\text{CO}_2$ avoided ($+50\text{ kg}$), and landfill space saved.
