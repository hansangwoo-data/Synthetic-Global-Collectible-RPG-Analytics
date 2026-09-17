# Synthetic Global Collectible RPG Analytics

[한국어](README_KR.md) · [Reproduce](#reproduce)

**A Game Operations → Data Analyst portfolio: DA 70% + Analytics Engineer 30%.**
This project reflects my transition from five years in Game Operations into data analysis. It explores acquisition, boss participation, monetization, and incident follow-up in a fictional collectible RPG using independently generated synthetic data.

**Questions:** Which acquisition cohorts brought in more players but retained them less effectively? Is weak boss participation an entry problem? Does a subscription add value or coincide with a spending shift? When should an incident response close?

**Data:** six scenario tables (2024–2025; KR, JP, Global West) plus a separate 360-user registration/login example. The two populations are not linked. The original D30 metric is a synthetic retention indicator, while the added SQL analysis calculates exact-day D7/D30 retention from login records.

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
| [Six analyses](#analysis-details) and [assumption sensitivity](docs/sensitivity.md) | [Cross-table validation checks](src/data_contracts.py) |
| [Proposed experiments](docs/decision_plan.md) | [User-level cohort SQL](sql/user_retention.sql): CTEs, joins, date logic, window function |
| [Connecting operations experience to analysis](docs/operations_to_da.md) | [Independent pandas reconciliation](src/user_retention.py), [edge-case tests](tests/test_user_retention.py) |

## User-level exact-day retention

[Metric specification](docs/user_retention.md) · [Generated cohort results](docs/user_retention_results.md)

The SQL calculates D7 and D30 retention from user login records. Only users who have had enough time to reach D7 or D30 are included in each calculation. Duplicate login records and multiple sessions on the same day are removed before counting retained users. D7 and D30 are calculated independently. This means a user can return on D30 even if they did not log in on D7. The SQL results are then cross-checked against pandas.

## Analysis details

These six analyses use the overall scenario data. Their D1/D7/D30 labels refer to the synthetic retention indicator described above.

1. [Lifecycle](docs/findings/analysis_01_lifecycle.md): event calendar and contextual persistence.
2. [Acquisition quality](docs/findings/analysis_02_retention.md): volume versus synthetic retention indicator.
3. [PvE participation](docs/findings/analysis_03_pve.md): entry and selection hypotheses.
4. [Monetization](docs/findings/analysis_04_monetization.md): total revenue versus adjacent-offer mix.
5. [Incident](docs/findings/analysis_05_incident.md): separate operational, activity and commercial indices.
6. [Regional response](docs/findings/analysis_06_regional_strategy.md): shared warnings, assumption-sensitive severity.

[Source dictionary](docs/data_dictionary.md) · [Synthetic scenario design](docs/scenario_design.md) · [Recomputed headline values](docs/verified_claims.md) · [Notebook](notebooks/game_user_behavior_analysis.ipynb)

## What changed after validation

During validation, I found that some daily unique payer counts were higher than the combined number of product-level buyers, which should not have been possible. The original tests did not catch this because that relationship was not included in the checks.

After correcting the PU logic, several payer-based conclusions changed, including the previous JP-only warning. Revenue, DAU, and the original retention source data did not change. I also added cross-table checks and SQL/pandas comparisons to catch the same type of issue in future runs. [Detailed before/after](docs/validation_changes.md).

## Reproduce

Python 3.12; SQLite is included in Python. Run from repository root:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
MPLBACKEND=Agg python -m src.run_pipeline
MPLBACKEND=Agg python -m src.verify_publication
```

The pipeline reads committed sources, regenerates analysis CSVs/charts and checks SQL parity and generated reports. `verify_publication` executes all notebook code cells in order and checks README claims against generated source evidence. CI runs these same commands. Generated outputs are in `outputs/`.

## Limitations

This project uses synthetic data, so the findings should be treated as scenario-based analysis rather than real production evidence. The dataset does not include individual transactions, VOC/CS records, or experiment assignments, so buyer switching, boss-entry behavior, and causal effects cannot be confirmed at the user level. The separate login example is only used to demonstrate exact-day retention measurement and is not linked to the main scenario data.
