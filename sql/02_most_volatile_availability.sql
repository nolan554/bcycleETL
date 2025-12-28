WITH deltas AS (
  SELECT
    s.station_id,
    s.last_reported,
    s.num_bikes_available,
    LAG(s.num_bikes_available) OVER (PARTITION BY s.station_id ORDER BY s.last_reported) AS prev_bikes,
    d.capacity
  FROM fact_station_status s
  JOIN dim_stations d ON d.station_id = s.station_id
)
SELECT
  station_id,
  STDDEV_POP(num_bikes_available) AS bikes_stddev,
  AVG(ABS(num_bikes_available - prev_bikes)) AS avg_abs_change,
  STDDEV_POP(num_bikes_available)::numeric / NULLIF(capacity, 0) AS stddev_per_capacity
FROM deltas
WHERE prev_bikes IS NOT NULL
GROUP BY station_id, capacity
ORDER BY stddev_per_capacity DESC NULLS LAST;
