# Analysis Specification

## 1. Scope

| Item | Definition |
|---|---|
| Service observation | 2024-01-01 through 2025-12-31 |
| Mature D30 cohorts | 2024-01 through 2025-11 |
| Regions | KR, JP, GLOBAL_WEST |
| Daily KPI grain | date × region |
| Currency | Synthetic USD |
| General event baseline | 14 days before event start |
| Stable pre-incident baseline | 2025-07-31 through 2025-08-11 |
| Post-event windows | days 1–14 and 15–28 |

Counts are summed across regions where appropriate. Rates are recalculated from their numerators and denominators rather than averaged.

## 2. Interpretation rules

This project uses synthetic scenario data, so comparisons are descriptive rather than causal.

D1/D7/D30 in the main scenario are synthetic retention indicators, not exact-day session retention. The separate user-level example demonstrates exact-day D7/D30 from login records.

When event windows overlap, the result is treated as contextual rather than attributed to one event.

## 3. Decision thresholds

### Major events

| Metric | Threshold |
|---|---:|
| DAU | +10% |
| NRU or returned users | +15% |
| Revenue | +15% |
| D7 retention | +1.0 pp |
| D30 retention | +1.0 pp |

### Seasonal events

| Metric | Threshold |
|---|---:|
| DAU | +5% |
| Revenue | +10% |

### Acquisition quality

| Metric | Threshold |
|---|---:|
| Cohort-size increase | +15% |
| D30 improvement | +1.0 pp |
| D30 warning | -1.0 pp |

### Subscription analysis

| Window | Dates |
|---|---|
| Baseline | 2025-04-15 to 2025-05-14 |
| Launch | 2025-05-15 to 2025-06-14 |
| Post-launch | 2025-06-15 to 2025-06-28 |

| Metric | Threshold |
|---|---:|
| Daily revenue | +10% |
| Daily paying users | +5% |
| Adjacent-offer revenue per payer-day | -5% warning |
| D30 vs February | -1.0 pp warning |

### Incident recovery

| Metric | Target |
|---|---:|
| DAU index | 95 |
| Paying-user index | 90 |
| Revenue index | 90 |
| D30 | ≥ -0.5 pp vs pre-incident reference |

### PvE participation

| Metric | Rule |
|---|---|
| Participation | at least 90% of reference |
| Clear-rate comparison | within ±2.0 pp |
| Attempts per participant | within ±0.10 |

## 4. Analysis notes

Retention is measured at month × region grain, so campaign months are treated as context rather than isolated causes.

Revenue per payer-day uses daily paying-user counts and is not deduplicated monthly ARPPU.

Boss participation is measured separately by difficulty; difficulty levels are not treated as a sequential funnel.

## 5. Analysis sequence

1. Service lifecycle and event dependence
2. Acquisition quality and retention
3. Core-content entry and PvE engagement
4. Revenue growth and subscription value
5. Incident impact and recovery
6. Regional comparison
