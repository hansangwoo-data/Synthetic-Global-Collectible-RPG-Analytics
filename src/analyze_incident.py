"""Analysis 5: outage impact and staged recovery analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, project_root
except ModuleNotFoundError:  # Support `python src/analyze_incident.py`.
    from analyze_game_data import load_data, project_root


REGION_ORDER = ["KR", "JP", "GLOBAL_WEST"]
REGION_COLORS = {
    "KR": "#2E8B57",
    "JP": "#E68613",
    "GLOBAL_WEST": "#3478BF",
}
REGION_LABELS = {
    "KR": "KR",
    "JP": "JP",
    "GLOBAL_WEST": "Global West",
}
INCIDENT_WINDOWS = {
    "pre_incident_baseline": ("2025-07-31", "2025-08-11"),
    "full_outage": ("2025-08-12", "2025-08-12"),
    "partial_restoration": ("2025-08-13", "2025-08-13"),
    "delayed_response": ("2025-08-14", "2025-08-16"),
    "extraordinary_compensation": ("2025-08-17", "2025-08-23"),
    "postmortem_remediation": ("2025-08-24", "2025-09-20"),
    "residual_post_recovery": ("2025-09-21", "2025-09-30"),
}
WINDOW_LABELS = {
    "pre_incident_baseline": "Pre-incident baseline",
    "full_outage": "Full outage",
    "partial_restoration": "Partial restoration",
    "delayed_response": "Delayed response",
    "extraordinary_compensation": "Extraordinary compensation",
    "postmortem_remediation": "Postmortem & remediation",
    "residual_post_recovery": "Residual post-recovery",
}
RECOVERY_THRESHOLDS = {
    "dau_recovery_index": 95,
    "pu_recovery_index": 90,
    "revenue_recovery_index": 90,
}
RETENTION_PERIODS = {
    "june_reference": ["2025-06-01"],
    "july_overlap": ["2025-07-01"],
    "august_incident": ["2025-08-01"],
    "september_remediation": ["2025-09-01"],
    "october_residual": ["2025-10-01"],
    "november_residual": ["2025-11-01"],
    "residual_oct_nov_pooled": ["2025-10-01", "2025-11-01"],
}
RETENTION_LABELS = {
    "june_reference": "Jun reference",
    "july_overlap": "Jul overlap",
    "august_incident": "Aug incident",
    "september_remediation": "Sep remediation",
    "october_residual": "Oct post-recovery*",
    "november_residual": "Nov post-recovery",
    "residual_oct_nov_pooled": "Oct–Nov post-recovery",
}


def _safe_ratio(numerator: float, denominator: float) -> float:
    return np.nan if denominator == 0 else numerator / denominator


def incident_window_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Summarize technical, activity, and commercial KPIs by recovery stage."""
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    rows: list[dict[str, object]] = []
    scopes = [("ALL", REGION_ORDER), *[(region, [region]) for region in REGION_ORDER]]
    for scope, regions in scopes:
        for order, (window, (start_text, end_text)) in enumerate(INCIDENT_WINDOWS.items()):
            start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
            period = frame[
                frame["region"].isin(regions) & frame["date"].between(start, end)
            ]
            days = int(period["date"].nunique())
            dau = float(period["dau"].sum())
            pu = float(period["pu"].sum())
            revenue = float(period["revenue"].sum())
            rows.append({
                "scope": scope,
                "window": window,
                "window_label": WINDOW_LABELS[window],
                "window_order": order,
                "start_date": start,
                "end_date": end,
                "days": days,
                "service_availability": float(period["service_availability"].mean()),
                "dau_per_day": dau / days,
                "nru_per_day": float(period["nru"].sum()) / days,
                "returned_users_per_day": float(period["returned_users"].sum()) / days,
                "user_outflow_per_day": float(period["user_outflow"].sum()) / days,
                "pu_per_day": pu / days,
                "revenue_per_day": revenue / days,
                "conversion_rate": _safe_ratio(pu, dau),
                "revenue_per_payer_day": _safe_ratio(revenue, pu),
                "outflow_observable": bool(period["service_availability"].gt(0).any()),
            })

    result = pd.DataFrame(rows)
    metric_columns = [
        "dau_per_day", "nru_per_day", "returned_users_per_day",
        "user_outflow_per_day", "pu_per_day", "revenue_per_day",
        "conversion_rate", "revenue_per_payer_day",
    ]
    for scope in result["scope"].unique():
        scope_mask = result["scope"].eq(scope)
        baseline = result[
            scope_mask & result["window"].eq("pre_incident_baseline")
        ].iloc[0]
        for metric in metric_columns:
            index_name = metric.replace("_per_day", "") + "_recovery_index"
            result.loc[scope_mask, index_name] = (
                result.loc[scope_mask, metric] / baseline[metric] * 100
            )
        full_outage = scope_mask & result["window"].eq("full_outage")
        result.loc[full_outage, "user_outflow_recovery_index"] = np.nan
    return result


