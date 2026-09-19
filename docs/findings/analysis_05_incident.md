# Analysis 5: Incident and Recovery

> This analysis uses synthetic scenario data. Recovery indices compare each recovery stage with the pre-incident reference.

## Summary

User activity recovered faster than commercial metrics after the outage.

During the compensation period, returned users reached 293.95% of the pre-incident baseline, while revenue recovered to 56.19%. By late September, DAU, paying users and revenue had returned close to their reference levels, but later D30 retention remained below the pre-incident cohort.

## Method

| Rule | Definition |
|---|---|
| Pre-incident reference | 2025-07-31 to 2025-08-11 |
| DAU recovery target | 95 |
| Paying-user recovery target | 90 |
| Revenue recovery target | 90 |
| D30 warning | below -0.5 pp vs June reference |

A recovery index of 100 matches the pre-incident reference.

## 1. Daily recovery

![Daily recovery](../../images/incident_daily_recovery_by_region.png)

| Stage | DAU index | Paying-user index | Revenue index | Returned-user index |
|---|---:|---:|---:|---:|
| Pre-incident baseline | 100.00 | 100.00 | 100.00 | 100.00 |
| Full outage | 0.00 | 0.00 | 0.00 | 0.00 |
| Partial restoration | 46.19 | 3.77 | 4.05 | 13.18 |
| Delayed response | 70.43 | 11.16 | 11.50 | 59.51 |
| Compensation | 92.21 | 56.02 | 56.19 | 293.95 |
| Remediation | 102.04 | 79.23 | 79.20 | 149.58 |
| Late September | 100.24 | 95.21 | 92.01 | 100.06 |

Activity recovered first. Compensation produced a large return spike, but payment and revenue recovery remained much lower during the same period.

![Commercial recovery](../../images/incident_reactivation_commercial_bridge.png)

This shows why technical recovery, user return and commercial recovery should be tracked separately.

## 2. Regional recovery

The regional results below use the late-September recovery stage, with D30 compared against the June reference cohort.

![Regional exits](../../images/incident_regional_exit_guardrails.png)

| Region | DAU index | Paying-user index | Revenue index | D30 change |
|---|---:|---:|---:|---:|
| KR | 100.25 | 93.38 | 90.36 | -0.67 pp |
| JP | 99.71 | 94.61 | 90.88 | -1.02 pp |
| Global West | 100.52 | 96.84 | 93.99 | -1.58 pp |

All three regions recovered the daily operational metrics by late September.

However, D30 retention remained below the June reference in every region, with the largest gap in Global West.

## 3. Post-incident D30

![Mature cohorts](../../images/incident_d30_recovery_by_region.png)

| Cohort | D30 retention | Change vs June |
|---|---:|---:|
| June reference | 8.52% | 0.00 pp |
| July | 6.09% | -2.43 pp |
| August | 3.94% | -4.58 pp |
| September | 7.61% | -0.91 pp |
| October | 7.10% | -1.42 pp |
| November | 7.48% | -1.04 pp |

Later cohorts improved from the August low, but October and November still remained below the June reference.

These are new acquisition cohorts, so they do not show whether the same incident-affected users fully recovered.

## Next step

Close the daily incident response only after activity, payer and revenue targets recover. Continue retention monitoring separately.

For future incidents, connect outage exposure, compensation, return and payment activity at the user level.
