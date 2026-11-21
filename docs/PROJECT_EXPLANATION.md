# Project Explanation: Weather Forecast & Alert Application

## 1. What is it?

**Simple explanation.** An app that shows the weather for any city (right now, hour by hour, and for the next
7 days) including air pollution. More importantly, it **warns you in advance** about dangerous conditions:
heat waves, cold waves, heavy rain, strong winds, dense fog, high UV and unhealthy air. Each warning says what
to do, and the app can email the warnings automatically on a schedule.

**Technical explanation.** A Python application that consumes three REST APIs from Open-Meteo (geocoding,
forecast and air quality) with `requests`, retries, caching and an offline fallback. The JSON responses are
normalised into Pandas hourly and daily tables. Daily AQI and minimum visibility are derived from the hourly
data, and WMO weather codes are mapped to text and icons. A configurable rule engine (thresholds in JSON,
IMD-style defaults) evaluates every day, keeps the most severe alert per hazard family, and merges consecutive
days into a single alert. Alerts are de-duplicated across runs with SQLite and delivered by email (SMTP or
dry-run). Interfaces: a Streamlit + Plotly dashboard and a Rich CLI with a `watch` scheduler.

### Why it matters

Weather alerts protect lives and money: IMD warnings, farmers planning irrigation and harvest, logistics firms
re-routing trucks, airlines and railways handling fog, event planners, insurers, and city corporations
preparing for floods. It's also a classic **API integration + automation** project, a skill used in almost
every software job.

### Workflow

```
city name → geocoding API → forecast API + air-quality API → JSON → Pandas tables
   → derive daily AQI / visibility → evaluate alert rules → merge & de-duplicate
   → dashboard, CLI, CSV, email notification
```

## 2. Tech stack options

| Option | Tools | Difficulty | Output |
|---|---|---|---|
| A. Easy | requests, one API call, print() | Beginner | Today's temperature in the terminal |
| **B. Intermediate** ✅ | requests, Pandas, JSON rules, SQLite, smtplib, Matplotlib, Plotly, Streamlit | Intermediate | 7-day forecast, AQI, rule-based alerts, email, dashboard |
| C. Advanced | B + FastAPI backend, Celery scheduler, SMS/WhatsApp (Twilio), PostGIS, ML nowcasting | Advanced | Multi-user alert service |

**Chosen: B.** Open-Meteo is free and needs no API key (no secrets to manage), and every piece can be tested
offline.

## 3. Architecture

```
  INPUT        city name / data/cities.json        data/alert_rules.json        .env (optional SMTP)
                      │
  API LAYER    api_client.py  geocode() ─► forecast + air quality ─► cache ─► sample fallback
                      │       (requests, timeout, 3 retries with exponential backoff)
  PROCESSING   processing.py  hourly_frame() · daily_frame() (+ daily AQI max, min visibility)
                              current_conditions() · WMO code → text/emoji · AQI category
                      │
  RULES        alerts.py      for each day × rule: metric OP threshold?
                              → keep most severe per family/day → merge consecutive days
                      │
  DELIVERY     notifier.py    AlertLog (SQLite: only new/worse alerts) · HTML email (SMTP / dry-run)
                      │
  OUTPUT       app.py (dashboard) · main.py (CLI, watch) · charts.py (PNG) · outputs/*.csv
```

### Default alert rules

| Alert | Condition | Severity | Basis |
|---|---|---|---|
| Heat wave | max temp ≥ 40 °C | critical | IMD plains heat-wave threshold |
| Very hot day | max temp ≥ 36 °C | warning | |
| Cold wave | min temp ≤ 8 °C | warning | |
| Heavy rain | rain ≥ 64.5 mm/day | critical | IMD "heavy rainfall" category |
| Rain likely | probability ≥ 70% | info | |
| Strong winds | gusts ≥ 50 km/h | warning | |
| Very high UV | UV index ≥ 8 | info | WHO UV scale |
| Unhealthy air | US AQI ≥ 151 | warning | US EPA AQI bands |
| Hazardous air | US AQI ≥ 301 | critical | US EPA AQI bands |
| Dense fog | visibility ≤ 500 m | warning | |

