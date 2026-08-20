# Analysis Specification

## 1. Portfolio Positioning

The project combines an approximate 70% decision-analysis emphasis with 30%
analytics-engineering practices.

- Analysis emphasis: business questions, KPI interpretation, operational
  judgment, guardrails, and recommended actions.
- Engineering emphasis: explicit table grain, deterministic generation, tested
  transformations, revenue reconciliation, and reproducible outputs.

All public artifacts use English. Interview preparation and working discussion
are outside the repository.

## 2. Observation Scope

| Item | Definition |
|---|---|
| Service observation | 2024-01-01 through 2025-12-31 |
| Mature D30 cohorts | 2024-01 through 2025-11 |
| Regions | KR, JP, GLOBAL_WEST |
| Daily KPI grain | date × region |
| Currency | Synthetic USD with one global list price |
| General event baseline | 14 calendar days immediately before event start |
| Stable pre-incident baseline | 2025-07-31 through 2025-08-11 (12 clean post-collaboration days) |
| Post-event windows | days 1–14 and 15–28 after event end |

Count metrics are summed across applicable regions. Rate metrics are recomputed
from summed numerators and denominators rather than averaged across regions.
Region-specific events use only their applicable region.

## 3. Evidence Language

### Statistical null

> H0-S: No observable KPI difference exists between an event window and its
> defined baseline.

### Business null

> H0-B: Any observed KPI difference is too small, too short-lived, or offset by
> guardrail deterioration to be operationally meaningful.

This synthetic, intervention-heavy time series is used for descriptive scenario
evaluation. Daily rows are not treated as independent samples for a naive
t-test, and p-values are not the primary decision criterion. Practical effect,
baseline variability, durability, and guardrails drive evaluation.

Observed results, interpretations, and untested hypotheses must be presented
separately. Terms such as “caused,” “proved,” and “measured trust” are avoided.

### Terminology boundary

Daily active users (DAU), paying users, D1/D7/D30 retention, average revenue
per user (ARPU), average revenue per paying user (ARPPU), and conversion rate
follow common game-analytics usage. The following metrics are project-defined
and are not presented as industry standards: recovery index, participation
benchmark index, revenue per service payer-day, and the D30 retained-user gap at
target volume. Their formulas and aggregation limits are stated in this
specification or the Data Dictionary, as applicable.

## 4. Practical Thresholds

An effect is material only when it exceeds both ordinary baseline variation and
the minimum practical threshold below.

### Growth and major events

| Dimension | Minimum practical effect |
|---|---:|
| DAU | +10% |
| NRU or returned users | +15% |
| Revenue | +15% |
| D7 retention | +1.0 percentage point |
| D30 retention | +1.0 percentage point |
| Post-event durability | evaluated only after immediate DAU clears its practical threshold and baseline variability; at least 30% of that lift must remain on days 1–14 |

### Acquisition quality and retention

| Dimension | Decision threshold |
|---|---:|
| Monthly cohort-size lift | +15% |
| D30 quality improvement | +1.0 percentage point |
| D30 quality guardrail | -1.0 percentage point indicates failure |
| D30 retained-user gap at target volume | observed D30 retained minus expected D30 retained at the target cohort size and baseline quality |

Retention is available at `cohort_month × region` grain. An event that occurs
within a month is therefore treated as cohort context, not as a uniquely
identified cause. When multiple events share a month, every overlapping event
is disclosed. Count-weighted retention is recomputed from retained users and
cohort size; regional percentages are not averaged.

The D30 retained-user decomposition separates the arithmetic change from an
average reference month into two parts: the change expected from cohort volume
at the baseline retention rate, and the remaining quality gap at the target
volume. This decomposition is descriptive and is not interpreted causally.

### Seasonal events

| Dimension | Minimum practical effect |
|---|---:|
| DAU | +5% |
| Revenue | +10% |

### New monetization

The PvE Growth Subscription is evaluated with three fixed windows:

| Window | Dates | Role |
|---|---|---|
| Local baseline | 2025-04-15 through 2025-05-14 | Immediate pre-launch comparison |
| Launch | 2025-05-15 through 2025-06-14 | First 31 days available |
| Post-launch days 1–14 | 2025-06-15 through 2025-06-28 | Early persistence and delayed adjacent-product check |

February 2025 is retained as a secondary historical reference. The local
baseline overlaps recovery from a designed content gap, while February reflects
a different service scale. Neither comparison is a randomized control, so the
observed change is not attributed exclusively to the new product.

`Revenue per service payer-day` divides period revenue by the sum of all daily
paying users in the service. It is not revenue per buyer of the measured
product, and it is not period ARPPU because identities cannot be deduplicated
across days. Adjacent-product diagnostics combine the monthly mission pass,
premium-currency pass, and account growth booster, then inspect each product
and region separately.

| Dimension | Decision threshold |
|---|---:|
| Daily total revenue | +10% |
| Daily paying users | +5% |
| Adjacent recurring revenue per service payer-day | -5% triggers reallocation warning |
| May–June service-cohort D30 vs February | -1.0 percentage point triggers guardrail failure |

The decomposition separates the launch-period daily revenue lift into
legacy-product change and new-product revenue. It is an arithmetic description,
not a causal incrementality estimate. Product-revenue HHI and top-three share
are concentration diagnostics rather than pass/fail criteria. Adding another
revenue-bearing product can mechanically lower concentration, so a decline is
not evidence of incremental value. Sales represent synthetic gross revenue at
list price and exclude refunds, taxes, discounts, and platform fees.

### Incident recovery

Daily operational recovery uses the clean 2025-07-31 through 2025-08-11
baseline and preserves the authored incident sequence:

