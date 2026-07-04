"""
fetch_weather.py

Pulls current weather data for a configured list of cities from the
OpenWeatherMap API, runs a simple anomaly check against each city's
recent history, and writes the results to a SQLite database.

Run once:
    python src/fetch_weather.py

This is the "E" and "T" and "L" of a lightweight ETL pipeline:
  Extract  -> call the OpenWeatherMap API
  Transform-> normalize the JSON response + flag anomalies
  Load     -> insert into SQLite
"""

import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

sys.path.append(os.path.dirname(__file__))
from db import init_db, insert_reading, get_recent_readings_for_city  # noqa: E402

load_dotenv()

API_KEY = os.getenv("OPENWEATHER_API_KEY")
CITIES = [c.strip() for c in os.getenv("CITIES", "London,New York").split(",")]
DB_PATH = os.getenv("DB_PATH", "weather_data.db")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Anomaly detection thresholds
TEMP_JUMP_THRESHOLD_C = 5.0     # sudden change vs. last reading
HUMIDITY_JUMP_THRESHOLD = 25    # sudden change vs. last reading
HEATWAVE_THRESHOLD_C = 40.0     # absolute high
COLD_SNAP_THRESHOLD_C = 0.0     # absolute low


def fetch_city_weather(city: str) -> dict:
    """Call the OpenWeatherMap API for a single city and return raw JSON."""
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    response = requests.get(BASE_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


def normalize_reading(city: str, raw: dict) -> dict:
    """Convert the raw API response into our flat dict schema."""
    return {
        "city": city,
        "country": raw.get("sys", {}).get("country"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "temperature_c": raw.get("main", {}).get("temp"),
        "feels_like_c": raw.get("main", {}).get("feels_like"),
        "humidity": raw.get("main", {}).get("humidity"),
        "pressure": raw.get("main", {}).get("pressure"),
        "wind_speed": raw.get("wind", {}).get("speed"),
        "weather_main": (raw.get("weather") or [{}])[0].get("main"),
        "weather_description": (raw.get("weather") or [{}])[0].get("description"),
    }


def detect_anomaly(city: str, reading: dict) -> dict:
    """
    Flag a reading as anomalous if:
      - temperature crosses heatwave / cold-snap thresholds, OR
      - temperature or humidity jumped sharply vs. the previous reading
    Mutates and returns the reading dict with is_anomaly / anomaly_reason set.
    """
    reasons = []
    temp = reading.get("temperature_c")
    humidity = reading.get("humidity")

    if temp is not None:
        if temp >= HEATWAVE_THRESHOLD_C:
            reasons.append(f"Heatwave: {temp}°C")
        elif temp <= COLD_SNAP_THRESHOLD_C:
            reasons.append(f"Cold snap: {temp}°C")

    history = get_recent_readings_for_city(city, limit=1)
    if history:
        last = history[0]
        last_temp = last.get("temperature_c")
        last_humidity = last.get("humidity")

        if temp is not None and last_temp is not None:
            if abs(temp - last_temp) >= TEMP_JUMP_THRESHOLD_C:
                reasons.append(
                    f"Sudden temp change: {last_temp}°C -> {temp}°C"
                )

        if humidity is not None and last_humidity is not None:
            if abs(humidity - last_humidity) >= HUMIDITY_JUMP_THRESHOLD:
                reasons.append(
                    f"Sudden humidity change: {last_humidity}% -> {humidity}%"
                )

    reading["is_anomaly"] = len(reasons) > 0
    reading["anomaly_reason"] = "; ".join(reasons) if reasons else None
    return reading


def fetch_all():
    """Fetch + store weather for every configured city. Entry point for the scheduler."""
    if not API_KEY:
        raise RuntimeError(
            "OPENWEATHER_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    init_db(DB_PATH)

    for city in CITIES:
        try:
            raw = fetch_city_weather(city)
            reading = normalize_reading(city, raw)
            reading = detect_anomaly(city, reading)
            insert_reading(reading, DB_PATH)

            flag = " ANOMALY" if reading["is_anomaly"] else ""
            print(
                f"[{reading['fetched_at']}] {city}: "
                f"{reading['temperature_c']}°C, "
                f"{reading['humidity']}% humidity{flag}"
            )
        except requests.RequestException as e:
            print(f"[ERROR] Failed to fetch weather for {city}: {e}")


if __name__ == "__main__":
    fetch_all()
