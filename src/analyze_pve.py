"""Analysis 3: core-content entry and limited-PvE engagement analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, prepare_metrics, project_root, safe_divide
    from src.analyze_lifecycle import lifecycle_event_performance
    from src.analyze_retention import (
        acquisition_quality_comparison,
        retention_monthly_summary,
    )
except ModuleNotFoundError:  # Support `python src/analyze_pve.py`.
    from analyze_game_data import load_data, prepare_metrics, project_root, safe_divide
    from analyze_lifecycle import lifecycle_event_performance
    from analyze_retention import acquisition_quality_comparison, retention_monthly_summary


REGION_ORDER = ["KR", "JP", "GLOBAL_WEST"]
REGION_COLORS = {
    "KR": "#2E8B57",
    "JP": "#E68613",
    "GLOBAL_WEST": "#3478BF",
}
DIFFICULTY_ORDER = ["NORMAL", "HARD", "NIGHTMARE"]
BENCHMARK_BOSS_IDS = ["BOSS001", "BOSS002", "BOSS003"]
PARTICIPATION_INDEX_THRESHOLD = 90.0
CLEAR_RATE_TOLERANCE_PP = 2.0
ATTEMPT_TOLERANCE = 0.10

BOSS_EVENT_MAP = {
    "BOSS001": ("Half-Anniversary Raid", "half_anniversary_2024"),
    "BOSS002": ("Fantasy Saga Crossover", "fantasy_crossover_2024"),
    "BOSS003": ("First Anniversary", "first_anniversary_2025"),
    "BOSS004": ("Astra Heroes Crossover", "astra_crossover_2025"),
}


def prepare_boss_funnel(bosses: pd.DataFrame, daily: pd.DataFrame) -> pd.DataFrame:
    result = bosses.copy()
    result["date"] = pd.to_datetime(result["date"])
    daily_scope = daily[["date", "region", "dau"]].copy()
    daily_scope["date"] = pd.to_datetime(daily_scope["date"])
    result = result.merge(
        daily_scope, on=["date", "region"], how="left", validate="many_to_one"
    )
    if result["dau"].isna().any():
        raise ValueError("boss rows failed to match daily DAU")
    result["participation_rate"] = safe_divide(result["participants"], result["dau"])
    result["clear_rate"] = safe_divide(result["clears"], result["participants"])
    result["attempts_per_participant"] = safe_divide(
        result["attempts"], result["participants"]
    )
    result["clear_yield_per_1000_dau"] = safe_divide(
        result["clears"], result["dau"]
    ) * 1000
    return result


def _aggregate_funnel(frame: pd.DataFrame, grain: list[str]) -> pd.DataFrame:
    result = (
        frame.groupby(grain, as_index=False)
        .agg(
            start_date=("date", "min"),
            end_date=("date", "max"),
            observed_days=("date", "nunique"),
            dau=("dau", "sum"),
            participants=("participants", "sum"),
            attempts=("attempts", "sum"),
            clears=("clears", "sum"),
        )
    )
    result["participation_rate"] = result["participants"] / result["dau"]
    result["clear_rate"] = result["clears"] / result["participants"]
    result["attempts_per_participant"] = result["attempts"] / result["participants"]
    result["clear_yield_per_1000_dau"] = result["clears"] / result["dau"] * 1000
    return result


def boss_performance_summary(funnel: pd.DataFrame) -> pd.DataFrame:
    """Aggregate by boss and difficulty and compare with healthy-content benchmarks."""
    summary = _aggregate_funnel(
        funnel, ["boss_id", "boss_name", "difficulty"]
    )
    benchmark = _aggregate_funnel(
        funnel[funnel["boss_id"].isin(BENCHMARK_BOSS_IDS)], ["difficulty"]
    ).rename(columns={
        "participation_rate": "benchmark_participation_rate",
        "clear_rate": "benchmark_clear_rate",
        "attempts_per_participant": "benchmark_attempts_per_participant",
    })
    keep = [
        "difficulty", "benchmark_participation_rate", "benchmark_clear_rate",
        "benchmark_attempts_per_participant",
    ]
    summary = summary.merge(benchmark[keep], on="difficulty", validate="many_to_one")
    summary["participation_benchmark_index"] = (
        summary["participation_rate"] / summary["benchmark_participation_rate"] * 100
    )
    summary["clear_rate_delta_pp"] = (
        summary["clear_rate"] - summary["benchmark_clear_rate"]
    ) * 100
    summary["attempts_delta"] = (
        summary["attempts_per_participant"]
        - summary["benchmark_attempts_per_participant"]
    )
    summary["participation_result"] = np.where(
        summary["participation_benchmark_index"] >= PARTICIPATION_INDEX_THRESHOLD,
        "Meets benchmark", "Below benchmark",
    )
    summary["clear_rate_result"] = np.where(
        summary["clear_rate_delta_pp"].abs() <= CLEAR_RATE_TOLERANCE_PP,
        "Comparable", "Materially different",
    )
    summary["attempt_burden_result"] = np.where(
        summary["attempts_delta"].abs() <= ATTEMPT_TOLERANCE,
        "Comparable", "Materially different",
    )
    summary["diagnostic_result"] = np.select(
        [
            summary["participation_result"].eq("Below benchmark")
            & summary["clear_rate_result"].eq("Comparable")
            & summary["attempt_burden_result"].eq("Comparable"),
            summary["participation_result"].eq("Below benchmark"),
        ],
        ["Pre-entry / entry gap", "Entry and participant-outcome gap"],
        default="No material entry gap",
    )
    return summary


def boss_regional_summary(funnel: pd.DataFrame) -> pd.DataFrame:
    """Compare each region with its own healthy-content difficulty benchmark."""
    summary = _aggregate_funnel(
        funnel, ["boss_id", "boss_name", "region", "difficulty"]
    )
    benchmark = _aggregate_funnel(
        funnel[funnel["boss_id"].isin(BENCHMARK_BOSS_IDS)],
        ["region", "difficulty"],
    ).rename(columns={
        "participation_rate": "benchmark_participation_rate",
        "clear_rate": "benchmark_clear_rate",
        "attempts_per_participant": "benchmark_attempts_per_participant",
    })
    keep = [
        "region", "difficulty", "benchmark_participation_rate",
        "benchmark_clear_rate", "benchmark_attempts_per_participant",
    ]
    summary = summary.merge(
        benchmark[keep], on=["region", "difficulty"], validate="many_to_one"
    )
    summary["participation_benchmark_index"] = (
        summary["participation_rate"] / summary["benchmark_participation_rate"] * 100
    )
    summary["clear_rate_delta_pp"] = (
        summary["clear_rate"] - summary["benchmark_clear_rate"]
    ) * 100
    summary["attempts_delta"] = (
        summary["attempts_per_participant"]
        - summary["benchmark_attempts_per_participant"]
    )
    return summary


def event_pve_alignment(boss_summary: pd.DataFrame,
                        lifecycle: pd.DataFrame,
                        acquisition: pd.DataFrame) -> pd.DataFrame:
    """Connect event traffic, NORMAL boss entry, and D30 cohort quality."""
    normal = boss_summary[boss_summary["difficulty"].eq("NORMAL")]
    rows: list[dict[str, object]] = []
    for boss_id, (event_name, comparison_id) in BOSS_EVENT_MAP.items():
        boss = normal[normal["boss_id"].eq(boss_id)].iloc[0]
        event = lifecycle[lifecycle["event_name"].eq(event_name)].iloc[0]
        cohort = acquisition[acquisition["comparison_id"].eq(comparison_id)].iloc[0]
        participation_ok = (
            boss["participation_benchmark_index"] >= PARTICIPATION_INDEX_THRESHOLD
        )
        quality_good = cohort["d30_retention_change_pp"] >= 1.0
        quality_failed = cohort["d30_retention_change_pp"] <= -1.0
        if participation_ok and quality_good:
            result = "Entry and retention aligned"
        elif not participation_ok and quality_failed:
            result = "Traffic-to-content disconnect"
        elif participation_ok:
            result = "Mixed: content reach without cohort quality"
        else:
            result = "Mixed: weak content reach"
        rows.append({
            "boss_id": boss_id,
            "boss_name": boss["boss_name"],
            "event_name": event_name,
            "event_dau_change_pct": event["dau_during_change_pct"],
            "normal_participation_rate": boss["participation_rate"],
            "normal_participation_benchmark_rate": boss["benchmark_participation_rate"],
            "normal_participation_benchmark_index": boss["participation_benchmark_index"],
            "normal_clear_rate": boss["clear_rate"],
            "normal_clear_rate_delta_pp": boss["clear_rate_delta_pp"],
            "normal_attempts_per_participant": boss["attempts_per_participant"],
            "d30_retention_change_pp": cohort["d30_retention_change_pp"],
            "d30_retained_gap_at_target_volume": cohort[
                "d30_retained_gap_vs_baseline_quality_at_target_volume"
            ],
            "alignment_result": result,
        })
    return pd.DataFrame(rows)


def save_pve_charts(boss_summary: pd.DataFrame,
                    regional: pd.DataFrame,
                    alignment: pd.DataFrame,
                    image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    astra = (
        boss_summary[boss_summary["boss_id"].eq("BOSS004")]
        .set_index("difficulty")
        .loc[DIFFICULTY_ORDER]
        .reset_index()
    )
    y = np.arange(len(astra))
    fig, axes = plt.subplots(
        1, 3, figsize=(14, 5.8), sharey=True,
        gridspec_kw={"width_ratios": [1.1, 1, 1]},
    )

    entry = axes[0].barh(
        y, astra["participation_benchmark_index"], color="#C44E52",
    )
    axes[0].axvline(
        PARTICIPATION_INDEX_THRESHOLD, color="#C44E52", linestyle="--",
        linewidth=1.5,
    )
    axes[0].axvline(100, color="#555555", linestyle=":", linewidth=1.2)
    axes[0].bar_label(entry, fmt="%.1f", padding=3)
    axes[0].set(
        title="Boss entry",
        xlabel="Participation benchmark index",
        yticks=y,
        yticklabels=astra["difficulty"],
        xlim=(0, 108),
    )

    clear_colors = np.where(
        astra["clear_rate_delta_pp"].abs() <= CLEAR_RATE_TOLERANCE_PP,
        "#55A868", "#C44E52",
    )
    clear_bars = axes[1].barh(y, astra["clear_rate_delta_pp"], color=clear_colors)
    axes[1].axvspan(
        -CLEAR_RATE_TOLERANCE_PP, CLEAR_RATE_TOLERANCE_PP,
        color="#55A868", alpha=.10,
    )
    axes[1].axvline(0, color="#555555", linewidth=.9)
    axes[1].axvline(-CLEAR_RATE_TOLERANCE_PP, color="#777777", linestyle="--")
    axes[1].axvline(CLEAR_RATE_TOLERANCE_PP, color="#777777", linestyle="--")
    axes[1].bar_label(clear_bars, fmt="%+.2f pp", padding=3)
    axes[1].set(
        title="Clear rate after entry",
        xlabel="Change vs benchmark (pp)",
        xlim=(-2.6, 2.6),
    )

    attempt_colors = np.where(
        astra["attempts_delta"].abs() <= ATTEMPT_TOLERANCE,
        "#55A868", "#C44E52",
    )
    axes[2].scatter(
        astra["attempts_delta"], y, color=attempt_colors, s=90, zorder=3,
    )
    axes[2].axvspan(-ATTEMPT_TOLERANCE, ATTEMPT_TOLERANCE,
                    color="#55A868", alpha=.10)
    axes[2].axvline(0, color="#555555", linewidth=.9)
    axes[2].axvline(-ATTEMPT_TOLERANCE, color="#777777", linestyle="--")
    axes[2].axvline(ATTEMPT_TOLERANCE, color="#777777", linestyle="--")
    for y_value, delta in zip(y, astra["attempts_delta"]):
        axes[2].annotate(
            f"{delta:+.3f}", (delta, y_value),
            xytext=(-7 if delta <= 0 else 7, 0), textcoords="offset points",
            ha="right" if delta <= 0 else "left", va="center",
        )
    axes[2].set(
        title="Attempt burden after entry",
        xlabel="Change in attempts per daily participant",
        xlim=(-.125, .125),
    )

    axes[0].invert_yaxis()
    fig.suptitle("Astra PvE Diagnosis: Entry vs Participant Outcomes", y=.99)
    fig.text(
        .5, .015,
        "Entry fails the 90 index threshold; participant outcomes remain within the shaded comparison ranges.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=[0, .05, 1, .94])
    fig.savefig(image_dir / "pve_difficulty_funnel.png", dpi=180)
    plt.close(fig)

    normal_regional = regional[
        regional["difficulty"].eq("NORMAL")
        & regional["boss_id"].eq("BOSS004")
    ].copy()
    normal_regional["region"] = pd.Categorical(
        normal_regional["region"], REGION_ORDER, ordered=True,
    )
    normal_regional = normal_regional.sort_values("region")
    region_labels = {"KR": "KR", "JP": "JP", "GLOBAL_WEST": "Global West"}
    fig, ax = plt.subplots(figsize=(9.5, 5.8))
    region_bars = ax.bar(
        normal_regional["region"].map(region_labels),
        normal_regional["participation_benchmark_index"],
        color=[REGION_COLORS[region] for region in normal_regional["region"]],
        width=.62,
    )
    ax.axhline(PARTICIPATION_INDEX_THRESHOLD, color="#C44E52", linestyle="--",
               linewidth=1.5, label="Minimum index = 90")
    ax.axhline(100, color="#555555", linestyle=":", linewidth=1.2,
               label="Regional benchmark = 100")
    ax.bar_label(region_bars, fmt="%.1f", padding=3)
    ax.set(
        title="Astra NORMAL Boss Entry by Region",
        xlabel="", ylabel="Participation benchmark index", ylim=(0, 108),
    )
    ax.legend(ncol=2, frameon=False, loc="lower center")
    fig.tight_layout()
    fig.savefig(image_dir / "pve_participation_index_by_region.png", dpi=180)
    plt.close(fig)

    plot_alignment = alignment.copy()
    colors = plot_alignment["alignment_result"].map({
        "Entry and retention aligned": "#55A868",
        "Traffic-to-content disconnect": "#C44E52",
        "Mixed: content reach without cohort quality": "#E68613",
        "Mixed: weak content reach": "#8172B2",
    })
    y = np.arange(len(plot_alignment))
    fig, axes = plt.subplots(
        1, 2, figsize=(13, 6.5), sharey=True,
        gridspec_kw={"width_ratios": [1.05, 1]},
    )

    entry = axes[0].barh(
        y, plot_alignment["normal_participation_benchmark_index"], color=colors,
    )
    axes[0].axvline(
        PARTICIPATION_INDEX_THRESHOLD, color="#C44E52", linestyle="--",
    )
    axes[0].axvline(100, color="#555555", linestyle=":")
    axes[0].bar_label(entry, fmt="%.1f", padding=3)
    axes[0].set(
        title="Core boss entry\nMinimum = 90; benchmark = 100",
        xlabel="NORMAL participation benchmark index",
        yticks=y,
        yticklabels=plot_alignment["event_name"].str.replace(" Saga", "", regex=False),
        xlim=(0, 108),
    )

    retention = axes[1].barh(
        y, plot_alignment["d30_retention_change_pp"], color=colors,
    )
    axes[1].axvline(0, color="#555555", linewidth=.8)
    axes[1].axvline(1, color="#3478BF", linestyle="--")
    axes[1].axvline(-1, color="#C44E52", linestyle=":")
    axes[1].bar_label(retention, fmt="%+.1f pp", padding=3)
    axes[1].set(
        title="Long-term cohort quality\n+1 pp = quality threshold; -1 pp = guardrail",
        xlabel="D30 retention change (percentage points)",
        xlim=(-3.2, 4.2),
    )

    axes[0].invert_yaxis()
    fig.suptitle("Event Contexts: NORMAL Boss Entry and D30 Retention", y=.995)
    fig.text(
        .5, .015,
        "The first three bosses define the entry benchmark; Astra is held out. Labels cover entry and D30, not total event success.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=[0, .04, 1, .96])
    fig.savefig(image_dir / "event_pve_alignment.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, events, _, _, bosses = load_data(root)
    daily_metrics, _, _ = prepare_metrics(daily, retention, bosses)
    funnel = prepare_boss_funnel(bosses, daily)
    boss_summary = boss_performance_summary(funnel)
    regional = boss_regional_summary(funnel)
    lifecycle = lifecycle_event_performance(daily_metrics, events)
    monthly = retention_monthly_summary(retention, events)
    acquisition = acquisition_quality_comparison(retention, monthly)
    alignment = event_pve_alignment(boss_summary, lifecycle, acquisition)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    funnel.to_csv(output_dir / "boss_funnel_enriched.csv", index=False)
    boss_summary.to_csv(output_dir / "boss_performance_summary.csv", index=False)
    regional.to_csv(output_dir / "boss_regional_summary.csv", index=False)
    alignment.to_csv(output_dir / "event_pve_alignment.csv", index=False)
    save_pve_charts(boss_summary, regional, alignment, root / "images")

    columns = [
        "event_name", "event_dau_change_pct", "normal_participation_benchmark_index",
        "normal_clear_rate_delta_pp", "d30_retention_change_pp", "alignment_result",
    ]
    print("Analysis 3 PvE outputs created")
    print(alignment[columns].round(2).to_string(index=False))
    astra = boss_summary[boss_summary["boss_id"].eq("BOSS004")][[
        "difficulty", "participation_rate", "participation_benchmark_index",
        "clear_rate", "clear_rate_delta_pp", "attempts_per_participant", "attempts_delta",
    ]]
    print("\nAstra boss funnel")
    print(astra.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
