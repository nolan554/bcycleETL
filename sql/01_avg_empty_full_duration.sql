WITH ordered AS (
  SELECT
    s.station_id,
    s.last_reported,
    s.num_bikes_available,
    d.capacity,
    CASE
      WHEN s.num_bikes_available = 0 THEN 'empty'
      WHEN d.capacity IS NOT NULL AND s.num_bikes_available = d.capacity THEN 'full'
      ELSE 'other'
    END AS state,
    LAG(CASE
      WHEN s.num_bikes_available = 0 THEN 'empty'
      WHEN d.capacity IS NOT NULL AND s.num_bikes_available = d.capacity THEN 'full'
      ELSE 'other'
    END) OVER (PARTITION BY s.station_id ORDER BY s.last_reported) AS prev_state
  FROM fact_station_status s
  JOIN dim_stations d ON d.station_id = s.station_id
),
transitions AS (
  SELECT
    station_id,
    last_reported AS transition_time,
    state,
    prev_state
  FROM ordered
  WHERE state IN ('empty', 'full')
),
runs AS (
  SELECT
    station_id,
    state,
    transition_time AS start_time,
    LEAD(transition_time) OVER (PARTITION BY station_id ORDER BY transition_time) AS end_time,
    prev_state
  FROM transitions
)
SELECT
  station_id,
  state,
  AVG(EXTRACT(EPOCH FROM (end_time - start_time))) / 60.0 AS avg_minutes_in_state,
  COUNT(*) AS run_count
FROM runs
WHERE
  prev_state IS DISTINCT FROM state
  AND end_time IS NOT NULL
GROUP BY station_id, state
ORDER BY avg_minutes_in_state DESC;
