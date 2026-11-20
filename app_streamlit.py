"""Interactive Streamlit dashboard for Weather Forecast & Alert Application."""

from pathlib import Path
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Weather Forecast & Alerts", layout="wide", page_icon="🌦️")
st.title("🌦️ Weather Forecast & Risk Alert Dashboard")

forecast_path = ROOT / "outputs" / "7day_forecast.csv"
alerts_path = ROOT / "reports" / "active_alerts.csv"
images_dir = ROOT / "images"

alerts_df = pd.read_csv(alerts_path) if alerts_path.exists() else pd.DataFrame()
forecast_df = pd.read_csv(forecast_path) if forecast_path.exists() else pd.DataFrame()

# Top KPI metrics
c1, c2, c3, c4 = st.columns(4)
total_locations = forecast_df["city"].nunique() if not forecast_df.empty else 0
c1.metric("Monitored Cities", total_locations)
total_alerts = len(alerts_df)
c2.metric("Active Risk Alerts", total_alerts)
critical_alerts = int((alerts_df["severity"] == "critical").sum()) if not alerts_df.empty else 0
c3.metric("Critical Alerts", critical_alerts)
warning_alerts = int((alerts_df["severity"] == "warn").sum()) if not alerts_df.empty else 0
c4.metric("Warnings", warning_alerts)

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["⚠️ Active Risk Alerts", "📈 7-Day Forecast Charts", "📅 Detailed Daily Forecasts"])

with tab1:
    st.subheader("Current Weather Risk Alerts & Early Warnings")
    if not alerts_df.empty:
        sev_filter = st.selectbox("Filter by Severity", ["All", "critical", "warn", "info"])
        filtered_alerts = alerts_df if sev_filter == "All" else alerts_df[alerts_df["severity"] == sev_filter]
        st.dataframe(filtered_alerts, use_container_width=True)
    else:
        st.info("No active weather alerts. Run `python main.py` to refresh.")

with tab2:
    st.subheader("Multi-City 7-Day Forecast Visualizations")
    chart_files = list(images_dir.glob("*_forecast.png")) if images_dir.exists() else []
    if chart_files:
        for cf in chart_files:
            city_title = cf.stem.replace("_", " ").title()
            st.image(str(cf), caption=city_title, use_container_width=True)
    else:
        st.info("Forecast charts not yet generated. Run `python main.py` first.")

with tab3:
    st.subheader("Detailed 7-Day Meteorological Tables")
    if not forecast_df.empty:
        city_sel = st.selectbox("Select City", ["All"] + sorted(forecast_df["city"].unique().tolist()))
        city_df = forecast_df if city_sel == "All" else forecast_df[forecast_df["city"] == city_sel]
        st.dataframe(city_df, use_container_width=True)
    else:
        st.info("Forecast data not found. Run `python main.py` first.")
