# AI-Powered Food Waste Prediction & Inventory Optimization Service

A production-grade microservice built with **FastAPI**, **PyTorch**, and **Meta Prophet** for the Infosys Springboard Project:
> *"AI-Powered Food Waste Management Platform for Surplus Identification and Redistribution Optimization"*

---

## 1. Features

- **Multi-Category Demand Forecasting**: Prophet & PyTorch LSTM models per product category (`dairy`, `bakery`, `produce`, `meat`, `packaged`, `beverages`).
- **Benchmark Evaluation**: Automated comparison against a Naive Seasonal Baseline (Lag-7) with MAE, RMSE, and MAPE.
- **Calibrated Waste-Risk Engine**: 0–100 risk scoring formula combining days to expiry, current inventory, and forecast demand over remaining shelf life.
- **Smart Replenishment Recommendations**: Order optimization adhering to lead-time demand, statistical safety stock, perishable shelf-life bounds, and storage capacity limits.
- **Scheduled Batch Intelligence**: Built-in APScheduler daily job for scheduled tenant-wide inventory risk audits.
- **Security & Integrity**: API-Key header authentication (`X-API-Key`) and configurable CORS.
- **Resilient Fallback Mode**: Standard-library HTTP client in Django (`MLServiceClient`) with automatic fallback to Milestone 1 heuristic rules when the microservice is offline.

---

## 2. Directory Structure

```text
ml-service/
├── .env                  # Local environment configuration
├── .env.example          # Sample environment variables
├── requirements.txt      # Python dependencies (fastapi, torch, prophet, apscheduler, etc.)
├── Dockerfile            # Container deployment image
├── README.md             # Run instructions and API docs
├── MILESTONE2_REPORT.md  # Comprehensive project milestone report
├── api/
│   ├── config.py         # Pydantic Settings
│   ├── main.py           # FastAPI application & route definitions
│   ├── schemas.py        # Pydantic request/response validation schemas
│   └── scheduler.py      # APScheduler daily background job
├── data/
│   ├── generate_data.py  # Realistic multi-tenant synthetic data generator
│   ├── preprocess.py     # Cleaning, missing-day imputation, temporal split
│   ├── daily_transactions.csv
│   └── inventory_snapshot.csv
├── models/
│   ├── baseline_prophet.py # Meta Prophet baseline model
│   ├── lstm_model.py       # PyTorch recurrent neural network (weights_only=False for PyTorch 2.6+)
│   ├── train_and_eval.py   # Training, metrics evaluation & plotting
│   ├── metrics.json        # Evaluation metrics comparison store
│   └── saved/              # Serialized weights (.joblib, .pt)
├── reports/              # Plots and batch prediction outputs
│   └── batch_predictions/
├── risk/
│   └── risk_scorer.py    # 0-100 waste risk scoring engine
├── reorder/
│   └── optimizer.py      # Replenishment optimizer & reasoning generator
└── tests/                # Automated pytest suite (31 tests passing)
```

---

## 3. Local Setup & Execution

### Prerequisites
- Python 3.10 to 3.13
- Core dependencies: `fastapi`, `uvicorn`, `torch>=2.2.0`, `prophet>=1.1.5`, `apscheduler>=3.10.0`, `pandas`, `scikit-learn`

### Installation
```bash
# Navigate to ml-service
cd ml-service

# Install dependencies
pip install -r requirements.txt
```

> **Note on Windows Dependencies**:
> - `prophet` uses `cmdstanpy`. A prebuilt binary wheel (`prophet-1.5.0`) is installed in the Python environment.
> - `torch.load` in PyTorch 2.6+ defaults to `weights_only=True`. The `LSTMForecaster.load()` method explicitly passes `weights_only=False` to safely load the serialised `MinMaxScaler` object.

### Run Step-by-Step

```bash
# 1. Generate 365-day realistic synthetic data
python -m data.generate_data --days 365 --businesses biz_001,biz_002,biz_003 --seed 42

# 2. Train models and generate benchmark report
python -m models.train_and_eval --data data/daily_transactions.csv --business-id biz_001

# 3. Start the FastAPI microservice
uvicorn api.main:app --host 127.0.0.1 --port 8001 --reload
```

Interactive Swagger API Documentation:
Visit [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs) in your browser.

---

## 4. API Reference

All requests (except `/health`) require the header:
```http
X-API-Key: dev-secret-key-food-waste-2026
```

### Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service liveness & loaded models check (Public) |
| `POST` | `/predict/demand` | Returns future demand forecast per category (Prophet or PyTorch LSTM) |
| `POST` | `/risk/score` | Real-time 0–100 waste risk score for an inventory batch |
| `GET` | `/risk/batch/{business_id}` | Batch risk evaluation of active inventory |
| `POST` | `/reorder/recommend` | Optimal purchase quantity with transparent reasoning |
| `GET` | `/models/metrics` | Out-of-sample evaluation metrics benchmark |

---

## 5. Django Platform Integration & Resilient Fallback

The Django application connects to this microservice via `food_management/ml_client.py`:
- **Zero Extra Dependencies**: Uses Python's standard-library `urllib.request` without adding external HTTP packages.
- **Fail-Safe Operation**: If the FastAPI service is offline or unreachable, `ml_client` automatically activates fallback heuristic algorithms:
  - Waste risk scoring defaults to local decay velocity rules.
  - Replenishment recommendations default to baseline min-stock thresholds.
  - Forecast visualizations render a baseline corridor with a "Fallback Heuristics Active" badge on the UI.
- **Live Integration**: When the microservice is running on port 8001, the Django dashboard switches to "Live ML Service (PROPHET/LSTM)" and displays 7-day predicted demand bounds and live inventory surplus risk.

---

## 6. Testing

### Run Microservice Test Suite
```bash
cd ml-service
python -m pytest tests/ -v
# Output: 31 passed in ~11s
```

### Run Tabular Waste-Level Classifier Evaluation
```bash
python ml_service/train_model.py
# Output:
# Test Accuracy: 87.31%
# Macro Precision: 84.78% | Macro Recall: 83.34% | Macro F1: 83.91%
```

### Run Full Django Integration Test Suite
```bash
python manage.py test -v 2
# Output: 10 passed in ~19s (including ML client mocking and fallback verification)
```

---

## 7. Running with Docker

```bash
# Build the Docker image
docker build -t food-waste-ml-service .

# Run the container
docker run -d -p 8001:8001 \
  -e API_KEY=dev-secret-key-food-waste-2026 \
  --name food-waste-ml food-waste-ml-service
```
