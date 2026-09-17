# Data Model and Metric Contracts

The six CSVs are synthetic analysis-ready facts/dimensions, not raw event logs.
The SQLite schema mirrors them with explicit PK/FK/CHECK constraints. A complete
rebuild loads validated CSVs into a fresh in-memory database, then builds views.
No production incremental ETL, identity graph or warehouse deployment is claimed.

| Table | Primary grain | Relationships | Additivity |
|---|---|---|---|
| daily_kpis | UTC date × region | parent of sales/boss date-region | revenue additive; DAU/PU sum across disjoint regions, but across days are user-days |
| products | product_id | parent of sales product_id | price and intended purchase cycle are attributes |
| daily_product_sales | date × region × product_id | daily_kpis and products | revenue/units additive; purchasers overlap across products and days |
| retention_cohorts | registration month × region | cohort size reconciles to monthly NRU | sum counts before rates; custom nested retention, not session-derived |
| events | event_id × region | temporal range joins to facts | overlaps allowed; never join directly then sum facts without deduplication |
| boss_event_metrics | date × region × boss_id × difficulty | daily_kpis; configured event mapping | participants overlap across days and difficulties |

Avoid joining product facts to boss facts: their grains create many-to-many
fan-out. Aggregate each to the intended date-region grain before joining.
`sql/metrics.sql` demonstrates this for sales and service denominators.

The fixed scenario covers 2024-01-01 through 2025-12-31 and exactly three regions.
Contracts reject missing edge dates or entire regions, unknown product IDs,
missing zero-sales rows, immature/missing cohorts, nonfinite/fractional counts,
cohort-NRU mismatches and impossible payer unions. Monthly D30 is mature only
when month-end +30 days is within the observation window.

Cash reconciliation uses absolute half-cent tolerance and zero relative tolerance.
Undefined rates use NULL/NaN when their denominator is zero, including the full
outage. Zero activity and absent data are different states.

Product purchase cycles are metadata, not simulated renewal constraints. The
payer union is feasible but not identified; see the sensitivity report. A future
user-event model is needed to demonstrate renewal, buyer migration, event
attribution and conventional exact-day cohort SQL.
