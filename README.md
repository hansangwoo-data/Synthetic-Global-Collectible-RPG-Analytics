# Synthetic Global Collectible RPG Analytics

[한국어](README_KR.md) · [Reproduce](#reproduce)

**A Game Operations → Data Analyst portfolio: DA 70% + Analytics Engineer 30%.**
AThis project reflects my transition from five years in Game Operations into data analysis. It explores acquisition, boss participation, monetization, and incident follow-up in a fictional collectible RPG using independently generated synthetic data.

**Questions:** Which acquisition cohorts brought in more players but retained them less effectively? Is weak boss participation an entry problem? Does a subscription add value or coincide with a spending shift? When should an incident response close?

**Data:** six aggregate scenario tables (2024–2025; KR, JP, Global West) plus a separate 360-user registration/login example. The two populations are not linked. The original D30 metric is a synthetic retention indicator, while the added SQL analysis calculates exact-day D7/D30 retention from login records.

**Methods:** Python/pandas for analysis, SQLite for both overall metrics and user-level queries, and Matplotlib/Seaborn for charts. SQL results are checked against pandas.

| Finding | What to check next |
|---|---|
| Astra collaboration cohort size +50.07%, D30 synthetic retention indicator −2.44 pp | Instrument acquisition mix and test onboarding before scaling acquisition. | <!-- claim:astra_crossover_2025_cohort_change_pct:50.07 claim:astra_crossover_2025_d30_change_pp:-2.44 -->
| Astra collaboration normal boss participation index 82.17 (reference 100) | Test entry communication for eligible users. | <!-- claim:astra_normal_participation_index:82.17 -->
| Subscription-window revenue +72.21%; adjacent-offer revenue per paying user per day −13.32% during the 14 days after launch | Test offer differentiation in all regions. | <!-- claim:subscription_revenue_change_pct:72.21 claim:adjacent_post14_change_pct:-13.32 -->
| During the compensation period, returned users reached 293.95% of the pre-incident baseline, while revenue recovered to only 56.19%. | Separate technical restoration, user activity and commercial follow-up. | <!-- claim:compensation_returned_index:293.95 claim:compensation_revenue_index:56.19 -->

**Next steps:** collect exposure, eligibility and payment logs, then test the proposed changes on a small scale. The [experiment plan](docs/decision_plan.md) sets out success measures and when to stop.

## Methods and analysis

| Analysis | Data preparation and checks |
|---|---|
| [Business questions and metric definitions](docs/analysis_spec.md) | [Table grain and data model](docs/data_model.md) |
| [Six analyses](#analysis-details) and [assumption sensitivity](docs/sensitivity.md) | [Cross-table business contracts](src/data_contracts.py) |
| [Proposed experiments](docs/decision_plan.md) | [User-level cohort SQL](sql/user_retention.sql): CTEs, joins, date logic, window function |
| [Connecting operations experience to analysis](docs/operations_to_da.md) | [Independent pandas reconciliation](src/user_retention.py), [edge-case tests](tests/test_user_retention.py) |

## User-level exact-day retention

[Metric specification](docs/user_retention.md) · [Generated cohort results](docs/user_retention_results.md)

The SQL counts registered users who log in on exactly day 7 or 30. Each horizon has its own mature-user denominator. It handles duplicate deliveries, multiple sessions, late arrivals and an explicit UTC snapshot. A user can return on D30 without returning on D7. SQL and pandas must agree on every output count and rate.

March cohorts have incomplete observation and must not be compared as full-month D30 results.

## Analysis details

These six analyses use the aggregate scenario. Their D1/D7/D30 labels refer to the checkpoint proxy described above.

1. [Lifecycle](docs/findings/analysis_01_lifecycle.md): event calendar and contextual persistence.
2. [Acquisition quality](docs/findings/analysis_02_retention.md): volume versus checkpoint proxy.
3. [PvE participation](docs/findings/analysis_03_pve.md): entry and selection hypotheses.
4. [Monetization](docs/findings/analysis_04_monetization.md): total revenue versus adjacent-offer mix.
5. [Incident](docs/findings/analysis_05_incident.md): separate operational, activity and commercial indices.
6. [Regional response](docs/findings/analysis_06_regional_strategy.md): shared warnings, assumption-sensitive severity.

[Source dictionary](docs/data_dictionary.md) · [Synthetic scenario design](docs/scenario_design.md) · [Recomputed headline values](docs/verified_claims.md) · [Notebook](notebooks/game_user_behavior_analysis.ipynb)

## What changed after validation

A cross-check found that some daily unique payer counts exceeded the sum of product-level buyers. The original tests did not check that relationship. Correcting PU changed payer-derived conclusions and removed the JP-only warning. Revenue, DAU and checkpoint source data stayed unchanged. Cross-table checks and SQL/pandas comparisons now cover the corrected metrics. [Detailed before/after](docs/validation_changes.md).

## Reproduce

Python 3.12; SQLite is included in Python. Run from repository root:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
MPLBACKEND=Agg python -m src.run_pipeline
MPLBACKEND=Agg python -m src.verify_publication
```

The pipeline reads committed sources, regenerates analysis CSVs/charts and checks SQL parity and generated reports. `verify_publication` executes all notebook code cells in order and checks README claims against generated source evidence. CI runs these same commands. Generated outputs are in `outputs/`.

Intentional source/document regeneration only:

```bash
MPLBACKEND=Agg python -m src.run_pipeline --regenerate --refresh-docs
```

`--regenerate` reproduces both the six-table scenario and the separate user-log population. Review any resulting source/evidence diff. Four aggregate SQL views and one user-cohort SQL query are reconciled independently with pandas. Tests include business bounds and manually constructed temporal edge cases.

## Limitations

The findings describe synthetic scenarios, not measured production effects. No experiment has been run, and the results cannot establish causality or real-world ROI.

Daily PU remains a modeled feasible union, not observed unique buyers. There are no individual transactions, VOC/CS records or experiment assignments. Aggregate data cannot show whether individual buyers switched products or where users left the boss-entry path. Comparable entrant outcomes do not rule out difficulty-related selection. “Recovery” means a return toward a reference level, not restored trust or the same players returning.

The separate login example does not explain the aggregate scenario or establish regional rankings. Cohort maturity and baseline selection matter; regional severity can change with payer assumptions. [Remaining weaknesses and interview preparation](docs/hiring_readiness_review.md).
