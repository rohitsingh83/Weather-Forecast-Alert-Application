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
    """Evaluate meteorological thresholds and return triggered warnings."""
    alerts = []
    for row in daily_rows:
        if row.get("precip_prob_pct", 0) >= 60:
            alerts.append(Alert(location_name, row["date"], "RAIN_SOON", "warn", f"High rain probability ({row['precip_prob_pct']}%)"))
        if row.get("temp_max_c", 0) >= 40.0:
            alerts.append(Alert(location_name, row["date"], "HEAT_WAVE", "critical", f"Extreme heat warning ({row['temp_max_c']} C)"))
        if row.get("wind_gust_ms", 0) >= 15.0:
            alerts.append(Alert(location_name, row["date"], "WIND_HIGH", "warn", f"High wind gusts ({row['wind_gust_ms']} m/s)"))
        if row.get("uv_index", 0) >= 8.0:
            alerts.append(Alert(location_name, row["date"], "UV_HIGH", "info", f"High UV index ({row['uv_index']})"))
        if row.get("temp_min_c", 99.0) <= 2.0:
            alerts.append(Alert(location_name, row["date"], "FROST_WARNING", "warn", f"Frost hazard: low temp ({row['temp_min_c']} C)"))
    return alerts
