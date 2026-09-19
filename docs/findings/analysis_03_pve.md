# Analysis 3: Core-Content Entry and PvE Engagement

> This analysis uses synthetic scenario data. Boss metrics are aggregate daily counts, not player-level funnels.

## Summary

Astra increased event traffic, but its featured boss reached only about 82% of the usual NORMAL-difficulty participation level.

Participation was lower across all three difficulties and all three regions. However, clear rates and attempts per participant stayed close to the reference bosses.

This suggests the first issue to check is boss discovery or entry, not combat difficulty itself.

## Method

| Rule | Definition |
|---|---|
| Source grain | date × region × boss × difficulty |
| Entry measure | participants ÷ DAU |
| Reference | pooled results from the first three limited bosses |
| Participation threshold | at least 90% of reference |
| Clear-rate comparison | within ±2.0 pp |
| Attempts per participant | within ±0.10 |

Difficulty levels are analyzed separately and are not treated as a sequential user funnel.

## 1. Boss participation and outcomes

![Astra entry and participant outcomes](../../images/pve_difficulty_funnel.png)

| Difficulty | Astra participation | Reference | Entry index | Clear-rate change | Attempt change |
|---|---:|---:|---:|---:|---:|
| NORMAL | 18.11% | 22.04% | 82.17 | -0.13 pp | -0.001 |
| HARD | 9.00% | 10.98% | 81.99 | +0.43 pp | -0.002 |
| NIGHTMARE | 3.70% | 4.45% | 83.10 | -0.24 pp | +0.000 |

Astra falls below the participation threshold at every difficulty.

By contrast, clear-rate and attempt differences remain close to the reference. This does not show a clear combat-performance problem among users who entered the boss.

The first areas to check are therefore event exposure, boss discovery, eligibility, progression readiness and reward communication.

## 2. Regional consistency

![Astra regional entry index](../../images/pve_participation_index_by_region.png)

| Region | Astra participation | Reference | Entry index |
|---|---:|---:|---:|
| KR | 17.97% | 22.03% | 81.57 |
| JP | 17.99% | 22.13% | 81.29 |
| Global West | 18.25% | 22.00% | 82.97 |

All three regions show a similar participation gap, so the result is not driven by one regional mix.

This supports checking the common boss-entry path first, while still monitoring regional differences.

## 3. Traffic, boss entry and D30

![Event context, boss entry, and retention](../../images/event_pve_alignment.png)

| Event context | Event DAU change | NORMAL entry index | D30 change |
|---|---:|---:|---:|
| Half-Anniversary | +7.63% | 100.39 | +3.17 pp |
| Fantasy Crossover | +30.91% | 99.82 | +2.74 pp |
| First Anniversary | +34.67% | 99.97 | +3.21 pp |
| Astra Crossover | +13.59% | 82.17 | -2.44 pp |

Astra increased traffic, but boss participation and D30 retention were both below their reference levels.

The aggregate data cannot show whether low boss entry caused weaker retention, but the combination makes the entry path a reasonable next area to investigate.

## Next step

Before changing combat balance, collect player-level exposure, eligibility and first-attempt data to see where users stop before entering the boss.
