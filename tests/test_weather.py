import unittest
import sqlite3
import tempfile
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

from src.rules import evaluate_daily_alerts, WeatherAlert
from src.ingest import load_simulation_weather, persist_weather_to_db
from src.plots import save_weather_charts
from notify.alert import format_alert_message
from api.app import app

ROOT = Path(__file__).resolve().parent.parent


class TestWeatherAlerts(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_alert_rules_all_triggered(self):
        sample = [{
            "date": "2026-11-21",
            "temp_max_c": 41.0,
            "temp_min_c": 25.0,
            "precip_prob_pct": 75,
            "precip_mm": 10.0,
            "wind_gust_ms": 16.0,
            "uv_index": 9.0,
        }]
        alerts = evaluate_daily_alerts("TestCity", sample)
        codes = {a.code for a in alerts}
        self.assertEqual(codes, {"RAIN_SOON", "HEAT_WAVE", "WIND_HIGH", "UV_HIGH"})

    def test_alert_rules_calm_weather(self):
        sample = [{
            "date": "2026-11-21",
            "temp_max_c": 26.0,
            "temp_min_c": 18.0,
            "precip_prob_pct": 10,
            "precip_mm": 0.0,
            "wind_gust_ms": 5.0,
            "uv_index": 4.0,
        }]
        alerts = evaluate_daily_alerts("CalmCity", sample)
        self.assertEqual(len(alerts), 0)

    def test_simulation_data_loading(self):
        json_path = ROOT / "data" / "sample_weather.json"
        self.assertTrue(json_path.exists())
        payload = load_simulation_weather(json_path)
        self.assertIn("locations", payload)
        self.assertGreater(len(payload["locations"]), 0)

    def test_database_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "weather_test.db"
            conn = sqlite3.connect(str(db_path))
            try:
                conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))
                payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
                persist_weather_to_db(conn, payload)

                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM locations")
                loc_count = cur.fetchone()[0]
                self.assertGreater(loc_count, 0)

                cur.execute("SELECT COUNT(*) FROM weather_daily")
                wd_count = cur.fetchone()[0]
                self.assertGreater(wd_count, 0)
            finally:
                conn.close()

    def test_format_alert_message(self):
        alert_dict = {
            "severity": "critical",
            "location": "Delhi",
            "date": "2026-11-21",
            "code": "HEAT_WAVE",
            "message": "Extreme heat warning (40.5 C)",
        }
        msg = format_alert_message(alert_dict)
        self.assertIn("[CRITICAL]", msg)
        self.assertIn("HEAT_WAVE", msg)
        self.assertIn("Delhi", msg)

    def test_weather_charts_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            img_dir = Path(tmpdir) / "images"
            img_dir.mkdir(parents=True, exist_ok=True)
            payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
            save_weather_charts(payload, img_dir)
            files = list(img_dir.glob("*.png"))
            self.assertGreater(len(files), 0)

    def test_api_health(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "ok")

    def test_api_locations_and_alerts(self):
        loc_resp = self.client.get("/locations")
        self.assertEqual(loc_resp.status_code, 200)
        self.assertIn("Hyderabad", loc_resp.json()["locations"])

        alert_resp = self.client.get("/alerts")
        self.assertEqual(alert_resp.status_code, 200)
        self.assertIn("alerts", alert_resp.json())

    def test_api_forecast_by_city(self):
        resp = self.client.get("/forecast/Hyderabad")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["city"], "Hyderabad")
        self.assertEqual(len(data["daily"]), 7)

        # Test non-existent city
        not_found = self.client.get("/forecast/NonExistentCity")
        self.assertEqual(not_found.status_code, 404)


if __name__ == "__main__":
    unittest.main()