| Stage | Dates | Analytical role |
|---|---|---|
| Full outage | 2025-08-12 | Zero observable activity and commerce |
| Partial restoration | 2025-08-13 | 50% availability after 36 total hours offline |
| Delayed response | 2025-08-14 through 2025-08-16 | Technical instability and weak communication |
| Extraordinary compensation | 2025-08-17 through 2025-08-23 | Return response versus commercial recovery |
| Postmortem and remediation | 2025-08-24 through 2025-09-20 | Root-cause disclosure and safeguards |
| Residual post-recovery | 2025-09-21 through 2025-09-30 | Persistence before the next seasonal event |

| Recovery index | Target |
|---|---:|
| DAU | at least 95 |
| Paying users | at least 90 |
| Revenue | at least 90 |
| D30 retention | within -0.5 percentage point of mature pre-incident baseline |

Recovery Index is calculated as post-recovery KPI divided by stable
pre-incident KPI, multiplied by 100.

The June 2025 cohort is the latest D30 cohort whose observation is complete
before the outage. July is displayed but not used as the clean retention
reference because its acquisition context includes Astra and its D30 observation
overlaps the incident. October overlaps the regional autumn event, while
November has no planned-event overlap. The final post-recovery D30 check is
count-weighted across both cohorts for stability, but both months must also fail
the guardrail independently in every region before the pooled gap is described
as persistent. This is a cross-context quality check, not an incident-level
causal estimate.

`user_outflow = 0` during the full outage means outflow is unobservable while
the service is unavailable; it is not interpreted as zero latent attrition.
Post-recovery outflow is a secondary diagnostic with no pass/fail threshold;
the final Mixed classification is determined by operational KPI recovery and
the D30 guardrail. Outflow, payer behavior, and retention are behavioral
proxies. They do not directly measure player trust or sentiment.

### Regional synthesis

The final analysis preserves the original units and thresholds from Analyses 1
through 5. It does not create a composite regional score because revenue lift,
retention percentage points, participation indices, and recovery indices are
not commensurable without subjective weights.

- A shared priority requires the same defined guardrail to fail in all three
  regions.
- A localized priority requires a unique threshold failure or a clearly worst
  regional result with a decision-relevant gap. An isolated diagnostic remains
  an investigation priority rather than a causal conclusion.
- A regional strength is retained alongside each risk so high-upside regions
  are not ranked as simply “good” or “bad.”
- Actions are ordered by decision urgency, not by a fabricated numeric score.

### Limited PvE bosses

| Dimension | Decision rule |
|---|---|
| Participation | at least 90% of comparable-boss benchmark |
| Clear rate | evaluated by difficulty, not against one universal target |
| Clear-rate comparability | within ±2.0 percentage points of difficulty benchmark |
| Attempts per daily participant | within ±0.10 of difficulty benchmark is comparable burden |

The benchmark pools the first three limited-boss contexts separately by
difficulty. Astra is excluded from its construction and is the held-out
comparison. The first three bosses' near-100 indices must not be presented as
independent validation results.

Low participation with comparable participant outcomes is treated as a
pre-entry or entry-stage gap, not proof that combat difficulty is normal for all
eligible players. Monetization pressure, perceived required power, reward
appeal, and audience fit remain hypotheses unless player-level power,
ownership, and purchase data are available.

Difficulty-level participants may overlap. They must not be summed and labeled
as unique total boss participants. The same player may also appear on multiple
days. NORMAL participation is used as the broadest available entry proxy;
HARD and NIGHTMARE remain separate difficulty-level comparisons rather than
sequential stages.

## 5. Outcome Labels

### Successful

- primary KPI exceeds its practical threshold;
- quality or durability is also positive; and
- no critical guardrail deteriorates.

### Mixed

- the primary KPI improves materially;
- durability, user quality, product cannibalization, or another guardrail
  fails.

### Underperforming

- the primary KPI does not reach its practical threshold; or
- short-term improvement is outweighed by material quality or guardrail damage.

Analysis-level labels are provisional until all required dimensions are analyzed.
For example, Analysis 1 can assess immediate traffic and durability, but a final
collaboration label also requires retention and PvE participation evidence.

## 6. Overlapping Events

Post-event durability is not attributed to one event when another material
event overlaps the measurement window. The output must:

1. list overlapping events;
2. mark the window as contaminated; and
3. avoid a definitive durability label for that window.

This prevents a later seasonal event, collaboration, or incident from being
misattributed to the earlier event.

The same overlap check is reported for the baseline window, but it answers a
different question. A post-window overlap prevents a durability conclusion
because persistence cannot be observed independently. A baseline overlap can
still support a relative comparison with the prior event context, but it cannot
support a standalone event-effect label. Such results must be marked
`contextual` and must name the overlapping baseline event. When the immediate
DAU change clears materiality and the post-window is clean, the result may be
labeled `Contextual persistence`. If either condition is not met, it remains
`Contextual comparison only`.

## 7. Visualization Standard

- KR: green
- JP: orange
- GLOBAL_WEST: blue
- Regional series appear together in one chart whenever legibility permits.
- Absolute charts communicate scale.
- Indexed charts communicate relative change when scale differences obscure
  regional patterns.
- Small multiples are a fallback, not the default.
- Count and rate metrics are not mixed on one axis.
- Every comparison chart names its baseline.

## 8. Analysis Sequence

1. Service lifecycle and event dependence
2. Acquisition quality and retention
3. Core-content entry and PvE engagement
4. Revenue growth and subscription value
5. Incident impact and recovery resilience
6. Regional strategy synthesis

Formal ARIMA forecasting is excluded from the core scope. Known interventions
and structural breaks dominate the series, while the portfolio questions focus
on operational diagnosis rather than forecasting. Trend, seasonality,
7-day smoothing, and event-aware windows remain part of the analysis.
