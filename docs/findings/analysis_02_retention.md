# Analysis 2: Acquisition Quality and Retention

> This analysis uses synthetic scenario data. D1/D7/D30 in the main scenario are synthetic retention indicators.

## Summary

Fantasy and Astra both increased acquisition, but their retention paths differed. Fantasy improved both cohort size and D30 retention, while Astra increased cohort size but showed weaker D7 and D30 retention.

## Method

| Rule | Definition |
|---|---|
| Cohort grain | acquisition month × region |
| Cohort-size threshold | +15% |
| D30 improvement | +1.0 pp |
| D30 warning | -1.0 pp |
| Mature cohorts | through November 2025 |

Retention rates are recalculated from retained-user counts and cohort size. Campaign months are treated as context when other events overlap.

## 1. Regional D30 trend

![Regional retention](../../images/retention_trend_by_region.png)

All three regions show the same broad pattern: stronger Fantasy-context retention, weaker Astra-context retention, and the lowest D30 around the August incident period.

Regional levels differ, but the direction of the major changes is shared.

## 2. Acquisition volume and D30 quality

![Acquisition quality matrix](../../images/acquisition_quality_matrix.png)

| Campaign context | Cohort-size change | D30 change |
|---|---:|---:|
| Half-Anniversary | +0.1% | +3.17 pp |
| Fantasy Crossover | +79.2% | +2.74 pp |
| First Anniversary | +100.2% | +3.21 pp |
| Astra Crossover | +50.1% | -2.44 pp |

Fantasy and the First Anniversary increased both acquisition volume and D30 retention. The Half-Anniversary improved retention without meaningful volume growth.

Astra increased cohort size by 50.1%, but D30 fell by 2.44 pp. The campaign therefore brought in more users without maintaining the same long-term retention quality.

## 3. Collaboration retention path

![Collaboration retention](../../images/collaboration_retention_comparison.png)

| Collaboration | Cohort-size change | D1 | D7 | D30 |
|---|---:|---:|---:|---:|
| Fantasy | +79.2% | +5.43 pp | +5.04 pp | +2.74 pp |
| Astra | +50.1% | +1.99 pp | -1.40 pp | -2.44 pp |

Fantasy improved at every checkpoint. Astra started slightly above its reference at D1, then fell below it at D7 and D30.

This suggests the main issue appears after the initial acquisition response rather than at first-day activity. The current aggregate data cannot show whether the cause is audience fit, onboarding, progression, content entry or another factor.

## Next step

Analysis 3 checks whether Astra's weaker retention appears together with lower entry into its featured PvE content.
