# 🌦️ Real-Time Weather Analytics Dashboard

A lightweight ETL pipeline and live dashboard that tracks weather conditions
across multiple cities, stores the history in SQL, and flags anomalies
(heatwaves, cold snaps, sudden swings) as they happen.

Built to demonstrate core data analyst skills: **API integration, automation,
SQL data modeling, anomaly detection, and dashboarding** — without needing
heavy infrastructure like Kafka or Spark.

## Architecture

```
OpenWeatherMap API
        │
        ▼
  fetch_weather.py   (Extract + Transform: pulls data, flags anomalies)
        │
        ▼
   SQLite database   (Load: weather_readings table)
        │
        ▼
  scheduler.py        ──── runs fetch_weather.py every N minutes (the "real-time" part)
        │
        ▼
  Streamlit dashboard  (dashboard/app.py) — live trends, comparisons, alerts
```

## Features

- **Automated data pipeline** — pulls live weather for a configurable list of cities on a schedule
- **SQL-backed storage** — all historical readings persisted in SQLite (swap in Postgres/MySQL easily)
- **Anomaly detection** — flags heatwaves, cold snaps, and sudden temperature/humidity swings vs. the previous reading
- **Interactive dashboard** — compare cities side by side, view trend lines, and browse a live anomaly log
- **Zero heavy infra** — just Python + SQL + Streamlit; runs on a laptop or a free-tier cloud instance

## Tech Stack

| Layer          | Tool                          |
|----------------|-------------------------------|
| Data source    | OpenWeatherMap API             |
| Language       | Python 3.10+                   |
| Scheduling     | `schedule` library              |
| Storage        | SQLite                         |
| Visualization  | Streamlit + Plotly             |

## Getting Started

### 1. Clone and install dependencies
```bash
git clone https://github.com/<your-username>/realtime-weather-dashboard.git
cd realtime-weather-dashboard
pip install -r requirements.txt
```

### 2. Get a free API key
Sign up at [openweathermap.org/api](https://openweathermap.org/api) (free tier is enough).

### 3. Configure environment
```bash
cp .env.example .env
```
Then edit `.env`:
```
OPENWEATHER_API_KEY=your_api_key_here
CITIES=London,New York,Mumbai,Tokyo,Sydney
FETCH_INTERVAL_MINUTES=15
DB_PATH=weather_data.db
```

### 4. Run the pipeline
Fetch data once:
```bash
python src/fetch_weather.py
```

Or run continuously in the background (this is what makes it "live"):
```bash
python src/scheduler.py
```

### 5. Launch the dashboard
In a separate terminal:
```bash
streamlit run dashboard/app.py
```
Open the URL Streamlit prints (usually `http://localhost:8501`).

## How the anomaly detection works

Each new reading is compared against:
- **Absolute thresholds** — flags anything ≥ 40°C (heatwave) or ≤ 0°C (cold snap)
- **Relative change** — flags a jump of ≥ 5°C or ≥ 25% humidity vs. the city's previous reading

This is intentionally simple (rule-based, no ML) so it's easy to explain in an
interview — and easy to extend with z-scores, rolling averages, or a proper
anomaly-detection model later.

## Possible extensions

- Swap SQLite for PostgreSQL and deploy on a free-tier cloud DB
- Add email/Slack alerts when an anomaly is detected
- Deploy the dashboard on Streamlit Community Cloud for a shareable live link
- Add historical weather comparison (e.g., vs. same day last year)
- Containerize with Docker for one-command setup

## Project structure

```
realtime-weather-dashboard/
├── src/
│   ├── db.py              # SQLite schema + helper functions
│   ├── fetch_weather.py   # API call, transform, anomaly detection, load
│   └── scheduler.py       # Runs fetch_weather.py on a repeating interval
├── dashboard/
│   └── app.py             # Streamlit dashboard
├── requirements.txt
├── .env.example
└── README.md
```

## License

MIT — feel free to fork and adapt for your own portfolio.
