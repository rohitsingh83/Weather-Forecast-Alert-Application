"""
Rule-based alert engine.

Rules live in data/alert_rules.json, so thresholds can be changed without
touching code. Defaults follow IMD conventions where possible (heavy rain
>= 64.5 mm/day, heat wave >= 40 °C in the plains).

When several rules of the same family fire on the same day (e.g. HOT and
HEAT, or AQI_POOR and AQI_SEVERE), only the most severe one is kept.
"""

import json
import operator
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

RULES_FILE = Path(__file__).resolve().parent.parent / "data" / "alert_rules.json"
OPS = {">=": operator.ge, ">": operator.gt, "<=": operator.le, "<": operator.lt}
SEVERITY_RANK = {"info": 1, "warning": 2, "critical": 3}
FAMILY = {"HOT": "HEAT", "HEAT": "HEAT", "AQI_POOR": "AQI", "AQI_SEVERE": "AQI", "RAIN": "RAIN",
          "HEAVY_RAIN": "RAIN"}
UNITS = {"temperature_2m_max": "°C", "temperature_2m_min": "°C", "precipitation_sum": " mm",
         "precipitation_probability_max": "%", "wind_gusts_10m_max": " km/h", "uv_index_max": "",
         "us_aqi_max": " AQI", "visibility_min": " m"}


@dataclass
class Alert:
    city: str
    start: str        # first day (YYYY-MM-DD)
    end: str          # last day of a run of consecutive days
    rule_id: str
    name: str
    severity: str
    value: float      # worst value over the period
    threshold: float
    message: str
    advice: str
    metric: str = ""

    @property
    def days(self) -> int:
        return (pd.Timestamp(self.end) - pd.Timestamp(self.start)).days + 1

    def to_dict(self) -> dict:
        return asdict(self)


def load_rules(path: Path = RULES_FILE) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_rules(rules: list[dict], path: Path = RULES_FILE) -> None:
    path.write_text(json.dumps(rules, indent=2), encoding="utf-8")


def _describe(a: "Alert") -> str:
    unit = UNITS.get(a.metric, "")
    start, end = pd.Timestamp(a.start), pd.Timestamp(a.end)
    when = f"on {start:%a %d %b}" if a.days == 1 else f"from {start:%a %d} to {end:%a %d %b} ({a.days} days)"
    word = "lowest" if a.metric in ("temperature_2m_min", "visibility_min") else "peak"
    return f"{a.name} in {a.city} {when}: {word} {a.value:g}{unit} (limit {a.threshold:g}{unit})"


def evaluate(city: str, daily: pd.DataFrame, rules: list[dict] | None = None) -> list[Alert]:
    """Check every rule against every forecast day, then merge consecutive days into one alert."""
    rules = rules if rules is not None else load_rules()
    hits: list[Alert] = []
    for _, day in daily.iterrows():
        for rule in rules:
            value = day.get(rule["metric"])
            if value is None or pd.isna(value):
                continue
            if OPS[rule["operator"]](float(value), float(rule["threshold"])):
                d = day["time"].strftime("%Y-%m-%d")
                hits.append(Alert(city, d, d, rule["id"], rule["name"], rule["severity"], round(float(value), 1),
                                  float(rule["threshold"]), "", rule.get("advice", ""), rule["metric"]))

    # 1. keep only the most severe alert per family per day (HEAT beats HOT, AQI_SEVERE beats AQI_POOR)
    best: dict[tuple, Alert] = {}
    for a in hits:
        key = (a.start, FAMILY.get(a.rule_id, a.rule_id))
        if key not in best or SEVERITY_RANK[a.severity] > SEVERITY_RANK[best[key].severity]:
            best[key] = a

    # 2. merge consecutive days of the same rule into one alert, keeping the worst value
    merged: list[Alert] = []
    for a in sorted(best.values(), key=lambda x: (x.rule_id, x.start)):
        prev = merged[-1] if merged else None
        if prev and prev.rule_id == a.rule_id and (pd.Timestamp(a.start) - pd.Timestamp(prev.end)).days == 1:
            prev.end = a.end
            lower_is_worse = a.metric in ("temperature_2m_min", "visibility_min")
            prev.value = min(prev.value, a.value) if lower_is_worse else max(prev.value, a.value)
        else:
            merged.append(a)
    for a in merged:
        a.message = _describe(a)
    return sorted(merged, key=lambda a: (-SEVERITY_RANK[a.severity], a.start))


def to_frame(alerts: list[Alert]) -> pd.DataFrame:
    cols = ["city", "start", "end", "rule_id", "name", "severity", "value", "threshold", "message", "advice"]
    return pd.DataFrame([a.to_dict() for a in alerts], columns=cols + ["metric"])[cols]
