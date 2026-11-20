"""Weather risk alert rule engine."""

from dataclasses import dataclass
from typing import List


@dataclass
class Alert:
    location: str
    date: str
    code: str
    severity: str
    message: str


WeatherAlert = Alert


def evaluate_daily_alerts(location_name: str, daily_rows: List[dict]) -> List[Alert]:
    alerts = []
    for row in daily_rows:
        if row["precip_prob_pct"] >= 60:
            alerts.append(Alert(location_name, row["date"], "RAIN_SOON", "warn", f"High rain probability ({row['precip_prob_pct']}%)"))
        if row["temp_max_c"] >= 40.0:
            alerts.append(Alert(location_name, row["date"], "HEAT_WAVE", "critical", f"Extreme heat warning ({row['temp_max_c']} C)"))
        if row["wind_gust_ms"] >= 15.0:
            alerts.append(Alert(location_name, row["date"], "WIND_HIGH", "warn", f"High wind gusts ({row['wind_gust_ms']} m/s)"))
        if row["uv_index"] >= 8.0:
            alerts.append(Alert(location_name, row["date"], "UV_HIGH", "info", f"High UV index ({row['uv_index']})"))
    return alerts
