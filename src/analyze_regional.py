"""Analysis 6: cross-analysis regional strategy synthesis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, prepare_metrics, project_root
    from src.analyze_incident import (
        incident_final_evaluation,
        incident_retention_summary,
        incident_stage_evaluation,
        incident_window_summary,
    )
    from src.analyze_lifecycle import event_dependency_summary
    from src.analyze_monetization import (
        bm_evaluation_summary,
        monetization_window_summary,
        prepare_sales,
    )
    from src.analyze_pve import boss_regional_summary, prepare_boss_funnel
    from src.analyze_retention import regional_quality_summary, retention_monthly_summary
except ModuleNotFoundError:  # Support `python src/analyze_regional.py`.
    from analyze_game_data import load_data, prepare_metrics, project_root
    from analyze_incident import (
        incident_final_evaluation,
        incident_retention_summary,
        incident_stage_evaluation,
        incident_window_summary,
    )
    from analyze_lifecycle import event_dependency_summary
    from analyze_monetization import (
        bm_evaluation_summary,
        monetization_window_summary,
        prepare_sales,
    )
    from analyze_pve import boss_regional_summary, prepare_boss_funnel
    from analyze_retention import regional_quality_summary, retention_monthly_summary


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


def regional_evidence_summary(dependency: pd.DataFrame,
                              collaboration: pd.DataFrame,
                              boss_regional: pd.DataFrame,
                              bm_evaluation: pd.DataFrame,
                              incident_evaluation: pd.DataFrame) -> pd.DataFrame:
    """Join comparable regional evidence from Analyses 1 through 5."""
    liveops = dependency[
        dependency["year"].eq(2025) & dependency["scope"].isin(REGION_ORDER)
    ][[
        "scope", "liveops_revenue_share", "revenue_share_overindex",
        "liveops_vs_quiet_revenue_mean_pct",
    ]].rename(columns={
        "scope": "region",
        "liveops_revenue_share": "liveops_revenue_share_2025",
        "revenue_share_overindex": "liveops_revenue_overindex_2025",
        "liveops_vs_quiet_revenue_mean_pct": "liveops_vs_quiet_revenue_change_pct_2025",
    })

    fantasy = collaboration[
        collaboration["comparison_id"].eq("fantasy_crossover_2024")
    ][["region", "d30_retention_change_pp"]].rename(columns={
        "d30_retention_change_pp": "fantasy_d30_change_pp",
    })
    astra = collaboration[
        collaboration["comparison_id"].eq("astra_crossover_2025")
    ][["region", "d30_retention_change_pp"]].rename(columns={
        "d30_retention_change_pp": "astra_d30_change_pp",
    })

    astra_entry = boss_regional[
        boss_regional["boss_id"].eq("BOSS004")
        & boss_regional["difficulty"].eq("NORMAL")
    ][["region", "participation_benchmark_index"]].rename(columns={
        "participation_benchmark_index": "astra_normal_participation_index",
    })

    bm = bm_evaluation[bm_evaluation["scope"].isin(REGION_ORDER)][[
        "scope", "launch_revenue_per_day_change_pct",
        "launch_pu_per_day_change_pct",
        "adjacent_launch_revenue_per_payer_day_change_pct",
        "adjacent_post_14_revenue_per_payer_day_change_pct",
        "d30_change_pp",
    ]].rename(columns={
        "scope": "region",
        "launch_revenue_per_day_change_pct": "bm_launch_revenue_change_pct",
        "launch_pu_per_day_change_pct": "bm_launch_pu_change_pct",
        "adjacent_launch_revenue_per_payer_day_change_pct": (
            "bm_adjacent_launch_change_pct"
        ),
        "adjacent_post_14_revenue_per_payer_day_change_pct": (
            "bm_adjacent_post_14_change_pct"
        ),
        "d30_change_pp": "bm_d30_change_pp",
    })

    incident = incident_evaluation[
        incident_evaluation["scope"].isin(REGION_ORDER)
    ][[
        "scope", "nru_recovery_index", "dau_recovery_index",
        "pu_recovery_index", "revenue_recovery_index",
        "user_outflow_recovery_index", "d30_change_pp",
        "operational_thresholds_met",
    ]].rename(columns={
        "scope": "region",
        "nru_recovery_index": "incident_nru_recovery_index",
        "dau_recovery_index": "incident_dau_recovery_index",
        "pu_recovery_index": "incident_pu_recovery_index",
        "revenue_recovery_index": "incident_revenue_recovery_index",
        "user_outflow_recovery_index": "incident_outflow_recovery_index",
        "d30_change_pp": "incident_d30_change_pp",
        "operational_thresholds_met": "incident_operational_thresholds_met",
    })

    result = liveops.merge(fantasy, on="region", validate="one_to_one")
    for frame in [astra, astra_entry, bm, incident]:
        result = result.merge(frame, on="region", validate="one_to_one")
    order = {region: index for index, region in enumerate(REGION_ORDER)}
    result["region_order"] = result["region"].map(order)
    return result.sort_values("region_order").reset_index(drop=True)


def regional_guardrail_matrix(evidence: pd.DataFrame) -> pd.DataFrame:
    """Evaluate shared thresholds without inventing a composite regional score."""
    rules = [
        ("astra_d30", "Astra D30 quality", "astra_d30_change_pp", -1.0, "{:.2f} pp"),
        ("astra_entry", "Astra NORMAL entry", "astra_normal_participation_index", 90.0, "{:.2f}"),
        ("bm_launch", "Launch adjacent-product change", "bm_adjacent_launch_change_pct", -5.0, "{:.2f}%"),
        ("bm_post_14", "Post-launch adjacent-product change", "bm_adjacent_post_14_change_pct", -5.0, "{:.2f}%"),
        ("incident_d30", "Post-recovery D30", "incident_d30_change_pp", -.5, "{:.2f} pp"),
    ]
    rows: list[dict[str, object]] = []
    for order, (guardrail_id, label, column, threshold, value_format) in enumerate(rules):
        for _, region_row in evidence.iterrows():
            value = float(region_row[column])
            passed = value >= threshold
            rows.append({
                "guardrail_id": guardrail_id,
                "guardrail_label": label,
                "guardrail_order": order,
                "region": region_row["region"],
                "value": value,
                "minimum_pass_value": threshold,
                "status": "Pass" if passed else "Warning",
                "status_score": int(passed),
                "display_value": value_format.format(value),
            })

    operational_order = len(rules)
    for _, region_row in evidence.iterrows():
        passed = bool(region_row["incident_operational_thresholds_met"])
        rows.append({
            "guardrail_id": "incident_operations",
            "guardrail_label": "Post-incident daily operations",
            "guardrail_order": operational_order,
            "region": region_row["region"],
            "value": int(passed),
            "minimum_pass_value": 1,
            "status": "Pass" if passed else "Warning",
            "status_score": int(passed),
            "display_value": "All 3 pass" if passed else "At least 1 fails",
        })
    result = pd.DataFrame(rows)
    region_order = {region: index for index, region in enumerate(REGION_ORDER)}
    result["region_order"] = result["region"].map(region_order)
    return result.sort_values(["guardrail_order", "region_order"]).reset_index(drop=True)


def regional_action_plan(evidence: pd.DataFrame) -> pd.DataFrame:
    """Create shared and regional priorities linked to observed evidence."""
    by_region = evidence.set_index("region")
    rows = [
        {
            "scope": "ALL",
            "priority": "P0-1",
            "theme": "Event-to-core bridge",
            "action": "Instrument and repair exposure → eligibility → first-attempt flow.",
            "evidence": (
                "Astra NORMAL entry is 81.29–82.97 of benchmark and D30 is "
                "-2.13 to -2.58 pp in every region."
            ),
        },
        {
            "scope": "ALL",
            "priority": "P0-2",
            "theme": "Recurring-offer protection",
            "action": "Separate PvE-subscription value from adjacent recurring offers.",
            "evidence": (
                "Post-14 adjacent revenue per service payer-day is -8.01% to -9.89% "
                "in every region."
            ),
        },
        {
            "scope": "ALL",
            "priority": "P0-3",
            "theme": "Incident exit criteria",
            "action": "Keep recovery open until daily and mature-cohort guardrails pass.",
            "evidence": (
                "Daily operational thresholds recover everywhere, but post-recovery "
                "D30 remains -0.67 to -1.58 pp."
            ),
        },
        {
            "scope": "KR",
            "priority": "P1",
            "theme": "Acquisition recovery",
            "action": "Restore qualified acquisition before adding broader traffic spend.",
            "evidence": (
                f"Post-recovery NRU index is {by_region.loc['KR', 'incident_nru_recovery_index']:.2f}, "
                "the weakest regional result and 13.80% below its baseline."
            ),
        },
        {
            "scope": "KR",
            "priority": "P2",
            "theme": "Delayed offer overlap",
            "action": "Monitor renewal timing and reduce delayed recurring-offer overlap.",
            "evidence": (
                f"Subscription adjacency moves from {by_region.loc['KR', 'bm_adjacent_launch_change_pct']:.2f}% "
                f"at launch to {by_region.loc['KR', 'bm_adjacent_post_14_change_pct']:.2f}% post-14."
            ),
        },
        {
            "scope": "JP",
            "priority": "P1",
            "theme": "Immediate offer-positioning warning",
            "action": "Test differentiated benefits and launch messaging for recurring payers.",
            "evidence": (
                f"Launch adjacency is {by_region.loc['JP', 'bm_adjacent_launch_change_pct']:.2f}%, "
                "the only immediate regional warning."
            ),
        },
        {
            "scope": "JP",
            "priority": "P2",
            "theme": "Post-incident durability",
            "action": "Pair payer recovery with cohort and outflow follow-up.",
            "evidence": (
                f"Post-recovery D30 is {by_region.loc['JP', 'incident_d30_change_pp']:.2f} pp "
                f"and outflow index is {by_region.loc['JP', 'incident_outflow_recovery_index']:.2f}."
            ),
        },
        {
            "scope": "GLOBAL_WEST",
            "priority": "P1",
            "theme": "Quality before more scale",
            "action": "Gate acquisition expansion on D30 and core-content entry quality.",
            "evidence": (
                f"Launch-period daily revenue grows {by_region.loc['GLOBAL_WEST', 'bm_launch_revenue_change_pct']:.2f}%, "
                f"but Astra D30 is {by_region.loc['GLOBAL_WEST', 'astra_d30_change_pp']:.2f} pp "
                f"and post-recovery D30 is {by_region.loc['GLOBAL_WEST', 'incident_d30_change_pp']:.2f} pp."
            ),
        },
        {
            "scope": "GLOBAL_WEST",
            "priority": "P2",
            "theme": "Live-ops revenue dependence",
            "action": "Build durable quiet-period value and monitor event-to-quiet decay.",
            "evidence": (
                f"2025 live-ops revenue share is "
                f"{by_region.loc['GLOBAL_WEST', 'liveops_revenue_share_2025']:.1%}, "
                "the highest regional share."
            ),
        },
    ]
    return pd.DataFrame(rows)


def save_regional_charts(evidence: pd.DataFrame,
                         guardrails: pd.DataFrame,
                         image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    ordered = evidence.set_index("region").loc[REGION_ORDER]
    plots = [
        ("liveops_revenue_share_2025", "2025 live-ops revenue share", None, 100,
         "Revenue share (%)"),
        ("astra_d30_change_pp", "Astra D30 change", -1, 1,
         "Change (percentage points)"),
        ("astra_normal_participation_index", "Astra NORMAL entry index", 90, 1,
         "Benchmark index"),
        ("bm_launch_revenue_change_pct", "Launch-period daily revenue growth", 10, 1,
         "Change (%)"),
        ("bm_adjacent_post_14_change_pct", "Post-launch adjacent-product change", -5, 1,
         "Change (%)"),
        ("incident_d30_change_pp", "Post-recovery D30", -.5, 1,
         "Change (percentage points)"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    for ax, (column, title, threshold, scale, ylabel) in zip(axes.flat, plots):
        values = ordered[column] * scale
        bars = ax.bar(
            [REGION_LABELS[region] for region in REGION_ORDER], values,
            color=[REGION_COLORS[region] for region in REGION_ORDER],
        )
        if threshold is not None:
            ax.axhline(threshold, color="#C44E52", linestyle="--", linewidth=1.1)
        if values.min() < 0:
            ax.axhline(0, color="#666666", linewidth=.8)
        labels = [f"{value:.1f}" for value in values]
        ax.bar_label(bars, labels=labels, padding=3, fontsize=9)
        ax.set(title=title, ylabel=ylabel)
        if threshold is not None:
            unit = " pp" if "percentage points" in ylabel else "%" if "%" in ylabel else ""
            ax.text(
                .98, .92 if values.min() < 0 else .04,
                f"Threshold: {threshold:g}{unit}", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=8, color="#A23A3E",
            )
    fig.suptitle("Regional Scale Signals and Quality Guardrails", y=.99)
    fig.text(
        .5, .01,
        "Panels preserve original units; dashed red lines are metric-specific rules. Live-ops revenue share is diagnostic only.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, .035, 1, .96))
    fig.savefig(image_dir / "regional_cross_analysis_evidence.png", dpi=180)
    plt.close(fig)

    matrix = guardrails.pivot(
        index="guardrail_label", columns="region", values="status_score"
    ).loc[
        guardrails.sort_values("guardrail_order")["guardrail_label"].unique(),
        REGION_ORDER,
    ]
    values = guardrails.pivot(
        index="guardrail_label", columns="region", values="display_value"
    ).loc[matrix.index, REGION_ORDER]
    statuses = guardrails.pivot(
        index="guardrail_label", columns="region", values="status"
    ).loc[matrix.index, REGION_ORDER]
    annotations = statuses + "\n" + values
    matrix.columns = [REGION_LABELS[region] for region in matrix.columns]
    annotations.columns = matrix.columns
    fig, ax = plt.subplots(figsize=(10, 6.5))
    sns.heatmap(
        matrix, annot=annotations, fmt="", cmap=ListedColormap(["#E7A0A0", "#9FD3B0"]),
        vmin=0, vmax=1, cbar=False, linewidths=1, linecolor="white", ax=ax,
    )
    ax.set(
        title="Shared Warnings and the JP-Specific Launch Signal",
        xlabel="Region", ylabel="",
    )
    fig.text(
        .5, .01,
        "Colors show pass/warning status; labels retain the original metric value or operational result.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=(0, .04, 1, 1))
    fig.savefig(image_dir / "regional_guardrail_matrix.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, events, products, sales, bosses = load_data(root)
    daily_metrics, _, _ = prepare_metrics(daily, retention, bosses)

    dependency = event_dependency_summary(daily_metrics)
    retention_monthly = retention_monthly_summary(retention, events)
    collaboration = pd.concat([
        regional_quality_summary(retention_monthly, "fantasy_crossover_2024"),
        regional_quality_summary(retention_monthly, "astra_crossover_2025"),
    ], ignore_index=True)
    boss_funnel = prepare_boss_funnel(bosses, daily)
    boss_regional = boss_regional_summary(boss_funnel)
    sales_enriched = prepare_sales(sales, products)
    monetization_windows = monetization_window_summary(daily, sales_enriched)
    bm_evaluation = bm_evaluation_summary(monetization_windows, retention)
    incident_windows = incident_window_summary(daily)
    incident_stages = incident_stage_evaluation(incident_windows)
    incident_retention = incident_retention_summary(retention)
    incident_evaluation = incident_final_evaluation(
        incident_stages, incident_retention
    )

    evidence = regional_evidence_summary(
        dependency, collaboration, boss_regional, bm_evaluation,
        incident_evaluation,
    )
    guardrails = regional_guardrail_matrix(evidence)
    actions = regional_action_plan(evidence)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    evidence.to_csv(output_dir / "regional_evidence_summary.csv", index=False)
    guardrails.to_csv(output_dir / "regional_guardrail_matrix.csv", index=False)
    actions.to_csv(output_dir / "regional_action_plan.csv", index=False)
    save_regional_charts(evidence, guardrails, root / "images")

    print("Analysis 6 regional synthesis outputs created")
    print(evidence.round(2).to_string(index=False))
    print("\nRegional guardrails")
    print(guardrails.pivot(
        index="guardrail_label", columns="region", values="status"
    )[REGION_ORDER].to_string())
    print("\nAction plan")
    print(actions[["scope", "priority", "theme"]].to_string(index=False))


if __name__ == "__main__":
    main()
