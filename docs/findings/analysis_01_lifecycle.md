# Analysis 1: Service Lifecycle and Event Dependence

> This analysis uses synthetic scenario data. D1/D7/D30 in the main scenario are synthetic retention indicators.

## Summary

The First Anniversary produced a large DAU increase that remained elevated after the event. Planned events also accounted for a growing share of annual revenue, while revenue intensity per event day declined slightly as the event calendar expanded.

## Method

| Rule | Definition |
|---|---|
| Baseline | 14 days before each event |
| Immediate change | Event period vs baseline |
| Major-event DAU threshold | +10% |
| Seasonal-event DAU threshold | +5% |
| Durability | At least 30% of the initial lift remains during days 1–14 |
| Overlap | Results are treated as contextual when another event overlaps |

Regional counts are summed and rates are recalculated from their components.

## 1. Regional DAU trend

[chart]

Each region follows the same broad lifecycle: early growth, decline, anniversary peaks, a 2025 content gap, partial recovery and the August outage. Global West shows larger swings, while JP is more stable.

The common direction supports one global lifecycle view, but the different amplitudes justify checking regions separately.

## 2. Event lift and durability

[chart + table]

### Key findings

- First Anniversary: +34.7% DAU during the event and +49.9% in the following 14 days relative to its elevated holiday baseline.
- PvE Growth Subscription: +13.0% during launch and +20.0% afterward.
- Both collaborations increased traffic, but their post-event windows overlap other events, so durability cannot be isolated.
- Half-Anniversary remained elevated afterward, but its initial +7.6% lift did not clear the +10% major-event threshold.

The event results show where traffic increased, but retention and monetization must be checked separately.

## 3. Planned-event dependence

[chart + table]

Planned events covered 17.5% of 2024 and 31.0% of 2025, while accounting for 33.3% and 54.5% of annual revenue respectively.

However, the revenue-share/day-share ratio declined from 1.90× to 1.76×. Event days therefore became more common, but slightly less revenue-dense relative to the average day.

## Next step

Analysis 2 checks whether the larger acquisition cohorts also retained users better.