All of these can be edited in the dashboard's **Alert rules** tab or in `data/alert_rules.json`.

### Smart alert handling

1. **Severity families:** when both "Very hot day" and "Heat wave" fire on the same day, only "Heat wave" is shown.
2. **Merging:** five days of hazardous air become one alert, "from Sat 21 to Wed 25 Nov (5 days): peak 422 AQI".
3. **No repeat notifications:** the SQLite log remembers sent alerts. On the next scheduled run only new alerts,
   or alerts whose value got more than 5% worse, are emailed.

## 4. Implementation plan

| Phase | What | Why | Output | Common mistakes |
|---|---|---|---|---|
| 1. Setup | venv + requirements | Reproducible | Libraries | — |
| 2. Folders | data, src, outputs, images, docs, tests | Organisation | Tree | — |
| 3. API client | geocoding, forecast, air quality | Real data | JSON | No timeout; app hangs offline |
| 4. Resilience | retries, cache, sample fallback | Networks fail | Always-working app | Crashing on one failed request |
| 5. Processing | JSON → DataFrames | Easier analysis | Hourly/daily tables | Timezone mistakes |
| 6. Rules | JSON thresholds, evaluator | Configurable alerts | Alert objects | Hard-coding thresholds |
| 7. Smart alerts | severity families, merging | Avoid alert fatigue | Fewer, clearer alerts | 30 repeated warnings |
| 8. Notifications | SQLite log + email | Automation | Email / .eml | Re-sending every hour |
| 9. Charts + dashboard | Plotly, Streamlit | Insight | Dashboard | Unreadable dual axes |
| 10. Scheduler | `watch` / Task Scheduler / cron | Hands-free | Periodic checks | — |
| 11. Tests + GitHub | pytest, screenshots | Proof of work | Repo | Committing `.env` |

## 8. Virtual simulation

1. **Live (your PC):** `python main.py forecast Delhi` calls the real Open-Meteo APIs; any city works
   (`python main.py forecast "Jaipur"`).
2. **Offline:** `scripts/generate_sample_data.py` writes forecasts in Open-Meteo's exact JSON format for six
   Indian cities for 21–27 Nov 2026, modelled on typical late-November weather: Delhi smog, cold nights and fog;
   a Chennai north-east-monsoon rain spell; a hot, hazy Mumbai; mild Bengaluru showers; Kolkata haze; and a calm
   Hyderabad. These are clearly labelled as simulated in the CLI and dashboard.
3. **Alert scenario:** the sample produces 15 alerts across 5 cities (2 critical: Delhi hazardous air and
   Chennai heavy rain). Running `alerts` a second time reports 0 new alerts, which demonstrates de-duplication.
4. **Email:** without SMTP settings the alert email is saved to `outputs/alert_emails/` as `.eml` and `.html`.

## 12. Proof-building plan

| Day | Work | Commit message | Screenshot |
|---|---|---|---|
| 1 | Setup, cities, rules, sample data | `chore: project setup with cities, alert rules and sample forecasts` | Folder |
| 2 | API client + processing | `feat: Open-Meteo client with retries, cache and offline fallback` | `forecast` output |
| 3 | Alert engine | `feat: configurable alert rules with severity and merging` | Alerts table |
| 4 | Notifications + CLI | `feat: alert history, email notifications and CLI` | Email preview |
| 5 | Dashboard | `feat: Streamlit weather dashboard` | Each tab |
| 6 | Tests + docs | `docs: README, explanation, interview Q&A` | pytest, GitHub |

## 13. Screenshot checklist

- [ ] `python main.py forecast Chennai`
- [ ] `python main.py compare` and `python main.py alerts`
- [ ] Alert email (`outputs/alert_emails/*.html`)
- [ ] Dashboard: Hourly, Alerts, Air quality, Compare cities
- [ ] pytest passing
- [ ] GitHub repository page
