"""Run with:  python -m pytest -q"""

import pandas as pd
import pytest

from src import api_client
from src.alerts import evaluate, load_rules
from src.api_client import City, geocode, get_weather, load_cities
from src.notifier import AlertLog, alert_email_html, send_email
from src.processing import aqi_category, current_conditions, daily_frame, describe, hourly_frame

DELHI = City("Delhi", 28.6139, 77.2090, "Delhi")


def weather(name: str):
    return get_weather(next(c for c in load_cities() if c.name == name), "sample")


def test_sample_data_has_open_meteo_shape():
    w = weather("Chennai")
    assert w.source == "sample"
    assert len(w.forecast["hourly"]["time"]) == 7 * 24
    assert len(w.forecast["daily"]["time"]) == 7
    assert set(api_client.DAILY) <= set(w.forecast["daily"])


def test_live_failure_falls_back_to_sample(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise ConnectionError("offline")
    monkeypatch.setattr(api_client, "fetch_live", boom)
    monkeypatch.setattr(api_client, "CACHE", tmp_path)          # no cached copy either
    assert get_weather(DELHI, "auto").source == "sample"
    with pytest.raises(ConnectionError):
        get_weather(DELHI, "live")


def test_geocode_known_city_without_network():
    assert geocode("delhi").lat == pytest.approx(28.6139)


def test_weather_codes_and_aqi_bands():
    assert describe(65) == ("Heavy rain", "🌧️")
    assert describe(1234)[0] == "Unknown"
    assert aqi_category(42)[0] == "Good"
    assert aqi_category(151)[0] == "Unhealthy"
    assert aqi_category(450)[0] == "Hazardous"


def test_daily_frame_adds_aqi_and_visibility():
    d = daily_frame(weather("Delhi"))
    assert {"us_aqi_max", "visibility_min", "description", "icon"} <= set(d.columns)
    h = hourly_frame(weather("Delhi"))
    assert d["us_aqi_max"].iloc[0] == h[h["time"].dt.date == h["time"].dt.date.iloc[0]]["us_aqi"].max()


def test_current_conditions():
    cur = current_conditions(weather("Mumbai"))
    assert cur["aqi_label"] != "No data" and "temperature_2m" in cur


def test_heavy_rain_alert_for_chennai():
    alerts = evaluate("Chennai", daily_frame(weather("Chennai")))
    heavy = [a for a in alerts if a.rule_id == "HEAVY_RAIN"]
    assert len(heavy) == 1 and heavy[0].days == 2 and heavy[0].severity == "critical"
    assert heavy[0].value >= 64.5


def test_only_most_severe_alert_per_family_and_day():
    alerts = evaluate("Delhi", daily_frame(weather("Delhi")))
    days_severe = {pd.Timestamp(a.start) for a in alerts if a.rule_id == "AQI_SEVERE"}
    for a in alerts:
        if a.rule_id == "AQI_POOR":
            assert pd.Timestamp(a.start) not in days_severe


def test_consecutive_days_are_merged():
    alerts = evaluate("Kolkata", daily_frame(weather("Kolkata")))
    assert len(alerts) == 1 and alerts[0].days == 7


def test_rules_are_configurable():
    rules = [{"id": "T", "name": "Test", "metric": "temperature_2m_max", "level": "daily", "operator": ">=",
              "threshold": 0, "severity": "info", "advice": ""}]
    assert evaluate("Hyderabad", daily_frame(weather("Hyderabad")), rules)[0].days == 7
    assert evaluate("Hyderabad", daily_frame(weather("Hyderabad"))) == []   # default rules: calm week
    assert all({"id", "metric", "operator", "threshold", "severity"} <= set(r) for r in load_rules())


def test_alert_log_only_reports_new_alerts(tmp_path):
    log = AlertLog(tmp_path / "h.db")
    alerts = evaluate("Chennai", daily_frame(weather("Chennai")))
    assert len(log.new_alerts(alerts)) == len(alerts)
    assert log.new_alerts(alerts) == []
    log.close()


def test_email_dry_run(tmp_path, monkeypatch):
    alerts = evaluate("Delhi", daily_frame(weather("Delhi")))
    assert "Hazardous air" in alert_email_html(alerts)
    monkeypatch.setattr("src.notifier.ROOT", tmp_path)
    assert send_email(alerts, "me@example.com", dry_run=True).startswith("dry-run")
    assert list((tmp_path / "outputs" / "alert_emails").glob("*.eml"))
