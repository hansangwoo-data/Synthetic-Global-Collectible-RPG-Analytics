# What changed after validation

The first audit challenged business meaning, not only code execution. The second pass adds a separate user-level measurement example while preserving corrected aggregate results.

| Question | Evidence |
|---|---|
| Semantic inconsistency | Daily unique payers exceeded summed product purchasers in 1,302 of 2,193 region-days (and exceeded units in 968). A unique buyer union cannot exceed its constituent buyer counts. |
| Why earlier tests missed it | The original 64 passing tests checked structure and authored scenario expectations without that cross-table business invariant. Agreement with a generator was not proof of valid business semantics. |
| Source correction | Changed only 1,302 PU values using a feasible payer-union bound. The union remains an explicit modeled assumption, not reconstructed individual behavior. Revenue, units, DAU and original checkpoint cohorts did not change. |
| Changed interpretation | Launch PU increase: 44.16% → 57.94%. Adjacent-offer revenue per payer-day post14: −9.89% → −13.32%. The subscription warning now applies to all regions; the JP-only claim was withdrawn. Remediation payer index: 104.42 → 79.23, close to revenue 79.20; “payers recovered ahead of revenue” was withdrawn. |
| Unchanged evidence | Subscription revenue increase 72.21%; cohort-size and checkpoint-proxy changes; content participation; compensation-window returned-user index 293.95 and revenue index 56.19. These remain descriptive synthetic comparisons. |
| First-pass safeguards | Cross-table payer bounds, event-label checks, SQL/pandas parity, generated evidence documents and sensitivity analyses. |
| Second-pass safeguards | Independent user/login tables, exact-day SQL/pandas reconciliation, explicit as-of and cohort maturity rules, duplicate/late-login fixtures, generated retention table, executable notebook verification. No original six-table results were recalibrated to improve the story. |

See [first-pass audit](audit_review.md), [verified claims](verified_claims.md), [assumption sensitivity](sensitivity.md) and [second-pass review](hiring_readiness_review.md).
