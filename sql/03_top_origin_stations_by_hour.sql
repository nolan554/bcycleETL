WITH deltas AS (
  SELECT
    station_id,
    last_reported,
    num_bikes_available,
    LAG(num_bikes_available) OVER (PARTITION BY station_id ORDER BY last_reported) AS prev_bikes
  FROM fact_station_status
),
station_hour AS (
  SELECT
    station_id,
    date_trunc('hour', last_reported) AS hour_bucket,
    GREATEST(0, prev_bikes - num_bikes_available) AS bikes_departed
  FROM deltas
  WHERE prev_bikes IS NOT NULL
)
SELECT
  hour_bucket,
  station_id,
  SUM(bikes_departed) AS estimated_departures
FROM station_hour
GROUP BY hour_bucket, station_id
ORDER BY hour_bucket, estimated_departures DESC;