def incident_stage_evaluation(summary: pd.DataFrame) -> pd.DataFrame:
    """Apply operational recovery thresholds to every post-incident stage."""
    result = summary[~summary["window"].eq("pre_incident_baseline")].copy()
    result["dau_pass"] = (
        result["dau_recovery_index"] >= RECOVERY_THRESHOLDS["dau_recovery_index"]
    )
    result["pu_pass"] = (
        result["pu_recovery_index"] >= RECOVERY_THRESHOLDS["pu_recovery_index"]
    )
    result["revenue_pass"] = (
        result["revenue_recovery_index"]
        >= RECOVERY_THRESHOLDS["revenue_recovery_index"]
    )
    result["operational_thresholds_met"] = result[
        ["dau_pass", "pu_pass", "revenue_pass"]
    ].all(axis=1)
    result["stage_result"] = np.where(
        result["operational_thresholds_met"],
        "Operational thresholds met",
        "Incomplete operational recovery",
    )
    return result


def incident_retention_summary(retention: pd.DataFrame) -> pd.DataFrame:
    """Compare incident and post-recovery D30 cohorts with the June reference."""
    frame = retention.copy()
    frame["cohort_month"] = pd.to_datetime(frame["cohort_month"])
    rows: list[dict[str, object]] = []
    scopes = [("ALL", REGION_ORDER), *[(region, [region]) for region in REGION_ORDER]]
    for scope, regions in scopes:
        scoped = frame[frame["region"].isin(regions)]
        for order, (period, month_texts) in enumerate(RETENTION_PERIODS.items()):
            months = pd.to_datetime(month_texts)
            selected = scoped[scoped["cohort_month"].isin(months)]
            cohort_size = int(selected["cohort_size"].sum())
            d1 = int(selected["d1_retained"].sum())
            d7 = int(selected["d7_retained"].sum())
            d30 = int(selected["d30_retained"].sum())
            rows.append({
                "scope": scope,
                "period": period,
                "period_label": RETENTION_LABELS[period],
                "period_order": order,
                "cohort_months": " | ".join(month.strftime("%Y-%m") for month in months),
                "cohort_size": cohort_size,
                "d1_retention": _safe_ratio(d1, cohort_size),
                "d7_retention": _safe_ratio(d7, cohort_size),
                "d30_retention": _safe_ratio(d30, cohort_size),
            })
    result = pd.DataFrame(rows)
    for scope in result["scope"].unique():
        scope_mask = result["scope"].eq(scope)
        reference = result[
            scope_mask & result["period"].eq("june_reference")
        ]["d30_retention"].iat[0]
        result.loc[scope_mask, "d30_change_pp"] = (
            result.loc[scope_mask, "d30_retention"] - reference
        ) * 100
    result["d30_guardrail_failed"] = result["d30_change_pp"] < -.5
    return result


def incident_final_evaluation(stage_evaluation: pd.DataFrame,
                              retention_summary: pd.DataFrame) -> pd.DataFrame:
    """Combine residual operational and cohort-quality recovery by region."""
    residual = stage_evaluation[
        stage_evaluation["window"].eq("residual_post_recovery")
    ].copy()
    cohort = retention_summary[
        retention_summary["period"].eq("residual_oct_nov_pooled")
    ][["scope", "d30_retention", "d30_change_pp", "d30_guardrail_failed"]]
    result = residual.merge(cohort, on="scope", validate="one_to_one")
    result["outflow_above_baseline"] = result["user_outflow_recovery_index"] > 100
    result["final_outcome"] = np.select(
        [
            ~result["operational_thresholds_met"],
            result["d30_guardrail_failed"],
        ],
        [
            "Underperforming: operational recovery incomplete",
            "Mixed: operational recovery, retention gap remains",
        ],
        default="Successful",
    )
    return result


