# Reports

This directory contains the Power BI presentation layer for the Chinook Data
Warehouse.

## Artifact

- `chinook_analytics.pbix`: dashboard connected to the Athena analytical model.

## Expected Data Model

Power BI should import or query these Athena tables:

- `dim_date`
- `dim_customer`
- `dim_track`
- `fact_sales`

Recommended relationships:

- `fact_sales[InvoiceDateKey]` -> `dim_date[DateKey]`
- `fact_sales[CustomerKey]` -> `dim_customer[CustomerKey]`
- `fact_sales[TrackKey]` -> `dim_track[TrackKey]`

The dashboard focuses on daily track sales, best-selling artists, weekday
purchase behavior, and monthly sales volume.
