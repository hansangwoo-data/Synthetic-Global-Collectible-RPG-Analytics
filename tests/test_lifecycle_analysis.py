"""Tests for Analysis 1 lifecycle and event-dependence logic."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analyze_game_data import prepare_metrics
from src.generate_synthetic_data import (
    RANDOM_SEED,
    events_frame,
    generate_activity_kpis,
    generate_boss_metrics,
    generate_product_sales,
    generate_retention_cohorts,
)
from src.analyze_lifecycle import (
    event_dependency_summary,
    indexed_regional_lifecycle,
    lifecycle_event_performance,
    lifecycle_phase_summary,
)


class LifecycleAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        daily, _ = generate_product_sales(rng, activity)
        retention = generate_retention_cohorts(rng, daily)
        bosses = generate_boss_metrics(rng, daily)
        cls.daily, _, _ = prepare_metrics(daily, retention, bosses)
        cls.events = events_frame()
        cls.performance = lifecycle_event_performance(cls.daily, cls.events)

    def test_one_row_per_event_and_region_scope(self) -> None:
        self.assertFalse(self.performance["event_id"].duplicated().any())
        jp = self.performance[self.performance["event_name"].eq("JP Star Festival")].iloc[0]
        self.assertEqual(jp["regions"], "JP")

    def test_stable_incident_baseline_excludes_collaboration(self) -> None:
        recovery = self.performance[
            self.performance["event_name"].eq("Extraordinary Compensation")
        ].iloc[0]
        self.assertEqual(recovery["baseline_start"], pd.Timestamp("2025-07-31"))
        self.assertEqual(recovery["baseline_end"], pd.Timestamp("2025-08-11"))
        self.assertFalse(bool(recovery["baseline_contaminated"]))

    def test_overlap_flags_prevent_false_durability_attribution(self) -> None:
        crossover = self.performance[
            self.performance["event_name"].eq("Fantasy Saga Crossover")
        ].iloc[0]
        self.assertTrue(bool(crossover["post_14_contaminated"]))
        self.assertIn("Regional Autumn Festival", crossover["post_14_overlapping_events"])
        self.assertEqual(crossover["durability_result"],
                         "Not attributable: overlapping event")

    def test_subthreshold_dau_is_not_eligible_for_durability(self) -> None:
        half_anniversary = self.performance[
            self.performance["event_name"].eq("Half-Anniversary Raid")
        ].iloc[0]
        self.assertFalse(bool(half_anniversary["dau_lift_is_material"]))
        self.assertEqual(
            half_anniversary["durability_result"],
            "Not evaluable: immediate DAU below materiality threshold",
        )

    def test_overlapping_baseline_produces_contextual_persistence(self) -> None:
        anniversary = self.performance[
            self.performance["event_name"].eq("First Anniversary")
        ].iloc[0]
        self.assertTrue(bool(anniversary["baseline_contaminated"]))
        self.assertTrue(bool(anniversary["dau_lift_is_material"]))
        self.assertEqual(
            anniversary["durability_result"],
            "Contextual persistence: overlapping baseline",
        )

    def test_overlapping_baseline_without_material_lift_is_context_only(self) -> None:
        autumn = self.performance[
            self.performance["event_name"].eq("Regional Autumn Festival")
            & self.performance["start_date"].eq(pd.Timestamp("2024-09-26"))
        ].iloc[0]
        self.assertTrue(bool(autumn["baseline_contaminated"]))
        self.assertFalse(bool(autumn["dau_lift_is_material"]))
        self.assertEqual(
            autumn["durability_result"],
            "Contextual comparison only: immediate DAU below materiality threshold",
        )

    def test_incomplete_horizon_is_explicit(self) -> None:
        christmas = self.performance[
            self.performance["event_name"].eq("Christmas Festival 2025")
        ].iloc[0]
        self.assertTrue(bool(christmas["post_14_incomplete"]))
        self.assertEqual(christmas["durability_result"],
                         "Not evaluable: incomplete horizon")

    def test_dependency_shares_and_overindex_are_valid(self) -> None:
        result = event_dependency_summary(self.daily)
        for column in ["liveops_day_share", "liveops_dau_share", "liveops_revenue_share"]:
            self.assertTrue(result[column].between(0, 1).all())
        self.assertTrue((result[["dau_share_overindex", "revenue_share_overindex"]] > 0).all().all())

    def test_index_starts_at_one_hundred_for_every_region(self) -> None:
        indexed = indexed_regional_lifecycle(self.daily)
        first = indexed.groupby("region")["dau_index"].first()
        np.testing.assert_allclose(first, 100)

    def test_phase_summary_is_complete_and_ordered(self) -> None:
        result = lifecycle_phase_summary(self.daily)
        self.assertEqual(len(result), 8 * 4)
        self.assertEqual(result["phase_order"].nunique(), 8)
        self.assertFalse(result[["dau", "revenue"]].isna().any().any())


if __name__ == "__main__":
    unittest.main()
