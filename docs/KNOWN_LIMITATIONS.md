# FoodWasteAI – Known Limitations & Future Roadmap

## 1. Current System Boundaries & Known Limitations

### 1.1 Time-Series Data History Requirements
- **LSTM Sequence Window:** The deep PyTorch LSTM forecasting model requires a minimum lookback window of 14 historical observations ($N \ge 14$).
- **Mitigation:** If a brand-new food category has fewer than 14 days of recorded transaction history, the platform automatically falls back to Meta Prophet or moving-average heuristic baselines until sufficient sequential data accumulates.

### 1.2 Cold-Chain Internet of Things (IoT) Integration
- **Current Architecture:** Storage temperatures and refrigerator ambient conditions are logged by kitchen managers via form inputs and CSV uploads.
- **Limitation:** Live telemetry from hardware IoT BLE/WiFi temperature sensors is not currently streamed automatically in real time.
- **Mitigation:** The risk scoring engine conservatively penalizes categories if temperatures deviate from optimal ranges (e.g. ambient storage for dairy items).

### 1.3 Geographical Distance Calculations
- **Current Architecture:** Proximity scoring in `matching.py` performs lexical neighborhood and municipality token intersection matching.
- **Limitation:** Precise driving distance is calculated using regional district clustering rather than real-time Google Maps / OpenStreetMap road routing matrices.
- **Mitigation:** The system defaults to flexible proximity scoring ($8/10$) when coordinates are unconstrained, ensuring no viable donations are excluded.

### 1.4 Single-Node In-Memory Circuit Breaker
- **Current Architecture:** The ML microservice circuit breaker in `ml_client.py` uses process-level in-memory timestamp tracking.
- **Limitation:** In multi-worker Gunicorn deployments without shared caching, each worker maintains its own 15-second offline cooldown timer.
- **Mitigation:** A centralized Redis cache key can be adopted in multi-server horizontal cloud clusters.

---

## 2. Future Technical Roadmap

1. **Autonomous Cold-Chain Sensor Integration:**
   - MQTT / Webhook ingestion pipelines for real-time ESP32 / Raspberry Pi chiller temperature monitors.
2. **Geographical GIS Distance Matrix:**
   - Haversine distance and real-time transit routing API integration (OSRM / OpenRouteService) for dynamic traffic-aware pickup windows.
3. **Automated WhatsApp / SMS Volunteer Dispatch:**
   - Twilio / WhatsApp Business API webhooks alerting NGO driver rosters the second a compatible surplus lot is posted.
4. **Computer Vision Food Quality Auditing:**
   - Mobile camera upload analyzing photographic spoilage or visual freshness before listing confirmation.
