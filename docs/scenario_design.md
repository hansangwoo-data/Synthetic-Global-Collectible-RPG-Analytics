# Scenario and Synthetic Data Design

## Purpose

This document explains how the fictional service, events, products, and data
relationships were designed. It separates professional domain judgment from
production data and makes the authored assumptions reviewable.

## Data Provenance and Security Boundary

This project is **domain-informed, not production-data-derived**.

The analytical questions and operational trade-offs reflect the author's
experience with live-service game operations. Examples include separating
traffic from retention quality, checking whether event traffic reaches core
content, evaluating product cannibalization, and distinguishing activity
recovery from trust recovery.

The published data does not originate from an employer or live game:

- no production rows or aggregates were copied;
- no proprietary schema was reproduced;
- no real title, company, event, product, or incident is represented;
- no transformed or anonymized company dataset was used;
- no production metric was used to calibrate a synthetic distribution; and
- all records can be regenerated deterministically from the public source code.

The numerical effects are authored scenario assumptions. They demonstrate how
the analysis handles a coherent business narrative; they are not estimates of
typical mobile-game performance.

## Design Process

The dataset was constructed from business questions rather than by generating
independent random columns.

1. Define a fictional product and two-year operational narrative.
2. Define each table's grain and the relationships between KPIs.
3. Encode regional seasonality, lifecycle decay, and explicit interventions.
4. Generate product, retention, and boss funnels from compatible constraints.
5. Reconcile product-level revenue to daily service revenue.
6. Test invariants, event availability, mature cohort coverage, and incident
   behavior.
7. Analyze the resulting scenario under pre-declared decision rules.

Random variation uses a fixed seed, so the same source produces the same public
tables and results on every run.

## Fictional Product

- Genre: character-collection, turn-based mobile PvE RPG
- Regions: `KR`, `JP`, and `GLOBAL_WEST`
- Core content: story stages, unit growth, limited PvE bosses, and event combat
- Service model: one global service with regional behavioral differences
- Currency: one synthetic USD list price without regional price variation

The product catalog includes daily and weekly packs, monthly and seasonal
passes, a login-based premium-currency pass, equipment and growth products,
limited event bundles, a PvE growth subscription, and standard currency
top-ups.

The premium-currency pass distributes value across 30 days and requires login
to claim it. The PvE subscription launches before the incident so the product
change can be evaluated separately from incident-driven behavior.

Direct sales of complete limited characters and gacha pull logs are excluded.
This keeps the project focused on service-level behavior and avoids implying a
player-level monetization analysis that the public tables cannot support.

## Two-Year Service Narrative

| Act | Period | Analytical purpose |
|---|---|---|
| Launch and growth | Jan–Dec 2024 | Observe launch normalization, milestone recovery, regional content, and a genre-fit collaboration. |
| Event dependence and monetization pressure | Jan–Jul 2025 | Contrast an anniversary peak with a content gap, a new subscription product, and a well-known but weak-fit collaboration. |
| Crisis and incomplete recovery | Aug–Dec 2025 | Separate outage impact, delayed response, compensation, operational remediation, and incomplete behavioral recovery. |

## Event Timeline

| Period | Fictional event | Intended analytical role |
|---|---|---|
| Jan 2024 | Global Launch | High acquisition and onboarding |
| Jun–Jul 2024 | Half-Anniversary Raid | Milestone event and limited PvE boss |
| Jul 2024 | Regional Summer Events | KR check-in, JP star festival, and Global West summer event |
| Sep 2024 | Fantasy Saga Crossover | Genre-fit collaboration |
| Sep–Oct 2024 | Regional Autumn Festival | Seasonal follow-up that overlaps the crossover's post-window |
| Dec 2024 | Christmas Festival | Shared seasonal event |
| Jan 2025 | New Year Festival | Login rewards before the anniversary |
| Jan 2025 | First Anniversary | Highest-value milestone event |
| Mar–Apr 2025 | Spring Content Gap | Acquisition and retention deterioration |
| May–Jun 2025 | PvE Growth Subscription | Revenue lift with possible adjacent-product cannibalization |
| Jul 2025 | Astra Heroes Crossover | Strong awareness with weaker audience fit |
| Aug 12, 2025 | Data Center Outage | Full-day unavailability and zero observed activity |
| Aug 13, 2025 | Partial Service Restoration | Noon restoration after 36 hours offline |
| Aug 2025 | Delayed Initial Response | Repeated extensions and delayed communication |
| Aug 2025 | Extraordinary Compensation | Awakened/limited-character selector |
| Aug–Sep 2025 | Postmortem and Trust Recovery | Root cause, safeguards, and recurrence-prevention plan |
| Oct 2025 | Regional Autumn Festival | Localized return campaign |
| Dec 2025 | Christmas Festival | Seasonal pass and event story |

The outage and all recovery actions are fictional. The sequence deliberately
separates technical availability, communication quality, compensation, and
later remediation so they are not compressed into one undifferentiated event.

## Regional Design

The three regional curves are related but not mechanically scaled copies.

- KR reacts more strongly to content cadence.
- JP has steadier retention and stronger recurring-product behavior.
- Global West has greater acquisition volatility and weaker baseline
  retention.

These are scenario characteristics, not claims about real regional markets.
They exist to make regional comparison analytically meaningful.
`GLOBAL_WEST` is a fictional aggregate label rather than a claim that real
English-speaking Western markets behave as one uniform region.

## Key Modeling Constraints

- Daily activity has one complete row per date and region.
- A full outage produces zero DAU, acquisition, return, outflow, payer, and
  revenue observations for that day.
- Missed activity loss during an outage is reflected through post-restoration
  non-return rather than impossible churn events while the server is offline.
- Observed DAU is separated from latent addressable population so one outage
  does not mechanically delete all future players.
- Retention follows `D30 ≤ D7 ≤ D1 ≤ cohort size`.
- Boss funnels follow `clears ≤ participants ≤ attempts`.
- Product revenue follows `units sold × global list price` and reconciles to
  daily revenue.
- Seasonal and limited products sell only during eligible event windows.
- D30 is published only for cohorts mature by the dataset end date.

Field-level definitions are available in the
[Data Dictionary](data_dictionary.md). Evaluation thresholds and attribution
rules are available in the [Analysis Specification](analysis_spec.md).

## What the Data Can and Cannot Support

The tables support service-level lifecycle, cohort, product, regional, incident,
and boss-funnel analysis. They do not support claims about an individual
player's power, unit ownership, purchase sequence, gacha outcomes, sentiment,
or combat decisions.

For example, low boss participation can be observed. A perceived paywall may be
proposed as a hypothesis, but it cannot be established without player-level
power, ownership, purchase, and exposure data.
