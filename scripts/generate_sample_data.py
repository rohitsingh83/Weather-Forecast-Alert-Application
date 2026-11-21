"""
Create offline sample forecasts in the exact JSON format returned by the
Open-Meteo forecast and air-quality APIs, so the app runs without internet.

These are SIMULATED forecasts for 21-27 November 2026, designed to resemble
typical late-November weather in Indian cities (and to trigger a range of
alerts). When online, the app fetches real forecasts instead.

Run:  python scripts/generate_sample_data.py
"""

import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "data" / "sample"
CITIES = json.loads((OUT.parent / "cities.json").read_text())
START = datetime(2026, 11, 21)
DAYS = 7
rng = np.random.default_rng(3)

# per-day profiles: max temp, min temp, rain mm, rain probability %, max gust km/h, max UV, AQI base, min visibility m
PROFILES = {
    "Delhi": dict(tmax=[26, 25, 25, 23, 22, 24, 25], tmin=[11, 10, 9, 7, 7, 8, 9], rain=[0] * 7,
                  prob=[2, 0, 0, 5, 5, 0, 0], gust=[14, 12, 15, 10, 11, 16, 14], uv=[5, 5, 5, 4, 4, 5, 5],
                  aqi=[265, 320, 345, 290, 280, 240, 230], vis=[2500, 1800, 1200, 300, 250, 1500, 3000]),
    "Mumbai": dict(tmax=[34, 35, 36, 36, 34, 33, 34], tmin=[24, 24, 25, 25, 24, 23, 23], rain=[0] * 7,
                   prob=[5, 5, 10, 10, 5, 5, 5], gust=[24, 26, 28, 25, 22, 22, 24], uv=[8, 9, 9, 9, 8, 8, 8],
                   aqi=[150, 165, 172, 160, 140, 130, 135], vis=[6000] * 7),
    "Bengaluru": dict(tmax=[27, 27, 26, 27, 28, 28, 27], tmin=[18, 18, 17, 17, 17, 18, 18], rain=[2, 8, 16, 4, 0, 0, 3],
                      prob=[40, 75, 85, 50, 10, 10, 35], gust=[28, 32, 35, 30, 24, 22, 26], uv=[7, 6, 5, 7, 8, 8, 7],
                      aqi=[70, 62, 55, 64, 78, 80, 72], vis=[10000] * 7),
    "Chennai": dict(tmax=[30, 29, 28, 27, 28, 30, 31], tmin=[25, 24, 24, 23, 24, 24, 25], rain=[12, 45, 92, 118, 30, 5, 2],
                    prob=[80, 95, 100, 100, 85, 40, 20], gust=[36, 48, 64, 72, 46, 30, 26], uv=[5, 3, 2, 2, 4, 7, 8],
                    aqi=[55, 42, 35, 32, 40, 58, 62], vis=[8000, 5000, 2000, 1500, 6000, 10000, 10000]),
    "Kolkata": dict(tmax=[29, 29, 28, 28, 29, 29, 28], tmin=[18, 18, 17, 17, 18, 18, 17], rain=[0] * 7,
                    prob=[5, 0, 0, 5, 10, 5, 0], gust=[14, 15, 13, 12, 16, 15, 14], uv=[6, 6, 6, 6, 6, 6, 6],
                    aqi=[175, 190, 205, 198, 180, 170, 168], vis=[3500, 3000, 2500, 2800, 3500, 4000, 4000]),
    "Hyderabad": dict(tmax=[31, 30, 29, 30, 31, 31, 30], tmin=[17, 17, 16, 16, 17, 17, 16], rain=[0, 1, 5, 0, 0, 0, 0],
                      prob=[10, 30, 55, 20, 5, 5, 5], gust=[20, 24, 28, 22, 18, 18, 20], uv=[7, 7, 6, 7, 7, 7, 7],
                      aqi=[105, 112, 96, 108, 118, 122, 110], vis=[8000] * 7),
}


def temp_curve(hour: int, tmin: float, tmax: float) -> float:
    """Coldest around 06:00, warmest around 14:30."""
    phase = math.cos((hour - 14.5) / 24 * 2 * math.pi)
    return tmin + (tmax - tmin) * (phase + 1) / 2


def weather_code(rain_mm_h: float, vis: float, cloud: float) -> int:
    """WMO weather interpretation codes used by Open-Meteo."""
    if rain_mm_h >= 7.6:
        return 65
    if rain_mm_h >= 2.5:
        return 63
    if rain_mm_h >= 0.1:
        return 61
    if vis <= 1000:
        return 45
    return 0 if cloud < 20 else 1 if cloud < 45 else 2 if cloud < 75 else 3


