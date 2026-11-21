"""
Deliver alerts.

- AlertLog: SQLite history of every alert, so the same alert is not sent
  again on the next scheduled run (only new or worsened alerts are "new").
- send_email(): HTML email through SMTP (Gmail etc.) using settings from .env.
  In dry-run mode the email is saved to outputs/alert_emails/ instead.
"""

import os
import smtplib
import sqlite3
import ssl
from datetime import datetime
from email.message import EmailMessage
from html import escape
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

from .alerts import SEVERITY_RANK, Alert

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
COLOURS = {"critical": "#DC2626", "warning": "#F59E0B", "info": "#2563EB"}
ICONS = {"critical": "🔴", "warning": "🟠", "info": "🔵"}


class AlertLog:
    def __init__(self, path: Path = ROOT / "outputs" / "alert_history.db"):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("""CREATE TABLE IF NOT EXISTS alerts (
            city TEXT, start TEXT, end TEXT, rule_id TEXT, severity TEXT, value REAL, message TEXT,
            first_seen TEXT, PRIMARY KEY (city, start, rule_id))""")

    def new_alerts(self, alerts: list[Alert]) -> list[Alert]:
        """Store alerts; return only those not seen before (or whose value got worse)."""
        fresh = []
        for a in alerts:
            row = self.conn.execute("SELECT value FROM alerts WHERE city=? AND start=? AND rule_id=?",
                                    (a.city, a.start, a.rule_id)).fetchone()
            worse = row is not None and abs(a.value) > abs(row[0]) * 1.05
            if row is None or worse:
                fresh.append(a)
                self.conn.execute("INSERT OR REPLACE INTO alerts VALUES (?,?,?,?,?,?,?,?)",
                                  (a.city, a.start, a.end, a.rule_id, a.severity, a.value, a.message,
                                   datetime.now().isoformat(timespec="seconds")))
        self.conn.commit()
        return fresh

    def history(self) -> pd.DataFrame:
        return pd.read_sql_query("SELECT * FROM alerts ORDER BY first_seen DESC", self.conn)

    def close(self) -> None:
        self.conn.close()


def alert_email_html(alerts: list[Alert]) -> str:
    rows = "".join(
        f'<tr><td style="padding:10px;border-left:5px solid {COLOURS[a.severity]};background:#F8FAFC">'
        f'<b>{ICONS[a.severity]} {escape(a.message)}</b><br><span style="color:#475569">{escape(a.advice)}</span>'
        f'</td></tr><tr><td style="height:8px"></td></tr>'
        for a in sorted(alerts, key=lambda x: -SEVERITY_RANK[x.severity]))
    return (f'<div style="font-family:Segoe UI,Arial;max-width:640px;margin:auto">'
            f'<div style="background:#0369A1;color:white;padding:18px 22px;border-radius:12px 12px 0 0">'
            f'<div style="font-size:22px;font-weight:700">⛈️ Weather alerts</div>'
            f'<div style="opacity:.9">{len(alerts)} new alert(s) · {datetime.now():%d %b %Y %H:%M}</div></div>'
            f'<table width="100%" style="border-collapse:collapse;margin-top:12px">{rows}</table>'
            f'<p style="color:#94A3B8;font-size:12px">Weather Forecast &amp; Alert Application · data: Open-Meteo</p></div>')


def send_email(alerts: list[Alert], to: str, dry_run: bool | None = None) -> str:
    if not alerts:
        return "no alerts to send"
    user, password = os.getenv("SMTP_USER", ""), os.getenv("SMTP_PASSWORD", "")
    dry = (os.getenv("DRY_RUN", "true").lower() == "true") if dry_run is None else dry_run
    msg = EmailMessage()
    worst = max(alerts, key=lambda a: SEVERITY_RANK[a.severity])
    msg["Subject"] = f"{ICONS[worst.severity]} {len(alerts)} weather alert(s): {worst.name} in {worst.city}"
    msg["From"], msg["To"] = user or "weather-bot@example.com", to
    msg.set_content("\n\n".join(f"{a.message}\n{a.advice}" for a in alerts))
    msg.add_alternative(alert_email_html(alerts), subtype="html")
    if dry or not (user and password):
        folder = ROOT / "outputs" / "alert_emails"
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"alerts_{datetime.now():%Y%m%d_%H%M%S}.eml"
        path.write_bytes(bytes(msg))
        (path.with_suffix(".html")).write_text(alert_email_html(alerts), encoding="utf-8")
        return f"dry-run: saved {path.relative_to(ROOT)}"
    with smtplib.SMTP(os.getenv("SMTP_HOST", "smtp.gmail.com"), int(os.getenv("SMTP_PORT", "587")), timeout=30) as s:
        s.starttls(context=ssl.create_default_context())
        s.login(user, password)
        s.send_message(msg)
    return f"emailed {len(alerts)} alert(s) to {to}"
