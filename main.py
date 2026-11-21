"""
Weather Forecast & Alert Application: command-line tool.

    python main.py forecast Delhi               current weather + 7-day forecast + alerts
    python main.py forecast "Pune"              any city worldwide (live API looks it up)
    python main.py alerts                       alerts for all cities in data/cities.json
    python main.py alerts --email you@gmail.com email new alerts (dry-run saves an .html copy)
    python main.py watch --every 60             re-check every 60 minutes, notify only new alerts
    python main.py compare                      side-by-side summary of all cities

--source auto (default) uses the live Open-Meteo API and falls back to bundled sample data offline.
"""

import argparse
import os
import time
from pathlib import Path

import pandas as pd
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.alerts import evaluate, to_frame
from src.api_client import City, geocode, get_weather, load_cities
from src.charts import city_comparison_chart, forecast_chart
from src.notifier import AlertLog, send_email
from src.processing import aqi_category, current_conditions, daily_frame, hourly_frame

ROOT = Path(__file__).resolve().parent
OUT, IMG = ROOT / "outputs", ROOT / "images"
console = Console()
SEV = {"critical": "bold red", "warning": "yellow", "info": "cyan"}
SOURCE = {"live": "[green]live Open-Meteo data[/]", "cache": "[yellow]cached forecast[/]",
          "sample": "[yellow]offline SAMPLE forecast (simulated)[/]"}


def resolve(name: str) -> City:
    city = geocode(name)
    if city is None:
        raise SystemExit(f"City '{name}' not found (offline you can use: "
                         f"{', '.join(c.name for c in load_cities())})")
    return city


def print_alerts(alerts) -> None:
    if not alerts:
        console.print("[green]✔ No weather alerts.[/]")
        return
    t = Table(title="⚠️ Alerts", header_style="bold white on dark_red")
    for col in ["Severity", "Alert", "What to do"]:
        t.add_column(col)
    for a in alerts:
        t.add_row(f"[{SEV[a.severity]}]{a.severity.upper()}[/]", a.message, a.advice)
    console.print(t)


def cmd_forecast(args):
    city = resolve(args.city)
    w = get_weather(city, args.source)
    daily, hourly, cur = daily_frame(w), hourly_frame(w), current_conditions(w)
    aqi = f" · AQI {cur['us_aqi']:.0f} ({cur['aqi_label']})" if pd.notna(cur.get("us_aqi")) else ""
    console.print(Panel.fit(
        f"[bold]{cur['icon']}  {cur['temperature_2m']:.1f}°C[/]  {cur['description']} · feels like "
        f"{cur['apparent_temperature']:.1f}°C\n💧 {cur['relative_humidity_2m']:.0f}% humidity · 💨 "
        f"{cur['wind_speed_10m']:.0f} km/h wind{aqi}\n{SOURCE[w.source]}",
        title=f"📍 {city.name}{', ' + city.state if city.state else ''}", border_style="blue"))

    t = Table(title="7-day forecast", header_style="bold white on blue")
    for col in ["Day", "", "Weather", "Max", "Min", "Rain", "Chance", "Gusts", "UV", "AQI"]:
        t.add_column(col, justify="right" if col in {"Max", "Min", "Rain", "Chance", "Gusts", "UV", "AQI"} else "left")
    for _, d in daily.iterrows():
        aqi_val = d.get("us_aqi_max")
        t.add_row(f"{d['time']:%a %d %b}", d["icon"], d["description"], f"{d['temperature_2m_max']:.0f}°",
                  f"{d['temperature_2m_min']:.0f}°", f"{d['precipitation_sum']:.0f} mm",
                  f"{d['precipitation_probability_max']:.0f}%", f"{d['wind_gusts_10m_max']:.0f} km/h",
                  f"{d['uv_index_max']:.0f}", f"{aqi_val:.0f}" if pd.notna(aqi_val) else "-")
    console.print(t)
    print_alerts(evaluate(city.name, daily))
    IMG.mkdir(exist_ok=True)
    path = forecast_chart(city.name, daily, hourly, IMG / f"{city.key}_forecast.png")
    console.print(f"Chart saved to {path.relative_to(ROOT)}")


def check_all(source: str, email: str | None) -> list:
    cities = load_cities()
    all_alerts = []
    for city in cities:
        w = get_weather(city, source)
        all_alerts += evaluate(city.name, daily_frame(w))
    console.print(f"Checked {len(cities)} cities · {SOURCE[w.source]}")
    print_alerts(all_alerts)
    log = AlertLog()
    fresh = log.new_alerts(all_alerts)
    log.close()
    OUT.mkdir(exist_ok=True)
    to_frame(all_alerts).to_csv(OUT / "active_alerts.csv", index=False)
    console.print(f"{len(fresh)} new alert(s) since the last run · saved outputs/active_alerts.csv")
    if email and fresh:
        console.print(send_email(fresh, email))
    return fresh


def cmd_alerts(args):
    check_all(args.source, args.email or os.getenv("ALERT_EMAIL_TO"))


def cmd_watch(args):
    console.print(f"Watching every {args.every} minutes. Press Ctrl+C to stop.")
    while True:
        check_all(args.source, args.email or os.getenv("ALERT_EMAIL_TO"))
        time.sleep(args.every * 60)


def cmd_compare(args):
    rows = []
    for city in load_cities():
        w = get_weather(city, args.source)
        d = daily_frame(w)
        alerts = evaluate(city.name, d)
        rows.append({"City": city.name, "Max temp": d["temperature_2m_max"].max(),
                     "Min temp": d["temperature_2m_min"].min(), "Rain (mm)": round(d["precipitation_sum"].sum(), 1),
                     "Peak AQI": d.get("us_aqi_max", pd.Series([float("nan")])).max(),
                     "Alerts": len(alerts), "Critical": sum(a.severity == "critical" for a in alerts)})
    df = pd.DataFrame(rows)
    t = Table(title=f"City comparison · next 7 days · {SOURCE[w.source]}", header_style="bold white on blue")
    for col in df.columns:
        t.add_column(col, justify="left" if col == "City" else "right")
    for r in df.itertuples(index=False):
        label = aqi_category(r[4])[0]
        t.add_row(r[0], f"{r[1]:.1f}°C", f"{r[2]:.1f}°C", f"{r[3]:.0f}", f"{r[4]:.0f} ({label})", str(r[5]),
                  f"[red]{r[6]}[/]" if r[6] else "0")
    console.print(t)
    OUT.mkdir(exist_ok=True)
    IMG.mkdir(exist_ok=True)
    df.to_csv(OUT / "city_comparison.csv", index=False)
    city_comparison_chart(df, IMG / "city_comparison.png")
    console.print("Saved outputs/city_comparison.csv and images/city_comparison.png")


def main():
    p = argparse.ArgumentParser(description="Weather Forecast & Alert Application")
    p.add_argument("--source", choices=["auto", "live", "sample"], default="auto")
    sub = p.add_subparsers(dest="command")
    f = sub.add_parser("forecast")
    f.add_argument("city", nargs="?", default="Delhi")
    a = sub.add_parser("alerts")
    a.add_argument("--email")
    w = sub.add_parser("watch")
    w.add_argument("--every", type=int, default=60)
    w.add_argument("--email")
    sub.add_parser("compare")
    args = p.parse_args()
    if args.command is None:
        args = p.parse_args(["forecast"])
    {"forecast": cmd_forecast, "alerts": cmd_alerts, "watch": cmd_watch, "compare": cmd_compare}[args.command](args)


if __name__ == "__main__":
    main()
