CREATE TABLE IF NOT EXISTS dim_stations (
  station_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  capacity INTEGER,
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE EXTENSION IF NOT EXISTS system_stats;

CREATE TABLE IF NOT EXISTS fact_station_status (
  id BIGSERIAL PRIMARY KEY,
  station_id TEXT NOT NULL REFERENCES dim_stations (station_id),
  num_bikes_available INTEGER NOT NULL,
  num_docks_available INTEGER NOT NULL,
  is_installed INTEGER,
  is_renting INTEGER,
  is_returning INTEGER,
  last_reported TIMESTAMP WITH TIME ZONE NOT NULL,
  ingested_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fact_station_status_station_time
  ON fact_station_status (station_id, last_reported DESC);
