"""Interactive Streamlit dashboard for Weather Forecast & Alert Application."""
from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Weather Forecast & Risk Alert Center",
    layout="wide",
    page_icon="🌦️",
)

st.title("🌦️ Weather Forecast & Risk Alert Center")
st.caption("7-Day Meteorological Monitoring, Dual-Axis Visualizations & Risk Warnings")

forecast_path = ROOT / "outputs" / "7day_forecast.csv"
alerts_path = ROOT / "reports" / "active_alerts.csv"
images_dir = ROOT / "images"

alerts_df = pd.read_csv(alerts_path) if alerts_path.exists() else pd.DataFrame()
forecast_df = pd.read_csv(forecast_path) if forecast_path.exists() else pd.DataFrame()

# Top KPIs
c1, c2, c3, c4 = st.columns(4)
total_locations = forecast_df["city"].nunique() if not forecast_df.empty else 0
c1.metric("Monitored Cities", total_locations)
total_alerts = len(alerts_df)
c2.metric("Active Hazard Alerts", total_alerts)
critical_alerts = int((alerts_df["severity"] == "critical").sum()) if not alerts_df.empty else 0
c3.metric("Critical Alerts", critical_alerts)
warning_alerts = int((alerts_df["severity"] == "warn").sum()) if not alerts_df.empty else 0
c4.metric("Warnings", warning_alerts)

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["⚠️ Risk Alerts", "📈 7-Day Charts", "📅 Detailed Tables", "🛡️ Hazard Rules"])

with tab1:
    st.subheader("Active Weather Risk Alerts & Early Warnings")
    if not alerts_df.empty:
        sev_filter = st.radio("Severity Level:", ["All", "critical", "warn", "info"], horizontal=True)
        filtered_alerts = alerts_df if sev_filter == "All" else alerts_df[alerts_df["severity"] == sev_filter]
        
        for _, r in filtered_alerts.iterrows():
            sev = r["severity"]
            badge_icon = "🔴" if sev == "critical" else ("🟡" if sev == "warn" else "🔵")
            st.markdown(f"**{badge_icon} [{r['code']}] {r['location_name']} ({r['date']})** — {r['message']}")
        
        st.dataframe(filtered_alerts, use_container_width=True)
    else:
        st.info("No active weather alerts reported.")

with tab2:
    st.subheader("7-Day Temperature & Rainfall Plots")
    chart_files = list(images_dir.glob("*_forecast.png")) if images_dir.exists() else []
    if chart_files:
        for cf in chart_files:
            city_title = cf.stem.replace("_", " ").title()
            st.image(str(cf), caption=city_title, use_container_width=True)
    else:
        st.info("Forecast charts not yet generated. Run `python main.py` first.")

with tab3:
    st.subheader("Daily Meteorological Data")
    if not forecast_df.empty:
        city_sel = st.selectbox("Select City", ["All"] + sorted(forecast_df["city"].unique().tolist()))
        city_df = forecast_df if city_sel == "All" else forecast_df[forecast_df["city"] == city_sel]
        st.dataframe(city_df, use_container_width=True)

with tab4:
    st.subheader("Defined Hazard Rules")
    st.markdown("""
    - **RAIN_SOON:** Precipitation probability $\ge 60\%$ (`warn`)
    - **HEAT_WAVE:** Max Temperature $\ge 40^\circ\text{C}$ (`critical`)
    - **WIND_HIGH:** Wind Gusts $\ge 15\text{ m/s}$ (`warn`)
    - **UV_HIGH:** UV Index $\ge 8.0$ (`info`)
    - **FROST_WARNING:** Min Temperature $\le 2^\circ\text{C}$ (`warn`)
    """)
