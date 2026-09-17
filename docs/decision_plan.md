# Proposed next steps

## Where I would start

Before recommending more acquisition spend, I would collect the missing user-level
logs and test changes to boss-entry communication and offer benefits. These proposals
follow from the synthetic analysis; they have not been tested in a live service.

| Priority | Decision owner (proposed) | What is observed | Competing explanations | Evidence needed | Next decision |
|---|---|---|---|---|---|
| 1 | Product analyst + content PM | Astra NORMAL participation index 82.2; entrant outcomes comparable | Eligibility, exposure, reward appeal, audience mix, power selection | exposure, eligibility with reason, boss page, first attempt, clear; join by user and event | Choose an entry intervention only after locating the loss among eligible users |
| 2 | Monetization PM + analyst | Adjacent revenue per payer-day declines in all regions | Buyer migration, new payer composition, renewal timing, assumed payer overlap | User-level transactions, entitlements, renewal, refunds and assignment | Test benefit differentiation before removing or repricing offers |
| 3 | Incident owner + analyst | Activity indices return toward baseline before commerce; later new-cohort D30 checkpoint proxy remains below reference | Acquisition mix, seasonal context, incident exposure, communication | Affected users, time of failed login, communication exposure, claim, session, purchase | Close operational response separately from cohort quality follow-up |

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

The user-event SQL cohort and late-arrival/deduplication checks are now implemented. A next independent project should use an unseen
public dataset for a separate question to demonstrate analysis beyond generator
assumptions. Keep this project explicitly synthetic and avoid claiming source-system
or production warehouse ownership that has not been demonstrated.

## Decision rules: proposed pilots, not observed impact

All numeric thresholds below are **illustrative design choices**, not estimated optimal thresholds or approved launch criteria. Owners must approve them using a real baseline, practical loss tolerance and sample-size calculation before assignment. The synthetic data cannot size these experiments. Each row distinguishes descriptive evidence from a testable hypothesis.

| Affected segment / evidence | Hypothesis and reversible action | Primary success KPI / proposed continue criterion | Guardrails / stop criterion | Iterate when |
|---|---|---|---|---|
| Acquisition/event planning: anniversary DAU remains above its local reference | A lower-cost event cadence could preserve activity; test cadence on comparable markets only if interference can be controlled | Incremental net contribution per assigned user: lower 95% CI > 0 after a complete event and 14-day follow-up | Stop for confirmed critical payment/service incident; do not continue unless D7 difference lower CI > −1 pp and support-contact increase upper CI < 0.5 pp | Calendar confounding or few independent markets makes identification weak; collect more seasons rather than claim event ROI |
| New users in a future comparable collaboration: Astra monthly checkpoint proxy is lower despite larger acquisition | Onboarding/expectation mismatch; randomize a clearer progression path within channel and region | Session-based exact-day D7 ITT difference: estimate ≥ +2 pp and lower 95% CI > 0; require mature D30 follow-up before broad rollout | D30 lower CI > −1 pp; net revenue per assigned user relative change lower CI > −5%; stop confirmed critical defects immediately | Confidence intervals overlap practical gain/loss; review channel mix and missing logs, then redesign rather than extend indefinitely |
| Boss-eligible users: aggregate Astra entry index 82.17, entrant outcomes comparable | Clarify unlocks/rewards; test entry communication, not difficulty reduction by default | Seven-day first-attempt / all assigned eligible users: estimate ≥ +3 pp and lower 95% CI > 0 | D7 lower CI > −1 pp; crash-user rate increase upper CI < 0.2 pp; support-contact increase upper CI < 0.5 pp | Entry improves but clear yield does not; investigate selection and accessibility |
| Eligible offer audience, all regions: adjacent revenue per payer-day falls | Benefit differentiation may reduce substitution; randomize presentation while preserving entitlements | 30-day net total revenue per assigned user: estimate ≥ +3% and lower 95% CI > 0; include refunds | Refund-user rate increase upper CI < 0.5 pp; D30 lower CI > −1 pp; stop billing/entitlement errors immediately | Adjacent mix changes but total net value is uncertain; do not call it incremental revenue |
| Outage-exposed users: returned-user index and revenue index differ | Post-restoration guidance may help affected users; test optional guidance after universal required remediation | Among all assigned affected users, 14-day successful-return share: estimate ≥ +2 pp and lower 95% CI > 0 | Failed-login rate must return to service SLO; support-contact increase upper CI < 0.5 pp; no withholding necessary compensation | Contacts fall but payment failures persist: escalate engineering instead of closing on activity alone |
| Regional planning: offer warnings shared, severity rank assumption-sensitive | Common diagnosis with regional stratification before localized rollout | Use the relevant pilot's pooled primary KPI; regional harm bounds must satisfy its guardrails | No region-specific rollout based only on rank; no unplanned subgroup winner selection | Regional intervals are wide or reverse across assumptions; collect exposure and acquisition-mix evidence |

Use fixed-horizon analysis with adequate sample size, at least two weekly cycles and each user's complete follow-up. Do not stop early for a positive efficacy estimate. Safety incidents can stop immediately; statistical guardrail failures are evaluated at the planned analysis unless an approved sequential safety plan exists. Continue means advance to a controlled rollout, not universal deployment. Stop for a failed guardrail or a CI whose upper bound excludes the minimum worthwhile effect; iterate for inconclusive evidence. Prespecify one primary metric, handling of multiple secondary/region comparisons and an analysis date. Zero/invalid revenue baselines require an absolute margin before launch, not a post-hoc relative metric.

The new [user-level SQL example](user_retention.md) implements the registration/login portion of the telemetry proposal. Eligibility, assignment, payments, exposure and CS data remain future requirements. [Operations evidence prompts](operations_to_da.md) distinguish portfolio work from unverified employment examples.
