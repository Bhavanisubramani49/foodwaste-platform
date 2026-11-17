# FoodWasteAI – Project Overview

## 1. Executive Summary

**FoodWasteAI** is an AI-powered food waste management and surplus redistribution platform designed to bridge commercial food businesses (restaurants, supermarkets, caterers, bakeries) with verified non-governmental organizations (NGOs, community kitchens, food shelters).

Every year, millions of tonnes of edible food are discarded into landfills, generating potent methane emissions while communities face acute food insecurity. FoodWasteAI tackles this systemic challenge through an end-to-end operational pipeline:
1. **Intelligent Inventory & Spoilage Prevention:** Tracking batch shelf-life and flagging near-expiry inventory before waste occurs.
2. **AI-Powered Demand & Spoilage Forecasting:** Utilizing Meta Prophet time-series models, PyTorch Deep LSTM networks, and Scikit-Learn Random Forest classifiers to predict demand trends, detect waste risk, and generate automated replenishment reorder quantities.
3. **Smart Surplus Marketplace & Automated NGO Matching:** Multi-criteria weighted matching connecting excess inventory with registered NGO nutritional requirements within a 45-minute claim window.
4. **Secure Logistics & Chain of Custody:** Time-slot dispatching, atomic lock allocations, and driver verification PINs (`RC-XXXX`) ensuring verified handoff.
5. **Real-Time ESG & Environmental Impact Telemetry:** Measuring kilograms of edible food diverted, meals served ($2.22 \times \text{kg}$ diverted), greenhouse gas mitigation ($2.5 \times \text{kg } \text{CO}_2\text{e}$ prevented), and landfill volume saved.

---

## 2. Platform Milestones & Capabilities

```
+---------------------------------------------------------------------------------------------------+
|                                  FoodWasteAI Platform Architecture                                |
+---------------------------------------------------------------------------------------------------+
|  [Milestone 1: Operations Foundation]                                                             |
|   - Django 5 MVC Architecture & PostgreSQL Relational Backend                                     |
|   - Role-Based Authentication: Business, NGO, and Administrator Portals                           |
|   - Inventory CRUD, Expiry Date Tracking, Dynamic Risk Classification, and RFC CSV Bulk Import     |
+---------------------------------------------------------------------------------------------------+
|  [Milestone 2: Machine Learning & Microservices]                                                  |
|   - FastAPI High-Throughput Microservice on Port 8001 with API Key Authentication                 |
|   - Dual Demand Forecasting: Meta Prophet & 2-Layer PyTorch LSTM with Category Selection          |
|   - 87.3% Accurate Random Forest Classifier for Multi-Class Food Waste Risk Level Assessment     |
|   - Automated Replenishment Reorder Recommender with Lead-Time Safety Buffers                     |
|   - Resilient Fallback Engine & Microsecond Circuit Breaker if ML Microservice is Offline         |
+---------------------------------------------------------------------------------------------------+
|  [Milestone 3: Surplus Redistribution & NGO Network]                                              |
|   - Real-Time Surplus Food Marketplace with Split Map & Urgent Expiry Countdowns                 |
|   - NGO Community Requirements Registry (Category, Quantity, Urgency, Regional Delivery Area)    |
|   - Multi-Criteria Smart Matching Engine (Category 40%, Quantity 30%, Urgency 20%, Location 10%)  |
|   - Atomic Claim Allocations with Concurrency Protection (select_for_update)                      |
|   - Secure Pickup Scheduling & Cryptographic Handoff PIN Verification (#RC-XXXX)                  |
|   - Real-Time Environmental Impact Dashboard & Community Gamification Leaderboard                |
+---------------------------------------------------------------------------------------------------+
|  [Milestone 4: Comprehensive QA, Optimization & Technical Delivery]                               |
|   - 91 Automated Automated Test Cases (60 Django Unit/E2E Tests, 31 FastAPI Pytest Scenarios)    |
|   - End-to-End Performance Benchmark & Query Optimization (< 50ms p50 Latencies Across App)     |
|   - Complete Security Audit: CSRF, RBAC, SQL Injection Prevention, Secure Secrets Management      |
|   - Standardized Technical Documentation Suite & Local Delivery Package                           |
+---------------------------------------------------------------------------------------------------+
```

---

## 3. Technology Stack Summary

| Layer | Component | Specification | Purpose |
|---|---|---|---|
| **Frontend** | HTML5 / CSS3 / Vanilla JS | Bootstrap 5.3.3, Chart.js 4.4.2, Bootstrap Icons 1.11.3 | Responsive operational interface with real-time Chart.js telemetry |
| **Backend** | Python 3.13 / Django 5.x | Django MVC, ORM, Session Authentication | Core business logic, access control, atomic transaction processing |
| **Database** | PostgreSQL 16 / SQLite | `foodwaste_db` with zero-config test fallback | Relational persistence, transactional locking, indexing |
| **ML Microservice** | FastAPI / Uvicorn | Port 8001, `X-API-Key` Authentication | High-throughput asynchronous prediction & optimization endpoints |
| **Forecasting** | Meta Prophet & PyTorch | 2-Layer LSTM with 64 units, Lookback Window = 14d | 7-day to 14-day daily inventory category demand projection |
| **Classification**| Scikit-learn Random Forest | 100 Trees, Balanced Class Weights | Multiclass food spoilage risk level prediction (Low, Medium, High) |
| **Data Pipelines**| Pandas 2.x & NumPy | Vectorized time-series transformation | Aggregations, dataset cleaning, data preprocessing pipelines |

---

## 4. Key Metrics & Impact Benchmarks

All platform telemetry is calculated directly from persistent database records using scientifically documented methodologies:

1. **Nutritious Meals Served:**
   $$\text{Meals} = \text{Recovered Food (kg)} \times 2.22$$
   *Standard USDA / FAO / Feeding America benchmark: 1 meal portion = 0.45 kg of edible food.*

2. **Greenhouse Gas Avoidance ($\text{CO}_2\text{e}$):**
   $$\text{CO}_2\text{e Avoided (kg)} = \text{Recovered Food (kg)} \times 2.5$$
   *EPA WARM & FAO Food Wastage Footprint methodology: Preventing anaerobic decomposition of organic waste into methane ($CH_4$).*

3. **Landfill Space Conserved:**
   $$\text{Landfill Volume Saved (m}^3) = \frac{\text{Recovered Food (kg)}}{500}$$
   *Average compacted municipal solid organic waste density = $500 \text{ kg/m}^3$.*

4. **Economic Wholesale Valuation:**
   $$\text{Value Rescued (₹)} = \text{Recovered Food (kg)} \times ₹120$$
   *Average wholesale commercial food replacement valuation benchmark.*
