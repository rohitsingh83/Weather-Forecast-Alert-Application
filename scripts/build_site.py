"""Build the GitHub Pages report: python scripts/build_site.py  -> docs/index.html (uses bundled sample forecasts)"""

import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from site_template import fig_html, page, table_html
from src.alerts import evaluate, load_rules
from src.api_client import get_weather, load_cities
from src.processing import aqi_category, daily_frame, hourly_frame

SEV = {"critical": "#EF4444", "warning": "#F59E0B", "info": "#38BDF8"}


def main() -> None:
    cities = load_cities()
    weather = {c.name: get_weather(c, "sample") for c in cities}
    rows, all_alerts = [], []
    for name, w in weather.items():
        d = daily_frame(w)
        a = evaluate(name, d)
        all_alerts += a
        rows.append({"City": name, "Max °C": d["temperature_2m_max"].max(), "Min °C": d["temperature_2m_min"].min(),
                     "Rain mm (7d)": round(d["precipitation_sum"].sum()), "Peak AQI": int(d["us_aqi_max"].max()),
                     "AQI category": aqi_category(d["us_aqi_max"].max())[0], "Alerts": len(a)})
    comp = pd.DataFrame(rows)

    h = hourly_frame(weather["Chennai"])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=h["time"], y=h["precipitation"], name="Rain mm/h", marker_color="#3B82F6"))
    fig.add_trace(go.Scatter(x=h["time"], y=h["temperature_2m"], name="Temperature °C", line=dict(color="#F97316")),
                  secondary_y=True)
    fig.update_layout(title="Chennai: 7-day hourly rain and temperature")
    aq = hourly_frame(weather["Delhi"])
    aqf = go.Figure(go.Scatter(x=aq["time"], y=aq["us_aqi"], line=dict(color="#e2e8f0")))
    for lo, hi, c in [(0, 50, "#22C55E"), (50, 100, "#EAB308"), (100, 150, "#F97316"), (150, 200, "#EF4444"),
                      (200, 300, "#A855F7"), (300, 500, "#7F1D1D")]:
        aqf.add_hrect(y0=lo, y1=hi, fillcolor=c, opacity=.15, line_width=0)
    aqf.update_layout(title="Delhi: hourly AQI forecast", yaxis_range=[0, 460])
    rng = px.bar(comp, x="City", y=["Min °C", "Max °C"], barmode="group", title="Temperature range by city",
                 color_discrete_sequence=["#38BDF8", "#F97316"])
    al = pd.DataFrame([{"City": a.city, "Severity": a.severity.upper(), "Alert": a.message, "Advice": a.advice}
                       for a in all_alerts])
    rules = pd.DataFrame(load_rules())[["name", "metric", "operator", "threshold", "severity"]]
    html = page(
        title="Weather Forecast & Alert Application",
        tagline="Hourly and 7-day forecasts with air quality, plus early warnings for heat, rain, wind, fog and "
                "toxic air, each with practical advice.",
        accent="#38BDF8", repo="Weather-Forecast-Alert-Application",
        kpis=[("Cities monitored", str(len(cities))), ("Alert rules", str(len(rules))),
              ("Active alerts", str(len(all_alerts))), ("Critical alerts", str(sum(a.severity == "critical" for a in all_alerts))),
              ("Automated tests", "12")],
        sections=[
            ("Active alerts", "Most severe alert per hazard; consecutive days merged into one warning.",
             f'<div class="scroll">{table_html(al)}</div>'),
            ("City comparison", "Next 7 days across six Indian cities.",
             f'<div class="grid2">{fig_html(rng, 380)}<div>{table_html(comp)}</div></div>'),
            ("Hourly forecast", "Chennai's heavy-rain spell, hour by hour.", fig_html(fig, 420)),
            ("Air quality", "Background colours show US AQI categories.", fig_html(aqf, 380)),
            ("Alert rules", "Configurable thresholds (data/alert_rules.json), IMD-style defaults.", table_html(rules)),
        ],
        note="Forecasts on this page are SIMULATED sample data for 21–27 Nov 2026, bundled for offline use. "
             "Run the app on your computer for the live Open-Meteo forecast.",
        run_cmds=["pip install -r requirements.txt", "python main.py forecast Chennai", "python main.py alerts",
                  "streamlit run app.py"])
    out = ROOT / "docs" / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main()
