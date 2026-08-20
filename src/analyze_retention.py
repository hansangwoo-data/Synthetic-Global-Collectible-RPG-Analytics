"""Analysis 2: acquisition quality and cohort-retention analysis."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, project_root, safe_divide
except ModuleNotFoundError:  # Support `python src/analyze_retention.py`.
    from analyze_game_data import load_data, project_root, safe_divide


REGION_ORDER = ["KR", "JP", "GLOBAL_WEST"]
REGION_COLORS = {
    "KR": "#2E8B57",
    "JP": "#E68613",
    "GLOBAL_WEST": "#3478BF",
}

COMPARISONS = [
    {
        "comparison_id": "half_anniversary_2024",
        "label": "Half-Anniversary",
        "target_months": ["2024-06-01"],
        "baseline_months": ["2024-03-01", "2024-04-01", "2024-05-01"],
        "basis": "June launch month vs March–May recent cohorts",
    },
    {
        "comparison_id": "fantasy_crossover_2024",
        "label": "Fantasy Crossover",
        "target_months": ["2024-09-01"],
        "baseline_months": ["2024-07-01", "2024-08-01"],
        "basis": "September event-context cohort vs July–August cohorts",
    },
    {
        "comparison_id": "first_anniversary_2025",
        "label": "First Anniversary",
        "target_months": ["2025-01-01"],
        "baseline_months": ["2024-10-01", "2024-11-01", "2024-12-01"],
        "basis": "January anniversary-context cohort vs October–December cohorts",
    },
    {
        "comparison_id": "astra_crossover_2025",
        "label": "Astra Crossover",
        "target_months": ["2025-07-01"],
        "baseline_months": ["2025-05-01", "2025-06-01"],
        "basis": "July event-context cohort vs May–June cohorts",
    },
]


def add_retention_rates(retention: pd.DataFrame) -> pd.DataFrame:
    result = retention.copy()
    result["cohort_month"] = pd.to_datetime(result["cohort_month"])
    for day in (1, 7, 30):
        result[f"d{day}_retention"] = safe_divide(
            result[f"d{day}_retained"], result["cohort_size"]
        )
    return result


def _event_context(events: pd.DataFrame, month: pd.Timestamp,
                   regions: list[str]) -> tuple[str, str]:
    month_end = month + pd.offsets.MonthEnd(0)
    overlap = events[
        events["region"].isin(regions)
        & events["start_date"].le(month_end)
        & events["end_date"].ge(month)
    ]
    names = sorted(overlap["event_name"].unique().tolist())
    types = sorted(overlap["event_type"].unique().tolist())
    return " | ".join(names), " | ".join(types)


def retention_monthly_summary(retention: pd.DataFrame,
                              events: pd.DataFrame) -> pd.DataFrame:
    """Aggregate retained counts and recompute rates at region and global scope."""
    retention = add_retention_rates(retention)
    events = events.copy()
    events[["start_date", "end_date"]] = events[["start_date", "end_date"]].apply(
        pd.to_datetime
    )
    rows: list[dict[str, object]] = []
    scopes = [(r, [r]) for r in REGION_ORDER] + [("ALL", REGION_ORDER)]
    for scope, regions in scopes:
        scoped = retention[retention["region"].isin(regions)]
        for month, month_frame in scoped.groupby("cohort_month", sort=True):
            names, types = _event_context(events, month, regions)
            row: dict[str, object] = {
                "cohort_month": month,
                "scope": scope,
                "event_context": names,
                "event_types": types,
                "cohort_size": int(month_frame["cohort_size"].sum()),
            }
            for day in (1, 7, 30):
                retained = int(month_frame[f"d{day}_retained"].sum())
                row[f"d{day}_retained"] = retained
                row[f"d{day}_retention"] = retained / row["cohort_size"]
            row["d30_retained_per_1000"] = row["d30_retention"] * 1000
            rows.append(row)
    result = pd.DataFrame(rows).sort_values(["scope", "cohort_month"])
    first_size = result.groupby("scope")["cohort_size"].transform("first")
    result["cohort_size_index"] = result["cohort_size"] / first_size * 100
    result["cohort_size_mom_change_pct"] = (
        result.groupby("scope")["cohort_size"].pct_change() * 100
    )
    return result


def _pooled_retention(frame: pd.DataFrame) -> dict[str, float]:
    values: dict[str, float] = {
        "months": float(frame["cohort_month"].nunique()),
        "cohort_size": float(frame["cohort_size"].sum()),
    }
    for day in (1, 7, 30):
        retained = float(frame[f"d{day}_retained"].sum())
        values[f"d{day}_retained"] = retained
        values[f"d{day}_retention"] = retained / values["cohort_size"]
    return values


def acquisition_quality_comparison(retention: pd.DataFrame,
                                   monthly: pd.DataFrame) -> pd.DataFrame:
    """Evaluate volume and retention quality for selected campaign-context cohorts."""
    retention = add_retention_rates(retention)
    global_monthly = monthly[monthly["scope"].eq("ALL")].copy()
    rows: list[dict[str, object]] = []
    for spec in COMPARISONS:
        target_months = pd.to_datetime(spec["target_months"])
        baseline_months = pd.to_datetime(spec["baseline_months"])
        target = retention[retention["cohort_month"].isin(target_months)]
        baseline = retention[retention["cohort_month"].isin(baseline_months)]
        if target.empty or baseline.empty:
            raise ValueError(f"missing cohort months for {spec['comparison_id']}")
        target_stats, baseline_stats = _pooled_retention(target), _pooled_retention(baseline)
        target_monthly_avg = target_stats["cohort_size"] / target_stats["months"]
        baseline_monthly_avg = baseline_stats["cohort_size"] / baseline_stats["months"]
        volume_change = (target_monthly_avg / baseline_monthly_avg - 1) * 100

        baseline_month_rows = global_monthly[
            global_monthly["cohort_month"].isin(baseline_months)
        ]
        baseline_d30_std_pp = float(
            baseline_month_rows["d30_retention"].std(ddof=1) * 100
        ) if len(baseline_month_rows) > 1 else 0.0
        d30_effective_threshold_pp = max(1.0, baseline_d30_std_pp)
        d30_change_pp = (
            target_stats["d30_retention"] - baseline_stats["d30_retention"]
        ) * 100
        volume_pass = volume_change >= 15.0
        quality_pass = d30_change_pp >= d30_effective_threshold_pp
        quality_guardrail_failed = d30_change_pp <= -1.0

        if volume_pass and quality_pass:
            outcome = "Successful"
        elif volume_pass and quality_guardrail_failed:
            outcome = "Mixed: volume-quality trade-off"
        elif quality_pass and not volume_pass:
            outcome = "Mixed: quality gain without volume lift"
        elif volume_pass or quality_pass:
            outcome = "Mixed"
        else:
            outcome = "Underperforming"

        baseline_d30_monthly_avg = (
            baseline_stats["d30_retained"] / baseline_stats["months"]
        )
        target_d30_monthly_avg = target_stats["d30_retained"] / target_stats["months"]
        expected_d30_at_target_volume = (
            target_monthly_avg * baseline_stats["d30_retention"]
        )
        target_context_series = global_monthly[
            global_monthly["cohort_month"].isin(target_months)
        ]["event_context"]
        target_context = target_context_series[
            target_context_series.ne("")
        ].unique().tolist()
        baseline_context_series = baseline_month_rows["event_context"]
        baseline_context = baseline_context_series[
            baseline_context_series.ne("")
        ].unique().tolist()
        row: dict[str, object] = {
            "comparison_id": spec["comparison_id"],
            "comparison_label": spec["label"],
            "comparison_basis": spec["basis"],
            "target_months": " | ".join(pd.Index(target_months).strftime("%Y-%m")),
            "baseline_months": " | ".join(pd.Index(baseline_months).strftime("%Y-%m")),
            "target_event_context": " || ".join(target_context),
            "baseline_event_context": " || ".join(baseline_context),
            "target_cohort_size_monthly_avg": target_monthly_avg,
            "baseline_cohort_size_monthly_avg": baseline_monthly_avg,
            "cohort_size_change_pct": volume_change,
            "volume_threshold_pct": 15.0,
            "volume_pass": volume_pass,
            "d30_baseline_variability_pp": baseline_d30_std_pp,
            "d30_effective_threshold_pp": d30_effective_threshold_pp,
            "d30_quality_guardrail_failed": quality_guardrail_failed,
            "baseline_d30_retained_monthly_avg": baseline_d30_monthly_avg,
            "target_d30_retained_monthly_avg": target_d30_monthly_avg,
            "expected_d30_retained_at_target_volume_and_baseline_quality": (
                expected_d30_at_target_volume
            ),
            "d30_retained_change_vs_reference_month": (
                target_d30_monthly_avg - baseline_d30_monthly_avg
            ),
            "d30_retained_volume_component_at_baseline_quality": (
                expected_d30_at_target_volume - baseline_d30_monthly_avg
            ),
            "d30_retained_gap_vs_baseline_quality_at_target_volume": (
                target_d30_monthly_avg - expected_d30_at_target_volume
            ),
            "outcome": outcome,
        }
        for day in (1, 7, 30):
            row[f"d{day}_retention_baseline"] = baseline_stats[f"d{day}_retention"]
            row[f"d{day}_retention_target"] = target_stats[f"d{day}_retention"]
            row[f"d{day}_retention_change_pp"] = (
                target_stats[f"d{day}_retention"]
                - baseline_stats[f"d{day}_retention"]
            ) * 100
        rows.append(row)
    return pd.DataFrame(rows)


def regional_quality_summary(monthly: pd.DataFrame,
                             comparison_id: str) -> pd.DataFrame:
    """Return regional baseline and target D30 for a configured comparison."""
    spec = next(item for item in COMPARISONS if item["comparison_id"] == comparison_id)
    target_months = pd.to_datetime(spec["target_months"])
    baseline_months = pd.to_datetime(spec["baseline_months"])
    rows: list[dict[str, object]] = []
    for region in REGION_ORDER:
        frame = monthly[monthly["scope"].eq(region)]
        target = frame[frame["cohort_month"].isin(target_months)]
        baseline = frame[frame["cohort_month"].isin(baseline_months)]
        target_rate = target["d30_retained"].sum() / target["cohort_size"].sum()
        baseline_rate = baseline["d30_retained"].sum() / baseline["cohort_size"].sum()
        rows.append({
            "comparison_id": comparison_id,
            "comparison_label": spec["label"],
            "region": region,
            "d30_retention_baseline": baseline_rate,
            "d30_retention_target": target_rate,
            "d30_retention_change_pp": (target_rate - baseline_rate) * 100,
        })
    return pd.DataFrame(rows)


def save_retention_charts(monthly: pd.DataFrame, comparisons: pd.DataFrame,
                          image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    regional = monthly[monthly["scope"].isin(REGION_ORDER)]

    fig, ax = plt.subplots(figsize=(12, 5.8))
    region_labels = {"KR": "KR", "JP": "JP", "GLOBAL_WEST": "Global West"}
    for region in REGION_ORDER:
        frame = regional[regional["scope"].eq(region)]
        ax.plot(frame["cohort_month"], frame["d30_retention"] * 100,
                marker="o", markersize=4, linewidth=1.9,
                color=REGION_COLORS[region], label=region_labels[region])
    markers = [
        (pd.Timestamp("2024-09-01"), "Fantasy", "#4C7A57"),
        (pd.Timestamp("2025-07-01"), "Astra", "#B56A00"),
        (pd.Timestamp("2025-08-01"), "Incident", "#A33A3A"),
    ]
    for month, label, color in markers:
        ax.axvline(month, color=color, linestyle="--", linewidth=1, alpha=.75)
        ax.text(month, .98, label, transform=ax.get_xaxis_transform(), rotation=90,
                va="top", ha="right", fontsize=8, color=color)
    ax.set(
        title="Regional D30 Cohort Retention Trend",
        xlabel="Cohort month",
        ylabel="D30 retention (%)",
    )
    ax.legend(ncol=3, frameon=False)
    fig.tight_layout()
    fig.savefig(image_dir / "retention_trend_by_region.png", dpi=180)
    plt.close(fig)

    colors = comparisons["outcome"].map({
        "Successful": "#55A868",
        "Mixed: volume-quality trade-off": "#E68613",
        "Mixed: quality gain without volume lift": "#8172B2",
        "Mixed": "#CCB974",
        "Underperforming": "#C44E52",
    })
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(comparisons["cohort_size_change_pct"],
               comparisons["d30_retention_change_pp"],
               s=650, c=colors, edgecolor="white", linewidth=1.2)
    chart_labels = {
        "Half-Anniversary": "Half-Anniversary\nQuality gain only",
        "Fantasy Crossover": "Fantasy Crossover\nVolume + quality",
        "First Anniversary": "First Anniversary\nVolume + quality",
        "Astra Crossover": "Astra Crossover\nVolume–quality trade-off",
    }
    for _, row in comparisons.iterrows():
        right_side = row["cohort_size_change_pct"] >= 90
        ax.annotate(chart_labels[row["comparison_label"]],
                    (row["cohort_size_change_pct"], row["d30_retention_change_pp"]),
                    xytext=(-7 if right_side else 7, 7), textcoords="offset points",
                    ha="right" if right_side else "left", fontsize=8.5)
    ax.axvline(15, color="#555555", linestyle="--", linewidth=1,
               label="Volume threshold (+15%)")
    ax.axhline(1, color="#3478BF", linestyle="--", linewidth=1,
               label="D30 quality threshold (+1 pp)")
    ax.axhline(-1, color="#C44E52", linestyle=":", linewidth=1,
               label="D30 guardrail (-1 pp)")
    ax.set(title="Campaign Cohorts: Acquisition Volume vs D30 Quality",
           xlabel="Monthly cohort-size change from baseline (%)",
           ylabel="D30 retention change (percentage points)",
           xlim=(-5, 105), ylim=(-3, 3.8))
    ax.legend(frameon=False, loc="lower left")
    fig.tight_layout()
    fig.savefig(image_dir / "acquisition_quality_matrix.png", dpi=180)
    plt.close(fig)

    collaboration_ids = ["fantasy_crossover_2024", "astra_crossover_2025"]
    plot = comparisons[comparisons["comparison_id"].isin(collaboration_ids)].copy()
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    x = np.arange(3)
    width = .36
    fantasy = plot[plot["comparison_id"].eq("fantasy_crossover_2024")].iloc[0]
    astra = plot[plot["comparison_id"].eq("astra_crossover_2025")].iloc[0]
    fantasy_change = [fantasy[f"d{day}_retention_change_pp"] for day in (1, 7, 30)]
    astra_change = [astra[f"d{day}_retention_change_pp"] for day in (1, 7, 30)]
    fantasy_bars = ax.bar(
        x - width / 2, fantasy_change, width,
        label="Fantasy Crossover", color="#55A868",
    )
    astra_bars = ax.bar(
        x + width / 2, astra_change, width,
        label="Astra Crossover", color="#E68613",
    )
    for bars in (fantasy_bars, astra_bars):
        ax.bar_label(bars, labels=[f"{value:+.2f} pp" for value in bars.datavalues],
                     padding=3, fontsize=8)
    ax.axhline(0, color="#444444", linewidth=.9)
    ax.set(
        title="Collaboration Cohorts: Retention Change vs Reference",
        xlabel="Retention checkpoint",
        ylabel="Change from reference cohorts (percentage points)",
        xticks=x,
        xticklabels=["D1", "D7", "D30"],
        ylim=(-3.5, 6.5),
    )
    ax.legend(frameon=False, ncol=2)
    fig.tight_layout()
    fig.savefig(image_dir / "collaboration_retention_comparison.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    _, retention, events, _, _, _ = load_data(root)
    monthly = retention_monthly_summary(retention, events)
    comparisons = acquisition_quality_comparison(retention, monthly)
    regional = pd.concat([
        regional_quality_summary(monthly, "fantasy_crossover_2024"),
        regional_quality_summary(monthly, "astra_crossover_2025"),
    ], ignore_index=True)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    monthly.to_csv(output_dir / "retention_monthly_summary.csv", index=False)
    comparisons.to_csv(output_dir / "acquisition_quality_comparison.csv", index=False)
    regional.to_csv(output_dir / "collaboration_regional_quality.csv", index=False)
    save_retention_charts(monthly, comparisons, root / "images")

    columns = ["comparison_label", "cohort_size_change_pct",
               "d1_retention_change_pp", "d7_retention_change_pp",
               "d30_retention_change_pp",
               "d30_retained_gap_vs_baseline_quality_at_target_volume", "outcome"]
    print("Analysis 2 retention outputs created")
    print(comparisons[columns].round(2).to_string(index=False))
    print("\nCollaboration D30 change by region")
    print(regional.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
