"""Static Matplotlib charts for the README and reports."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 9})


def forecast_chart(city: str, daily: pd.DataFrame, hourly: pd.DataFrame, path: Path) -> Path:
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 7), gridspec_kw={"height_ratios": [3, 2]})
    ax1.fill_between(hourly["time"], hourly["temperature_2m"], color="#FDBA74", alpha=.25)
    ax1.plot(hourly["time"], hourly["temperature_2m"], color="#EA580C", lw=1.6, label="Temperature")
    ax1.plot(hourly["time"], hourly["apparent_temperature"], color="#9A3412", lw=1, ls="--", label="Feels like")
    for _, d in daily.iterrows():
        # emoji are not in Matplotlib's fonts, so the chart uses the text description
        ax1.annotate(f"{d['description']}\n{d['temperature_2m_max']:.0f}° / {d['temperature_2m_min']:.0f}°",
                     (d["time"] + pd.Timedelta(hours=12), hourly["temperature_2m"].max() + 1.2),
                     ha="center", fontsize=7.5, color="#334155")
    ax1.set_ylim(hourly["temperature_2m"].min() - 2, hourly["temperature_2m"].max() + 5)
    ax1.set_ylabel("°C")
    ax1.legend(loc="lower left", frameon=False)
    ax1.set_title(f"{city}: 7-day forecast", weight="bold", fontsize=13)
    ax2.bar(hourly["time"], hourly["precipitation"], width=0.04, color="#2563EB", label="Rain (mm/h)")
    ax2b = ax2.twinx()
    ax2b.plot(hourly["time"], hourly["precipitation_probability"], color="#60A5FA", lw=1, label="Rain chance %")
    ax2b.set_ylim(0, 105)
    ax2b.spines["top"].set_visible(False)
    ax2.set_ylabel("mm per hour")
    ax2b.set_ylabel("Chance of rain (%)")
    for ax in (ax1, ax2):
        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d"))
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def city_comparison_chart(summary: pd.DataFrame, path: Path) -> Path:
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.2))
    s = summary.sort_values("Max temp")
    axes[0].barh(s["City"], s["Max temp"], color="#F97316", label="Max")
    axes[0].barh(s["City"], s["Min temp"], color="#38BDF8", label="Min")
    axes[0].set_title("Temperature range (°C)", weight="bold")
    axes[0].legend(frameon=False)
    s = summary.sort_values("Rain (mm)")
    axes[1].barh(s["City"], s["Rain (mm)"], color="#2563EB")
    axes[1].set_title("Total rain next 7 days (mm)", weight="bold")
    s = summary.sort_values("Peak AQI")
    colours = ["#22C55E" if v <= 50 else "#EAB308" if v <= 100 else "#F97316" if v <= 150 else "#EF4444" if v <= 200
               else "#A855F7" if v <= 300 else "#7F1D1D" for v in s["Peak AQI"]]
    axes[2].barh(s["City"], s["Peak AQI"], color=colours)
    axes[2].set_title("Peak air quality index (US AQI)", weight="bold")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
