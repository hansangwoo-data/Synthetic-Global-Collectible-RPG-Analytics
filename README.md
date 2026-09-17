# Synthetic Global Collectible RPG Analytics

[한국어](README_KR.md) · [Hiring review](docs/hiring_readiness_review.md) · [Reproduce](#reproduce)

**A Game Operations → Data Analyst portfolio: DA 70% + Analytics Engineer 30%.**
I frame live-service business questions, check whether the metrics are valid, and turn descriptive findings into testable decisions. All data is independently generated and fictional; no production player records or commercial impact are claimed.

**Questions:** Which acquisition cohorts warrant follow-up? Is weak boss participation an entry problem? Does a subscription add value or coincide with a spending shift? When should an incident response close?

**Data:** six aggregate scenario tables (2024–2025; KR, JP, Global West) plus a separate 360-user registration/login example. The two populations are not linked. Aggregate D30 is a **nested checkpoint proxy**; the added SQL analysis measures **session-based exact-day D7/D30**.

| Evidence from the synthetic scenario | Decision supported, not a causal conclusion |
|---|---|
| Astra cohort size +50.07%, D30 checkpoint proxy −2.44 pp | Instrument acquisition mix and test onboarding before scaling acquisition. | <!-- claim:astra_crossover_2025_cohort_change_pct:50.07 claim:astra_crossover_2025_d30_change_pp:-2.44 -->
| Astra normal boss participation index 82.17 (reference 100) | Test eligible-user entry communication; comparable entrant outcomes do not rule out selection. | <!-- claim:astra_normal_participation_index:82.17 -->
| Subscription-window revenue +72.21%; adjacent-offer revenue per payer-day −13.32% in post14 | Test offer differentiation in all regions; buyer switching is unobserved. | <!-- claim:subscription_revenue_change_pct:72.21 claim:adjacent_post14_change_pct:-13.32 -->
| Compensation-window returned-user index 293.95 vs revenue index 56.19 (reference 100) | Separate technical restoration, user activity and commercial follow-up. | <!-- claim:compensation_returned_index:293.95 claim:compensation_revenue_index:56.19 -->

**Why trust the workflow:** cross-table business invariants exposed impossible payer counts that earlier tests missed. Corrected source data, independent SQL/pandas reconciliation, generated evidence and a reproducible pipeline now check the results. [What changed after validation](docs/validation_changes.md).

**What I would do next:** instrument missing exposure/eligibility/payment facts, then run a reversible pilot with defined primary KPIs, guardrails and stop rules. No experiment has been run. [Action framework](docs/decision_plan.md).

## Evidence of DA 70% + AE 30%

| DA: decision-making and communication | AE: trustworthy analytical inputs |
|---|---|
| [Business questions and metric definitions](docs/analysis_spec.md) | [Table grain and data model](docs/data_model.md) |
| [Six analyses](#analysis-details) and [assumption sensitivity](docs/sensitivity.md) | [Cross-table business contracts](src/data_contracts.py) |
| [Evidence → hypothesis → action → stopping rules](docs/decision_plan.md) | [User-level cohort SQL](sql/user_retention.sql): CTEs, joins, date logic, window function |
| [Operations experience: contribution/evidence prompts](docs/operations_to_da.md) | [Independent pandas reconciliation](src/user_retention.py), [edge-case tests](tests/test_user_retention.py) |

The ratio describes portfolio emphasis, not measured job tenure. Five years of operations experience is not presented as five years of DA experience. Specific workplace accomplishments require the author's own supporting evidence.

## User-level exact-day retention

[Metric specification](docs/user_retention.md) · [Generated cohort results](docs/user_retention_results.md)

The SQL counts registered users who log in on exactly day 7 or 30. Each horizon has its own mature-user denominator. It handles duplicate deliveries, multiple sessions, late arrivals and an explicit UTC snapshot. A user can return on D30 without returning on D7. SQL and pandas must agree on every output count and rate.

The small supplemental population demonstrates measurement correctness; it neither validates the original aggregate scenario's player-level mechanisms nor establishes regional rankings. March cohorts have incomplete observation and must not be compared as full-month D30 results.

## Analysis details

All six legacy analyses use the aggregate scenario. “Recovery” refers to a return toward a declared reference, not restored trust or the same individuals returning. Retention labels in legacy charts/column names denote the documented checkpoint proxy.

1. [Lifecycle](docs/findings/analysis_01_lifecycle.md): event calendar and contextual persistence.
2. [Acquisition quality](docs/findings/analysis_02_retention.md): volume versus checkpoint proxy.
3. [PvE participation](docs/findings/analysis_03_pve.md): entry/selection hypothesis, no individual funnel claim.
4. [Monetization](docs/findings/analysis_04_monetization.md): total revenue versus adjacent-offer mix.
5. [Incident](docs/findings/analysis_05_incident.md): separate operational, activity and commercial indices.
6. [Regional response](docs/findings/analysis_06_regional_strategy.md): shared warnings, assumption-sensitive severity.

[Source dictionary](docs/data_dictionary.md) · [Synthetic scenario design](docs/scenario_design.md) · [Recomputed headline values](docs/verified_claims.md) · [Notebook](notebooks/game_user_behavior_analysis.ipynb)

## What changed after validation

A payer-union inconsistency survived the original tests because those tests did not reconcile unique payers with product-level buyer bounds. Correcting PU changed payer-derived conclusions and removed the JP-only warning. Revenue, DAU and checkpoint source data stayed unchanged. New safeguards check business meaning as well as reproducibility. The second pass adds independent exact-day logs without changing those validated aggregate results. [Detailed before/after](docs/validation_changes.md).

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

`--regenerate` reproduces both the six-table scenario and the separate user-log population. Review any resulting source/evidence diff. Four aggregate SQL views and one user-cohort SQL query are reconciled independently with pandas. Tests include business bounds and manually constructed temporal edge cases; passing tests do not establish external validity.

## Limitations

Authored synthetic relationships cannot establish causality, real-world ROI or generalizable retention rates. Daily PU remains a modeled feasible union, not observed unique buyers. There are no individual transactions, VOC/CS records or experiment assignments. Cohort maturity and baseline selection matter; regional severity can change with payer assumptions. [Remaining weaknesses and interview preparation](docs/hiring_readiness_review.md).
