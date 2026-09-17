# Decision Brief and Next Evidence

## Decision now

Fund measurement and a reversible offer/entry test before more acquisition spend.
The synthetic analysis demonstrates how to define a decision and reject weak
interpretations. It does not establish real commercial ROI or a production impact.

| Priority | Decision owner (proposed) | What is observed | Competing explanations | Evidence needed | Next decision |
|---|---|---|---|---|---|
| 1 | Product analyst + content PM | Astra NORMAL participation index 82.2; entrant outcomes comparable | Eligibility, exposure, reward appeal, audience mix, power selection | exposure, eligibility with reason, boss page, first attempt, clear; join by user and event | Choose an entry intervention only after locating the loss among eligible users |
| 2 | Monetization PM + analyst | Adjacent revenue per payer-day declines in all regions | Buyer migration, new payer composition, renewal timing, assumed payer overlap | User-level transactions, entitlements, renewal, refunds and assignment | Test benefit differentiation before removing or repricing offers |
| 3 | Incident owner + analyst | Activity recovers before commerce; later acquisition-cohort D30 remains weak | Acquisition mix, seasonal context, incident exposure, communication | Affected users, time of failed login, communication exposure, claim, session, purchase | Close operational response separately from cohort quality follow-up |

## One executable experiment proposal: boss-entry communication

- Question: does clearer reward/unlock communication increase first boss attempts
  among eligible active users?
- Population: users eligible for the next comparable boss at assignment; define
  bot/test exclusions before randomization. Do not select users based on treatment exposure.
- Unit: stable user-level assignment, 50/50, stratified by region and tenure.
  If social spillovers are material, assess guild-level assignment and the resulting
  sample-size penalty before launch.
- Treatment: clearer entry and reward information; control: current experience.
- Primary metric: any first boss attempt within seven days / all assigned eligible
  users (intention to treat), deduplicated at user-event grain.
- Secondary: clear yield per assigned user and repeated participation. Compare
  conditional clear rates cautiously because treatment changes who enters.
- Guardrails: crash/error rate, D7 activity, net revenue per assigned user and
  support-contact rate. Lock practical loss margins with owners before launch.
- Sizing: calculate sample size from the instrumented eligible-user baseline,
  business MDE, power and assignment design. The current 18% participant-day/DAU
  rate is not a valid substitute for a user-level eligible-entry baseline.
- Duration: cover at least two weekly cycles, then complete each user's seven-day
  follow-up. Choose the stopping rule and analysis date before observing outcomes.
- Checks: assignment uniqueness, sample-ratio mismatch, event latency/deduplication,
  cross-variant contamination, and comparable missingness by arm.
- Decision: ship only if the prespecified effect criterion is met and guardrails
  satisfy agreed margins. If inconclusive, report the interval and attainable MDE;
  do not reinterpret a positive point estimate as success.

No experiment was run in this repository. This is a design proposal.

## Minimum production telemetry contract

| Event/fact | Grain/key | Required fields | Failure checks |
|---|---|---|---|
| registration | user_id | registered_at_utc, acquisition channel, region | duplicates, unknown region, late ingestion |
| session | event_id | user_id, occurred_at_utc, received_at_utc | idempotency, time inversion, late arrivals |
| boss eligibility | user_id × boss_id × evaluated_at | eligibility, reason, power, assignment | missing eligibility, post-treatment selection |
| boss action | event_id | user_id, boss_id, action, occurred_at | duplicate attempts, unknown boss, broken sequence |
| transaction | transaction_id | user_id, product_id, gross, currency, tax, fee, refund | duplicate charge, FX convention, refund reconciliation |
| experiment assignment | experiment_id × user_id | variant, assigned_at, strata | reassignment, ratio mismatch |

Define a single UTC date boundary, immutable event IDs and a documented late-data
reprocessing window. Exact-day D30 must be derived from registration and session
logs with complete 30-day follow-up; keep immature users out of the denominator.
The existing nested synthetic checkpoint counts cannot substitute for this pipeline.

## Operations-to-DA transition

Position the author as a game-domain practitioner moving into analytics, not a
five-year data analyst. Operations experience provides a starting hypothesis and
knowledge of decisions; the portfolio must demonstrate independent measurement.

Prepare three interview stories using actual, non-confidential work:

1. A log discrepancy: how it was detected, alternative explanations, reconciliation
   with engineering, and what changed. State the real scope and personal contribution.
2. An event decision: the KPI denominator, reference window, confounders, recommendation
   and whether anyone acted on it. Do not substitute synthetic uplift for real impact.
3. A reporting improvement: original process, automation, error controls, and measured
   time saved if available. Label estimates and omit unsupported numbers.

Next portfolio increment: one small user-event model with SQL-derived cohorts,
late-arrival/deduplication tests and a decision-facing dashboard. Prioritize this
over adding more charts or more synthetic event stories. Use a genuinely unseen
public dataset for a separate question to demonstrate analysis beyond generator
assumptions. Keep this project explicitly synthetic and avoid claiming source-system
or production warehouse ownership that has not been demonstrated.
