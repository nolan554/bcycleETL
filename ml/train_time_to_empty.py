import os
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "bcycle")
DB_USER = os.getenv("DB_USER", "bcycle")
DB_PASSWORD = os.getenv("DB_PASSWORD", "bcycle_pw")

LABEL_QUERY = """
WITH ordered AS (
  SELECT
    s.station_id,
    s.last_reported,
    s.num_bikes_available,
    s.num_docks_available,
    d.capacity,
    LAG(s.num_bikes_available) OVER (
      PARTITION BY s.station_id ORDER BY s.last_reported
    ) AS prev_bikes
  FROM fact_station_status s
  JOIN dim_stations d ON d.station_id = s.station_id
),
next_empty AS (
  SELECT
    o.station_id,
    o.last_reported,
    o.num_bikes_available,
    o.num_docks_available,
    o.capacity,
    o.prev_bikes,
    (
      SELECT MIN(o2.last_reported)
      FROM ordered o2
      WHERE o2.station_id = o.station_id
        AND o2.last_reported > o.last_reported
        AND o2.num_bikes_available = 0
    ) AS next_empty_time
  FROM ordered o
)
SELECT
  station_id,
  last_reported,
  num_bikes_available,
  num_docks_available,
  capacity,
  prev_bikes,
  EXTRACT(EPOCH FROM (next_empty_time - last_reported)) / 60.0
    AS minutes_until_empty
FROM next_empty
WHERE next_empty_time IS NOT NULL
ORDER BY last_reported;
"""


def load_training_data():
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )
    try:
        return pd.read_sql_query(LABEL_QUERY, conn)
    finally:
        conn.close()


def make_features(df):
    df = df.copy()
    df["hour"] = df["last_reported"].dt.hour
    df["dow"] = df["last_reported"].dt.dayofweek
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["bike_ratio"] = df["num_bikes_available"] / df["capacity"].replace(0, np.nan)
    df["prev_bikes"] = df["prev_bikes"].fillna(df["num_bikes_available"])
    df["delta_bikes"] = df["num_bikes_available"] - df["prev_bikes"]

    feature_cols = [
        "num_bikes_available",
        "num_docks_available",
        "capacity",
        "bike_ratio",
        "prev_bikes",
        "delta_bikes",
        "hour",
        "dow",
        "is_weekend",
    ]
    return df[feature_cols], df["minutes_until_empty"]


def time_split(df, test_fraction=0.2):
    df = df.sort_values("last_reported")
    split_idx = int(len(df) * (1 - test_fraction))
    return df.iloc[:split_idx], df.iloc[split_idx:]


def main():
    df = load_training_data()
    if df.empty or len(df) < 50:
        print("Not enough labeled rows to train. Collect more data.")
        return

    train_df, test_df = time_split(df)

    X_train, y_train = make_features(train_df)
    X_test, y_test = make_features(test_df)

    model = LinearRegression()
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = mean_squared_error(y_test, preds, squared=False)

    print(f"Train rows: {len(train_df)} | Test rows: {len(test_df)}")
    print(f"MAE (minutes): {mae:.2f}")
    print(f"RMSE (minutes): {rmse:.2f}")


if __name__ == "__main__":
    main()
