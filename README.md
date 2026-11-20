# Weather Forecast & Alert Application

A weather intelligence engine that monitors multi-city meteorological forecasts, normalizes time-series metrics into SQLite, evaluates automated risk rules (`RAIN_SOON`, `HEAT_WAVE`, `WIND_HIGH`, `UV_HIGH`, `FROST_WARNING`), exports CSV alert feeds, generates dual-axis Matplotlib trend charts, and exposes a FastAPI REST service.

---

## 🏛 Architecture & Alert Pipeline

```
[Meteorological Forecast: Open-Meteo / Offline JSON]
                         │
                         ▼
             [Normalization & Unit Conversion]
           (°C Temperature, mm Rainfall, m/s Wind)
                         │
                         ▼
        [SQLite Persistence: weather_daily & locations]
                         │
                         ▼
           [Configurable Risk Rules Engine]
     ├── RAIN_SOON: Precip prob >= 60%
     ├── HEAT_WAVE: Max temp >= 40°C
     ├── WIND_HIGH: Gusts >= 15 m/s
     ├── UV_HIGH: UV Index >= 8.0
     └── FROST_WARNING: Min temp <= 2°C
                         │
                         ▼
[Dual-Axis Matplotlib Plots] + [Alert CSVs] + [FastAPI & Streamlit]
```

---

## ✨ Key Capabilities

- **Multi-City Monitoring:** Simultaneously models and stores 7-day meteorological forecasts across diverse geographical locations.
- **Configurable Multi-Severity Rules:** Detects extreme weather hazards categorized by severity (`info`, `warn`, `critical`) to empower early response.
- **Relational Integrity:** Normalizes city latitude, longitude, and timezone in `locations`, with composite foreign-keyed records in `weather_daily`.
- **Offline Simulation & Live Ingestion:** Offers both offline deterministic simulation (for testing and offline demos) and live Open-Meteo API ingestion.
- **Publication-Quality Forecast Plots:** Generates dual-axis plots tracking daily min/max temperature envelopes aligned with precipitation bars.
- **Microservice Integration:** Exposes clean RESTful endpoints for querying active alerts, city listings, and raw forecasts via FastAPI.

---

## 🚨 Configured Weather Alert Rules

| Rule Code | Threshold Trigger | Severity | Actionable Advice |
|---|---|---|---|
| `RAIN_SOON` | Rain probability $\ge 60\%$ | `warn` | Carry rain gear; reschedule outdoor activities. |
| `HEAT_WAVE` | Max Temperature $\ge 40^\circ\text{C}$ | `critical` | Stay hydrated; avoid direct afternoon sunlight. |
| `WIND_HIGH` | Wind Gusts $\ge 15\text{ m/s}$ | `warn` | Secure loose outdoor fixtures; drive cautiously. |
| `UV_HIGH` | UV Index $\ge 8.0$ | `info` | Apply SPF sunscreen; wear protective eyewear. |
| `FROST_WARNING` | Min Temperature $\le 2^\circ\text{C}$ | `warn` | Protect sensitive crops and exposed plumbing. |

---

## 🚀 Quick Start Guide

### 1. Installation
```bash
python -m venv venv
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
```

### 2. Run Weather Engine
```bash
python main.py
```

### 3. Launch Weather Dashboard
```bash
python -m streamlit run app_streamlit.py
```

### 4. Start FastAPI Service
```bash
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run Test Suite
```bash
python -m unittest discover -s tests -v
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health status. |
| `GET` | `/locations` | List of all monitored cities and locations. |
| `GET` | `/alerts` | Retreive all currently active weather risk alerts. |
| `GET` | `/forecast/{city}` | 7-day daily forecast and active alerts for a specific city. |
