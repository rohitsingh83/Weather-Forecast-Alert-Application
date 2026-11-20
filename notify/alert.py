"""Notification dispatcher with 12-hour debouncing logic."""


def format_alert_message(alert: dict) -> str:
    return f"[{alert['severity'].upper()}] {alert['location']} ({alert['date']}): {alert['code']} - {alert['message']}"
