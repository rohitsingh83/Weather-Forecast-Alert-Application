"""
Weather Forecast & Alert dashboard.

Run:  streamlit run app.py
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from src.alerts import SEVERITY_RANK, evaluate, load_rules, save_rules, to_frame
from src.api_client import geocode, get_weather, load_cities
from src.notifier import alert_email_html, send_email
from src.processing import AQI_BANDS, aqi_category, current_conditions, daily_frame, hourly_frame

st.set_page_config(page_title="Weather & Alerts", page_icon="⛅", layout="wide")
SEV_COLOUR = {"critical": "#DC2626", "warning": "#F59E0B", "info": "#0284C7"}
SEV_ICON = {"critical": "🔴", "warning": "🟠", "info": "🔵"}

st.markdown("""
<style>
.block-container {padding-top: 3.2rem;}
.now {background: linear-gradient(135deg, #0369A1 0%, #0EA5E9 60%, #7DD3FC 100%); color: white; border-radius: 20px;
      padding: 1.5rem 2rem; margin-bottom: 1rem;}
.now .city {font-size: 1.4rem; opacity: .95;}
.now .temp {font-size: 4.2rem; font-weight: 800; line-height: 1.05;}
.now .desc {font-size: 1.25rem;}
.now .meta {opacity: .92; margin-top: .4rem;}
.stat {background: rgba(255,255,255,.18); border-radius: 12px; padding: .55rem .8rem; text-align: center;}
.stat .v {font-size: 1.35rem; font-weight: 700;} .stat .l {font-size: .78rem; opacity: .9; text-transform: uppercase;}
.day {background: white; border-radius: 16px; padding: .8rem .4rem; text-align: center; border: 1px solid #BAE6FD;
      box-shadow: 0 1px 3px rgba(2,132,199,.08);}
.day .d {font-weight: 600; color: #0C4A6E;} .day .i {font-size: 2rem;} .day .t {font-size: 1.05rem; font-weight: 700;}
.day .s {font-size: .78rem; color: #64748B;}
.alert {background: white; border-left: 6px solid; border-radius: 12px; padding: .7rem 1rem; margin-bottom: .55rem;
        box-shadow: 0 1px 2px rgba(0,0,0,.05);}
.alert .adv {color: #475569; font-size: .88rem;}
.banner {background: #FEF3C7; color: #92400E; border-radius: 10px; padding: .5rem .9rem; margin-bottom: .8rem;}
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=1800, show_spinner="Fetching forecast...")
def fetch(city_name: str, lat: float, lon: float, state: str, source: str):
    from src.api_client import City
    w = get_weather(City(city_name, lat, lon, state), source)
    return w


cities = load_cities()
with st.sidebar:
    st.header("⛅ Location")
    preset = st.selectbox("City", [c.name for c in cities])
    search = st.text_input("…or search any city", placeholder="e.g. Pune, Jaipur, London")
    source = st.radio("Data source", ["auto", "live", "sample"], horizontal=True,
                      help="auto = live Open-Meteo forecast, falls back to bundled sample data when offline")
    st.caption("Forecast data: Open-Meteo (free, no API key).")

city = geocode(search) if search.strip() else next(c for c in cities if c.name == preset)
if city is None:
    st.error(f"Couldn't find '{search}'. Offline, only these cities are available: "
             f"{', '.join(c.name for c in cities)}")
    st.stop()
try:
    w = fetch(city.name, city.lat, city.lon, city.state, source)
except Exception as exc:
    st.error(str(exc))
    st.stop()

daily, hourly, cur = daily_frame(w), hourly_frame(w), current_conditions(w)
alerts = evaluate(city.name, daily)
if w.source == "sample":
    st.markdown('<div class="banner">⚠️ Offline mode: showing a bundled <b>simulated</b> forecast for 21–27 Nov 2026. '
                'Run on a computer with internet for the live forecast.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------ hero: current conditions
aqi_txt = f"{cur['us_aqi']:.0f}" if pd.notna(cur.get("us_aqi")) else "–"
uv_txt = f"{cur['uv_index']:.0f}" if pd.notna(cur.get("uv_index")) else "–"
stats = [("Feels like", f"{cur['apparent_temperature']:.0f}°"), ("Humidity", f"{cur['relative_humidity_2m']:.0f}%"),
         ("Wind", f"{cur['wind_speed_10m']:.0f} km/h"), ("UV index", uv_txt), ("AQI", aqi_txt)]
stat_html = "".join(f'<div class="stat"><div class="v">{v}</div><div class="l">{l}</div></div>' for l, v in stats)
top = max(alerts, key=lambda a: SEVERITY_RANK[a.severity]) if alerts else None
st.markdown(f"""
<div class="now">
  <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:1rem;align-items:center">
    <div>
      <div class="city">📍 {city.name}{', ' + city.state if city.state else ''}</div>
      <div class="temp">{cur['icon']} {cur['temperature_2m']:.0f}°C</div>
      <div class="desc">{cur['description']} · today {daily.iloc[0]['temperature_2m_max']:.0f}° / {daily.iloc[0]['temperature_2m_min']:.0f}°</div>
      <div class="meta">{"⚠️ " + top.name + " expected" if top else "✅ No weather alerts for the next 7 days"} ·
        air quality: <b style="color:white;background:{cur['aqi_colour']};padding:0 .45rem;border-radius:6px">{cur['aqi_label']}</b></div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(5, 1fr);gap:.5rem;min-width:420px">{stat_html}</div>
  </div>
</div>""", unsafe_allow_html=True)

cols = st.columns(len(daily))
for col, (_, d) in zip(cols, daily.iterrows()):
    col.markdown(f'<div class="day"><div class="d">{d["time"]:%a %d}</div><div class="i">{d["icon"]}</div>'
                 f'<div class="t">{d["temperature_2m_max"]:.0f}° <span style="color:#64748B;font-weight:400">'
                 f'{d["temperature_2m_min"]:.0f}°</span></div><div class="s">💧 {d["precipitation_probability_max"]:.0f}% · '
                 f'{d["precipitation_sum"]:.0f} mm</div></div>', unsafe_allow_html=True)
st.write("")

tab_hourly, tab_alerts, tab_air, tab_compare, tab_rules = st.tabs(
    [f"📈 Hourly forecast", f"⚠️ Alerts ({len(alerts)})", "🌫️ Air quality", "🗺️ Compare cities", "⚙️ Alert rules"])

# ------------------------------------------------------------------ hourly
with tab_hourly:
    hours = st.select_slider("Show next", [24, 48, 72, 120, 168], value=72, format_func=lambda h: f"{h} hours")
    h = hourly.head(hours)
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        specs=[[{"secondary_y": False}], [{"secondary_y": True}], [{"secondary_y": True}]],
                        subplot_titles=("Temperature (°C)", "Rain", "Wind and UV"))
    fig.add_trace(go.Scatter(x=h["time"], y=h["temperature_2m"], name="Temperature", line=dict(color="#EA580C", width=2.5),
                             fill="tozeroy", fillcolor="rgba(251,146,60,.12)"), 1, 1)
    fig.add_trace(go.Scatter(x=h["time"], y=h["apparent_temperature"], name="Feels like",
                             line=dict(color="#9A3412", dash="dot")), 1, 1)
    fig.add_trace(go.Bar(x=h["time"], y=h["precipitation"], name="Rain (mm/h)", marker_color="#2563EB"), 2, 1)
    fig.add_trace(go.Scatter(x=h["time"], y=h["precipitation_probability"], name="Chance of rain (%)",
                             line=dict(color="#60A5FA")), 2, 1, secondary_y=True)
    fig.add_trace(go.Scatter(x=h["time"], y=h["wind_gusts_10m"], name="Gusts (km/h)", line=dict(color="#0F766E")), 3, 1)
    fig.add_trace(go.Scatter(x=h["time"], y=h["wind_speed_10m"], name="Wind (km/h)", line=dict(color="#5EEAD4")), 3, 1)
    fig.add_trace(go.Bar(x=h["time"], y=h["uv_index"], name="UV index", marker_color="rgba(234,179,8,.45)"), 3, 1,
                  secondary_y=True)
    fig.update_yaxes(range=[h["temperature_2m"].min() - 3, h["temperature_2m"].max() + 3], row=1, col=1)
    fig.update_yaxes(range=[0, 105], row=2, col=1, secondary_y=True)
    fig.update_layout(height=760, hovermode="x unified", legend=dict(orientation="h", y=-0.06),
                      margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="white", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig, width="stretch")
    with st.expander("Hourly data table"):
        st.dataframe(h, hide_index=True, width="stretch")

# ------------------------------------------------------------------ alerts
with tab_alerts:
    if not alerts:
        st.success(f"No alerts for {city.name} in the next 7 days. 🎉")
    a1, a2 = st.columns([3, 2])
    with a1:
        for a in alerts:
            st.markdown(f'<div class="alert" style="border-color:{SEV_COLOUR[a.severity]}">'
                        f'<b>{SEV_ICON[a.severity]} {a.severity.upper()}: {a.name}</b><br>{a.message}'
                        f'<div class="adv">👉 {a.advice}</div></div>', unsafe_allow_html=True)
    with a2:
        if alerts:
            timeline = to_frame(alerts).assign(start=lambda d: pd.to_datetime(d["start"]),
                                               finish=lambda d: pd.to_datetime(d["end"]) + pd.Timedelta(days=1))
            tl = px.timeline(timeline, x_start="start", x_end="finish", y="name", color="severity",
                             color_discrete_map=SEV_COLOUR, title="When each alert applies")
            tl.update_yaxes(autorange="reversed", title=None)
            tl.update_layout(height=320, margin=dict(l=10, r=10, t=50, b=10), legend_title=None,
                             paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(tl, width="stretch")
            st.markdown("**📧 Email these alerts**")
            to = st.text_input("Send to", placeholder="you@gmail.com")
            if st.button("Send alert email", type="primary", disabled=not to):
                st.success(send_email(alerts, to))
            with st.expander("Preview email"):
                st.components.v1.html(alert_email_html(alerts), height=420, scrolling=True)

# ------------------------------------------------------------------ air quality
with tab_air:
    if "us_aqi" not in hourly or hourly["us_aqi"].isna().all():
        st.info("Air-quality data is not available for this location.")
    else:
        q1, q2 = st.columns([1, 2])
        label, colour = aqi_category(cur["us_aqi"])
        gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=float(cur["us_aqi"]), title={"text": f"US AQI now: {label}"},
            gauge={"axis": {"range": [0, 500]}, "bar": {"color": "#0F172A", "thickness": 0.25},
                   "steps": [{"range": [lo, hi], "color": c} for lo, (hi, _, c) in
                             zip([0] + [b[0] for b in AQI_BANDS[:-1]], [(min(b[0], 500), b[1], b[2]) for b in AQI_BANDS])]}))
        gauge.update_layout(height=330, margin=dict(l=20, r=20, t=60, b=10), paper_bgcolor="rgba(0,0,0,0)")
        q1.plotly_chart(gauge, width="stretch")
        q1.markdown(f"PM2.5: **{hourly['pm2_5'].iloc[14]:.0f} µg/m³** · PM10: **{hourly['pm10'].iloc[14]:.0f} µg/m³**")
        aq = go.Figure()
        for lo, (hi, name, c) in zip([0] + [b[0] for b in AQI_BANDS[:-1]], AQI_BANDS):
            aq.add_hrect(y0=lo, y1=min(hi, 500), fillcolor=c, opacity=0.12, line_width=0)
        aq.add_trace(go.Scatter(x=hourly["time"], y=hourly["us_aqi"], line=dict(color="#0F172A", width=2), name="AQI"))
        aq.update_layout(title="AQI forecast (background colours = AQI category)", height=330, plot_bgcolor="white",
                         yaxis=dict(range=[0, max(hourly["us_aqi"].max() * 1.15, 120)]),
                         margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
        q2.plotly_chart(aq, width="stretch")
        st.caption("Bands: 0–50 Good · 51–100 Moderate · 101–150 Unhealthy for sensitive groups · 151–200 Unhealthy · "
                   "201–300 Very unhealthy · 301+ Hazardous")

# ------------------------------------------------------------------ compare
with tab_compare:
    rows = []
    for c in cities:
        try:
            cw = fetch(c.name, c.lat, c.lon, c.state, source)
        except Exception:
            continue
        cd, cc = daily_frame(cw), current_conditions(cw)
        ca = evaluate(c.name, cd)
        rows.append({"City": c.name, "lat": c.lat, "lon": c.lon, "Now °C": cc["temperature_2m"],
                     "Weather": f"{cc['icon']} {cc['description']}", "Max °C": cd["temperature_2m_max"].max(),
                     "Min °C": cd["temperature_2m_min"].min(), "Rain mm (7d)": round(cd["precipitation_sum"].sum()),
                     "Peak AQI": cd.get("us_aqi_max", pd.Series([None])).max(), "Alerts": len(ca),
                     "Worst": max((a.severity for a in ca), key=lambda s: SEVERITY_RANK[s], default="none")})
    comp = pd.DataFrame(rows)
    m1, m2 = st.columns([1, 1])
    geo = px.scatter(comp, x="Max °C", y="Peak AQI", size=comp["Rain mm (7d)"] + 8, color="Worst", text="City",
                     color_discrete_map={**SEV_COLOUR, "none": "#22C55E"}, size_max=45, hover_data=["Weather", "Alerts"],
                     title="Heat vs air quality (bubble = 7-day rain)")
    geo.update_traces(textposition="top center")
    for lo, (hi, name, c) in zip([0] + [b[0] for b in AQI_BANDS[:-1]], AQI_BANDS):
        geo.add_hrect(y0=lo, y1=min(hi, 500), fillcolor=c, opacity=0.08, line_width=0)
    geo.update_layout(height=470, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="white", legend_title="Worst alert",
                      yaxis_range=[0, max(comp["Peak AQI"].max() * 1.15, 150)])
    m1.plotly_chart(geo, width="stretch")
    rng = go.Figure()
    for _, r in comp.sort_values("Max °C").iterrows():
        rng.add_trace(go.Scatter(x=[r["Min °C"], r["Max °C"]], y=[r["City"]] * 2, mode="lines+markers",
                                 line=dict(color="#0EA5E9", width=8), marker=dict(size=12, color=["#38BDF8", "#F97316"]),
                                 showlegend=False))
    rng.update_layout(title="Temperature range over the next 7 days (°C)", height=470, plot_bgcolor="white",
                      margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor="rgba(0,0,0,0)")
    m2.plotly_chart(rng, width="stretch")
    st.dataframe(comp.drop(columns=["lat", "lon"]), hide_index=True, width="stretch")

# ------------------------------------------------------------------ rules
with tab_rules:
    st.markdown("Alert thresholds are stored in `data/alert_rules.json`. Edit them here, then save. Defaults follow "
                "India Meteorological Department conventions where possible (heavy rain ≥ 64.5 mm/day, heat wave ≥ 40 °C).")
    rules = pd.DataFrame(load_rules())
    edited = st.data_editor(rules, hide_index=True, width="stretch", num_rows="dynamic", column_config={
        "severity": st.column_config.SelectboxColumn(options=["info", "warning", "critical"]),
        "operator": st.column_config.SelectboxColumn(options=[">=", ">", "<=", "<"]),
        "level": st.column_config.SelectboxColumn(options=["daily"])})
    if st.button("💾 Save rules", type="primary"):
        save_rules(edited.to_dict(orient="records"))
        st.success("Saved. Alerts will use the new thresholds.")
        st.rerun()
