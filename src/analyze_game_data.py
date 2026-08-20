"""Validate and analyze the public synthetic collectible-RPG dataset."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return pd.to_numeric(numerator, errors="coerce").div(
        pd.to_numeric(denominator, errors="coerce").replace(0, np.nan)
    )


def load_data(root: Path) -> tuple[pd.DataFrame, ...]:
    directory = root / "data" / "synthetic"
    daily = pd.read_csv(directory / "daily_kpis.csv", parse_dates=["date"])
    retention = pd.read_csv(directory / "retention_cohorts.csv", parse_dates=["cohort_month"])
    events = pd.read_csv(directory / "events.csv", parse_dates=["start_date", "end_date"])
    products = pd.read_csv(directory / "products.csv", parse_dates=["available_from"])
    sales = pd.read_csv(directory / "daily_product_sales.csv", parse_dates=["date"])
    bosses = pd.read_csv(directory / "boss_event_metrics.csv", parse_dates=["date"])
    return daily, retention, events, products, sales, bosses


def validate_data(daily: pd.DataFrame, retention: pd.DataFrame, events: pd.DataFrame,
                  products: pd.DataFrame, sales: pd.DataFrame,
                  bosses: pd.DataFrame) -> pd.DataFrame:
    datasets = {
        "daily_kpis": (daily, ["date", "region"]),
        "retention_cohorts": (retention, ["cohort_month", "region"]),
        "events": (events, ["event_id", "region"]),
        "products": (products, ["product_id"]),
        "daily_product_sales": (sales, ["date", "region", "product_id"]),
        "boss_event_metrics": (bosses, ["date", "region", "boss_id", "difficulty"]),
    }
    required_daily = {"date", "region", "dau", "nru", "returned_users",
                      "user_outflow", "pu", "revenue", "service_availability"}
    if missing := required_daily.difference(daily.columns):
        raise ValueError(f"daily_kpis missing fields: {sorted(missing)}")

    report_rows = []
    for name, (frame, grain) in datasets.items():
        if frame.empty:
            raise ValueError(f"{name} is empty")
        report_rows.append({
            "dataset": name, "rows": len(frame),
            "duplicate_grain_keys": int(frame.duplicated(grain).sum()),
            "null_cells": int(frame.isna().sum().sum()),
        })
    report = pd.DataFrame(report_rows)
    if report["duplicate_grain_keys"].sum() or report["null_cells"].sum():
        raise ValueError("duplicate keys or null cells detected")

    expected = pd.MultiIndex.from_product(
        [pd.date_range(daily["date"].min(), daily["date"].max()), sorted(daily["region"].unique())],
        names=["date", "region"],
    )
    actual = pd.MultiIndex.from_frame(daily[["date", "region"]])
    if len(expected.difference(actual)):
        raise ValueError("daily_kpis has missing date-region rows")
    numeric = ["dau", "nru", "returned_users", "user_outflow", "pu", "revenue"]
    if (daily[numeric] < 0).any().any() or (daily["pu"] > daily["dau"]).any():
        raise ValueError("daily KPI business constraints failed")
    if not daily["service_availability"].between(0, 1).all():
        raise ValueError("service availability must be between zero and one")
    full_outage = daily["service_availability"].eq(0)
    outage_metrics = ["dau", "nru", "returned_users", "user_outflow", "pu", "revenue"]
    if not (daily.loc[full_outage, outage_metrics] == 0).all().all():
        raise ValueError("activity and commerce must be zero during full outage")
    valid_retention = ((retention["d30_retained"] <= retention["d7_retained"])
                       & (retention["d7_retained"] <= retention["d1_retained"])
                       & (retention["d1_retained"] <= retention["cohort_size"]))
    if not valid_retention.all():
        raise ValueError("retention hierarchy failed")
    if (bosses["clears"] > bosses["participants"]).any() or (
            bosses["participants"] > bosses["attempts"]).any():
        raise ValueError("boss funnel constraints failed")

    sales_with_price = sales.merge(
        products[["product_id", "price_usd", "product_type"]],
        on="product_id", validate="many_to_one"
    )
    expected_revenue = sales_with_price["units_sold"] * sales_with_price["price_usd"]
    if not np.allclose(sales_with_price["gross_revenue_usd"], expected_revenue, atol=.01):
        raise ValueError("sales revenue does not equal units sold times list price")
    limited_types = {"seasonal_pass", "limited"}
    invalid_limited_sales = sales_with_price[
        sales_with_price["product_type"].isin(limited_types)
        & sales_with_price["gross_revenue_usd"].gt(0)
    ].merge(daily[["date", "region", "event_types"]], on=["date", "region"])
    eligible = invalid_limited_sales["event_types"].str.contains(
        "milestone|collaboration|anniversary|seasonal", regex=True
    )
    if not eligible.all():
        raise ValueError("seasonal or limited products sold outside eligible events")
    if retention["cohort_month"].max() > pd.Timestamp("2025-11-01"):
        raise ValueError("immature December D30 cohort must not be published")

    sales_total = sales.groupby(["date", "region"])["gross_revenue_usd"].sum()
    daily_total = daily.set_index(["date", "region"])["revenue"]
    if not np.allclose(sales_total.sort_index(), daily_total.sort_index(), atol=.01):
        raise ValueError("daily revenue does not reconcile with product sales")
    return report


def prepare_metrics(daily: pd.DataFrame, retention: pd.DataFrame,
                    bosses: pd.DataFrame) -> tuple[pd.DataFrame, ...]:
    daily = daily.sort_values(["region", "date"]).copy()
    daily["conversion_rate"] = safe_divide(daily["pu"], daily["dau"])
    daily["arpu"] = safe_divide(daily["revenue"], daily["dau"])
    daily["arppu"] = safe_divide(daily["revenue"], daily["pu"])
    previous_dau = daily.groupby("region")["dau"].transform(
        lambda values: values.replace(0, np.nan).ffill().shift(1)
    )
    daily["outflow_rate"] = safe_divide(daily["user_outflow"], previous_dau)
    daily["net_flow"] = daily["nru"] + daily["returned_users"] - daily["user_outflow"]
    for column in ["dau", "nru", "returned_users", "user_outflow", "pu",
                   "revenue", "conversion_rate", "arppu", "net_flow"]:
        daily[f"{column}_7d"] = (
            daily.groupby("region")[column]
            .transform(lambda values: values.rolling(7, min_periods=1).mean())
        )

    retention = retention.sort_values(["region", "cohort_month"]).copy()
    for day in (1, 7, 30):
        retention[f"d{day}_retention"] = safe_divide(
            retention[f"d{day}_retained"], retention["cohort_size"]
        )
    bosses = bosses.merge(
        daily[["date", "region", "dau"]], on=["date", "region"],
        how="left", validate="many_to_one"
    )
    bosses["participation_rate"] = safe_divide(bosses["participants"], bosses["dau"])
    bosses["clear_rate"] = safe_divide(bosses["clears"], bosses["participants"])
    bosses["attempts_per_participant"] = safe_divide(
        bosses["attempts"], bosses["participants"]
    )
    return daily, retention, bosses


def validate_derived_data(daily: pd.DataFrame, retention: pd.DataFrame,
                          events: pd.DataFrame, bosses: pd.DataFrame) -> pd.DataFrame:
    expected_daily = pd.DataFrame(False, index=daily.index, columns=daily.columns)
    for column in ["conversion_rate", "arpu"]:
        expected_daily.loc[daily["dau"].eq(0), column] = True
    expected_daily.loc[daily["pu"].eq(0), "arppu"] = True
    first_rows = daily.groupby("region", sort=False).head(1).index
    expected_daily.loc[first_rows, "outflow_rate"] = True
    daily_nulls = daily.isna()
    unexpected_daily = int((daily_nulls & ~expected_daily).sum().sum())
    expected_count = int((daily_nulls & expected_daily).sum().sum())

    expected_events = pd.DataFrame(False, index=events.index, columns=events.columns)
    if "dau_during" in events:
        zero_dau = events["dau_during"].eq(0)
        for column in ["conversion_rate_during", "conversion_rate_change_pct"]:
            expected_events.loc[zero_dau, column] = True
    if "pu_during" in events:
        zero_pu = events["pu_during"].eq(0)
        for column in ["arppu_during", "arppu_change_pct"]:
            expected_events.loc[zero_pu, column] = True
    event_nulls = events.isna()
    unexpected_events = int((event_nulls & ~expected_events).sum().sum())
    expected_event_count = int((event_nulls & expected_events).sum().sum())

    report = pd.DataFrame([
        {"dataset": "daily_metrics_enriched", "expected_undefined": expected_count,
         "unexpected_nulls": unexpected_daily},
        {"dataset": "retention_metrics", "expected_undefined": 0,
         "unexpected_nulls": int(retention.isna().sum().sum())},
        {"dataset": "boss_metrics_enriched", "expected_undefined": 0,
         "unexpected_nulls": int(bosses.isna().sum().sum())},
        {"dataset": "event_window_summary", "expected_undefined": expected_event_count,
         "unexpected_nulls": unexpected_events},
    ])
    if report["unexpected_nulls"].sum():
        raise ValueError("unexpected nulls detected in derived datasets")
    return report


def event_window_summary(daily: pd.DataFrame, events: pd.DataFrame,
                         window_days: int = 14) -> pd.DataFrame:
    unique_events = events.drop_duplicates("event_id")
    metrics = ["dau", "nru", "returned_users", "outflow_rate",
               "pu", "revenue", "conversion_rate", "arppu"]
    rows = []
    for _, event in unique_events.iterrows():
        start, end = pd.Timestamp(event["start_date"]), pd.Timestamp(event["end_date"])
        applicable_regions = events.loc[
            events["event_id"].eq(event["event_id"]), "region"
        ].tolist()
        scope = daily[daily["region"].isin(applicable_regions)]
        aggregate = (scope.groupby("date", as_index=False)
                     .agg(dau=("dau", "sum"), nru=("nru", "sum"),
                          returned_users=("returned_users", "sum"),
                          user_outflow=("user_outflow", "sum"), pu=("pu", "sum"),
                          revenue=("revenue", "sum")))
        aggregate["conversion_rate"] = safe_divide(aggregate["pu"], aggregate["dau"])
        aggregate["arppu"] = safe_divide(aggregate["revenue"], aggregate["pu"])
        prior_active = aggregate["dau"].replace(0, np.nan).ffill().shift(1)
        aggregate["outflow_rate"] = safe_divide(aggregate["user_outflow"], prior_active)

        if event["event_type"] in {"incident_response", "recovery"} and start >= pd.Timestamp("2025-08-13"):
            baseline_start, baseline_end = pd.Timestamp("2025-07-31"), pd.Timestamp("2025-08-11")
            comparison = "stable pre-incident baseline (2025-07-31 to 2025-08-11)"
        else:
            baseline_start = start - pd.Timedelta(days=window_days)
            baseline_end = start - pd.Timedelta(days=1)
            comparison = f"preceding {window_days} days"
        before = aggregate[aggregate["date"].between(baseline_start, baseline_end)]
        during = aggregate[aggregate["date"].between(start, end)]
        if before.empty or during.empty:
            continue
        result = {"event_id": event["event_id"], "event_name": event["event_name"],
                  "event_type": event["event_type"], "start_date": start.date(),
                  "end_date": end.date(), "regions": " | ".join(applicable_regions),
                  "comparison_basis": comparison}
        for metric in metrics:
            prior, current = before[metric].mean(), during[metric].mean()
            result[f"{metric}_before"] = prior
            result[f"{metric}_during"] = current
            result[f"{metric}_change_pct"] = np.nan if prior == 0 else (current/prior-1)*100
        rows.append(result)
    return pd.DataFrame(rows)


def product_summary(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    merged = sales.merge(products, on="product_id", validate="many_to_one")
    return (merged.groupby(["product_id", "product_name", "product_type"], as_index=False)
            .agg(purchasers=("purchasers", "sum"), units_sold=("units_sold", "sum"),
                 gross_revenue_usd=("gross_revenue_usd", "sum"))
            .sort_values("gross_revenue_usd", ascending=False))


def save_charts(daily: pd.DataFrame, retention: pd.DataFrame, events: pd.DataFrame,
                event_summary: pd.DataFrame, product_results: pd.DataFrame,
                bosses: pd.DataFrame, image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    lifecycle_markers = {
        2024: [("Global Launch", "Launch"),
               ("Half-Anniversary Raid", "Half-anniv."),
               ("Fantasy Saga Crossover", "Successful collab"),
               ("Christmas Festival 2024", "Christmas")],
        2025: [("First Anniversary", "1st anniv."),
               ("Spring Content Gap", "Content gap"),
               ("PvE Growth Subscription Launch", "PvE subscription"),
               ("Astra Heroes Crossover", "Weak-fit collab"),
               ("Data Center Outage", "Outage"),
               ("Extraordinary Compensation", "Compensation")],
    }
    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharey=True)
    for ax, year in zip(axes, [2024, 2025]):
        year_daily = daily[daily["date"].dt.year.eq(year)]
        for region, frame in year_daily.groupby("region"):
            ax.plot(frame["date"], frame["dau_7d"], label=region, linewidth=1.8)
        for event_name, short_label in lifecycle_markers[year]:
            date = events.loc[events["event_name"].eq(event_name), "start_date"].iloc[0]
            ax.axvline(date, color="gray", linestyle="--", alpha=.5)
            ax.text(date, .97, short_label, transform=ax.get_xaxis_transform(),
                    rotation=25, ha="left", va="top", fontsize=8)
        ax.set(title=f"{year} Regional DAU", ylabel="DAU (7-day average)")
    axes[0].legend(ncol=3)
    axes[1].set(xlabel="Date")
    fig.suptitle("Two-Year Live-Service Lifecycle: Growth, Pressure, and Recovery", y=.995)
    fig.tight_layout()
    fig.savefig(image_dir/"performance_overview.png", dpi=180)
    plt.close(fig)

    aggregate = daily.groupby("date", as_index=False)[
        ["nru", "returned_users", "user_outflow"]].sum()
    for column in ["nru", "returned_users", "user_outflow"]:
        aggregate[column] = aggregate[column].rolling(7, min_periods=1).mean()
    fig, ax = plt.subplots(figsize=(13, 5.5))
    for column, label in [("nru", "New users"), ("returned_users", "Returned users"),
                          ("user_outflow", "User outflow")]:
        ax.plot(aggregate["date"], aggregate[column], label=label)
    ax.set(title="Global Activity-Flow Drivers", xlabel="Date", ylabel="Users (7-day average)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(image_dir/"activity_flow_drivers.png", dpi=180)
    plt.close(fig)

    weighted = retention.groupby("cohort_month").agg(
        cohort_size=("cohort_size", "sum"), d1=("d1_retained", "sum"),
        d7=("d7_retained", "sum"), d30=("d30_retained", "sum"))
    heat = pd.DataFrame({day: weighted[day.lower()]/weighted["cohort_size"]*100
                         for day in ["D1", "D7", "D30"]})
    heat.index = heat.index.strftime("%Y-%m")
    fig, ax = plt.subplots(figsize=(9, 9))
    sns.heatmap(heat, annot=True, fmt=".1f", cmap="YlGnBu", ax=ax,
                cbar_kws={"label": "Retention (%)"})
    ax.set(title="Monthly Cohort Retention", xlabel="Checkpoint", ylabel="Cohort month")
    fig.tight_layout()
    fig.savefig(image_dir/"retention_heatmap.png", dpi=180)
    plt.close(fig)

    top_products = product_results.head(12).sort_values("gross_revenue_usd")
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.barh(top_products["product_name"], top_products["gross_revenue_usd"], color="#4C72B0")
    ax.set(title="Gross Revenue by Product", xlabel="Synthetic USD", ylabel="")
    fig.tight_layout()
    fig.savefig(image_dir/"monetization_drivers.png", dpi=180)
    plt.close(fig)

    incident = event_summary[event_summary["event_name"].eq("Data Center Outage")].iloc[0]
    compensation = event_summary[event_summary["event_name"].eq("Extraordinary Compensation")].iloc[0]
    labels = ["Outage: DAU", "Outage: revenue", "Compensation: return"]
    values = [incident["dau_change_pct"], incident["revenue_change_pct"],
              compensation["returned_users_change_pct"]]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, values, color=["#C44E52", "#C44E52", "#55A868"])
    ax.axhline(0, color="black", linewidth=.8)
    ax.bar_label(bars, fmt="%.1f%%", padding=3)
    ax.set(title="Service Incident and Immediate Recovery Signals",
           ylabel="Change from event-specific baseline (%)")
    fig.tight_layout()
    fig.savefig(image_dir/"service_disruption_comparison.png", dpi=180)
    plt.close(fig)

    boss_plot = (bosses.groupby(["boss_name", "difficulty"], as_index=False)
                 .agg(participants=("participants", "sum"), clears=("clears", "sum"),
                      dau=("dau", "sum")))
    boss_plot["participation_rate"] = boss_plot["participants"]/boss_plot["dau"]*100
    boss_plot["clear_rate"] = boss_plot["clears"]/boss_plot["participants"]*100
    order = ["NORMAL", "HARD", "NIGHTMARE"]
    fig, axes = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
    sns.barplot(data=boss_plot, x="boss_name", y="participation_rate",
                hue="difficulty", hue_order=order, ax=axes[0])
    axes[0].set(title="Limited PvE Boss Participation and Clear Rates",
                xlabel="", ylabel="Participation / DAU (%)")
    sns.barplot(data=boss_plot, x="boss_name", y="clear_rate",
                hue="difficulty", hue_order=order, ax=axes[1])
    axes[1].set(xlabel="", ylabel="Clear rate (%)")
    if axes[1].legend_:
        axes[1].legend_.remove()
    axes[1].tick_params(axis="x", rotation=15)
    fig.tight_layout()
    fig.savefig(image_dir/"boss_event_performance.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, events, products, sales, bosses = load_data(root)
    quality = validate_data(daily, retention, events, products, sales, bosses)
    daily, retention, bosses = prepare_metrics(daily, retention, bosses)
    event_results = event_window_summary(daily, events)
    product_results = product_summary(sales, products)
    derived_quality = validate_derived_data(daily, retention, event_results, bosses)
    output = root/"outputs"
    output.mkdir(exist_ok=True)
    for filename, frame in {
        "daily_metrics_enriched.csv": daily,
        "retention_metrics.csv": retention,
        "event_window_summary.csv": event_results,
        "product_summary.csv": product_results,
        "boss_metrics_enriched.csv": bosses,
        "data_quality_report.csv": quality,
        "derived_quality_report.csv": derived_quality,
    }.items():
        frame.to_csv(output/filename, index=False)
    save_charts(daily, retention, events, event_results,
                product_results, bosses, root/"images")
    print("Data quality checks passed")
    print(quality.to_string(index=False))
    print("\nSelected event-window results")
    print(event_results[event_results["event_name"].isin([
        "PvE Growth Subscription Launch", "Astra Heroes Crossover",
        "Data Center Outage", "Extraordinary Compensation",
        "Postmortem and Trust Recovery",
    ])][["event_name", "dau_change_pct", "returned_users_change_pct",
         "revenue_change_pct", "conversion_rate_change_pct"]].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
