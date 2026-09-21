# What changed after validation

During validation, I found that some daily unique payer counts were higher than the combined number of product-level buyers, which should not have been possible. I corrected the PU logic and updated the affected findings. Revenue, DAU, and the original retention source data did not change.

| Area | What changed |
|---|---|
| Issue found | Daily unique payers exceeded summed product purchasers in 1,302 of 2,193 region-days (and exceeded units in 968). A unique buyer union cannot exceed its constituent buyer counts. |
| Why tests missed it | The original 64 tests checked structure and expected scenario outputs, but they did not compare payer counts across related tables. |
| What I changed | I corrected 1,302 PU values so that daily unique payer counts stayed within valid product-level buyer limits. Revenue, units, DAU, and the original retention data did not change. |
| Findings that changed | Launch PU increase: 44.16% → 57.94%. Adjacent-offer revenue per payer-day post14: −9.89% → −13.32%. The subscription warning now applies to all regions; the JP-only claim was withdrawn. Remediation payer index: 104.42 → 79.23, close to revenue 79.20; “payers recovered ahead of revenue” was withdrawn. |
| Findings that stayed the same | Subscription revenue +72.21%, cohort size and retention changes, content participation, and the compensation-period returned-user and revenue results remained unchanged. |
| Checks added | Added cross-table payer checks, event-label checks, SQL/pandas comparisons, and sensitivity checks. |


See [verified claims](verified_claims.md) and [assumption sensitivity](sensitivity.md).
