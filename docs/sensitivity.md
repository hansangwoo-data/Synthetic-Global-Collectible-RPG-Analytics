# Sensitivity Checks

## 1. Payer assumptions

Daily service PU is not based on individual buyer identities, so the exact overlap between product purchasers is unknown.

To check whether the main monetization finding depends on that assumption, I compared three valid payer-count scenarios:

- Published assumption
- Maximum buyer overlap
- No overlap, capped at DAU

| Scope | Payer assumption | PU change | Adjacent launch change | Adjacent post-launch change |
|---|---|---:|---:|---:|
| ALL | Published | +57.94% | -11.55% | -13.32% |
| KR | Published | +51.48% | -10.63% | -12.64% |
| JP | Published | +33.03% | -7.55% | -10.83% |
| Global West | Published | +85.46% | -14.57% | -15.43% |
| ALL | Maximum overlap | +55.94% | -10.41% | -8.73% |
| KR | Maximum overlap | +50.40% | -9.99% | -8.45% |
| JP | Maximum overlap | +38.52% | -11.21% | -8.16% |
| Global West | Maximum overlap | +76.24% | -10.10% | -9.30% |
| ALL | No overlap | +63.86% | -14.74% | -14.10% |
| KR | No overlap | +56.92% | -13.72% | -12.64% |
| JP | No overlap | +45.81% | -15.66% | -13.59% |
| Global West | No overlap | +85.90% | -14.77% | -15.43% |

The exact size changes, but the direction is stable: paying users increase while adjacent-offer revenue per payer declines.

## 2. Baseline length

I also compared 7-, 14- and 28-day baselines for the subscription and compensation periods.

| Context | Baseline | Overlap | DAU | PU | Revenue | Returned users |
|---|---:|---|---:|---:|---:|---:|
| Subscription | 7 days | None | +10.81% | +46.70% | +61.38% | +14.42% |
| Subscription | 14 days | None | +13.02% | +50.13% | +63.19% | +15.68% |
| Subscription | 28 days | Spring Content Gap | +10.19% | +58.58% | +72.34% | +34.54% |
| Compensation | 7 days | None | -6.54% | -42.99% | -43.22% | +190.69% |
| Compensation | 14 days | Astra Heroes Crossover | -8.27% | -47.29% | -54.00% | +180.45% |
| Compensation | 28 days | Astra Heroes Crossover | -6.80% | -53.53% | -69.65% | +140.59% |

Baseline choice changes the size of the result, especially when longer windows include another event. The overall direction remains the same.

## Takeaway

These checks do not prove causal effects. They show that the main conclusions are not dependent on one payer assumption or one baseline length.

For a real service, user-level purchase, exposure and assignment data would be needed for stronger conclusions.
