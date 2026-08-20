"""Generate reproducible synthetic data for a global collectible mobile RPG.

The fictional game is a character-collection, turn-based PvE RPG operated in
KR, JP, and Global West. Every value, event, product, and timeline is invented.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

RANDOM_SEED = 20260815
START_DATE = pd.Timestamp("2024-01-01")
END_DATE = pd.Timestamp("2025-12-31")
REGIONS = ("KR", "JP", "GLOBAL_WEST")
REGION_SCALE = {"KR": 0.85, "JP": 0.70, "GLOBAL_WEST": 1.40}
REGION_PROFILE = {
    "KR": {"decay_days": 860, "season_phase": 0, "acquisition": 0.95,
           "return": 1.08, "outflow": 1.05, "event_response": 1.15,
           "season_amplitude": 0.09,
           "purchase_demand": 1.00, "retention_shift": 0.000},
    "JP": {"decay_days": 1_080, "season_phase": 24, "acquisition": 0.86,
           "return": 0.96, "outflow": 0.90, "event_response": 0.68,
           "season_amplitude": 0.045,
           "purchase_demand": 1.12, "retention_shift": 0.012},
    "GLOBAL_WEST": {"decay_days": 920, "season_phase": 49, "acquisition": 1.20,
                    "return": 0.84, "outflow": 1.12, "event_response": 1.32,
                    "season_amplitude": 0.12,
                    "purchase_demand": 0.90, "retention_shift": -0.010},
}


@dataclass(frozen=True)
class GameEvent:
    event_id: str
    event_name: str
    event_type: str
    start_date: str
    end_date: str
    acquisition_multiplier: float = 1.0
    return_multiplier: float = 1.0
    outflow_multiplier: float = 1.0
    conversion_lift: float = 0.0
    purchase_multiplier: float = 1.0
    availability_multiplier: float = 1.0
    narrative: str = ""
    regions: tuple[str, ...] = REGIONS


EVENTS = [
    GameEvent("EVT001", "Global Launch", "launch", "2024-01-01", "2024-01-21",
              2.80, 1.00, 0.85, 0.004, 1.08, 1.00,
              "Worldwide release with launch missions and starter rewards."),
    GameEvent("EVT002", "Half-Anniversary Raid", "milestone", "2024-06-26", "2024-07-09",
              1.35, 1.55, 0.90, 0.005, 1.10, 1.00,
              "Six-month celebration and limited cooperative PvE boss."),
    GameEvent("EVT016", "KR Summer Check-In", "regional", "2024-07-03", "2024-07-07",
              1.03, 1.08, 0.98, 0.001, 1.01, 1.00,
              "A culturally neutral summer check-in for KR.", ("KR",)),
    GameEvent("EVT017", "JP Star Festival", "regional", "2024-07-03", "2024-07-07",
              1.05, 1.11, 0.97, 0.001, 1.02, 1.00,
              "A localized star-festival mission series for JP.", ("JP",)),
    GameEvent("EVT018", "Global West Summer Celebration", "regional", "2024-07-03", "2024-07-07",
              1.08, 1.12, 0.97, 0.001, 1.03, 1.00,
              "A culturally neutral July summer celebration for Global West.", ("GLOBAL_WEST",)),
    GameEvent("EVT003", "Fantasy Saga Crossover", "collaboration", "2024-09-04", "2024-09-25",
              2.15, 1.95, 0.82, 0.011, 1.20, 1.00,
              "A well-matched fantasy IP collaboration with story and boss content."),
    GameEvent("EVT004", "Regional Autumn Festival", "seasonal", "2024-09-26", "2024-10-09",
              1.10, 1.22, 0.94, 0.002, 1.05, 1.00,
              "Localized Chuseok, harvest, and moon-viewing rewards by region."),
    GameEvent("EVT005", "Christmas Festival 2024", "seasonal", "2024-12-18", "2024-12-31",
              1.24, 1.35, 0.91, 0.005, 1.14, 1.00,
              "Shared holiday story, costumes, and login rewards."),
    GameEvent("EVT019", "New Year Festival 2025", "seasonal", "2025-01-01", "2025-01-07",
              1.18, 1.30, 0.92, 0.003, 1.08, 1.00,
              "Shared New Year login rewards before the anniversary."),
    GameEvent("EVT006", "First Anniversary", "anniversary", "2025-01-08", "2025-01-31",
              2.45, 2.25, 0.78, 0.014, 1.25, 1.00,
              "Anniversary selector rewards, raid, and progression support."),
    GameEvent("EVT007", "Spring Content Gap", "content_gap", "2025-03-20", "2025-04-30",
              0.62, 0.72, 1.27, -0.004, 0.98, 1.00,
              "Long interval without major story or end-game content."),
    GameEvent("EVT008", "PvE Growth Subscription Launch", "bm_launch", "2025-05-15", "2025-06-14",
              1.04, 1.10, 0.98, 0.004, 1.08, 1.00,
              "New subscription adds daily currency and modest PvE progression benefits."),
    GameEvent("EVT009", "Astra Heroes Crossover", "collaboration", "2025-07-09", "2025-07-30",
              1.85, 1.35, 1.06, 0.008, 1.16, 1.00,
              "Well-known but poor-fit collaboration; acquisition rises while retention weakens."),
    GameEvent("EVT010", "Data Center Outage", "incident", "2025-08-12", "2025-08-12",
              0.00, 0.00, 2.80, -0.020, 0.00, 0.00,
              "A power-chain failure makes the service unavailable for the full calendar day."),
    GameEvent("EVT020", "Partial Service Restoration", "incident_response", "2025-08-13", "2025-08-13",
              0.35, 0.30, 2.10, -0.012, 0.55, 0.50,
              "Service returns at noon after 36 total hours offline, with continuing instability."),
    GameEvent("EVT011", "Delayed Initial Response", "incident_response", "2025-08-14", "2025-08-16",
              0.55, 0.62, 1.72, -0.009, 0.72, 0.82,
              "Repeated extensions and delayed communication worsen player sentiment."),
    GameEvent("EVT012", "Extraordinary Compensation", "recovery", "2025-08-17", "2025-08-23",
              1.18, 2.85, 0.84, -0.003, 0.86, 1.00,
              "Apology grants a selector including awakened and previously limited characters."),
    GameEvent("EVT013", "Postmortem and Trust Recovery", "recovery", "2025-08-24", "2025-09-20",
              1.08, 1.42, 0.94, 0.001, 0.97, 1.00,
              "A follow-up notice explains root cause, safeguards, monitoring, and recurrence prevention."),
    GameEvent("EVT014", "Regional Autumn Festival", "seasonal", "2025-10-01", "2025-10-14",
              1.12, 1.28, 0.93, 0.002, 1.05, 1.00,
              "Localized autumn celebration and return missions."),
    GameEvent("EVT015", "Christmas Festival 2025", "seasonal", "2025-12-17", "2025-12-31",
              1.23, 1.33, 0.92, 0.004, 1.12, 1.00,
              "Shared holiday story and seasonal pass."),
]

PRODUCTS = [
    ("P001", "Daily Supply Pack", "daily", 0.99, "2024-01-01", 1),
    ("P002", "Weekly Growth Pack", "weekly", 4.99, "2024-01-01", 7),
    ("P003", "Monthly Mission Pass", "monthly_pass", 14.99, "2024-01-01", 28),
    ("P004", "Seasonal Event Pass", "seasonal_pass", 19.99, "2024-06-26", 21),
    ("P005", "30-Day Premium Currency Pass", "currency_subscription", 7.99, "2024-01-01", 30),
    ("P006", "Equipment Choice Pack", "equipment", 24.99, "2024-01-01", 14),
    ("P007", "Account Growth Booster", "growth_booster", 9.99, "2024-01-01", 14),
    ("P008", "PvE Growth Subscription", "pve_subscription", 12.99, "2025-05-15", 30),
    ("P009", "Limited Event Bundle", "limited", 29.99, "2024-01-01", 21),
    ("P010", "Small Premium Currency Pack", "currency_topup", 4.99, "2024-01-01", 1),
    ("P011", "Standard Premium Currency Pack", "currency_topup", 19.99, "2024-01-01", 1),
    ("P012", "Large Premium Currency Pack", "currency_topup", 79.99, "2024-01-01", 1),
]
PRODUCT_COLUMNS = ["product_id", "product_name", "product_type", "price_usd",
                   "available_from", "purchase_cycle_days"]

BOSS_EVENTS = [
    ("BOSS001", "Celestial Wyrm", "2024-06-26", "2024-07-09"),
    ("BOSS002", "Crossover Demon Lord", "2024-09-04", "2024-09-25"),
    ("BOSS003", "Anniversary Ancient One", "2025-01-08", "2025-01-31"),
    ("BOSS004", "Astra Void Beast", "2025-07-09", "2025-07-30"),
]


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def active_events(date: pd.Timestamp, region: str) -> list[GameEvent]:
    return [e for e in EVENTS if region in e.regions
            and pd.Timestamp(e.start_date) <= date <= pd.Timestamp(e.end_date)]


def effect(events: list[GameEvent], field: str, additive: bool = False) -> float:
    values = [getattr(event, field) for event in events]
    return float(sum(values)) if additive else (float(np.prod(values)) if values else 1.0)


def scaled_event_effect(events: list[GameEvent], field: str, region: str) -> float:
    """Scale event lift/decline around 1.0 to create distinct regional responses."""
    base = effect(events, field)
    sensitivity = REGION_PROFILE[region]["event_response"]
    return max(0.0, 1 + (base - 1) * sensitivity)


def generate_activity_kpis(rng: np.random.Generator) -> pd.DataFrame:
    rows = []
    previous_dau = {r: int(44_000 * REGION_SCALE[r]) for r in REGIONS}
    for date in pd.date_range(START_DATE, END_DATE, freq="D"):
        day_number = (date - START_DATE).days
        for region in REGIONS:
            events = active_events(date, region)
            profile = REGION_PROFILE[region]
            outflow_multiplier = scaled_event_effect(events, "outflow_multiplier", region)
            if date >= pd.Timestamp("2025-07-15"):
                outflow_multiplier *= 1.045  # delayed non-payer resistance to the subscription
            if date >= pd.Timestamp("2025-09-21"):
                outflow_multiplier *= 1.035  # residual trust loss after recovery measures

            decay = np.exp(-day_number / profile["decay_days"])
            seasonality = 1 + profile["season_amplitude"] * np.sin(
                2 * np.pi * (day_number + profile["season_phase"]) / 91
            )
            weekend = 1.06 if date.dayofweek in (4, 5, 6) else 1.0
            nru = max(20, int(rng.normal(
                760 * REGION_SCALE[region] * profile["acquisition"] * decay * seasonality
                * scaled_event_effect(events, "acquisition_multiplier", region), 35
            )))
            returned = max(10, int(rng.normal(
                (210 * REGION_SCALE[region] + previous_dau[region] * 0.0042)
                * profile["return"] * scaled_event_effect(events, "return_multiplier", region)
                * weekend, 24
            )))
            outflow_rate = max(0.004, rng.normal(
                (0.0215 + 0.0000055 * day_number) * profile["outflow"]
                * outflow_multiplier, 0.0013
            ))
            outflow = max(0, int(previous_dau[region] * outflow_rate))
            noise = int(rng.normal(0, 115 * REGION_SCALE[region]))
            availability = effect(events, "availability_multiplier")
            if availability == 0:
                # No activity metric is observable during a full service shutdown.
                nru = returned = outflow = 0
                latent_dau = previous_dau[region]
                dau = 0
            else:
                unconstrained = previous_dau[region] - outflow + nru + returned + noise
                latent_dau = max(1_500, int(unconstrained))
                dau = max(500, int(latent_dau * availability))
            rows.append({
                "date": date, "region": region, "dau": dau, "nru": nru,
                "returned_users": returned, "user_outflow": outflow,
                "event_names": " | ".join(e.event_name for e in events) or "No Event",
                "event_types": " | ".join(e.event_type for e in events) or "baseline",
                "service_availability": availability,
            })
            previous_dau[region] = latent_dau
    return pd.DataFrame(rows)


def product_frame() -> pd.DataFrame:
    return pd.DataFrame(PRODUCTS, columns=PRODUCT_COLUMNS)


def generate_product_sales(rng: np.random.Generator, activity: pd.DataFrame
                           ) -> tuple[pd.DataFrame, pd.DataFrame]:
    weights = {"daily": .24, "weekly": .12, "monthly_pass": .12, "seasonal_pass": .09,
               "currency_subscription": .14, "equipment": .07, "growth_booster": .09,
               "pve_subscription": .08, "limited": .13, "currency_topup": .05}
    currency_weights = {"P010": .070, "P011": .045, "P012": .018}
    sales_rows = []
    enriched = activity.copy()
    enriched["pu"], enriched["revenue"] = 0, 0.0

    for idx, row in enriched.iterrows():
        date, region = row["date"], row["region"]
        events = active_events(date, region)
        base_conversion = 0.031 - 0.000004 * (date - START_DATE).days
        if date >= pd.Timestamp("2025-05-15"):
            base_conversion += 0.0025
        if date >= pd.Timestamp("2025-09-21"):
            base_conversion -= 0.0012
        conversion = np.clip(
            base_conversion + effect(events, "conversion_lift", True)
            + rng.normal(0, .0008), .006, .075
        )
        unique_payers = 0 if row["dau"] == 0 else max(1, int(row["dau"] * conversion))
        event_types = {e.event_type for e in events}
        revenue = 0.0
        for product in product_frame().to_dict("records"):
            if date < pd.Timestamp(product["available_from"]):
                continue
            ptype, active_factor = product["product_type"], 1.0
            if ptype in {"seasonal_pass", "limited"} and not event_types.intersection(
                    {"milestone", "collaboration", "anniversary", "seasonal"}):
                active_factor = 0.0
            if ptype == "pve_subscription" and date >= pd.Timestamp("2025-07-15"):
                active_factor *= .78
            if date >= pd.Timestamp("2025-05-15"):
                # The new subscription partially cannibalizes adjacent recurring offers.
                active_factor *= {
                    "monthly_pass": .90,
                    "currency_subscription": .88,
                    "growth_booster": .82,
                }.get(ptype, 1.0)
            if ptype in {"equipment", "growth_booster", "pve_subscription"} and event_types.intersection(
                    {"milestone", "collaboration", "anniversary"}):
                active_factor *= 1.28
            if event_types.intersection({"incident", "incident_response"}):
                active_factor *= .32
            if "recovery" in event_types:
                active_factor *= .78
            active_factor *= REGION_PROFILE[region]["purchase_demand"]
            active_factor *= scaled_event_effect(events, "purchase_multiplier", region)
            product_weight = currency_weights.get(product["product_id"], weights[ptype])
            purchasers = 0 if unique_payers == 0 or active_factor == 0 else max(0, int(rng.normal(
                unique_payers * product_weight * active_factor,
                max(2, unique_payers * .012)
            )))
            units = max(purchasers, int(rng.normal(
                purchasers * 1.08, max(1, purchasers * .03)
            ))) if purchasers else 0
            gross = round(units * product["price_usd"], 2)
            revenue += gross
            sales_rows.append({
                "date": date, "region": region, "product_id": product["product_id"],
                "purchasers": purchasers, "units_sold": units,
                "gross_revenue_usd": gross,
            })
        enriched.at[idx, "pu"] = unique_payers
        enriched.at[idx, "revenue"] = round(revenue, 2)
    return enriched, pd.DataFrame(sales_rows)


def generate_retention_cohorts(rng: np.random.Generator, daily: pd.DataFrame) -> pd.DataFrame:
    source = daily.assign(cohort_month=daily["date"].dt.to_period("M").dt.to_timestamp())
    monthly = source.groupby(["cohort_month", "region"], as_index=False)["nru"].sum()
    monthly = monthly[monthly["cohort_month"] <= pd.Timestamp("2025-11-01")]
    rows = []
    for _, row in monthly.iterrows():
        month, region, size = pd.Timestamp(row["cohort_month"]), row["region"], int(row["nru"])
        shift = REGION_PROFILE[region]["retention_shift"]
        d1, d7, d30 = .36 + shift, .18 + shift * .65, .085 + shift * .45
        if month in {pd.Timestamp("2024-06-01"), pd.Timestamp("2024-09-01"), pd.Timestamp("2025-01-01")}:
            d1, d7, d30 = d1 + .055, d7 + .048, d30 + .032
        if month in {pd.Timestamp("2025-03-01"), pd.Timestamp("2025-04-01")}:
            d1, d7, d30 = d1 - .040, d7 - .045, d30 - .032
        if month == pd.Timestamp("2025-07-01"):
            d1, d7, d30 = d1 + .015, d7 - .018, d30 - .025
        if month == pd.Timestamp("2025-08-01"):
            d1, d7, d30 = d1 - .055, d7 - .060, d30 - .045
        if month >= pd.Timestamp("2025-09-01"):
            d30 -= .010
        if month >= pd.Timestamp("2025-05-01"):
            d1 += .012
        d1 = float(np.clip(rng.normal(d1, .007), .05, .80))
        d7 = float(np.clip(rng.normal(d7, .006), .02, d1))
        d30 = float(np.clip(rng.normal(d30, .004), .01, d7))
        c1, c7, c30 = int(round(size*d1)), int(round(size*d7)), int(round(size*d30))
        rows.append({"cohort_month": month, "region": region, "cohort_size": size,
                     "d1_retained": c1, "d7_retained": min(c1, c7),
                     "d30_retained": min(c1, c7, c30)})
    return pd.DataFrame(rows)


def generate_boss_metrics(rng: np.random.Generator, daily: pd.DataFrame) -> pd.DataFrame:
    rows = []
    settings = {"NORMAL": (.22, .78), "HARD": (.11, .47), "NIGHTMARE": (.045, .19)}
    for boss_id, boss_name, start, end in BOSS_EVENTS:
        for _, day in daily[daily["date"].between(start, end)].iterrows():
            poor_fit = .82 if boss_id == "BOSS004" else 1.0
            for difficulty, (share, clear_probability) in settings.items():
                participants = max(1, int(rng.normal(day["dau"]*share*poor_fit, day["dau"]*.004)))
                attempts = max(participants, int(rng.normal(
                    participants*(1.35 if difficulty == "NORMAL" else 1.75), participants*.04
                )))
                clears = min(participants, max(0, int(rng.normal(
                    participants*clear_probability, participants*.025
                ))))
                rows.append({"date": day["date"], "region": day["region"],
                             "boss_id": boss_id, "boss_name": boss_name,
                             "difficulty": difficulty, "participants": participants,
                             "attempts": attempts, "clears": clears})
    return pd.DataFrame(rows)


def events_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {"event_id": e.event_id, "event_name": e.event_name, "event_type": e.event_type,
         "region": region, "start_date": e.start_date, "end_date": e.end_date,
         "narrative": e.narrative}
        for e in EVENTS for region in e.regions
    ])


def validate_generated_data(daily: pd.DataFrame, retention: pd.DataFrame,
                            events: pd.DataFrame, products: pd.DataFrame,
                            sales: pd.DataFrame, bosses: pd.DataFrame) -> None:
    if daily[["date", "region"]].duplicated().any():
        raise ValueError("daily_kpis contains duplicate date-region keys")
    numeric = ["dau", "nru", "returned_users", "user_outflow", "pu", "revenue"]
    if daily[numeric].isna().any().any() or (daily[numeric] < 0).any().any():
        raise ValueError("daily_kpis contains null or negative KPI values")
    if (daily["pu"] > daily["dau"]).any():
        raise ValueError("pu cannot exceed dau")
    if retention[["cohort_month", "region"]].duplicated().any():
        raise ValueError("retention contains duplicate cohort-region keys")
    valid_retention = ((retention["d30_retained"] <= retention["d7_retained"])
                       & (retention["d7_retained"] <= retention["d1_retained"])
                       & (retention["d1_retained"] <= retention["cohort_size"]))
    if not valid_retention.all():
        raise ValueError("retention hierarchy is invalid")
    if events.empty or products["product_id"].duplicated().any():
        raise ValueError("event or product dimension is invalid")
    if sales[["date", "region", "product_id"]].duplicated().any():
        raise ValueError("sales contains duplicate grain keys")
    if bosses[["date", "region", "boss_id", "difficulty"]].duplicated().any():
        raise ValueError("boss metrics contains duplicate grain keys")
    if (bosses["clears"] > bosses["participants"]).any():
        raise ValueError("boss clears cannot exceed participants")


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    activity = generate_activity_kpis(rng)
    daily, sales = generate_product_sales(rng, activity)
    retention = generate_retention_cohorts(rng, daily)
    events, products = events_frame(), product_frame()
    bosses = generate_boss_metrics(rng, daily)
    validate_generated_data(daily, retention, events, products, sales, bosses)
    output_dir = project_root() / "data" / "synthetic"
    output_dir.mkdir(parents=True, exist_ok=True)
    datasets = {
        "daily_kpis.csv": daily, "retention_cohorts.csv": retention,
        "events.csv": events, "products.csv": products,
        "daily_product_sales.csv": sales, "boss_event_metrics.csv": bosses,
    }
    for filename, frame in datasets.items():
        frame.to_csv(output_dir / filename, index=False)
        print(f"Generated {len(frame):,} rows: {filename}")


if __name__ == "__main__":
    main()
