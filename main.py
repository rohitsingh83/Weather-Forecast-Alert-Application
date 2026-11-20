"""End-to-end Weather Forecast & Alert Application pipeline."""

import logging
import sqlite3
import pandas as pd

from src.config import settings
from src.ingest import load_simulation_weather, persist_weather_to_db
from src.rules import evaluate_daily_alerts
from src.plots import save_weather_charts

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("weather_app")


def main() -> None:
    logger.info("Starting Weather Forecast & Alert Processing Pipeline...")
    conn = sqlite3.connect(str(settings.db_path))
    try:
        conn.executescript(settings.schema_path.read_text(encoding="utf-8"))

        payload = load_simulation_weather(settings.sample_json_path)
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
    finally:
        conn.close()

    pd.DataFrame(forecast_rows).to_csv(settings.forecast_csv_path, index=False)
    alerts_df = pd.DataFrame(alerts_all)
    alerts_df.to_csv(settings.alerts_csv_path, index=False)
    save_weather_charts(payload, settings.images_dir)

    logger.info("Successfully generated forecasts and %d alerts across %d locations.", len(alerts_df), len(payload["locations"]))
    print("=== Weather Forecast & Alert Application ===")
    print(alerts_df.to_string(index=False))


if __name__ == "__main__":
    main()
