# Interview Preparation: Weather Forecast & Alert Application

### 1. Explain your project.

**HR version:** I built a weather app that shows current conditions, an hourly forecast and a 7-day forecast
for any city, including air pollution. Its main job is warning people early about dangerous weather: heat
waves, heavy rain, strong winds, fog or toxic air. Each warning explains what to do, and the app can send them
by email automatically.

**Technical version:** It's a Python app built on three Open-Meteo REST APIs: geocoding, forecast and air
quality. The API client uses `requests` with timeouts, retries with exponential backoff, a local cache and an
offline fallback. JSON is converted into Pandas hourly and daily tables. I derive daily AQI and minimum
visibility from the hourly data, and map WMO weather codes to text and icons. Alerts come from a configurable
rule engine with thresholds in JSON (IMD-style defaults). It keeps only the most severe alert per hazard per
day, merges consecutive days, and uses SQLite to notify only about new alerts. Delivery is by SMTP email. There's
a Streamlit + Plotly dashboard, a Rich CLI with a watch scheduler, and 12 pytest tests.

### 2. Why Open-Meteo instead of OpenWeatherMap?

It's free, needs no API key (so no secret to protect or leak), gives hourly data for 7+ days, and has an
air-quality API with the same format. The code structure would be the same for any provider: only the URL and
the JSON field names change.

### 3. How do you handle API failures?

Every request has a 10-second timeout and up to 3 attempts with exponential backoff (1 s, 2 s). If the live
call still fails, the app uses the last cached response, and if there's none, the bundled sample forecast. The
UI clearly labels which source is in use. Air quality is optional, so if only that call fails the forecast
still works.

### 4. Explain the alert rule engine.

Rules live in `data/alert_rules.json`: metric, operator, threshold, severity and advice. For each forecast day
and each rule, I check `value OP threshold` using Python's `operator` module, so no if-else chains or `eval`
are needed. Users can change thresholds in the dashboard without touching code.

### 5. How did you avoid "alert fatigue"?

Three things. Severity families: if "Very hot day" and "Heat wave" both trigger, only "Heat wave" is shown.
Merging: consecutive days of the same alert become one alert with a date range and the worst value. And an
SQLite history means scheduled runs only email new alerts or alerts that got noticeably worse. In the sample
data this turned nearly 50 day-by-day alerts into 15 clear ones.

### 6. What is AQI and how did you categorise it?

The Air Quality Index turns pollutant concentrations (PM2.5, PM10, ozone, etc.) into one 0–500 number. I use
the US EPA bands that Open-Meteo returns: 0–50 Good, 51–100 Moderate, 101–150 Unhealthy for sensitive groups,
151–200 Unhealthy, 201–300 Very unhealthy, 301+ Hazardous. India's NAQI uses different bands; supporting it
would mean adding another band table.

### 7. What are WMO weather codes?

A standard set of numbers that describe conditions: 0 clear sky, 45 fog, 61/63/65 light/moderate/heavy rain,
95 thunderstorm, and so on. Open-Meteo returns them, and I map each to a description and an emoji.

### 8. Why did you derive daily AQI and visibility yourself?

The daily forecast endpoint doesn't include them. I group the hourly data by date and take the maximum AQI and
the minimum visibility, because the worst hour is what matters for a warning.

### 9. How are notifications sent?

With `smtplib` over STARTTLS, using a Gmail App Password from a `.env` file. The email is multipart (HTML plus
plain text). Without credentials, or with `DRY_RUN=true`, it's saved as `.eml` and `.html` files, which keeps
testing safe.

### 10. How would you run it automatically?

`python main.py watch --every 60` checks every hour. In production I'd use Windows Task Scheduler or cron to run
`python main.py alerts` periodically. The de-duplication makes repeated runs safe.

### 11. How did you test code that depends on the internet?

Tests use the bundled sample data, and `monkeypatch` simulates network failure to check the fallback. Alert
logic is tested with known scenarios (Chennai heavy rain over 2 days, a week of unhealthy air in Kolkata, a
calm week in Hyderabad), plus the de-duplication log and the email dry-run.

### 12. What challenges did you face?

Designing alerts that are useful rather than noisy, handling missing air-quality data, timezones (Open-Meteo's
`timezone=auto` returns local times), and emoji: they work in the dashboard but Matplotlib's fonts can't draw
them, so the static charts use text labels instead.

### 13. How would you improve it?

SMS or WhatsApp alerts (Twilio), per-user locations and thresholds, push notifications, historical climate
comparison ("5 °C above normal"), IMD official warnings, and a FastAPI backend so a mobile app could use the
same alert engine.
