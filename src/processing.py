"""Turn API JSON into tidy Pandas tables and human-friendly labels."""

import pandas as pd

from .api_client import WeatherData

# WMO weather codes -> (description, emoji)
WMO = {
    0: ("Clear sky", "☀️"), 1: ("Mainly clear", "🌤️"), 2: ("Partly cloudy", "⛅"), 3: ("Overcast", "☁️"),
    45: ("Fog", "🌫️"), 48: ("Freezing fog", "🌫️"), 51: ("Light drizzle", "🌦️"), 53: ("Drizzle", "🌦️"),
    55: ("Heavy drizzle", "🌧️"), 61: ("Light rain", "🌦️"), 63: ("Rain", "🌧️"), 65: ("Heavy rain", "🌧️"),
    71: ("Light snow", "🌨️"), 73: ("Snow", "🌨️"), 75: ("Heavy snow", "❄️"), 80: ("Rain showers", "🌦️"),
    81: ("Heavy showers", "🌧️"), 82: ("Violent showers", "⛈️"), 95: ("Thunderstorm", "⛈️"),
    96: ("Thunderstorm with hail", "⛈️"), 99: ("Severe thunderstorm", "⛈️"),
}

# US AQI bands (used by Open-Meteo) -> label, colour
AQI_BANDS = [(50, "Good", "#22C55E"), (100, "Moderate", "#EAB308"), (150, "Unhealthy for sensitive groups", "#F97316"),
             (200, "Unhealthy", "#EF4444"), (300, "Very unhealthy", "#A855F7"), (10_000, "Hazardous", "#7F1D1D")]


def describe(code: int) -> tuple[str, str]:
    return WMO.get(int(code), ("Unknown", "🌡️"))


def aqi_category(aqi: float | None) -> tuple[str, str]:
    if aqi is None or pd.isna(aqi):
        return "No data", "#94A3B8"
    for upper, label, colour in AQI_BANDS:
        if aqi <= upper:
            return label, colour
    return AQI_BANDS[-1][1], AQI_BANDS[-1][2]


def hourly_frame(w: WeatherData) -> pd.DataFrame:
    df = pd.DataFrame(w.forecast["hourly"])
    df["time"] = pd.to_datetime(df["time"])
    if w.air and "hourly" in w.air:
        air = pd.DataFrame(w.air["hourly"])
        air["time"] = pd.to_datetime(air["time"])
        df = df.merge(air, on="time", how="left")
    return df


def daily_frame(w: WeatherData) -> pd.DataFrame:
    """Daily table, enriched with daily AQI max and minimum visibility derived from hourly data."""
    df = pd.DataFrame(w.forecast["daily"])
    df["time"] = pd.to_datetime(df["time"])
    h = hourly_frame(w)
    h["date"] = h["time"].dt.normalize()
    agg = {"visibility": "min"}
    if "us_aqi" in h:
        agg["us_aqi"] = "max"
    extra = h.groupby("date").agg(agg).rename(columns={"visibility": "visibility_min", "us_aqi": "us_aqi_max"})
    df = df.merge(extra, left_on="time", right_index=True, how="left")
    df["description"] = df["weather_code"].map(lambda c: describe(c)[0])
    df["icon"] = df["weather_code"].map(lambda c: describe(c)[1])
    return df


def current_conditions(w: WeatherData) -> dict:
    cur = dict(w.forecast.get("current", {}))
    h = hourly_frame(w)
    now = pd.to_datetime(cur.get("time")) if cur.get("time") else h["time"].iloc[0]
    row = h.iloc[(h["time"] - now).abs().argsort().iloc[0]]
    cur.setdefault("temperature_2m", row["temperature_2m"])
    cur["uv_index"] = row.get("uv_index")
    cur["us_aqi"] = row.get("us_aqi")
    cur["visibility"] = row.get("visibility")
    cur["description"], cur["icon"] = describe(cur.get("weather_code", row["weather_code"]))
    cur["aqi_label"], cur["aqi_colour"] = aqi_category(cur["us_aqi"])
    return cur