def save_incident_charts(daily: pd.DataFrame,
                         window_summary: pd.DataFrame,
                         retention_summary: pd.DataFrame,
                         image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    timeline = daily.copy()
    timeline["date"] = pd.to_datetime(timeline["date"])
    timeline = timeline[timeline["date"].between("2025-07-31", "2025-09-30")]
    baseline = timeline[timeline["date"].between("2025-07-31", "2025-08-11")]
    baseline_means = baseline.groupby("region")[["dau", "pu", "revenue"]].mean()
    for metric in ["dau", "pu", "revenue"]:
        timeline[f"{metric}_index"] = (
            timeline[metric] / timeline["region"].map(baseline_means[metric]) * 100
        )

    metrics = [
        ("dau_index", "DAU recovery index", 95),
        ("pu_index", "Paying-user recovery index", 90),
        ("revenue_index", "Revenue recovery index", 90),
    ]
    fig, axes = plt.subplots(3, 1, figsize=(13, 9.5), sharex=True, sharey=True)
    for ax, (metric, title, threshold) in zip(axes, metrics):
        for region in REGION_ORDER:
            region_data = timeline[timeline["region"].eq(region)]
            ax.plot(
                region_data["date"], region_data[metric],
                color=REGION_COLORS[region], label=REGION_LABELS[region], linewidth=1.8,
            )
        ax.axhline(100, color="#666666", linewidth=.9)
        ax.axhline(threshold, color="#C44E52", linestyle="--", linewidth=1.1)
        ax.axvspan(pd.Timestamp("2025-08-12"), pd.Timestamp("2025-08-16"),
                   color="#C44E52", alpha=.08)
        ax.set(title=title, ylabel="Baseline = 100", ylim=(0, 145))
    for date, label in [
        ("2025-08-12", "Outage"),
        ("2025-08-17", "Compensation"),
        ("2025-08-24", "Postmortem"),
        ("2025-09-21", "Residual"),
    ]:
        axes[0].axvline(pd.Timestamp(date), color="#777777", linestyle=":", alpha=.8)
        axes[0].text(
            pd.Timestamp(date), 141, label, rotation=90,
            va="top", ha="right", fontsize=8,
        )
    axes[0].legend(ncol=3, frameon=False)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    axes[-1].set(xlabel="Date")
    fig.suptitle("Daily Regional Recovery after the 36-Hour Outage", y=.995)
    fig.text(
        .5, .005,
        "Index 100 = regional pre-incident baseline; dashed red lines = metric-specific recovery targets.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, .025, 1, .98))
    fig.savefig(image_dir / "incident_daily_recovery_by_region.png", dpi=180)
    plt.close(fig)

    bridge_windows = [
        "extraordinary_compensation",
        "postmortem_remediation",
        "residual_post_recovery",
    ]
    global_windows = window_summary[
        window_summary["scope"].eq("ALL")
        & window_summary["window"].isin(bridge_windows)
    ].sort_values("window_order")
    bridge = global_windows.melt(
        id_vars=["window_label", "window_order"],
        value_vars=[
            "returned_users_recovery_index", "pu_recovery_index",
            "revenue_recovery_index",
        ],
        var_name="metric", value_name="recovery_index",
    )
    bridge["metric"] = bridge["metric"].map({
        "returned_users_recovery_index": "Returned users",
        "pu_recovery_index": "Paying users",
        "revenue_recovery_index": "Revenue",
    })
    fig, ax = plt.subplots(figsize=(11, 6.5))
    plot = sns.barplot(
        data=bridge, x="window_label", y="recovery_index", hue="metric", ax=ax,
        palette=["#55A868", "#4C72B0", "#E68613"],
    )
    for container in plot.containers:
        plot.bar_label(container, fmt="%.0f", padding=3, fontsize=9)
    ax.axhline(100, color="#666666", linestyle="--", linewidth=1)
    ax.set(
        title="Reactivation Outpaced Commercial Recovery",
        xlabel="", ylabel="Recovery index (pre-incident = 100)",
    )
    ax.tick_params(axis="x", rotation=0)
    ax.legend(frameon=False)
    fig.text(
        .5, .01,
        "Returned users measure reactivation, not unique compensation claimants or buyer conversion.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(image_dir / "incident_reactivation_commercial_bridge.png", dpi=180)
    plt.close(fig)

    regional_exit = window_summary[
        window_summary["scope"].isin(REGION_ORDER)
        & window_summary["window"].eq("residual_post_recovery")
    ][[
        "scope", "dau_recovery_index", "pu_recovery_index",
        "revenue_recovery_index",
    ]].copy()
    regional_d30 = retention_summary[
        retention_summary["scope"].isin(REGION_ORDER)
        & retention_summary["period"].eq("residual_oct_nov_pooled")
    ][["scope", "d30_change_pp"]]
    regional_exit = regional_exit.merge(
        regional_d30, on="scope", validate="one_to_one",
    ).set_index("scope").loc[REGION_ORDER].reset_index()

    regional_panels = [
        ("dau_recovery_index", "DAU index", 95, (0, 110), "%.1f"),
        ("pu_recovery_index", "Paying-user index", 90, (0, 110), "%.1f"),
        ("revenue_recovery_index", "Revenue index", 90, (0, 110), "%.1f"),
        ("d30_change_pp", "D30 change from June", -.5, (-1.8, .1), "%.2f pp"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    for ax, (metric, title, threshold, ylim, value_format) in zip(
        axes.flat, regional_panels,
    ):
        values = regional_exit[metric]
        bars = ax.bar(
            [REGION_LABELS[region] for region in REGION_ORDER], values,
            color=[REGION_COLORS[region] for region in REGION_ORDER], width=.62,
        )
        ax.axhline(100 if metric != "d30_change_pp" else 0,
                   color="#666666", linewidth=.9)
        ax.axhline(threshold, color="#C44E52", linestyle="--", linewidth=1.2)
        ax.set(title=title, ylim=ylim, xlabel="")
        ax.bar_label(bars, fmt=value_format, padding=3, fontsize=9)
        ax.text(
            .98, .92 if metric == "d30_change_pp" else .06,
            f"Target: {threshold:g}" + (" pp" if metric == "d30_change_pp" else ""),
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8.5,
            color="#A23A3E",
        )
    fig.suptitle(
        "Regional Exit Check: Daily Operations Passed, D30 Did Not", y=.98,
    )
    fig.text(
        .5, .01,
        "Daily indices use Sep 21–30; D30 is pooled across Oct–Nov. October overlaps the regional autumn event.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, .04, 1, .95))
    fig.savefig(image_dir / "incident_regional_exit_guardrails.png", dpi=180)
    plt.close(fig)

    cohort_order = [
        "june_reference", "july_overlap", "august_incident",
        "september_remediation", "october_residual", "november_residual",
    ]
    cohort_plot = retention_summary[
        retention_summary["scope"].isin(REGION_ORDER)
        & retention_summary["period"].isin(cohort_order)
    ].copy()
    cohort_plot["period"] = pd.Categorical(
        cohort_plot["period"], categories=cohort_order, ordered=True
    )
    cohort_plot = cohort_plot.sort_values("period")
    fig, ax = plt.subplots(figsize=(11, 6))
    for region in REGION_ORDER:
        region_data = cohort_plot[cohort_plot["scope"].eq(region)]
        ax.plot(
            region_data["period_label"], region_data["d30_change_pp"],
            color=REGION_COLORS[region], marker="o", linewidth=2,
            label=REGION_LABELS[region],
        )
    ax.axhline(0, color="#666666", linewidth=.9)
    ax.axhline(-.5, color="#C44E52", linestyle="--", linewidth=1.1,
               label="-0.5 pp guardrail")
    ax.set(
        title="D30 Cohort Quality Remained Below the June Reference",
        xlabel="", ylabel="Change from June reference (percentage points)",
    )
    ax.tick_params(axis="x", rotation=12)
    ax.legend(ncol=4, frameon=False)
    fig.text(
        .5, .01,
        "* October overlaps the regional autumn event; July acquisition and observation contexts also overlap later events.",
        ha="center", fontsize=8.5, color="#555555",
    )
    fig.tight_layout(rect=(0, .05, 1, 1))
    fig.savefig(image_dir / "incident_d30_recovery_by_region.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, _, _, _, _ = load_data(root)
    windows = incident_window_summary(daily)
    stages = incident_stage_evaluation(windows)
    retention_results = incident_retention_summary(retention)
    final = incident_final_evaluation(stages, retention_results)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    windows.to_csv(output_dir / "incident_window_summary.csv", index=False)
    stages.to_csv(output_dir / "incident_stage_evaluation.csv", index=False)
    retention_results.to_csv(output_dir / "incident_retention_summary.csv", index=False)
    final.to_csv(output_dir / "incident_final_evaluation.csv", index=False)
    save_incident_charts(daily, windows, retention_results, root / "images")

    stage_columns = [
        "window_label", "service_availability", "dau_recovery_index",
        "pu_recovery_index", "revenue_recovery_index",
        "returned_users_recovery_index", "stage_result",
    ]
    print("Analysis 5 incident outputs created")
    print(stages[stages["scope"].eq("ALL")][stage_columns].round(2).to_string(index=False))
    print("\nFinal recovery evaluation")
    final_columns = [
        "scope", "dau_recovery_index", "pu_recovery_index",
        "revenue_recovery_index", "user_outflow_recovery_index",
        "d30_change_pp", "final_outcome",
    ]
    print(final[final_columns].round(2).to_string(index=False))


if __name__ == "__main__":
    main()
