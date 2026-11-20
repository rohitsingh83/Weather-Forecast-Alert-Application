"""End-to-end Weather Forecast & Alert Application pipeline."""

import sqlite3
from pathlib import Path
import pandas as pd

from src.ingest import load_simulation_weather, persist_weather_to_db
from src.rules import evaluate_daily_alerts
from src.plots import save_weather_charts

ROOT = Path(__file__).resolve().parent


def main() -> None:
    conn = sqlite3.connect(str(ROOT / "db" / "weather.db"))
    conn.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))

    payload = load_simulation_weather(ROOT / "data" / "sample_weather.json")
    persist_weather_to_db(conn, payload)

    alerts_all = []
    forecast_rows = []
    for loc in payload["locations"]:
        for day in loc["daily"]:
            forecast_rows.append({"city": loc["name"], **day})
        for alert in evaluate_daily_alerts(loc["name"], loc["daily"]):
            alerts_all.append(vars(alert))
            conn.execute(
                "INSERT INTO alert_log (location_name, alert_code, severity, message) VALUES (?, ?, ?, ?)",
                (alert.location, alert.code, alert.severity, alert.message),
            )

    conn.commit()
    conn.close()

    pd.DataFrame(forecast_rows).to_csv(ROOT / "outputs" / "7day_forecast.csv", index=False)
    alerts_df = pd.DataFrame(alerts_all)
    alerts_df.to_csv(ROOT / "reports" / "active_alerts.csv", index=False)
    save_weather_charts(payload, ROOT / "images")

    print("=== Weather Forecast & Alert Application ===")
    print(alerts_df.to_string(index=False))


if __name__ == "__main__":
    main()
