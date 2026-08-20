"""Analysis 4: revenue structure and subscription-launch evaluation."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, project_root
except ModuleNotFoundError:  # Support `python src/analyze_monetization.py`.
    from analyze_game_data import load_data, project_root


REGION_ORDER = ["KR", "JP", "GLOBAL_WEST"]
REGION_COLORS = {
    "KR": "#2E8B57",
    "JP": "#E68613",
    "GLOBAL_WEST": "#3478BF",
}
WINDOWS = {
    "february_reference": ("2025-02-01", "2025-02-28"),
    "local_baseline": ("2025-04-15", "2025-05-14"),
    "launch": ("2025-05-15", "2025-06-14"),
    "post_14": ("2025-06-15", "2025-06-28"),
}
ADJACENT_TYPES = {"monthly_pass", "currency_subscription", "growth_booster"}
ADJACENT_PRODUCT_IDS = ["P003", "P005", "P007"]
NEW_BM_ID = "P008"


def prepare_sales(sales: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    result = sales.copy()
    result["date"] = pd.to_datetime(result["date"])
    products = products.copy()
    products["available_from"] = pd.to_datetime(products["available_from"])
    result = result.merge(products, on="product_id", validate="many_to_one")
    expected = result["units_sold"] * result["price_usd"]
    if not np.allclose(result["gross_revenue_usd"], expected, atol=.01):
        raise ValueError("product revenue failed list-price reconciliation")
    return result


def monetization_window_summary(daily: pd.DataFrame,
                                sales: pd.DataFrame) -> pd.DataFrame:
    """Summarize service and product KPIs for each decision window and region."""
    daily = daily.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    rows: list[dict[str, object]] = []
    scopes = [("ALL", REGION_ORDER), *[(r, [r]) for r in REGION_ORDER]]
    for scope, regions in scopes:
        for window, (start_text, end_text) in WINDOWS.items():
            start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
            daily_window = daily[
                daily["region"].isin(regions) & daily["date"].between(start, end)
            ]
            sales_window = sales[
                sales["region"].isin(regions) & sales["date"].between(start, end)
            ]
            days = int(daily_window["date"].nunique())
            revenue = float(sales_window["gross_revenue_usd"].sum())
            dau = float(daily_window["dau"].sum())
            pu = float(daily_window["pu"].sum())
            adjacent_revenue = float(
                sales_window[sales_window["product_type"].isin(ADJACENT_TYPES)][
                    "gross_revenue_usd"
                ].sum()
            )
            new_bm_revenue = float(
                sales_window[sales_window["product_id"].eq(NEW_BM_ID)][
                    "gross_revenue_usd"
                ].sum()
            )
            product_revenue = sales_window.groupby("product_id")[
                "gross_revenue_usd"
            ].sum()
            shares = product_revenue / revenue
            rows.append({
                "scope": scope,
                "window": window,
                "start_date": start,
                "end_date": end,
                "days": days,
                "dau": dau,
                "pu": pu,
                "revenue": revenue,
                "dau_per_day": dau / days,
                "pu_per_day": pu / days,
                "revenue_per_day": revenue / days,
                "conversion_rate": pu / dau,
                "revenue_per_payer_day": revenue / pu,
                "revenue_per_dau_day": revenue / dau,
                "adjacent_revenue_per_day": adjacent_revenue / days,
                "adjacent_revenue_per_payer_day": adjacent_revenue / pu,
                "adjacent_revenue_share": adjacent_revenue / revenue,
                "new_bm_revenue_per_day": new_bm_revenue / days,
                "new_bm_revenue_share": new_bm_revenue / revenue,
                "legacy_revenue_per_day": (revenue - new_bm_revenue) / days,
                "product_revenue_hhi": float((shares ** 2).sum()),
                "top_3_product_revenue_share": float(shares.nlargest(3).sum()),
            })
    return pd.DataFrame(rows)


def _pct_change(current: float, baseline: float) -> float:
    return (current / baseline - 1) * 100


def _retention_guardrail(retention: pd.DataFrame, regions: list[str]) -> dict[str, float]:
    frame = retention.copy()
    frame["cohort_month"] = pd.to_datetime(frame["cohort_month"])
    frame = frame[frame["region"].isin(regions)]
    baseline = frame[frame["cohort_month"].eq(pd.Timestamp("2025-02-01"))]
    target = frame[frame["cohort_month"].isin(pd.to_datetime([
        "2025-05-01", "2025-06-01",
    ]))]
    baseline_rate = baseline["d30_retained"].sum() / baseline["cohort_size"].sum()
    target_rate = target["d30_retained"].sum() / target["cohort_size"].sum()
    return {
        "d30_reference": baseline_rate,
        "d30_launch_cohorts": target_rate,
        "d30_change_pp": (target_rate - baseline_rate) * 100,
    }


def bm_evaluation_summary(windows: pd.DataFrame,
                          retention: pd.DataFrame) -> pd.DataFrame:
    """Apply primary and guardrail thresholds to the subscription launch."""
    rows: list[dict[str, object]] = []
    for scope, regions in [("ALL", REGION_ORDER), *[(r, [r]) for r in REGION_ORDER]]:
        frame = windows[windows["scope"].eq(scope)].set_index("window")
        baseline, launch = frame.loc["local_baseline"], frame.loc["launch"]
        post, february = frame.loc["post_14"], frame.loc["february_reference"]
        retention_result = _retention_guardrail(retention, regions)
        revenue_change = _pct_change(launch["revenue_per_day"], baseline["revenue_per_day"])
        pu_change = _pct_change(launch["pu_per_day"], baseline["pu_per_day"])
        adjacent_launch_change = _pct_change(
            launch["adjacent_revenue_per_payer_day"],
            baseline["adjacent_revenue_per_payer_day"],
        )
        adjacent_post_change = _pct_change(
            post["adjacent_revenue_per_payer_day"],
            baseline["adjacent_revenue_per_payer_day"],
        )
        revenue_pass = revenue_change >= 10
        pu_pass = pu_change >= 5
        launch_adjacent_warning = adjacent_launch_change <= -5
        post_adjacent_warning = adjacent_post_change <= -5
        retention_failed = retention_result["d30_change_pp"] <= -1
        if revenue_pass and pu_pass:
            if launch_adjacent_warning or post_adjacent_warning or retention_failed:
                outcome = "Mixed: growth with guardrail warning"
            else:
                outcome = "Successful"
        else:
            outcome = "Underperforming"
        rows.append({
            "scope": scope,
            "launch_revenue_per_day_change_pct": revenue_change,
            "launch_pu_per_day_change_pct": pu_change,
            "launch_conversion_rate_change_pct": _pct_change(
                launch["conversion_rate"], baseline["conversion_rate"]
            ),
            "launch_revenue_per_payer_day_change_pct": _pct_change(
                launch["revenue_per_payer_day"], baseline["revenue_per_payer_day"]
            ),
            "launch_vs_february_revenue_per_day_change_pct": _pct_change(
                launch["revenue_per_day"], february["revenue_per_day"]
            ),
            "new_bm_launch_revenue_share": launch["new_bm_revenue_share"],
            "adjacent_launch_revenue_per_day_change_pct": _pct_change(
                launch["adjacent_revenue_per_day"],
                baseline["adjacent_revenue_per_day"],
            ),
            "adjacent_post_14_revenue_per_day_change_pct": _pct_change(
                post["adjacent_revenue_per_day"],
                baseline["adjacent_revenue_per_day"],
            ),
            "adjacent_launch_revenue_per_payer_day_change_pct": adjacent_launch_change,
            "adjacent_post_14_revenue_per_payer_day_change_pct": adjacent_post_change,
            "adjacent_launch_share_change_pp": (
                launch["adjacent_revenue_share"] - baseline["adjacent_revenue_share"]
            ) * 100,
            "launch_hhi_change": (
                launch["product_revenue_hhi"] - baseline["product_revenue_hhi"]
            ),
            "launch_top_3_share_change_pp": (
                launch["top_3_product_revenue_share"]
                - baseline["top_3_product_revenue_share"]
            ) * 100,
            **retention_result,
            "revenue_pass": revenue_pass,
            "pu_pass": pu_pass,
            "launch_adjacent_reallocation_warning": launch_adjacent_warning,
            "post_14_adjacent_reallocation_warning": post_adjacent_warning,
            "retention_guardrail_failed": retention_failed,
            "outcome": outcome,
        })
    return pd.DataFrame(rows)


def adjacent_product_summary(daily: pd.DataFrame,
                             sales: pd.DataFrame) -> pd.DataFrame:
    """Measure adjacent revenue per service payer-day before and after launch."""
    daily = daily.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    rows: list[dict[str, object]] = []
    product_lookup = sales.drop_duplicates("product_id").set_index("product_id")
    for product_id in ADJACENT_PRODUCT_IDS:
        row: dict[str, object] = {
            "product_id": product_id,
            "product_name": product_lookup.loc[product_id, "product_name"],
            "product_type": product_lookup.loc[product_id, "product_type"],
        }
        for window, (start_text, end_text) in WINDOWS.items():
            start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
            revenue = sales[
                sales["product_id"].eq(product_id)
                & sales["date"].between(start, end)
            ]["gross_revenue_usd"].sum()
            payer_days = daily[daily["date"].between(start, end)]["pu"].sum()
            row[f"{window}_revenue_per_payer_day"] = revenue / payer_days
        row["launch_change_pct"] = _pct_change(
            row["launch_revenue_per_payer_day"],
            row["local_baseline_revenue_per_payer_day"],
        )
        row["post_14_change_pct"] = _pct_change(
            row["post_14_revenue_per_payer_day"],
            row["local_baseline_revenue_per_payer_day"],
        )
        row["launch_warning"] = row["launch_change_pct"] <= -5
        row["post_14_warning"] = row["post_14_change_pct"] <= -5
        rows.append(row)

    combined: dict[str, object] = {
        "product_id": "ADJACENT_SET",
        "product_name": "Combined adjacent set",
        "product_type": "adjacent_set",
    }
    for window in WINDOWS:
        combined[f"{window}_revenue_per_payer_day"] = sum(
            float(row[f"{window}_revenue_per_payer_day"]) for row in rows
        )
    combined["launch_change_pct"] = _pct_change(
        float(combined["launch_revenue_per_payer_day"]),
        float(combined["local_baseline_revenue_per_payer_day"]),
    )
    combined["post_14_change_pct"] = _pct_change(
        float(combined["post_14_revenue_per_payer_day"]),
        float(combined["local_baseline_revenue_per_payer_day"]),
    )
    combined["launch_warning"] = combined["launch_change_pct"] <= -5
    combined["post_14_warning"] = combined["post_14_change_pct"] <= -5
    rows.append(combined)
    return pd.DataFrame(rows)


def revenue_decomposition(windows: pd.DataFrame) -> pd.DataFrame:
    """Decompose launch-period daily revenue lift into legacy and subscription components."""
    frame = windows[windows["scope"].eq("ALL")].set_index("window")
    baseline, launch = frame.loc["local_baseline"], frame.loc["launch"]
    baseline_total = baseline["revenue_per_day"]
    legacy_change = launch["legacy_revenue_per_day"] - baseline_total
    new_bm = launch["new_bm_revenue_per_day"]
    total_lift = launch["revenue_per_day"] - baseline_total
    return pd.DataFrame([
        {"component": "Baseline total", "revenue_per_day": baseline_total,
         "share_of_total_lift": np.nan},
        {"component": "Legacy-product change", "revenue_per_day": legacy_change,
         "share_of_total_lift": legacy_change / total_lift},
        {"component": "New PvE subscription", "revenue_per_day": new_bm,
         "share_of_total_lift": new_bm / total_lift},
        {"component": "Launch total", "revenue_per_day": launch["revenue_per_day"],
         "share_of_total_lift": np.nan},
    ])


def save_monetization_charts(windows: pd.DataFrame,
                             evaluation: pd.DataFrame,
                             adjacent: pd.DataFrame,
                             decomposition: pd.DataFrame,
                             image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    baseline = decomposition.loc[
        decomposition["component"].eq("Baseline total"), "revenue_per_day"
    ].iat[0]
    legacy_change = decomposition.loc[
        decomposition["component"].eq("Legacy-product change"), "revenue_per_day"
    ].iat[0]
    new_bm = decomposition.loc[
        decomposition["component"].eq("New PvE subscription"), "revenue_per_day"
    ].iat[0]
    launch_total = decomposition.loc[
        decomposition["component"].eq("Launch total"), "revenue_per_day"
    ].iat[0]
    positions = np.arange(4)
    bottoms = [0, baseline, baseline + legacy_change, 0]
    heights = [baseline, legacy_change, new_bm, launch_total]
    colors = ["#A0A0A0", "#4C72B0", "#55A868", "#3478BF"]
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(positions, heights, bottom=bottoms, color=colors, width=.65)
    labels = [
        f"${baseline:,.0f}",
        (
            f"+${legacy_change:,.0f}\n"
            f"({legacy_change / (launch_total - baseline):.1%} of lift)"
        ),
        (
            f"+${new_bm:,.0f}\n"
            f"({new_bm / (launch_total - baseline):.1%} of lift)"
        ),
        f"${launch_total:,.0f}",
    ]
    ax.bar_label(bars, labels=labels, padding=3)
    ax.set(title="Observed Daily Revenue Lift — Arithmetic Decomposition",
           ylabel="Synthetic USD per day", xticks=positions,
           xticklabels=["Baseline", "Legacy change", "PvE subscription", "Launch total"])
    ax.set_ylim(0, launch_total * 1.15)
    fig.tight_layout()
    fig.savefig(image_dir / "bm_revenue_decomposition.png", dpi=180)
    plt.close(fig)

    plot = adjacent.copy()
    plot["display_name"] = plot["product_id"].map({
        "P003": "Mission Pass",
        "P005": "Currency Pass",
        "P007": "Growth Booster",
        "ADJACENT_SET": "Combined set",
    })
    plot = plot.melt(
        id_vars=["display_name"],
        value_vars=["launch_change_pct", "post_14_change_pct"],
        var_name="window", value_name="change_pct",
    )
    plot["window"] = plot["window"].map({
        "launch_change_pct": "Launch window",
        "post_14_change_pct": "Post-launch days 1–14",
    })
    fig, ax = plt.subplots(figsize=(10.5, 6))
    sns.barplot(data=plot, x="display_name", y="change_pct", hue="window", ax=ax,
                palette=["#4C72B0", "#E68613"])
    ax.axhline(-5, color="#C44E52", linestyle="--", label="-5% warning threshold")
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels, frameon=False)
    ax.set(title="Adjacent-Product Guardrail by Window",
           xlabel="", ylabel="Revenue change per service payer-day (%)")
    fig.tight_layout()
    fig.savefig(image_dir / "adjacent_product_cannibalization.png", dpi=180)
    plt.close(fig)

    regional = evaluation[evaluation["scope"].isin(REGION_ORDER)].copy()
    regional = regional.set_index("scope").loc[REGION_ORDER].reset_index()
    display_regions = {"KR": "KR", "JP": "JP", "GLOBAL_WEST": "Global West"}
    fig, axes = plt.subplots(
        1, 2, figsize=(13, 6.3), gridspec_kw={"width_ratios": [1, 1.25]},
    )

    revenue_bars = axes[0].bar(
        regional["scope"].map(display_regions),
        regional["launch_revenue_per_day_change_pct"],
        color=[REGION_COLORS[region] for region in regional["scope"]],
        width=.62,
    )
    axes[0].axhline(10, color="#555555", linestyle="--", linewidth=1.2)
    axes[0].bar_label(revenue_bars, fmt="%+.1f%%", padding=3)
    axes[0].set(
        title="Daily revenue growth",
        xlabel="", ylabel="Change from local baseline (%)", ylim=(0, 105),
    )

    x = np.arange(2)
    for region in REGION_ORDER:
        row = regional[regional["scope"].eq(region)].iloc[0]
        values = [
            row["adjacent_launch_revenue_per_payer_day_change_pct"],
            row["adjacent_post_14_revenue_per_payer_day_change_pct"],
        ]
        axes[1].plot(
            x, values, color=REGION_COLORS[region], marker="o", linewidth=2.2,
            markersize=7, label=display_regions[region],
        )
        for x_value, value in zip(x, values):
            axes[1].annotate(
                f"{value:+.1f}%", (x_value, value), xytext=(0, 7),
                textcoords="offset points", ha="center", va="bottom", fontsize=9,
            )
    axes[1].axhline(-5, color="#C44E52", linestyle="--", linewidth=1.2)
    axes[1].axhline(0, color="#555555", linewidth=.8)
    axes[1].set(
        title="Adjacent revenue per service payer-day",
        xlabel="", ylabel="Change from local baseline (%)",
        xticks=x, xticklabels=["Launch window", "Post-launch days 1–14"],
        ylim=(-12, 2),
    )
    axes[1].legend(title="Region", frameon=False, ncol=3, loc="lower left")

    fig.suptitle("Regional Launch Growth and Adjacent-Product Guardrail", y=.995)
    fig.text(
        .5, .015,
        "Revenue minimum = +10%; adjacent-product warning = -5%. Paying-user growth also passes in every region.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=[0, .05, 1, .95])
    fig.savefig(image_dir / "bm_regional_guardrails.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, _, products, sales, _ = load_data(root)
    sales_enriched = prepare_sales(sales, products)
    windows = monetization_window_summary(daily, sales_enriched)
    evaluation = bm_evaluation_summary(windows, retention)
    adjacent = adjacent_product_summary(daily, sales_enriched)
    decomposition = revenue_decomposition(windows)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    windows.to_csv(output_dir / "monetization_window_summary.csv", index=False)
    evaluation.to_csv(output_dir / "bm_evaluation_summary.csv", index=False)
    adjacent.to_csv(output_dir / "adjacent_product_summary.csv", index=False)
    decomposition.to_csv(output_dir / "bm_revenue_decomposition.csv", index=False)
    save_monetization_charts(
        windows, evaluation, adjacent, decomposition, root / "images"
    )

    columns = [
        "scope", "launch_revenue_per_day_change_pct", "launch_pu_per_day_change_pct",
        "adjacent_launch_revenue_per_payer_day_change_pct",
        "adjacent_post_14_revenue_per_payer_day_change_pct", "d30_change_pp", "outcome",
    ]
    print("Analysis 4 monetization outputs created")
    print(evaluation[columns].round(2).to_string(index=False))
    print("\nAdjacent products")
    print(adjacent[["product_name", "launch_change_pct", "post_14_change_pct",
                    "launch_warning", "post_14_warning"]].round(2).to_string(index=False))
    print("\nRevenue decomposition")
    print(decomposition.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
