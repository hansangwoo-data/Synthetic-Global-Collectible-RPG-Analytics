# Proposed next steps

## Where I would start

Before recommending more acquisition spend, I would collect the missing user-level
logs and test changes to boss-entry communication and offer benefits. These proposals
follow from the synthetic analysis; they have not been tested in a live service.

| Priority | What I found | What I would check | Next step | 
|---|---|---|---|
| 1 | Astra normal boss participation index was 82.2, while users who entered showed similar outcomes | Whether eligible users saw the boss, understood the entry conditions, and found the rewards appealing | Test clearer entry and reward information before changing difficulty | 
| 2 | Revenue increased after the subscription launch, while adjacent-offer revenue per paying user declined | User-level purchases, subscription ownership, renewals and refunds | Test whether clearer differences between offers reduce spending shifts | 
| 3 | User activity recovered faster than revenue after the incident | Which users were affected, whether they returned, and whether payment activity recovered | Track technical recovery, user activity and revenue separately |

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
The new [user-level SQL example](user_retention.md) implements the registration/login portion of the telemetry proposal. Eligibility, assignment, payments, exposure and CS data remain future requirements. [Operations evidence prompts](operations_to_da.md) distinguish portfolio work from unverified employment examples.