def build(city: dict) -> tuple[dict, dict]:
    p = PROFILES[city["name"]]
    h = {k: [] for k in ["time", "temperature_2m", "apparent_temperature", "relative_humidity_2m",
                         "precipitation_probability", "precipitation", "weather_code", "cloud_cover",
                         "wind_speed_10m", "wind_gusts_10m", "uv_index", "visibility"]}
    air = {"time": [], "us_aqi": [], "pm2_5": [], "pm10": []}
    daily = {k: [] for k in ["time", "weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
                             "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max",
                             "uv_index_max", "sunrise", "sunset"]}
    for d in range(DAYS):
        day = START + timedelta(days=d)
        weights = np.array([0.2 if hr < 11 else 1.6 if 13 <= hr <= 21 else 0.6 for hr in range(24)])
        rain_h = p["rain"][d] * weights / weights.sum() * rng.uniform(0.7, 1.3, 24)
        rain_h = rain_h / rain_h.sum() * p["rain"][d] if p["rain"][d] else np.zeros(24)
        codes = []
        for hr in range(24):
            t = temp_curve(hr, p["tmin"][d], p["tmax"][d]) + rng.normal(0, 0.3)
            rh = float(np.clip(92 - (t - p["tmin"][d]) / max(p["tmax"][d] - p["tmin"][d], 1) * 45
                               + (25 if rain_h[hr] > 0.5 else 0) + rng.normal(0, 3), 20, 100))
            cloud = float(np.clip(p["prob"][d] + rng.normal(0, 12) + (30 if rain_h[hr] > 0 else 0), 0, 100))
            fog = p["vis"][d] < 1000 and 2 <= hr <= 9
            vis = p["vis"][d] * (1 if fog else 4) if p["vis"][d] < 10000 else 24000
            vis = min(vis, 24000) if not fog else p["vis"][d] + abs(rng.normal(0, 60))
            gust = p["gust"][d] * (0.6 + 0.4 * math.sin((hr - 6) / 24 * 2 * math.pi) ** 2) * rng.uniform(.85, 1.0)
            uv = max(0.0, p["uv"][d] * math.sin((hr - 6.5) / 11 * math.pi)) if 7 <= hr <= 17 else 0.0
            aqi = p["aqi"][d] * (1.15 if hr <= 8 or hr >= 21 else 0.9) * rng.uniform(.93, 1.07)
            code = weather_code(rain_h[hr], vis, cloud)
            codes.append(code)
            h["time"].append(f"{day:%Y-%m-%d}T{hr:02d}:00")
            h["temperature_2m"].append(round(t, 1))
            h["apparent_temperature"].append(round(t + (rh - 50) / 15 * (1 if t > 26 else 0.3), 1))
            h["relative_humidity_2m"].append(round(rh))
            h["precipitation_probability"].append(int(np.clip(p["prob"][d] * (1.1 if 13 <= hr <= 21 else .6), 0, 100)))
            h["precipitation"].append(round(float(rain_h[hr]), 1))
            h["weather_code"].append(code)
            h["cloud_cover"].append(round(cloud))
            h["wind_speed_10m"].append(round(gust * 0.55, 1))
            h["wind_gusts_10m"].append(round(gust, 1))
            h["uv_index"].append(round(uv, 1))
            h["visibility"].append(round(vis))
            air["time"].append(f"{day:%Y-%m-%d}T{hr:02d}:00")
            air["us_aqi"].append(round(aqi))
            air["pm2_5"].append(round(aqi * 0.42, 1))
            air["pm10"].append(round(aqi * 0.75, 1))
        daily["time"].append(f"{day:%Y-%m-%d}")
        daily["weather_code"].append(max(codes, key=lambda c: (c >= 61, c == 45, c)))
        daily["temperature_2m_max"].append(round(max(h["temperature_2m"][-24:]), 1))
        daily["temperature_2m_min"].append(round(min(h["temperature_2m"][-24:]), 1))
        daily["precipitation_sum"].append(round(float(rain_h.sum()), 1))
        daily["precipitation_probability_max"].append(max(h["precipitation_probability"][-24:]))
        daily["wind_speed_10m_max"].append(round(max(h["wind_speed_10m"][-24:]), 1))
        daily["wind_gusts_10m_max"].append(round(max(h["wind_gusts_10m"][-24:]), 1))
        daily["uv_index_max"].append(round(max(h["uv_index"][-24:]), 1))
        daily["sunrise"].append(f"{day:%Y-%m-%d}T06:{20 + d % 5:02d}")
        daily["sunset"].append(f"{day:%Y-%m-%d}T17:{40 + d % 5:02d}")

    i = 14  # "current" = 14:00 on the first day
    current = {k: h[k][i] for k in ["temperature_2m", "apparent_temperature", "relative_humidity_2m", "precipitation",
                                     "weather_code", "cloud_cover", "wind_speed_10m", "wind_gusts_10m"]}
    current["time"] = h["time"][i]
    forecast = {"latitude": city["lat"], "longitude": city["lon"], "timezone": "Asia/Kolkata",
                "current": current, "hourly": h, "daily": daily, "sample": True}
    return forecast, {"latitude": city["lat"], "longitude": city["lon"], "hourly": air, "sample": True}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for city in CITIES:
        forecast, air = build(city)
        key = city["name"].lower()
        (OUT / f"{key}_forecast.json").write_text(json.dumps(forecast))
        (OUT / f"{key}_air.json").write_text(json.dumps(air))
        d = forecast["daily"]
        print(f"{city['name']:10} max {max(d['temperature_2m_max'])}°C  min {min(d['temperature_2m_min'])}°C  "
              f"rain {sum(d['precipitation_sum']):.0f} mm  max AQI {max(air['hourly']['us_aqi'])}")


if __name__ == "__main__":
    main()
