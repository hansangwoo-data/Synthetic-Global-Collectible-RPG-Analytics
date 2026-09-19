# Scenario and Synthetic Data Design

## Purpose

This document explains how the fictional service, events, products and data relationships were designed.

The project is informed by live-service game operations experience, but all published data is synthetic and generated from public code. No employer data, proprietary schema or real service data is used.

## Design process

1. Define a fictional product and two-year service narrative.
2. Define table grains and KPI relationships.
3. Add regional seasonality, lifecycle changes and major service events.
4. Generate compatible product, retention and boss metrics.
5. Reconcile product revenue with daily service revenue.
6. Validate key constraints and event windows.
7. Analyze the resulting scenario.

A fixed random seed makes the generated data reproducible.

## Fictional product

- Genre: character-collection, turn-based mobile PvE RPG
- Regions: KR, JP and GLOBAL_WEST
- Core content: story stages, unit growth, limited PvE bosses and event combat
- Service model: one global service with regional differences
- Currency: synthetic USD

The product catalog includes packs, passes, growth products, event bundles, a PvE subscription and currency top-ups.

The project focuses on service-level behavior. Individual gacha pulls, purchase sequences and combat logs are not generated.

## Two-year service narrative

| Act | Period | Analytical purpose |
|---|---|---|
| Launch and growth | Jan–Dec 2024 | Launch normalization, milestone events and collaboration performance |
| Event dependence and monetization pressure | Jan–Jul 2025 | Anniversary peak, content gap and subscription launch |
| Crisis and recovery | Aug–Dec 2025 | Outage, compensation and post-incident recovery |

## Event timeline

[기존 표 유지]

The outage and recovery sequence are fictional and were designed to separate technical recovery, user return and commercial recovery.

## Regional design

The three regions follow the same overall service narrative but have different synthetic response patterns.

- KR reacts more strongly to content cadence.
- JP has steadier retention and stronger recurring-product behavior.
- Global West has higher acquisition volatility and weaker baseline retention.

These are scenario design choices, not claims about real regional markets.

## Key modeling constraints

- One daily KPI row exists for each date × region.
- Full outage days have zero observable activity and revenue.
- `D30 ≤ D7 ≤ D1 ≤ cohort size` for the main synthetic retention indicator.
- Daily service PU stays within valid product-purchaser limits.
- Boss metrics follow `clears ≤ participants ≤ attempts`.
- Product revenue follows `units sold × price`.
- Seasonal and limited products sell only during valid event windows.
- D30 is published only for mature cohorts.

See the [Data Dictionary](data_dictionary.md) for field definitions and the [Analysis Specification](analysis_spec.md) for analysis thresholds.

## Data limits

The main scenario supports service-level lifecycle, cohort, product, regional, incident and boss analysis.

It does not contain individual purchase histories, combat paths, exposure logs or sentiment data, so player-level causes cannot be confirmed.

## Supplemental login example

A separate generator creates 360 synthetic users and login events for exact-day D7/D30 analysis. This population is independent of the main scenario and is used only to demonstrate user-level retention logic.

See the [metric contract](user_retention.md) for details.
