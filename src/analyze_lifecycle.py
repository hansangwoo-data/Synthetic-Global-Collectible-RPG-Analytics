"""Analysis 1: service lifecycle and live-ops event dependence."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np
import pandas as pd
import seaborn as sns

try:
    from src.analyze_game_data import load_data, prepare_metrics, project_root, safe_divide
except ModuleNotFoundError:  # Support `python src/analyze_lifecycle.py`.
    from analyze_game_data import load_data, prepare_metrics, project_root, safe_divide


REGION_ORDER = ["KR", "JP", "GLOBAL_WEST"]
REGION_COLORS = {
    "KR": "#2E8B57",
    "JP": "#E68613",
    "GLOBAL_WEST": "#3478BF",
}
COUNT_METRICS = ["dau", "nru", "returned_users", "user_outflow", "pu", "revenue"]
LIVEOPS_TYPES = {
    "milestone", "regional", "collaboration", "seasonal", "anniversary", "bm_launch"
}

PHASES = [
    ("2024 launch", "2024-01-01", "2024-01-21"),
    ("2024 stabilization", "2024-01-22", "2024-06-25"),
    ("2024 H2 event growth", "2024-06-26", "2024-12-31"),
    ("2025 anniversary peak", "2025-01-01", "2025-02-28"),
    ("2025 content gap", "2025-03-01", "2025-04-30"),
    ("2025 monetization and collaboration", "2025-05-01", "2025-08-11"),
    ("2025 incident and recovery", "2025-08-12", "2025-09-20"),
    ("2025 post-recovery", "2025-09-21", "2025-12-31"),
]


def aggregate_scope(daily: pd.DataFrame, regions: list[str]) -> pd.DataFrame:
    """Aggregate regional counts by date and recompute rates from their components."""
    frame = (
        daily[daily["region"].isin(regions)]
        .groupby("date", as_index=False)[COUNT_METRICS]
        .sum()
        .sort_values("date")
    )
    frame["conversion_rate"] = safe_divide(frame["pu"], frame["dau"])
    frame["arpu"] = safe_divide(frame["revenue"], frame["dau"])
    frame["arppu"] = safe_divide(frame["revenue"], frame["pu"])
    prior_dau = frame["dau"].replace(0, np.nan).ffill().shift(1)
    frame["outflow_rate"] = safe_divide(frame["user_outflow"], prior_dau)
    return frame


def _window_stats(frame: pd.DataFrame, start: pd.Timestamp,
                  end: pd.Timestamp) -> dict[str, float]:
    window = frame[frame["date"].between(start, end)]
    values: dict[str, float] = {"days": float(window["date"].nunique())}
    for metric in [*COUNT_METRICS, "conversion_rate", "arpu", "arppu", "outflow_rate"]:
        values[metric] = float(window[metric].mean()) if not window.empty else np.nan
    return values


def _overlaps(events: pd.DataFrame, event_id: str, regions: list[str],
              start: pd.Timestamp, end: pd.Timestamp) -> list[str]:
    overlap = events[
        events["region"].isin(regions)
        & events["event_id"].ne(event_id)
        & events["start_date"].le(end)
        & events["end_date"].ge(start)
    ]
    return sorted(overlap["event_name"].unique().tolist())


def _change_pct(current: float, baseline: float) -> float:
    if pd.isna(current) or pd.isna(baseline) or baseline == 0:
        return np.nan
    return (current / baseline - 1) * 100


def _thresholds(event_type: str) -> dict[str, float]:
    if event_type in {"milestone", "anniversary", "collaboration"}:
        return {"dau": 10, "revenue": 15, "nru_or_returned": 15}
    if event_type in {"seasonal", "regional"}:
        return {"dau": 5, "revenue": 10}
    if event_type == "bm_launch":
        return {"revenue": 10, "pu": 5}
    return {}


def _dau_practical_threshold(event_type: str) -> float | None:
    """Return the DAU floor required before persistence can be classified."""
    if event_type in {"milestone", "anniversary", "collaboration", "bm_launch"}:
        return 10
    if event_type in {"seasonal", "regional"}:
        return 5
    return None


def _has_material_dau_lift(row: dict[str, object]) -> bool:
    practical = _dau_practical_threshold(str(row["event_type"]))
    if practical is None:
        return False
    lift = float(row.get("dau_during_change_pct", np.nan))
    variability = float(row.get("dau_baseline_cv_pct", np.nan))
    effective_floor = max(practical, 0 if pd.isna(variability) else variability)
    return not pd.isna(lift) and lift >= effective_floor


def _evaluate_immediate(row: dict[str, object]) -> str:
    event_type = str(row["event_type"])
    thresholds = _thresholds(event_type)
    if not thresholds:
        if event_type == "launch":
            return "Not evaluable: no pre-launch baseline"
        if event_type in {"incident", "incident_response", "recovery"}:
            return "Deferred to incident analysis"
        return "Context only"

    def passes(metric: str, practical: float) -> bool:
        lift = float(row[f"{metric}_during_change_pct"])
        variability = float(row.get(f"{metric}_baseline_cv_pct", np.nan))
        effective_floor = max(practical, 0 if pd.isna(variability) else variability)
        return not pd.isna(lift) and lift >= effective_floor

    if event_type in {"milestone", "anniversary", "collaboration"}:
        primary = [passes("dau", thresholds["dau"]), passes("revenue", thresholds["revenue"])]
        quality = passes("nru", thresholds["nru_or_returned"]) or passes(
            "returned_users", thresholds["nru_or_returned"]
        )
        if all(primary) and quality:
            return "Successful immediate lift"
        if any(primary) or quality:
            return "Mixed immediate lift"
        return "Underperforming immediate lift"
    if event_type in {"seasonal", "regional"}:
        checks = [passes("dau", thresholds["dau"]), passes("revenue", thresholds["revenue"])]
    else:
        checks = [passes("revenue", thresholds["revenue"]), passes("pu", thresholds["pu"])]
    if all(checks):
        return "Successful immediate lift"
    if any(checks):
        return "Mixed immediate lift"
    return "Underperforming immediate lift"


def _evaluate_durability(row: dict[str, object]) -> str:
    if bool(row["baseline_incomplete"]):
        return "Not evaluable: no complete baseline"
    if str(row["event_type"]) in {"incident", "incident_response", "recovery"}:
        return "Deferred to incident analysis"
    if _dau_practical_threshold(str(row["event_type"])) is None:
        return "Context only"
    if bool(row["post_14_incomplete"]):
        return "Not evaluable: incomplete horizon"
    if not bool(row["dau_lift_is_material"]):
        if bool(row["baseline_contaminated"]):
            return (
                "Contextual comparison only: immediate DAU below "
                "materiality threshold"
            )
        return "Not evaluable: immediate DAU below materiality threshold"
    if bool(row["post_14_contaminated"]):
        return "Not attributable: overlapping event"
    immediate = float(row.get("dau_during_change_pct", np.nan))
    post = float(row.get("dau_post_14_change_pct", np.nan))
    if pd.isna(immediate) or immediate <= 0 or pd.isna(post):
        return "No positive lift to retain"
    retained_share = post / immediate
    persistent = post > 0 and retained_share >= .30
    if bool(row["baseline_contaminated"]):
        return (
            "Contextual persistence: overlapping baseline"
            if persistent else "Contextual comparison: not persistent"
        )
    return "Durable" if persistent else "Not durable"


def lifecycle_event_performance(daily: pd.DataFrame,
                                events: pd.DataFrame) -> pd.DataFrame:
    """Compare each event with baseline and two post-event durability windows."""
    daily = daily.copy()
    events = events.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    events[["start_date", "end_date"]] = events[["start_date", "end_date"]].apply(
        pd.to_datetime
    )
    rows: list[dict[str, object]] = []
    data_min, data_max = daily["date"].min(), daily["date"].max()
    for event_id, event_rows in events.groupby("event_id", sort=False):
        first = event_rows.iloc[0]
        start, end = first["start_date"], first["end_date"]
        regions = [r for r in REGION_ORDER if r in set(event_rows["region"])]
        aggregate = aggregate_scope(daily, regions)

        if first["event_type"] in {"incident_response", "recovery"}:
            baseline_start, baseline_end = pd.Timestamp("2025-07-31"), pd.Timestamp("2025-08-11")
            baseline_name = "stable pre-incident: 2025-07-31 to 2025-08-11"
        else:
            baseline_start, baseline_end = start - pd.Timedelta(days=14), start - pd.Timedelta(days=1)
            baseline_name = "preceding 14 calendar days"

        post_14_start, post_14_end = end + pd.Timedelta(days=1), end + pd.Timedelta(days=14)
        post_28_start, post_28_end = end + pd.Timedelta(days=15), end + pd.Timedelta(days=28)
        baseline = _window_stats(aggregate, baseline_start, baseline_end)
        during = _window_stats(aggregate, start, end)
        post_14 = _window_stats(aggregate, post_14_start, post_14_end)
        post_28 = _window_stats(aggregate, post_28_start, post_28_end)

        row: dict[str, object] = {
            "event_id": event_id,
            "event_name": first["event_name"],
            "event_type": first["event_type"],
            "start_date": start,
            "end_date": end,
            "regions": " | ".join(regions),
            "baseline_basis": baseline_name,
            "baseline_start": baseline_start,
            "baseline_end": baseline_end,
            "baseline_expected_days": (baseline_end - baseline_start).days + 1,
            "baseline_incomplete": (
                baseline_start < data_min
                or baseline["days"] < (baseline_end - baseline_start).days + 1
            ),
            "post_14_start": post_14_start,
            "post_14_end": post_14_end,
            "post_14_incomplete": post_14_end > data_max or post_14["days"] < 14,
            "post_28_start": post_28_start,
            "post_28_end": post_28_end,
            "post_28_incomplete": post_28_end > data_max or post_28["days"] < 14,
        }
        baseline_overlaps = _overlaps(events, event_id, regions, baseline_start, baseline_end)
        post_14_overlaps = _overlaps(events, event_id, regions, post_14_start, post_14_end)
        post_28_overlaps = _overlaps(events, event_id, regions, post_28_start, post_28_end)
        row.update({
            "baseline_contaminated": bool(baseline_overlaps),
            "baseline_overlapping_events": " | ".join(baseline_overlaps),
            "post_14_contaminated": bool(post_14_overlaps),
            "post_14_overlapping_events": " | ".join(post_14_overlaps),
            "post_28_contaminated": bool(post_28_overlaps),
            "post_28_overlapping_events": " | ".join(post_28_overlaps),
        })

        for metric in [*COUNT_METRICS, "conversion_rate", "arpu", "arppu", "outflow_rate"]:
            row[f"{metric}_baseline"] = baseline[metric]
            row[f"{metric}_during"] = during[metric]
            row[f"{metric}_during_change_pct"] = _change_pct(during[metric], baseline[metric])
            row[f"{metric}_post_14"] = post_14[metric]
            row[f"{metric}_post_14_change_pct"] = _change_pct(post_14[metric], baseline[metric])
            row[f"{metric}_post_28"] = post_28[metric]
            row[f"{metric}_post_28_change_pct"] = _change_pct(post_28[metric], baseline[metric])
            base_slice = aggregate[aggregate["date"].between(baseline_start, baseline_end)][metric]
            row[f"{metric}_baseline_cv_pct"] = (
                float(base_slice.std(ddof=1) / base_slice.mean() * 100)
                if len(base_slice) > 1 and base_slice.mean() != 0 else np.nan
            )
        row["immediate_result"] = _evaluate_immediate(row)
        if baseline_overlaps and "lift" in str(row["immediate_result"]):
            row["immediate_result"] += " (contextual baseline)"
        row["dau_lift_is_material"] = _has_material_dau_lift(row)
        row["durability_result"] = _evaluate_durability(row)
        rows.append(row)
    return pd.DataFrame(rows)


def lifecycle_phase_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Summarize the eight narrative phases at global and regional scope."""
    daily = daily.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    rows: list[dict[str, object]] = []
    for phase_order, (phase, start_text, end_text) in enumerate(PHASES, start=1):
        start, end = pd.Timestamp(start_text), pd.Timestamp(end_text)
        for scope_name, regions in [("ALL", REGION_ORDER), *[(r, [r]) for r in REGION_ORDER]]:
            frame = aggregate_scope(daily, regions)
            metrics = _window_stats(frame, start, end)
            rows.append({
                "phase_order": phase_order,
                "phase": phase,
                "scope": scope_name,
                "start_date": start,
                "end_date": end,
                **metrics,
            })
    result = pd.DataFrame(rows)
    result["dau_change_vs_prior_phase_pct"] = result.groupby("scope")["dau"].pct_change() * 100
    result["revenue_change_vs_prior_phase_pct"] = result.groupby("scope")["revenue"].pct_change() * 100
    return result


