"""Tests for Analysis 3 core-content entry and PvE engagement analysis."""

from __future__ import annotations

import unittest

import numpy as np

from src.analyze_game_data import prepare_metrics
from src.analyze_lifecycle import lifecycle_event_performance
from src.analyze_pve import (
    BENCHMARK_BOSS_IDS,
    boss_performance_summary,
    boss_regional_summary,
    event_pve_alignment,
    prepare_boss_funnel,
)
from src.analyze_retention import (
    acquisition_quality_comparison,
    retention_monthly_summary,
)
from src.generate_synthetic_data import (
    RANDOM_SEED,
    events_frame,
    generate_activity_kpis,
    generate_boss_metrics,
    generate_product_sales,
    generate_retention_cohorts,
)


class PveAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        cls.daily, _ = generate_product_sales(rng, activity)
        cls.retention = generate_retention_cohorts(rng, cls.daily)
        cls.events = events_frame()
        cls.bosses = generate_boss_metrics(rng, cls.daily)
        cls.funnel = prepare_boss_funnel(cls.bosses, cls.daily)
        cls.summary = boss_performance_summary(cls.funnel)
        cls.regional = boss_regional_summary(cls.funnel)
        daily_metrics, _, _ = prepare_metrics(cls.daily, cls.retention, cls.bosses)
        lifecycle = lifecycle_event_performance(daily_metrics, cls.events)
        monthly = retention_monthly_summary(cls.retention, cls.events)
        acquisition = acquisition_quality_comparison(cls.retention, monthly)
        cls.alignment = event_pve_alignment(cls.summary, lifecycle, acquisition)

    def test_summary_keeps_difficulties_separate(self) -> None:
        self.assertEqual(len(self.summary), 4 * 3)
        self.assertFalse(
            self.summary[["boss_id", "difficulty"]].duplicated().any()
        )
        self.assertNotIn("ALL", set(self.summary["difficulty"]))

    def test_funnel_rates_reconcile(self) -> None:
        np.testing.assert_allclose(
            self.summary["participation_rate"],
            self.summary["participants"] / self.summary["dau"],
        )
        np.testing.assert_allclose(
            self.summary["clear_rate"],
            self.summary["clears"] / self.summary["participants"],
        )

    def test_benchmark_excludes_astra(self) -> None:
        self.assertNotIn("BOSS004", BENCHMARK_BOSS_IDS)
        self.assertEqual(set(BENCHMARK_BOSS_IDS), {"BOSS001", "BOSS002", "BOSS003"})

    def test_astra_has_low_entry_but_comparable_completion(self) -> None:
        astra = self.summary[self.summary["boss_id"].eq("BOSS004")]
        self.assertTrue((astra["participation_benchmark_index"] < 90).all())
        self.assertTrue((astra["clear_rate_delta_pp"].abs() <= 2).all())
        self.assertTrue((astra["attempts_delta"].abs() <= .10).all())
        self.assertEqual(set(astra["diagnostic_result"]), {"Pre-entry / entry gap"})

    def test_astra_entry_gap_is_consistent_across_regions(self) -> None:
        astra = self.regional[
            self.regional["boss_id"].eq("BOSS004")
            & self.regional["difficulty"].eq("NORMAL")
        ]
        self.assertEqual(len(astra), 3)
        self.assertTrue((astra["participation_benchmark_index"] < 90).all())

    def test_alignment_connects_content_reach_and_cohort_quality(self) -> None:
        fantasy = self.alignment[
            self.alignment["event_name"].eq("Fantasy Saga Crossover")
        ].iloc[0]
        astra = self.alignment[
            self.alignment["event_name"].eq("Astra Heroes Crossover")
        ].iloc[0]
        self.assertEqual(
            fantasy["alignment_result"], "Entry and retention aligned"
        )
        self.assertEqual(astra["alignment_result"], "Traffic-to-content disconnect")

    def test_derived_funnel_has_no_missing_values(self) -> None:
        columns = [
            "participation_rate", "clear_rate", "attempts_per_participant",
            "clear_yield_per_1000_dau",
        ]
        self.assertFalse(self.funnel[columns].isna().any().any())


if __name__ == "__main__":
    unittest.main()
