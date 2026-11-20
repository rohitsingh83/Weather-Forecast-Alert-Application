# Engineering Audit: Weather Forecast & Alert Application

**Project Context:**
- **What it does / who it's for:** A weather risk monitoring and intelligence service that ingests multi-city 7-day meteorological forecasts, stores normalized daily conditions in SQLite, evaluates automated hazard alert rules (`RAIN_SOON`, `HEAT_WAVE`, `WIND_HIGH`, `UV_HIGH`, `FROST_WARNING`), and outputs alert feeds, dual-axis trend charts, and FastAPI endpoints.
- **Stack & entry points:** Python 3.14 / 3.11, `sqlite3`, `pandas`, `matplotlib`, `fastapi`, `streamlit`. Entry points: `python main.py`, `python jobs/refresh.py`, `python -m uvicorn api.app:app`, `python -m streamlit run app_streamlit.py`.
- **Real usage:** Batch forecast processor & alert generator (`main.py`) + refresh cron (`jobs/refresh.py`) + REST API (`api/app.py`).
- **Constraint:** Preserve `data/sample_weather.json` format, SQLite schema, `reports/active_alerts.csv` structure, and FastAPI routes.

---

## Findings & Technical Debt

### 🔴 Critical Findings
1. **Multi-City Visualization Blindspot (`src/plots.py`):**
   - In `save_weather_charts(payload, images_dir)`, the code hardcodes:
     ```python
     loc = payload["locations"][0]
     ```
     Even though the dataset models multiple cities (Hyderabad, Bangalore, Mumbai), it **only ever plots the first location**! The remaining cities in the monitored fleet are completely omitted from visual reporting.
2. **Hardcoded Alert Rule Thresholds in Python Code (`src/rules.py`):**
   - Critical meteorological thresholds (`precip_prob_pct >= 60`, `temp_max_c >= 40.0`, `wind_gust_ms >= 15.0`, `uv_index >= 8.0`, `temp_min_c <= 2.0`) are hardcoded directly inside `if` statements. There is no mechanism to customize thresholds per climate region or seasonal variations.
3. **Stub Notification Module (`notify/alert.py`):**
   - The `notify/` directory contains an incomplete 5-line stub file that does not integrate with any dispatch channel (email, webhook, or logging dispatcher).

### 🟡 High Priority Findings
4. **Row-by-Row Nested SQL Ingestion (`src/ingest.py`):**
   - `persist_weather_to_db()` iterates row-by-row over locations and daily arrays executing individual SQL cursor statements without bulk parameter binding or batch transactions.
5. **Missing Alert Debouncing & State Tracking:**
   - Successive runs of `main.py` append duplicate alert rows into `alert_log` without deduplicating identical alerts for the same city and date within an active validity window.
6. **No Centralized Settings Configuration:**
   - Lacks Pydantic settings for API host, database path, alert thresholds, and refresh intervals.

### 🟢 Nice-to-Have / Polish
7. **No Open-Meteo Live API Fallback Handler:**
   - Ingestion relies purely on `sample_weather.json` without an integrated HTTP client calling the free Open-Meteo REST API when online.
8. **Missing Test Categorization:**
   - Tests lack fast/integration markers.

---

## What "Elite" Looks Like for This Exact Project

An elite weather intelligence application:
- Visualizes 7-day temperature envelopes and precipitation bars across **all** monitored locations in the fleet.
- Defines weather rules as structured, configurable schema objects with customizable severity and thresholds.
- Implements alert deduplication and lifecycle state tracking (Active, Acknowledged, Expired).
- Supports live Open-Meteo API ingestion with cached offline JSON fallback.
- Implements structured JSON logging, standard `pyproject.toml`, and strict type safety.
