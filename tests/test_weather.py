import unittest
import sqlite3
from pathlib import Path
from fastapi.testclient import TestClient

from src.ingest import load_simulation_weather, persist_weather_to_db
from src.rules import evaluate_daily_alerts, Alert
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestWeatherAlerts(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.sample_payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")

    def test_json_ingestion(self):
        """Verify weather simulation JSON loads with required locations."""
        self.assertIn("locations", self.sample_payload)
        self.assertGreater(len(self.sample_payload["locations"]), 0)

    def test_database_persistence(self):
        """Verify SQLite tables are populated with forecast records."""
        conn = sqlite3.connect(":memory:")
        conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
        persist_weather_to_db(conn, self.sample_payload)
        
        row_count = conn.execute("SELECT COUNT(*) FROM weather_daily").fetchone()[0]
        self.assertGreater(row_count, 0)
        conn.close()

    def test_alert_rules_evaluation(self):
        """Verify alert rule engine triggers on threshold conditions."""
        sample_days = [
            {"date": "2026-11-20", "temp_max_c": 42.0, "temp_min_c": 28.0, "precip_prob_pct": 20, "precip_mm": 0.0, "wind_gust_ms": 5.0, "uv_index": 5.0},
            {"date": "2026-11-21", "temp_max_c": 30.0, "temp_min_c": 20.0, "precip_prob_pct": 80, "precip_mm": 25.0, "wind_gust_ms": 18.0, "uv_index": 9.0},
            {"date": "2026-11-22", "temp_max_c": 12.0, "temp_min_c": 1.0, "precip_prob_pct": 10, "precip_mm": 0.0, "wind_gust_ms": 4.0, "uv_index": 2.0},
        ]
        alerts = evaluate_daily_alerts("TestCity", sample_days)
        codes = [a.code for a in alerts]
        self.assertIn("HEAT_WAVE", codes)
        self.assertIn("RAIN_SOON", codes)
        self.assertIn("WIND_HIGH", codes)
        self.assertIn("UV_HIGH", codes)
        self.assertIn("FROST_WARNING", codes)

    def test_api_health(self):
        """Verify API health status probe."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_api_locations(self):
        """Verify location listing endpoint."""
        resp = self.client.get("/locations")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("locations", resp.json())

    def test_api_alerts(self):
        """Verify alert endpoint returns active alerts."""
        resp = self.client.get("/alerts")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("alerts", resp.json())

    def test_api_forecast_city(self):
        """Verify specific city forecast endpoint."""
        first_city = self.sample_payload["locations"][0]["name"]
        resp = self.client.get(f"/forecast/{first_city}")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["city"].lower(), first_city.lower())


if __name__ == "__main__":
    unittest.main()
