"""
db.py
Handles all SQLite database setup and access for the weather dashboard.
"""

import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "weather_data.db")


@contextmanager
def get_connection(db_path: str = None):
    """Context manager for a SQLite connection."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(path)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: str = None):
    """Create the weather_readings table if it doesn't exist."""
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS weather_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                country TEXT,
                fetched_at TEXT NOT NULL,
                temperature_c REAL,
                feels_like_c REAL,
                humidity INTEGER,
                pressure INTEGER,
                wind_speed REAL,
                weather_main TEXT,
                weather_description TEXT,
                is_anomaly INTEGER DEFAULT 0,
                anomaly_reason TEXT
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_city_time
            ON weather_readings (city, fetched_at)
            """
        )
        conn.commit()


def insert_reading(reading: dict, db_path: str = None):
    """Insert a single weather reading (dict) into the database."""
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO weather_readings (
                city, country, fetched_at, temperature_c, feels_like_c,
                humidity, pressure, wind_speed, weather_main,
                weather_description, is_anomaly, anomaly_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                reading["city"],
                reading.get("country"),
                reading["fetched_at"],
                reading.get("temperature_c"),
                reading.get("feels_like_c"),
                reading.get("humidity"),
                reading.get("pressure"),
                reading.get("wind_speed"),
                reading.get("weather_main"),
                reading.get("weather_description"),
                int(reading.get("is_anomaly", False)),
                reading.get("anomaly_reason"),
            ),
        )
        conn.commit()


def get_recent_readings_for_city(city: str, limit: int = 20, db_path: str = None):
    """Return the most recent readings for a city, most recent first."""
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM weather_readings
            WHERE city = ?
            ORDER BY fetched_at DESC
            LIMIT ?
            """,
            (city, limit),
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
