# User-level exact-day retention

**Question:** Can a monthly acquisition cohort's exact-day login return rate be measured reproducibly without counting sessions twice or including users who have not reached D30?

This is a separate, small synthetic instrumentation example. Its 360 users are **not** the users behind the original six scenario tables. It cannot confirm the Astra, subscription, or outage hypotheses. No production records or individual purchase behavior are available.

## Data contract and metric

| Object | Grain / rule |
|---|---|
| `user_cohort_users.csv` | One registered synthetic user; unique `user_id`, canonical UTC registration timestamp, region at registration |
| `user_cohort_logins.csv` | One received login event delivery; `event_id` can repeat on delivery, but user and occurrence timestamp must agree |
| Output | Registration calendar month × registration region × horizon (7 or 30) |
| Cohort | All registered users in that UTC month, through the as-of date; registration, not first payment or first observed login |
| Denominator | Users whose registration date + N calendar days is on/before the as-of date |
| Numerator | Eligible users with at least one login on exactly registration date + N, received by the as-of date |
| Snapshot | End of 2025-03-31 UTC; include both event time and ingestion time cutoffs |
| Missing observation | Null rate when denominator is zero, never zero retention |

Use **calendar-day** differences, not elapsed 168/720-hour intervals. D30 users need not have logged in on D7. This differs from the original retention_cohorts.csv, which uses synthetic checkpoint counts rather than standard exact-day session retention.

[SQL](../sql/user_retention.sql) uses CTEs, a window function to select the earliest visible delivery, distinct user-days, horizon expansion, a left join and maturity-aware denominators. The independent [pandas implementation](../src/user_retention.py) uses timestamp normalization and user/date set membership. The SQL and pandas results must match. Validation checks reject orphan logins, conflicting duplicate events, null fields, duplicate users, and invalid timestamps.

## Interpretation and next step

[Generated results](user_retention_results.md) show observable exact-day return counts, with partial March maturity. These results come from a synthetic activity process, not real player behavior. Regional differences may reflect small sample sizes and registration-date mix.

**Hypothesis for a real pilot**: a clearer first-week progression path might improve D7 login return. For a real service, I would first collect complete login data, compare mature cohorts, and then test the change with a small controlled rollout.

## Reproduce and review

```bash
python -m src.user_retention                         # read committed CSVs, assert parity/report
python -m unittest tests.test_user_retention -v
```

The generator simulates activity on every observable day, repeated deliveries and multiple sessions. It does not merely create D7/D30 target rows. Manual edge fixtures cover leap-day dates, midnight boundaries, D30 returns without D7, late arrival, partial maturity and users registered after the snapshot.

Limitations: no device/account identity resolution, deletion history, acquisition channel or payments. This separate population is not intended to match the main scenario's DAU.
