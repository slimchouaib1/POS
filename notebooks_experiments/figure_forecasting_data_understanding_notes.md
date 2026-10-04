# Forecasting Data Understanding Figure Notes

Takeaway: Demand varies over time with clear trend, weekly, seasonal, and meal-period effects, which justifies the forecasting task.

## Dataset used
- Source: `backend\Ai models\data\raw\enterprise_pos_dataset.csv`
- Raw records: 178,839 transaction line rows
- Valid non-voided records used: 175,878 transaction line rows
- Time range: 2023-01-01 to 2025-12-31
- Distinct menu items: 122
- Distinct orders: 61,986

## Aggregations performed
- Panel A aggregates valid transaction lines into daily total item demand and overlays a 30-day rolling mean.
- Panel B averages daily demand by weekday to show recurring weekly behavior.
- Panel C averages daily demand by month of year to show broad seasonality without making Ramadan the centerpiece.
- Panel D derives meal periods from order hour using the deployed FM context mapping and normalizes item-line demand by the number of observed days.

## Why this figure fits the Forecasting - Data Understanding slide
- It answers why forecasting is needed: demand is visibly non-constant across time.
- It summarizes temporal structure rather than repeating dataset schema, global counts, or generator-validation evidence.
- It supports the report's forecasting data-understanding narrative: chronological demand, calendar patterns, seasonality, and restaurant meal periods matter before forecasting preparation and modeling.
