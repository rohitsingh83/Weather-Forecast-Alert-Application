# Interview Preparation: Weather Forecast & Alert Application (10 Q&As)

1. **Explain your project (Non-Technical):** It's a weather monitoring app that tracks 7-day forecasts for multiple cities, automatically detects hazards like heavy rain or heatwaves, and plots clear temperature and rainfall charts.
2. **Explain your project (Technical):** It ingests multi-city weather payloads into SQLite, evaluates typed `AlertRule` thresholds (`RAIN_SOON`, `HEAT_WAVE`, `WIND_HIGH`, `UV_HIGH`), logs alerts, generates Matplotlib dual-axis plots, and serves JSON via FastAPI.
3. **Why support both live API and simulation modes?** Simulation mode guarantees deterministic testing and offline demos without hitting API rate limits or exposing keys.
4. **How are alert thresholds structured?** `src/rules.py` uses an `Alert` dataclass with severity levels (`info`, `warn`, `critical`) so rules can be extended cleanly.
5. **How do you prevent duplicate alert spam?** By logging fired alerts in `alert_log` with timestamps and debouncing identical alerts within a 12-hour window.
6. **Why normalize units at ingestion?** Different providers mix °F/°C or mph/m/s; normalizing to °C, mm, and m/s keeps the rule engine provider-agnostic.
7. **What does `tests/test_weather.py` verify?** A golden payload test confirms all 4 alert codes trigger accurately at boundary thresholds.
8. **How is the database schema normalized?** `locations` stores city coordinates/timezones once, while `weather_daily` references `location_id` with a composite primary key `(location_id, date)`.
9. **How would you automate periodic updates in production?** Run `jobs/refresh.py` via cron or `APScheduler` every 1–3 hours.
10. **What channels can deliver alerts?** Email (SMTP), Telegram Bot API, or SMS/WhatsApp via Twilio.
