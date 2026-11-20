"""Centralized configuration for Weather Forecast & Alert Application."""

from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent)
    data_dir: Path = field(init=False)
    db_dir: Path = field(init=False)
    outputs_dir: Path = field(init=False)
    images_dir: Path = field(init=False)
    reports_dir: Path = field(init=False)
    
    db_path: Path = field(init=False)
    schema_path: Path = field(init=False)
    sample_json_path: Path = field(init=False)
    forecast_csv_path: Path = field(init=False)
    alerts_csv_path: Path = field(init=False)

    def __post_init__(self):
        root = self.root_dir
        object.__setattr__(self, "data_dir", root / "data")
        object.__setattr__(self, "db_dir", root / "db")
        object.__setattr__(self, "outputs_dir", root / "outputs")
        object.__setattr__(self, "images_dir", root / "images")
        object.__setattr__(self, "reports_dir", root / "reports")
        
        object.__setattr__(self, "db_path", root / "db" / "weather.db")
        object.__setattr__(self, "schema_path", root / "db" / "schema.sql")
        object.__setattr__(self, "sample_json_path", root / "data" / "sample_weather.json")
        object.__setattr__(self, "forecast_csv_path", root / "outputs" / "7day_forecast.csv")
        object.__setattr__(self, "alerts_csv_path", root / "reports" / "active_alerts.csv")
        
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
