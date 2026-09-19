# Analysis 6: Regional Comparison

> This analysis uses synthetic scenario data and summarizes the main regional differences from Analyses 1–5.

## Summary

All three regions show the same broad risks: weaker Astra D30 retention, lower boss participation, and weaker adjacent-offer revenue per payer after the subscription launch.

The size of those changes differs by region. Global West shows the strongest subscription revenue growth but also the largest adjacent-offer decline and post-incident D30 gap. KR shows the weakest NRU recovery index, while JP shows the strongest Fantasy-context D30 improvement.

## Regional comparison

![Regional evidence](../../images/regional_cross_analysis_evidence.png)

| Region | Fantasy D30 | Astra D30 | Astra boss entry index | Subscription revenue | Adjacent post-launch | Post-incident D30 |
|---|---:|---:|---:|---:|---:|---:|
| KR | +2.37 pp | -2.40 pp | 81.57 | +59.78% | -12.64% | -0.67 pp |
| JP | +3.79 pp | -2.13 pp | 81.29 | +57.70% | -10.83% | -1.02 pp |
| Global West | +2.64 pp | -2.58 pp | 82.97 | +94.96% | -15.43% | -1.58 pp |

## Shared findings

![Guardrails](../../images/regional_guardrail_matrix.png)

- Astra D30 retention is below the warning threshold in all three regions.
- Astra boss participation is below the reference threshold in all three regions.
- Adjacent-offer revenue per payer declines after subscription launch in all three regions.
- Daily operational metrics recover after the incident in all three regions.
- Post-incident D30 remains below the June reference in all three regions.

These shared patterns support common measurement and testing across regions before applying region-specific changes.

## Regional focus

**KR:** Check acquisition mix and boss-entry eligibility first. KR has the lowest NRU recovery index and a similar Astra entry gap to the other regions.

**JP:** Monitor offer differentiation and retention. JP has the strongest Fantasy-context D30 improvement, but still shows the same Astra entry and adjacent-offer warnings.

**Global West:** Review acquisition quality and offer mix before scaling further. It has the strongest subscription revenue growth, but also the largest adjacent-offer decline and post-incident D30 gap.

## Next step

Use the same core measurements across all three regions, then adjust experiments based on the regional differences above.

See the [decision plan](../decision_plan.md) for the proposed tests.
