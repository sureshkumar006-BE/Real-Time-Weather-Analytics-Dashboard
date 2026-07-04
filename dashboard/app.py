"""
dashboard/app.py

Streamlit dashboard for the real-time weather analytics project.

Run:
    streamlit run dashboard/app.py

Reads directly from the SQLite database that fetch_weather.py / scheduler.py
populate, so every time you refresh the page (or Streamlit auto-reruns)
you see the latest data.
"""

import os
import sys
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "weather_data.db")

st.set_page_config(page_title="Real-Time Weather Dashboard", layout="wide")


@st.cache_data(ttl=60)  # re-read from DB at most once a minute
def load_data(db_path: str) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM weather_readings", conn)
    conn.close()
    if not df.empty:
        df["fetched_at"] = pd.to_datetime(df["fetched_at"])
    return df


st.title("🌦️ Real-Time Weather Analytics Dashboard")
st.caption(
    "Data refreshes automatically as the background fetch script runs. "
    "Reload this page to pull the latest rows from the database."
)

df = load_data(DB_PATH)

if df.empty:
    st.warning(
        "No data yet. Run `python src/fetch_weather.py` at least once "
        "(or start `python src/scheduler.py`) to populate the database."
    )
    st.stop()

cities = sorted(df["city"].unique())
selected_cities = st.multiselect("Cities to compare", cities, default=cities)

filtered = df[df["city"].isin(selected_cities)].sort_values("fetched_at")

# ---- Top-line metrics ----
latest = (
    filtered.sort_values("fetched_at")
    .groupby("city")
    .tail(1)
    .sort_values("temperature_c", ascending=False)
)

st.subheader("Current Conditions")
cols = st.columns(len(latest)) if len(latest) > 0 else [st]
for col, (_, row) in zip(cols, latest.iterrows()):
    with col:
        st.metric(
            label=row["city"],
            value=f"{row['temperature_c']:.1f}°C",
            delta=f"{row['humidity']}% humidity",
        )
        if row["is_anomaly"]:
            st.error(f"⚠️ {row['anomaly_reason']}")

st.divider()

# ---- Temperature trend comparison ----
st.subheader("Temperature Trend by City")
fig_temp = px.line(
    filtered,
    x="fetched_at",
    y="temperature_c",
    color="city",
    markers=True,
    labels={"fetched_at": "Time", "temperature_c": "Temperature (°C)"},
)
st.plotly_chart(fig_temp, use_container_width=True)

# ---- Humidity trend comparison ----
st.subheader("Humidity Trend by City")
fig_humidity = px.line(
    filtered,
    x="fetched_at",
    y="humidity",
    color="city",
    markers=True,
    labels={"fetched_at": "Time", "humidity": "Humidity (%)"},
)
st.plotly_chart(fig_humidity, use_container_width=True)

st.divider()

# ---- Anomaly log ----
st.subheader("🚨 Anomaly Log")
anomalies = filtered[filtered["is_anomaly"] == 1].sort_values(
    "fetched_at", ascending=False
)
if anomalies.empty:
    st.success("No anomalies detected in the selected data.")
else:
    st.dataframe(
        anomalies[["fetched_at", "city", "temperature_c", "humidity", "anomaly_reason"]],
        use_container_width=True,
        hide_index=True,
    )

st.divider()

# ---- Raw data ----
with st.expander("View raw data"):
    st.dataframe(
        filtered.sort_values("fetched_at", ascending=False),
        use_container_width=True,
        hide_index=True,
    )
