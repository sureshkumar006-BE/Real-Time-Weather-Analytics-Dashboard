"""
scheduler.py

Runs fetch_weather.fetch_all() on a repeating schedule so the database
keeps filling up with fresh data — this is what makes the dashboard "live".

Run:
    python src/scheduler.py

Leave this running in a terminal (or as a background service / cron job)
while you view the Streamlit dashboard in another terminal.
"""

import os
import time
import schedule
from dotenv import load_dotenv
from fetch_weather import fetch_all

load_dotenv()

INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "15"))


def job():
    print(f"\n--- Running scheduled fetch ({time.strftime('%Y-%m-%d %H:%M:%S')}) ---")
    fetch_all()


if __name__ == "__main__":
    print(f"Starting scheduler: fetching weather every {INTERVAL_MINUTES} minute(s).")
    print("Press Ctrl+C to stop.\n")

    job()  # run once immediately on startup
    schedule.every(INTERVAL_MINUTES).minutes.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
