# AI-Powered Food Waste Prediction & Inventory Optimization Service

A production-ready microservice built with **FastAPI**, **PyTorch**, and **Meta Prophet** for the Infosys Springboard Project:
> *"AI-Powered Food Waste Management Platform for Surplus Identification and Redistribution Optimization"*

---

## 1. Features

- **Multi-Category Demand Forecasting**: Prophet & PyTorch LSTM models per product category (`dairy`, `bakery`, `produce`, `meat`, `packaged`, `beverages`).
- **Benchmark Evaluation**: Automated comparison against a Naive Seasonal Baseline (Lag-7) with MAE, RMSE, and MAPE.
- **Calibrated Waste-Risk Engine**: 0–100 risk scoring formula combining days to expiry, current inventory, and forecast demand over remaining shelf life.
- **Smart Replenishment Recommendations**: Order optimization adhering to lead-time demand, statistical safety stock, perishable shelf-life bounds, and storage capacity limits.
- **Scheduled Batch Intelligence**: Built-in APScheduler daily job for scheduled tenant-wide inventory risk audits.
- **Security & Integrity**: API-Key header authentication (`X-API-Key`) and configurable CORS.

---

## 2. Directory Structure

```text
ml-service/
├── .env                  # Local environment configuration
├── .env.example          # Sample environment variables
├── requirements.txt      # Python dependencies
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
│   ├── lstm_model.py       # PyTorch recurrent neural network
│   ├── train_and_eval.py   # Training, metrics evaluation & plotting
│   ├── metrics.json        # Evaluation metrics comparison store
│   └── saved/              # Serialized weights (.joblib, .pt)
├── reports/              # Plots and batch prediction outputs
│   └── batch_predictions/
├── risk/
│   └── risk_scorer.py    # 0-100 waste risk scoring engine
├── reorder/
│   └── optimizer.py      # Replenishment optimizer & reasoning generator
└── tests/                # Automated pytest suite
```

---

## 3. Local Setup & Execution

### Prerequisites
- Python 3.10+ (Tested up to Python 3.14)
- Virtual environment

### Installation
```bash
# Navigate to ml-service
cd ml-service

# Create virtual environment if needed
python -m venv .venv
source .venv/bin/activate       # On Linux/macOS
.\.venv\Scripts\activate        # On Windows

# Install dependencies
pip install -r requirements.txt
```

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
| `POST` | `/predict/demand` | Returns future demand forecast per category |
| `POST` | `/risk/score` | Real-time 0–100 waste risk score for an inventory batch |
| `GET` | `/risk/batch/{business_id}` | Batch risk evaluation of active inventory |
| `POST` | `/reorder/recommend` | Optimal purchase quantity with transparent reasoning |
| `GET` | `/models/metrics` | Out-of-sample evaluation metrics benchmark |

---

## 5. Running with Docker

```bash
# Build the Docker image
docker build -t food-waste-ml-service .

# Run the container
docker run -d -p 8001:8001 \
  -e API_KEY=dev-secret-key-food-waste-2026 \
  --name food-waste-ml food-waste-ml-service
```
