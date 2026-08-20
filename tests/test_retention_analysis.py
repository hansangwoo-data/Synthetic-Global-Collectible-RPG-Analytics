"""Tests for Analysis 2 acquisition-quality and retention analysis."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analyze_retention import (
    acquisition_quality_comparison,
    regional_quality_summary,
    retention_monthly_summary,
)
from src.generate_synthetic_data import (
    RANDOM_SEED,
    events_frame,
    generate_activity_kpis,
    generate_product_sales,
    generate_retention_cohorts,
)


class RetentionAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        daily, _ = generate_product_sales(rng, activity)
        cls.retention = generate_retention_cohorts(rng, daily)
        cls.events = events_frame()
        cls.monthly = retention_monthly_summary(cls.retention, cls.events)
        cls.comparisons = acquisition_quality_comparison(cls.retention, cls.monthly)

    def test_global_rates_are_count_weighted(self) -> None:
        january = self.retention[self.retention["cohort_month"].eq(pd.Timestamp("2024-01-01"))]
        expected = january["d30_retained"].sum() / january["cohort_size"].sum()
        actual = self.monthly[
            self.monthly["scope"].eq("ALL")
            & self.monthly["cohort_month"].eq(pd.Timestamp("2024-01-01"))
        ]["d30_retention"].iat[0]
        self.assertAlmostEqual(actual, expected)

    def test_monthly_event_context_respects_region(self) -> None:
        july = self.monthly[self.monthly["cohort_month"].eq(pd.Timestamp("2024-07-01"))]
        jp = july[july["scope"].eq("JP")]["event_context"].iat[0]
        kr = july[july["scope"].eq("KR")]["event_context"].iat[0]
        self.assertIn("JP Star Festival", jp)
        self.assertNotIn("JP Star Festival", kr)

    def test_fantasy_and_astra_have_opposite_long_term_quality(self) -> None:
        fantasy = self.comparisons[
            self.comparisons["comparison_id"].eq("fantasy_crossover_2024")
        ].iloc[0]
        astra = self.comparisons[
            self.comparisons["comparison_id"].eq("astra_crossover_2025")
        ].iloc[0]
        self.assertEqual(fantasy["outcome"], "Successful")
        self.assertGreater(fantasy["d30_retention_change_pp"], 1)
        self.assertEqual(astra["outcome"], "Mixed: volume-quality trade-off")
        self.assertLess(astra["d30_retention_change_pp"], -1)

    def test_overlapping_campaign_contexts_are_disclosed(self) -> None:
        fantasy = self.comparisons[
            self.comparisons["comparison_id"].eq("fantasy_crossover_2024")
        ].iloc[0]
        astra = self.comparisons[
            self.comparisons["comparison_id"].eq("astra_crossover_2025")
        ].iloc[0]
        self.assertIn("Fantasy Saga Crossover", fantasy["target_event_context"])
        self.assertIn("Regional Autumn Festival", fantasy["target_event_context"])
        self.assertIn("PvE Growth Subscription Launch", astra["baseline_event_context"])

    def test_d30_retained_user_decomposition_reconciles(self) -> None:
        for _, row in self.comparisons.iterrows():
            expected_total_change = (
                row["d30_retained_volume_component_at_baseline_quality"]
                + row["d30_retained_gap_vs_baseline_quality_at_target_volume"]
            )
            self.assertAlmostEqual(
                expected_total_change,
                row["d30_retained_change_vs_reference_month"],
            )

    def test_astra_quality_gap_is_not_an_absolute_user_decline(self) -> None:
        astra = self.comparisons[
            self.comparisons["comparison_id"].eq("astra_crossover_2025")
        ].iloc[0]
        self.assertGreater(astra["d30_retained_change_vs_reference_month"], 0)
        self.assertLess(
            astra["d30_retained_gap_vs_baseline_quality_at_target_volume"], 0
        )

    def test_collaboration_direction_is_consistent_across_regions(self) -> None:
        fantasy = regional_quality_summary(self.monthly, "fantasy_crossover_2024")
        astra = regional_quality_summary(self.monthly, "astra_crossover_2025")
        self.assertTrue((fantasy["d30_retention_change_pp"] > 1).all())
        self.assertTrue((astra["d30_retention_change_pp"] < -1).all())

    def test_only_mature_cohorts_are_analyzed(self) -> None:
        self.assertLessEqual(
            self.monthly["cohort_month"].max(), pd.Timestamp("2025-11-01")
        )
        self.assertFalse(self.monthly[[
            "d1_retention", "d7_retention", "d30_retention"
        ]].isna().any().any())


if __name__ == "__main__":
    unittest.main()
