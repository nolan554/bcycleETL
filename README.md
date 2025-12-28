# BCycle ETL Analytics Queries

This project collects Boulder B-Cycle GBFS data into Postgres. The queries below answer business-focused questions using the `dim_stations` and `fact_station_status` tables.

## ML: Time-to-Empty Regression

Baseline regression predicts minutes until a station becomes empty using recent status data.

- Label query: `sql/05_label_time_to_empty.sql`
- Training script: `ml/train_time_to_empty.py`

## Questions and SQL

1) Average time a station stays empty or full
- Query: `sql/01_avg_empty_full_duration.sql`
- Uses state transitions to compute average minutes per run.

2) Stations with the most volatile availability
- Query: `sql/02_most_volatile_availability.sql`
- Ranks stations by stddev of bikes available and average absolute change.

3) Top origin stations by hour (approx via net bike changes)
- Query: `sql/03_top_origin_stations_by_hour.sql`
- Estimates bike departures by hour using negative deltas.

4) Weekday vs weekend usage shift per station
- Query: `sql/04_weekday_weekend_shift.sql`
- Compares average departures on weekdays vs weekends.

## Running a query

Example:

```sh
sudo docker compose exec -T db psql -U bcycle -d bcycle -f sql/01_avg_empty_full_duration.sql
```

## Train the model

```sh
sudo docker compose exec -T etl python /app/ml/train_time_to_empty.py
```
