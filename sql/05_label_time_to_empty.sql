WITH ordered AS (
  SELECT
    station_id,
    last_reported,
    num_bikes_available
  FROM fact_station_status
),
next_empty AS (
  SELECT
    o.station_id,
    o.last_reported,
    o.num_bikes_available,
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
  EXTRACT(EPOCH FROM (next_empty_time - last_reported)) / 60.0 AS minutes_until_empty
FROM next_empty
WHERE next_empty_time IS NOT NULL
ORDER BY station_id, last_reported;
