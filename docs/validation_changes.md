# What changed after validation

During validation, I found that some daily unique payer counts were higher than the combined number of product-level buyers, which should not have been possible. I corrected the PU logic and updated the affected findings. Revenue, DAU, and the original retention source data did not change.

| Area | What changed |
|---|---|
| Issue found | Daily unique payers exceeded summed product purchasers in 1,302 of 2,193 region-days (and exceeded units in 968). A unique buyer union cannot exceed its constituent buyer counts. |
| Why tests missed it | The original 64 passing tests checked structure and authored scenario expectations without that cross-table business invariant. Agreement with a generator was not proof of valid business semantics. |
| What I changed | Changed only 1,302 PU values using a feasible payer-union bound. The union remains an explicit modeled assumption, not reconstructed individual behavior. Revenue, units, DAU and original checkpoint cohorts did not change. |
| Findings that changed | Launch PU increase: 44.16% → 57.94%. Adjacent-offer revenue per payer-day post14: −9.89% → −13.32%. The subscription warning now applies to all regions; the JP-only claim was withdrawn. Remediation payer index: 104.42 → 79.23, close to revenue 79.20; “payers recovered ahead of revenue” was withdrawn. |
| Findings that stayed the same | Subscription revenue increase 72.21%; cohort-size and checkpoint-proxy changes; content participation; compensation-window returned-user index 293.95 and revenue index 56.19. These remain descriptive synthetic comparisons. |
| Checks added | Cross-table payer bounds, event-label checks, SQL/pandas parity, generated evidence documents and sensitivity analyses. |


See [verified claims](verified_claims.md) and [assumption sensitivity](sensitivity.md) 