def event_dependency_summary(daily: pd.DataFrame) -> pd.DataFrame:
    """Measure how much activity and revenue occur on planned live-ops days."""
    frame = daily.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    pattern = "|".join(sorted(LIVEOPS_TYPES))
    frame["is_liveops_day"] = frame["event_types"].str.contains(pattern, regex=True, na=False)
    frame["year"] = frame["date"].dt.year
    rows: list[dict[str, object]] = []
    scopes = [(r, frame[frame["region"].eq(r)]) for r in REGION_ORDER]
    scopes.append(("ALL", frame))
    for scope, scope_frame in scopes:
        for year, year_frame in scope_frame.groupby("year"):
            daily_scope = year_frame.groupby("date", as_index=False).agg(
                dau=("dau", "sum"), revenue=("revenue", "sum"),
                is_liveops_day=("is_liveops_day", "max"),
            )
            live = daily_scope[daily_scope["is_liveops_day"]]
            quiet = daily_scope[~daily_scope["is_liveops_day"]]
            day_share = len(live) / len(daily_scope)
            dau_share = live["dau"].sum() / daily_scope["dau"].sum()
            revenue_share = live["revenue"].sum() / daily_scope["revenue"].sum()
            rows.append({
                "year": int(year),
                "scope": scope,
                "liveops_days": len(live),
                "observed_days": len(daily_scope),
                "liveops_day_share": day_share,
                "liveops_dau_share": dau_share,
                "liveops_revenue_share": revenue_share,
                "dau_share_overindex": dau_share / day_share,
                "revenue_share_overindex": revenue_share / day_share,
                "liveops_vs_quiet_dau_mean_pct": _change_pct(live["dau"].mean(), quiet["dau"].mean()),
                "liveops_vs_quiet_revenue_mean_pct": _change_pct(
                    live["revenue"].mean(), quiet["revenue"].mean()
                ),
            })
    return pd.DataFrame(rows)


