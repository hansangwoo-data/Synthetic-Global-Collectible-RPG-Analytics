# Hiring-Panel and Reproducibility Audit

Reviewed original commit: `952ebc94d33b661b3c5d544090978e4e4c7ca15e`.
Perspective: a senior analyst reviewing a game-operations professional transitioning
to DA, with 70% analysis / 30% analytics engineering emphasis.

## Verdict

Strong domain questions and evidence organization; the original version was not
ready to present as a fully validated analytics pipeline. An independent payer
model contradicted product purchases, and 64 passing tests did not detect it.
The corrected version demonstrates a defensible audit and reconciliation workflow.
It is still a synthetic portfolio, not evidence of senior production DA tenure.

## What was actually reproduced

- All six original checked-in CSVs reproduced from the fixed-seed generator
  (numeric tolerance 1e-9, identical row order and keys).
- All 64 original tests passed before changes.
- All seven original analysis entry points executed on those checked-in CSVs.
- Original headline values (anniversary DAU +34.67%, Fantasy D30 +2.74 pp,
  Astra D30 -2.44 pp, entry index 82.17, subscription revenue +72.21%,
  compensation return index 293.95 and revenue index 56.19) reproduced.
- Reproducing those values did not validate the semantic correctness of the model.
  There are no user-level source logs from which to independently reconstruct
  DAU, unique payers, individual retention or compensation journeys.

## Findings and corrections

| Severity | Evidence in original version | Impact | Correction |
|---|---|---|---|
| Critical | PU exceeded sum(product purchasers) on 1,302 / 2,193 date-region rows; on 968 rows it even exceeded sum(units) | Impossible unique-payer union; invalid payer denominators | Clamp synthetic union to feasible interval; preserve product sales, revenue, activity and RNG sequence; regenerate payer-derived findings |
| High | validate_data accepted an unknown product ID, removed zero-sales row, negative D30 count and complete removal of KR | Passing reports could hide dropped joins, missing scope and invalid data | Full fixed-period grains, foreign-key checks, finite integer checks, cohort-NRU reconciliation and payer union bounds |
| High | Original JP-only offer warning depended on impossible PU | Regional recommendation unsupported after correction | Withdraw JP-only narrative; all regions warn at launch and post-14 |
| High | Remediation PU index originally 104.42 vs revenue 79.20 | Incorrect sequence of commercial recovery | Corrected PU index 79.23; both payers and revenue remain below recovery thresholds |
| Medium | Regional guardrails passed equality at -1 pp / -5% while source analyses failed equality | Decision changes at boundary values | Align strict/inclusive operators and add explicit boundary tests |
| Medium | Incomplete baseline could still receive immediate lift label; stage functions accepted missing regions | Partial observations could look successful | Withhold immediate label on incomplete reference and require full date-region windows |
| Medium | Product summary called summed daily purchasers 'purchasers' | Could be read as deduplicated lifetime buyers | Rename to purchaser_days |
| Medium | SQL implementation absent | SQL and warehouse modeling skill unproven | Add executable SQLite PK/FK/CHECK schema, CTE/window metrics and independent pandas parity checks |
| Medium | Fixed regional evidence strings and manually copied affected findings | Code changes could leave stale conclusions | Derive action evidence and generated findings from results; CI checks document drift |
| Medium | Normal participant outcomes described as locating a pre-combat break | Aggregate participation cannot identify individual funnel dropout | Reframe as an entry/selection hypothesis and specify eligibility/exposure telemetry |
| Medium | Survival-style synthetic counts described as standard game D30 | Nested checkpoints are not conventional exact-day retention | Explicit custom metric boundary and next user-event implementation plan |
| Medium | Notebook regenerated source data before examining it | Could conceal stale checked-in source files | Load and validate committed CSVs by default; generation is an explicit pipeline option |

## Corrected commercial claims

| Claim | Original | Corrected |
|---|---:|---:|
| Launch daily paying-user change | +44.16% | +57.94% |
| Combined launch adjacent revenue/payer-day change | -3.09% | -11.55% |
| Combined post-14 adjacent revenue/payer-day change | -9.89% | -13.32% |
| Regions warning at launch | JP only | KR, JP, Global West |
| Remediation payer recovery index | 104.42 | 79.23 |

The union correction is a transparent modeling choice, not a reconstruction of
hidden real users. Maximum-overlap and no-overlap sensitivity scenarios retain
all-region launch warnings in this dataset, but regional ranking varies.
[Full sensitivity](sensitivity.md), [computed claims](verified_claims.md).

## Hiring interpretation

| Dimension | Evidence shown | Remaining gap |
|---|---|---|
| Business diagnosis | Six connected operational questions, explicit denominators and caveats | Cost, profit, budget constraints and real decision outcomes absent |
| SQL/Python | Reproducible scripts plus independent SQL calculations and mutation tests | User-level joins, sessionization, cohort SQL and realistic event imperfections not demonstrated |
| Analytical reasoning | Corrected conclusions follow corrected data; baseline/overlap sensitivity | Causal identification and experiment execution are proposals, not demonstrated outcomes |
| Data model / AE | Declared grains, schema constraints, reconciliations and CI | No production orchestration, incremental backfill, warehouse deployment, SCD or operational SLA evidence |
| Communication | Decision-first README and traceable findings | Author must explain each denominator and correction without relying on prepared prose |

For a domain-adjacent junior/transition DA role, this can be a strong interview
artifact when the author can defend the work independently. For a senior DA or
production AE role, the repository alone is insufficient. Five years in operations
should be presented as domain experience, not converted into five years of DA tenure.

## Scope limits

SQL parity covers daily rates/rolling DAU, monthly retention, monetization windows
and boss aggregates; it is not a second independent implementation of all six
business decisions. SQL consumes the same synthetic CSVs and cannot validate
real-world truth. Matplotlib charts and notebook are regenerated from corrected
metrics. Thresholds, regional traits and event effects remain authored assumptions.
The experiment and telemetry proposal in [decision_plan.md](decision_plan.md)
is future work; no production A/B test or causal finding is claimed.
