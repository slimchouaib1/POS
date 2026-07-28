# Generator Validation Summary

All validation plots are computed from generated output CSV files only: `enterprise_pos_dataset.csv`, `customers.csv`, and `anomalies_ground_truth.csv`. The generator script was not read for parameter constants and the dataset was not regenerated.

| Assumption | Plot or output | What the generated data shows | External citation placeholder |
|---|---|---|---|
| Weekday demand pattern | `figures/weekday_demand_pattern.png` | Overall demand peaks late week/weekend; Healthy_Vegan is comparatively weekday-heavy with Mon-Thu at 64.3% of its orders. |  |
| Meal-period / hourly demand | `figures/hourly_demand_distribution.png` | Cafe peaks at 8:00, while Steakhouse peaks at 20:00, matching the morning vs dinner demand structure. |  |
| Item seasonality | `figures/item_seasonality_summer_vs_winter.png` | Selected items show distinct monthly curves: 14oz Ribeye peaks in Dec, Espresso peaks in Dec, Iced Latte peaks in Jul. |  |
| Ramadan effect | `figures/ramadan_demand_effect.png` | Across the shaded Ramadan windows, Cafe daytime averages -64.0% vs adjacent periods while Steakhouse dinner averages -20.7%. |  |
| Customer archetype distribution | `figures/customer_archetype_distribution.png` | Infrequent and one-time customers account for 55.0% of customers, and visits show a long right tail. |  |
| Anomaly type breakdown | `figures/anomaly_type_distribution.png` | The ground-truth file contains 468 injected anomaly orders out of 63,049 total orders (0.74%). Rates are injected/illustrative, not empirical fraud statistics. |  |
| Growth trend | `figures/revenue_growth_trend.png` | Monthly revenue has a positive fitted trend of 22.7% from Jan 2023 to Dec 2025. |  |
| Product affinity recovery | `Existing Module 1/01_fp_growth.ipynb, section 'Validation against injected affinities'` | Not duplicated here; the FP-Growth notebook already checks recovered association rules against the injected affinity pairs. |  |