def indexed_regional_lifecycle(daily: pd.DataFrame) -> pd.DataFrame:
    result = daily[["date", "region", "dau"]].sort_values(["region", "date"]).copy()
    result["date"] = pd.to_datetime(result["date"])
    result["dau_7d"] = result.groupby("region")["dau"].transform(
        lambda values: values.rolling(7, min_periods=1).mean()
    )
    first = result.groupby("region")["dau_7d"].transform("first")
    result["dau_index"] = result["dau_7d"] / first * 100
    return result


def save_lifecycle_charts(daily: pd.DataFrame, event_results: pd.DataFrame,
                          dependency: pd.DataFrame, image_dir: Path) -> None:
    image_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    indexed = indexed_regional_lifecycle(daily)

    fig, axes = plt.subplots(2, 1, figsize=(14, 9), sharey=True)
    region_labels = {"KR": "KR", "JP": "JP", "GLOBAL_WEST": "Global West"}
    for ax, year in zip(axes, [2024, 2025]):
        year_data = indexed[indexed["date"].dt.year.eq(year)]
        for region in REGION_ORDER:
            values = year_data[year_data["region"].eq(region)]
            ax.plot(values["date"], values["dau_index"], label=region_labels[region],
                    color=REGION_COLORS[region], linewidth=1.8)
        ax.axhline(100, color="#555555", linewidth=.8, linestyle="--")
        ax.text(.01, 100, "Starting level = 100", transform=ax.get_yaxis_transform(),
                va="bottom", ha="left", fontsize=8, color="#555555")
        ax.set(title=f"{year}", ylabel="Relative DAU index")
    axes[0].legend(ncol=3, frameon=False)
    axes[1].set(xlabel="Date")
    fig.suptitle("Regional DAU Trend on a Common Index", y=.995)
    fig.text(
        .5, .005,
        "Index definition: each region's January 1, 2024 DAU = 100; "
        "lines show a seven-day rolling average.",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=[0, .03, 1, .98])
    fig.savefig(image_dir / "lifecycle_indexed_by_region.png", dpi=180)
    plt.close(fig)

    event_types = {"milestone", "anniversary", "collaboration", "seasonal", "bm_launch"}
    plot = event_results[event_results["event_type"].isin(event_types)].copy()
    plot = plot[~plot["baseline_incomplete"]]
    plot["post_plot"] = plot["dau_post_14_change_pct"].where(
        ~plot["post_14_contaminated"] & ~plot["post_14_incomplete"]
    )
    post_colors = np.where(plot["dau_lift_is_material"], "#55A868", "#A6A6A6")
    event_labels = plot["event_name"].replace({
        "PvE Growth Subscription Launch": "PvE Growth Subscription",
    }).copy()
    autumn = plot["event_name"].eq("Regional Autumn Festival")
    event_labels.loc[autumn] = (
        event_labels.loc[autumn] + " "
        + pd.to_datetime(plot.loc[autumn, "start_date"]).dt.year.astype(str)
    )
    y = np.arange(len(plot))
    height = .34
    fig, ax = plt.subplots(figsize=(12.5, 7.5))
    immediate = ax.barh(
        y - height / 2, plot["dau_during_change_pct"], height,
        label="During event", color="#4C72B0",
    )
    post = ax.barh(
        y + height / 2, plot["post_plot"], height,
        color=post_colors,
    )

    def label_bar(container: object) -> None:
        for bar in container:
            width = bar.get_width()
            if pd.isna(width):
                continue
            offset = 3 if width >= 0 else -3
            ax.annotate(
                f"{width:+.1f}%",
                (width, bar.get_y() + bar.get_height() / 2),
                xytext=(offset, 0), textcoords="offset points",
                va="center", ha="left" if width >= 0 else "right", fontsize=8,
            )

    label_bar(immediate)
    label_bar(post)
    for index, (_, row) in enumerate(plot.iterrows()):
        if row["post_14_contaminated"]:
            status, color, status_x = "Post window overlaps another event", "#8C2D2D", 54
        elif row["post_14_incomplete"]:
            status, color, status_x = "Post window not yet complete", "#555555", 54
        elif row["baseline_contaminated"]:
            status, color, status_x = (
                "Contextual baseline: overlaps prior event", "#8A6D3B", 59
            )
        else:
            continue
        ax.text(status_x, index + height / 2, status, va="center", ha="left",
                fontsize=8, color=color)

    ax.axvline(0, color="black", linewidth=.8)
    ax.axvline(10, color="#777777", linewidth=.8, linestyle="--")
    ax.text(10, -.75, "+10% major-event threshold", ha="center", va="bottom",
            fontsize=8, color="#555555")
    ax.set(
        title="Event DAU Change and Post-Event Evaluation",
        xlabel="Change from each event's stated baseline (%)",
        ylabel="", yticks=y, yticklabels=event_labels, xlim=(-15, 76),
    )
    ax.invert_yaxis()
    legend_handles = [
        immediate,
        Patch(facecolor="#55A868", label="Post period: eligible for evaluation"),
        Patch(facecolor="#A6A6A6", label="Post period: immediate lift below threshold"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="upper center",
              bbox_to_anchor=(.5, -.12), ncol=3)
    fig.tight_layout(rect=[0, .06, 1, 1])
    fig.savefig(image_dir / "event_lift_durability.png", dpi=180)
    plt.close(fig)

    global_dependency = dependency[dependency["scope"].eq("ALL")].copy()
    melted = global_dependency.melt(
        id_vars="year",
        value_vars=["liveops_day_share", "liveops_dau_share", "liveops_revenue_share"],
        var_name="measure", value_name="share",
    )
    labels = {
        "liveops_day_share": "Planned-event day share",
        "liveops_dau_share": "DAU during planned events",
        "liveops_revenue_share": "Revenue during planned events",
    }
    melted["measure"] = melted["measure"].map(labels)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    sns.barplot(data=melted, x="year", y="share", hue="measure", ax=ax,
                palette=["#9A9A9A", "#4C72B0", "#C44E52"])
    ax.yaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    for container in ax.containers:
        ax.bar_label(container, labels=[f"{value:.1%}" for value in container.datavalues],
                     padding=3, fontsize=8)
    ax.set(title="Planned Events: Share of Days, DAU, and Revenue",
           xlabel="Year", ylabel="Share of annual total")
    ax.legend(title="", frameon=False)
    ratios = global_dependency.set_index("year")["revenue_share_overindex"]
    fig.text(
        .5, .015,
        "Revenue-share/day-share ratio: "
        f"{ratios.loc[2024]:.2f}× (2024) → {ratios.loc[2025]:.2f}× (2025)",
        ha="center", fontsize=9, color="#555555",
    )
    fig.tight_layout(rect=[0, .04, 1, 1])
    fig.savefig(image_dir / "event_dependency.png", dpi=180)
    plt.close(fig)


def main() -> None:
    root = project_root()
    daily, retention, events, _, _, bosses = load_data(root)
    daily, _, _ = prepare_metrics(daily, retention, bosses)
    event_results = lifecycle_event_performance(daily, events)
    phases = lifecycle_phase_summary(daily)
    dependency = event_dependency_summary(daily)
    indexed = indexed_regional_lifecycle(daily)

    output_dir = root / "outputs"
    output_dir.mkdir(exist_ok=True)
    event_results.to_csv(output_dir / "lifecycle_event_performance.csv", index=False)
    phases.to_csv(output_dir / "lifecycle_phase_summary.csv", index=False)
    dependency.to_csv(output_dir / "event_dependency_summary.csv", index=False)
    indexed.to_csv(output_dir / "regional_dau_index.csv", index=False)
    save_lifecycle_charts(daily, event_results, dependency, root / "images")

    columns = ["event_name", "dau_during_change_pct", "dau_post_14_change_pct",
               "post_14_contaminated", "immediate_result", "durability_result"]
    print("Analysis 1 lifecycle outputs created")
    print(event_results[columns].round(2).to_string(index=False))
    print("\nGlobal live-ops dependency")
    print(dependency[dependency["scope"].eq("ALL")].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
