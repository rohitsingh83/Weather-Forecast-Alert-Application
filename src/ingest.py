"""Weather data ingestion (Open-Meteo live option + offline JSON simulation)."""

import json
import sqlite3
from pathlib import Path


def load_simulation_weather(json_path: Path) -> dict:
    return json.loads(json_path.read_text(encoding="utf-8"))


def persist_weather_to_db(conn: sqlite3.Connection, payload: dict) -> None:
    cur = conn.cursor()
    for loc in payload["locations"]:
        cur.execute(
            "INSERT OR IGNORE INTO locations (name, lat, lon, tz) VALUES (?, ?, ?, ?)",
            (loc["name"], loc["lat"], loc["lon"], loc["tz"]),
        )
        cur.execute("SELECT id FROM locations WHERE name = ?", (loc["name"],))
        loc_id = cur.fetchone()[0]

        for day in loc["daily"]:
            cur.execute(
                """INSERT OR REPLACE INTO weather_daily
                   (location_id, date, temp_max_c, temp_min_c, precip_prob_pct, precip_mm, wind_gust_ms, uv_index)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (loc_id, day["date"], day["temp_max_c"], day["temp_min_c"], day["precip_prob_pct"], day["precip_mm"], day["wind_gust_ms"], day["uv_index"]),
            )
    conn.commit()
