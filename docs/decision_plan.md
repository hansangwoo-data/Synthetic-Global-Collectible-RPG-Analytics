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

- Question: Does clearer reward and entry information increase first boss attempts among eligible users?
- Users: Eligible users for the next comparable boss.
- Test: Split users into two groups. One sees clearer entry/reward information, the other sees the current version.
- Main metric: Share of eligible users who make a first boss attempt within seven days.
- Supporting checks: D7 activity, crash/error rate, revenue per user, and support contacts.
- Duration: Run for at least two weekly cycles and complete seven days of follow-up for each user.
- Decision: Continue only if participation improves without meaningful negative changes in the supporting checks.

No experiment was run in this repository. This is a design proposal.

## Required data

| Event | Key fields | What to check |
|---|---|---|
| registration | user_id, registered_at, channel, region | duplicates, missing region |
| session | event_id, user_id, occurred_at | duplicate events, incorrect timestamps |
| boss eligibility | user_id, boss_id, eligibility | missing eligibility or assignment |
| boss action | event_id, user_id, boss_id, action | duplicate attempts, invalid sequence |
| transaction | transaction_id, user_id, product_id, amount, refund | duplicate charges, refund mismatch |
| experiment assignment | experiment_id, user_id, variant | reassignment or uneven split |

Use a consistent UTC date boundary and unique event IDs. Exact-day D30 should be calculated only for users with a full 30 days of observation. 
The current synthetic retention indicator is not a replacement for user-level production logs. The [user-level SQL example](user_retention.md) covers registration and login data; eligibility, payments, exposure, and CS data would still be needed for a real service.
