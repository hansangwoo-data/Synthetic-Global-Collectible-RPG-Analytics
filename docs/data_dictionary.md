# Data Dictionary

## daily_kpis.csv

Grain: one row per `date × region`.

| Field | Description |
|---|---|
| date | Calendar date |
| region | KR, JP, or GLOBAL_WEST |
| dau | Observed daily active users |
| nru | New registered users |
| returned_users | Previously inactive users returning that day |
| user_outflow | Synthetic activity-loss proxy; zero while service is fully unavailable, with missed recovery reflected after restoration |
| event_names | Active fictional scenario label |
| event_types | Active scenario type |
| service_availability | Observable service availability from 0 to 1; all activity and commerce fields are zero at 0 |
| pu | Unique paying users |
| revenue | Reconciled gross synthetic USD |

## retention_cohorts.csv

Grain: one row per `cohort_month × region`. Retained counts use a
survival-style definition and therefore follow `D30 ≤ D7 ≤ D1`. Only cohorts
through November 2025 are published because the December cohort is not mature
enough for D30 observation by the dataset end date.

| Field | Description |
|---|---|
| cohort_month | Registration cohort month |
| region | Service region |
| cohort_size | New users in the cohort |
| d1_retained | Users retained through D1 |
| d7_retained | Users retained through D7 |
| d30_retained | Users retained through D30 |

## events.csv

Grain: one row per `event_id × region`.

| Field | Description |
|---|---|
| event_id | Fictional event key |
| event_name | Public scenario label |
| event_type | Launch, seasonal, collaboration, monetization launch, incident, or recovery class |
| region | Applicable region |
| start_date / end_date | Inclusive event window |
| narrative | Fictional operational context |

## products.csv

Grain: one row per product.

| Field | Description |
|---|---|
| product_id | Product key |
| product_name | Fictional product label |
| product_type | Daily, weekly, pass, subscription, currency top-up, equipment, growth, or limited bundle |
| price_usd | Synthetic list price |
| available_from | First sale date |
| purchase_cycle_days | Intended repeat-purchase interval |

The catalog excludes direct sales of complete limited characters.

## daily_product_sales.csv

Grain: one row per `date × region × product_id`.

| Field | Description |
|---|---|
| purchasers | Purchasing users for that product |
| units_sold | Units sold; may exceed purchasers |
| gross_revenue_usd | Synthetic gross revenue before fees, refunds, and taxes |

Daily product revenue reconciles with `daily_kpis.revenue`, and each row follows
`gross_revenue_usd = units_sold × price_usd`. Prices do not vary by region.

Seasonal passes and limited bundles have sales only during eligible milestone,
collaboration, anniversary, or seasonal event windows.

## boss_event_metrics.csv

Grain: one row per `date × region × boss_id × difficulty`.

| Field | Description |
|---|---|
| boss_id / boss_name | Fictional limited-boss identifiers |
| difficulty | NORMAL, HARD, or NIGHTMARE |
| participants | Unique participants at that difficulty |
| attempts | Total attempts |
| clears | Participants recording a clear |

Constraints: `clears ≤ participants ≤ attempts`.

## Derived metrics

| Metric | Formula |
|---|---|
| conversion_rate | pu / dau |
| arpu | revenue / dau |
| arppu | revenue / pu |
| revenue_per_payer_day | period revenue / sum of all daily service PU; a project-defined service payer-day metric, not product-buyer revenue or deduplicated period ARPPU |
| adjacent_revenue_per_payer_day | monthly-pass, currency-subscription, and growth-booster revenue / sum of all daily service PU; a project-defined portfolio metric |
| product_revenue_hhi | sum of squared product revenue shares within a comparison window |
| top_3_product_revenue_share | revenue share of the three largest products in a comparison window |
| recovery_index | stage KPI / clean pre-incident KPI × 100 |
| outflow_rate | user_outflow / most recent non-zero regional dau |
| d1/d7/d30_retention | retained users / cohort size |
| clear_rate | clears / participants |
| attempts_per_participant | attempts / participants |
| participation_benchmark_index | participation rate / comparable-boss participation rate × 100 |
| clear_yield_per_1000_dau | clears / dau × 1,000 at one difficulty |

Difficulty-level participants may overlap. They must not be summed and
described as unique total boss participants.
