"""FastAPI service for Weather Forecast & Alert Application."""

from pathlib import Path
import sqlite3
from fastapi import FastAPI, HTTPException
from src.ingest import load_simulation_weather
from src.rules import evaluate_daily_alerts

ROOT = Path(__file__).resolve().parent.parent
app = FastAPI(title="Weather Forecast & Alert API", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "service": "Weather-Forecast-Alert-Application"}


@app.get("/locations")
def list_locations():
    payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
    return {"locations": [l["name"] for l in payload["locations"]]}


@app.get("/alerts")
def get_alerts():
    payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
    all_alerts = []
    for loc in payload["locations"]:
        all_alerts.extend([vars(a) for a in evaluate_daily_alerts(loc["name"], loc["daily"])])
    return {"alerts": all_alerts}


@app.get("/forecast/{city}")
def get_forecast(city: str):
    payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
    for loc in payload["locations"]:
        if loc["name"].lower() == city.lower():
            alerts = [vars(a) for a in evaluate_daily_alerts(loc["name"], loc["daily"])]
            return {
                "city": loc["name"],
                "daily": loc["daily"],
                "active_alerts": alerts,
            }
    raise HTTPException(status_code=404, detail=f"City '{city}' not found in weather forecast database")
