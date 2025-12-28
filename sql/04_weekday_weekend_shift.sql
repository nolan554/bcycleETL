WITH deltas AS (
  SELECT
    station_id,
    last_reported,
    num_bikes_available,
    LAG(num_bikes_available) OVER (PARTITION BY station_id ORDER BY last_reported) AS prev_bikes
  FROM fact_station_status
),
usage_by_day AS (
  SELECT
    station_id,
    date_trunc('day', last_reported) AS day_bucket,
    EXTRACT(DOW FROM last_reported) AS dow,
    SUM(GREATEST(0, prev_bikes - num_bikes_available)) AS bikes_departed
  FROM deltas
  WHERE prev_bikes IS NOT NULL
  GROUP BY station_id, day_bucket, dow
)
SELECT
  station_id,
  AVG(CASE WHEN dow BETWEEN 1 AND 5 THEN bikes_departed END) AS avg_weekday_departures,
  AVG(CASE WHEN dow IN (0, 6) THEN bikes_departed END) AS avg_weekend_departures,
  (AVG(CASE WHEN dow IN (0, 6) THEN bikes_departed END)
   - AVG(CASE WHEN dow BETWEEN 1 AND 5 THEN bikes_departed END)) AS weekend_minus_weekday
FROM usage_by_day
GROUP BY station_id
ORDER BY weekend_minus_weekday DESC NULLS LAST;
