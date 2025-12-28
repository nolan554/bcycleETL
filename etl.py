import os
from datetime import datetime, timezone

import psycopg2
import requests

GBFS_URL = os.getenv("GBFS_URL", "https://gbfs.bcycle.com/bcycle_boulder/gbfs.json")
DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "bcycle")
DB_USER = os.getenv("DB_USER", "bcycle")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bcycle_pw")
TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "10"))


def _utc_from_unix(seconds):
    return datetime.fromtimestamp(int(seconds), tz=timezone.utc)


def _fetch_feed_urls():
    resp = requests.get(GBFS_URL, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    data = resp.json()

    feeds = data["data"]["en"]["feeds"]
    urls = {item["name"]: item["url"] for item in feeds}
    return urls["station_information"], urls["station_status"]


def _fetch_json(url):
    resp = requests.get(url, timeout=TIMEOUT_SECONDS)
    resp.raise_for_status()
    return resp.json()


def _ensure_stations(cur, stations):
    for st in stations:
        cur.execute(
            """
            INSERT INTO dim_stations (station_id, name, lat, lon, capacity, last_updated)
            VALUES (%s, %s, %s, %s, %s, NOW())
            ON CONFLICT (station_id)
            DO UPDATE SET
              name = EXCLUDED.name,
              lat = EXCLUDED.lat,
              lon = EXCLUDED.lon,
              capacity = EXCLUDED.capacity,
              last_updated = NOW();
            """,
            (
                st["station_id"],
                st.get("name"),
                st.get("lat"),
                st.get("lon"),
                st.get("capacity"),
            ),
        )


def _get_latest_reported_map(cur):
    cur.execute(
        """
        SELECT station_id, MAX(last_reported) AS last_reported
        FROM fact_station_status
        GROUP BY station_id;
        """
    )
    return {row[0]: row[1] for row in cur.fetchall()}


def _insert_statuses(cur, statuses, latest_by_station):
    for st in statuses:
        last_reported = _utc_from_unix(st["last_reported"])
        last_seen = latest_by_station.get(st["station_id"])
        if last_seen and last_reported <= last_seen:
            continue

        cur.execute(
            """
            INSERT INTO fact_station_status (
              station_id,
              num_bikes_available,
              num_docks_available,
              is_installed,
              is_renting,
              is_returning,
              last_reported
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
            """,
            (
                st["station_id"],
                st.get("num_bikes_available"),
                st.get("num_docks_available"),
                st.get("is_installed"),
                st.get("is_renting"),
                st.get("is_returning"),
                last_reported,
            ),
        )


def run_etl():
    station_info_url, station_status_url = _fetch_feed_urls()

    info_json = _fetch_json(station_info_url)
    status_json = _fetch_json(station_status_url)

    stations = info_json["data"]["stations"]
    statuses = status_json["data"]["stations"]

    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        with conn:
            with conn.cursor() as cur:
                _ensure_stations(cur, stations)
                latest_by_station = _get_latest_reported_map(cur)
                _insert_statuses(cur, statuses, latest_by_station)
    finally:
        conn.close()


if __name__ == "__main__":
    run_etl()
