"""
Talk to the free Open-Meteo APIs (no API key needed):

  geocoding    https://geocoding-api.open-meteo.com/v1/search
  forecast     https://api.open-meteo.com/v1/forecast
  air quality  https://air-quality-api.open-meteo.com/v1/air-quality

source="auto"   live API, then the last cached response, then bundled sample data
source="live"   live API only
source="sample" bundled sample data only (offline demo)
"""

import json
import time
from dataclasses import dataclass
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CACHE = DATA / "cache"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

HOURLY = ["temperature_2m", "apparent_temperature", "relative_humidity_2m", "precipitation_probability",
          "precipitation", "weather_code", "cloud_cover", "wind_speed_10m", "wind_gusts_10m", "uv_index", "visibility"]
DAILY = ["weather_code", "temperature_2m_max", "temperature_2m_min", "precipitation_sum",
         "precipitation_probability_max", "wind_speed_10m_max", "wind_gusts_10m_max", "uv_index_max",
         "sunrise", "sunset"]
CURRENT = ["temperature_2m", "apparent_temperature", "relative_humidity_2m", "precipitation", "weather_code",
           "cloud_cover", "wind_speed_10m", "wind_gusts_10m"]


@dataclass
class City:
    name: str
    lat: float
    lon: float
    state: str = ""

    @property
    def key(self) -> str:
        return self.name.lower().replace(" ", "_")


@dataclass
class WeatherData:
    city: City
    forecast: dict
    air: dict | None
    source: str        # live / cache / sample


def load_cities() -> list[City]:
    return [City(**c) for c in json.loads((DATA / "cities.json").read_text(encoding="utf-8"))]


def _get(url: str, params: dict, retries: int = 3, timeout: int = 10) -> dict:
    """GET with retries and exponential backoff for flaky networks."""
    last = None
    for attempt in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    raise ConnectionError(f"Request to {url} failed: {last}")


def geocode(name: str) -> City | None:
    """Find a city's coordinates by name (live API, falls back to the built-in list)."""
    for c in load_cities():
        if c.name.lower() == name.strip().lower():
            return c
    try:
        data = _get(GEOCODE_URL, {"name": name, "count": 1, "language": "en", "format": "json"}, retries=1)
    except ConnectionError:
        return None
    if not data.get("results"):
        return None
    r = data["results"][0]
    return City(r["name"], r["latitude"], r["longitude"], r.get("admin1", ""))


def fetch_live(city: City) -> tuple[dict, dict | None]:
    common = {"latitude": city.lat, "longitude": city.lon, "timezone": "auto"}
    forecast = _get(FORECAST_URL, {**common, "hourly": ",".join(HOURLY), "daily": ",".join(DAILY),
                                   "current": ",".join(CURRENT), "forecast_days": 7})
    try:
        air = _get(AIR_URL, {**common, "hourly": "us_aqi,pm2_5,pm10", "forecast_days": 7}, retries=2)
    except ConnectionError:
        air = None   # air quality is optional
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"{city.key}.json").write_text(json.dumps({"forecast": forecast, "air": air}))
    return forecast, air


def get_weather(city: City, source: str = "auto") -> WeatherData:
    if source in ("auto", "live"):
        try:
            forecast, air = fetch_live(city)
            return WeatherData(city, forecast, air, "live")
        except ConnectionError:
            if source == "live":
                raise
            cached = CACHE / f"{city.key}.json"
            if cached.exists():
                data = json.loads(cached.read_text())
                return WeatherData(city, data["forecast"], data["air"], "cache")
    f = DATA / "sample" / f"{city.key}_forecast.json"
    if not f.exists():
        raise FileNotFoundError(f"No internet and no sample data for {city.name}. "
                                f"Offline cities: {', '.join(c.name for c in load_cities())}")
    a = DATA / "sample" / f"{city.key}_air.json"
    return WeatherData(city, json.loads(f.read_text()), json.loads(a.read_text()) if a.exists() else None, "sample")
