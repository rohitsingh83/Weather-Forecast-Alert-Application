"""Multi-city 7-day temperature and rainfall visualization charts."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_weather_charts(payload: dict, images_dir: Path) -> None:
    """Generate and save dual-axis forecast charts for all monitored locations.
    
    Args:
        payload: Ingested weather dictionary containing a list of 'locations'.
        images_dir: Destination directory for rendered chart images.
    """
    images_dir.mkdir(parents=True, exist_ok=True)
    
    for loc in payload.get("locations", []):
        df = pd.DataFrame(loc["daily"])
        if df.empty:
            continue

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
        ax1.plot(df["date"], df["temp_max_c"], marker="o", color="#D84315", linewidth=2, label="Max Temp (°C)")
        ax1.plot(df["date"], df["temp_min_c"], marker="o", color="#1565C0", linewidth=2, label="Min Temp (°C)")
        ax1.set_title(f"{loc['name']} — 7-Day Temperature Envelope & Rainfall", fontweight="bold", fontsize=12)
        ax1.set_ylabel("Temperature (°C)")
        ax1.legend(loc="upper right")
        ax1.grid(alpha=0.3)

        ax2.bar(df["date"], df["precip_mm"], color="#0288D1", alpha=0.8, label="Rainfall (mm)")
        ax2.set_ylabel("Precipitation (mm)")
        ax2.set_xlabel("Forecast Date")
        ax2.legend(loc="upper right")
        ax2.grid(alpha=0.3)

        plt.xticks(rotation=25)
        plt.tight_layout()
        chart_filename = f"{loc['name'].lower().replace(' ', '_')}_7day_forecast.png"
        plt.savefig(images_dir / chart_filename, dpi=150)
        plt.close(fig)
