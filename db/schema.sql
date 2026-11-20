CREATE TABLE IF NOT EXISTS locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    tz TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_daily (
    location_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    temp_max_c REAL NOT NULL,
    temp_min_c REAL NOT NULL,
    precip_prob_pct REAL NOT NULL,
    precip_mm REAL NOT NULL,
    wind_gust_ms REAL NOT NULL,
    uv_index REAL NOT NULL,
    PRIMARY KEY (location_id, date),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE TABLE IF NOT EXISTS alert_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_name TEXT NOT NULL,
    alert_code TEXT NOT NULL,
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
