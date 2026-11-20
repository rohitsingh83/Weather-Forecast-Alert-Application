"""7-day temperature and rainfall visualization charts."""

from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def save_weather_charts(payload: dict, images_dir: Path) -> None:
    loc = payload["locations"][0]
    df = pd.DataFrame(loc["daily"])

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)
    ax1.plot(df["date"], df["temp_max_c"], marker="o", color="#D84315", label="Max Temp (C)")
    ax1.plot(df["date"], df["temp_min_c"], marker="o", color="#1565C0", label="Min Temp (C)")
    ax1.set_title(f"{loc['name']} - 7-Day Temperature & Rainfall Forecast", fontweight="bold")
    ax1.set_ylabel("Temperature (C)")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.bar(df["date"], df["precip_mm"], color="#0288D1", alpha=0.8, label="Rainfall (mm)")
    ax2.set_ylabel("Rainfall (mm)")
    ax2.set_xlabel("Date")
    ax2.legend()
    ax2.grid(alpha=0.3)

    plt.xticks(rotation=25)
    plt.tight_layout()
    plt.savefig(images_dir / f"{loc['name'].lower()}_7day_forecast.png", dpi=150)
    plt.close(fig)
