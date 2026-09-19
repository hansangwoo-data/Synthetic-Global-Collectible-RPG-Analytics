# Analysis 4: Revenue Growth and Subscription Value

> This analysis uses synthetic scenario data. Paying-user counts are service-level daily values, not deduplicated monthly users.

## Summary

Revenue increased strongly after the PvE Growth Subscription launched, but adjacent offers weakened on a revenue-per-payer basis.

The subscription contributed part of the total increase, while most of the revenue lift came from the existing product catalog. This suggests the launch increased overall revenue but may also have shifted spending across offers.

## Method

| Rule | Definition |
|---|---|
| Baseline | 2025-04-15 to 2025-05-14 |
| Launch | 2025-05-15 to 2025-06-14 |
| Post-launch | 2025-06-15 to 2025-06-28 |
| Revenue threshold | +10% |
| Paying-user threshold | +5% |
| Adjacent-offer warning | -5% revenue per payer-day |
| D30 warning | -1.0 pp vs February |

February is kept as a secondary historical reference.

## 1. Revenue and payer growth

![Revenue bridge](../../images/bm_revenue_decomposition.png)

| Metric | Baseline | Launch |
|---|---:|---:|
| Paying users per day | 1,812.37 | 2,862.52 |
| Conversion rate | 2.37% | 3.43% |
| Revenue per service payer-day | $10.55 | $11.50 |

Revenue per day increased by 72.21%, while paying users per day increased by 57.94%.

The new subscription contributed about 25% of the total revenue increase. Most of the lift came from higher revenue in existing products.

## 2. Adjacent offers

![Adjacent offers](../../images/adjacent_product_cannibalization.png)

| Product | Launch change | Post-launch change |
|---|---:|---:|
| Monthly Mission Pass | -8.85% | -10.05% |
| 30-Day Premium Currency Pass | -12.78% | -15.89% |
| Account Growth Booster | -15.33% | -16.54% |
| Combined adjacent set | -11.55% | -13.32% |

All three adjacent offers fell below the -5% warning threshold on a revenue-per-payer basis.

However, their absolute revenue per day was still above baseline after launch. This means the data suggests a change in spending mix, not an overall collapse in those products.

## 3. Regional results

![Regional checks](../../images/bm_regional_guardrails.png)

| Region | Revenue change | Paying-user change | Adjacent post-launch change |
|---|---:|---:|---:|
| KR | +59.78% | +51.48% | -12.64% |
| JP | +57.70% | +33.03% | -10.83% |
| Global West | +94.96% | +85.46% | -15.43% |

The same pattern appears in all three regions: overall revenue and payer counts increased, while adjacent-offer revenue per payer declined.

Global West shows the largest change in both directions.

## Validation note

During validation, service-level paying-user counts were corrected so they stayed within valid product-level buyer limits. Revenue and sales data did not change.

See [validation changes](../validation_changes.md) for details.

## Next step

Collect user-level purchase and subscription data to check whether the same users moved spending between offers.

Analysis 5 looks at how activity and revenue recovered after the service incident.
