"""Tests for Analysis 4 revenue structure and subscription-launch analysis."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analyze_monetization import (
    WINDOWS,
    adjacent_product_summary,
    bm_evaluation_summary,
    monetization_window_summary,
    prepare_sales,
    revenue_decomposition,
)
from src.generate_synthetic_data import (
    RANDOM_SEED,
    generate_activity_kpis,
    generate_product_sales,
    generate_retention_cohorts,
    product_frame,
)


class MonetizationAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        cls.daily, sales = generate_product_sales(rng, activity)
        cls.retention = generate_retention_cohorts(rng, cls.daily)
        cls.sales = prepare_sales(sales, product_frame())
        cls.windows = monetization_window_summary(cls.daily, cls.sales)
        cls.evaluation = bm_evaluation_summary(cls.windows, cls.retention)
        cls.adjacent = adjacent_product_summary(cls.daily, cls.sales)
        cls.decomposition = revenue_decomposition(cls.windows)

    def test_window_days_and_revenue_reconcile(self) -> None:
        global_windows = self.windows[self.windows["scope"].eq("ALL")]
        for _, row in global_windows.iterrows():
            start, end = WINDOWS[row["window"]]
            expected_days = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
            expected_revenue = self.daily[
                pd.to_datetime(self.daily["date"]).between(start, end)
            ]["revenue"].sum()
            self.assertEqual(row["days"], expected_days)
            self.assertAlmostEqual(row["revenue"], expected_revenue, places=2)

    def test_new_bm_is_absent_before_launch(self) -> None:
        global_windows = self.windows[self.windows["scope"].eq("ALL")].set_index("window")
        self.assertEqual(global_windows.loc["local_baseline", "new_bm_revenue_per_day"], 0)
        self.assertGreater(global_windows.loc["launch", "new_bm_revenue_per_day"], 0)

    def test_payer_day_metrics_use_all_service_payer_days(self) -> None:
        global_windows = self.windows[
            self.windows["scope"].eq("ALL")
        ].set_index("window")
        baseline = global_windows.loc["local_baseline"]
        self.assertAlmostEqual(
            baseline["revenue_per_payer_day"],
            baseline["revenue"] / baseline["pu"],
        )
        combined = self.adjacent[
            self.adjacent["product_id"].eq("ADJACENT_SET")
        ].iloc[0]
        self.assertAlmostEqual(
            combined["local_baseline_revenue_per_payer_day"],
            baseline["adjacent_revenue_per_payer_day"],
        )

    def test_primary_growth_thresholds_pass(self) -> None:
        global_result = self.evaluation[self.evaluation["scope"].eq("ALL")].iloc[0]
        self.assertTrue(global_result["revenue_pass"])
        self.assertTrue(global_result["pu_pass"])
        self.assertGreaterEqual(global_result["launch_revenue_per_day_change_pct"], 10)
        self.assertGreaterEqual(global_result["launch_pu_per_day_change_pct"], 5)

    def test_revenue_decomposition_reconciles(self) -> None:
        values = self.decomposition.set_index("component")["revenue_per_day"]
        reconstructed = (
            values["Baseline total"]
            + values["Legacy-product change"]
            + values["New PvE subscription"]
        )
        self.assertAlmostEqual(reconstructed, values["Launch total"])

    def test_adjacent_product_warning_is_delayed_and_broad(self) -> None:
        global_result = self.evaluation[self.evaluation["scope"].eq("ALL")].iloc[0]
        self.assertGreater(
            global_result["adjacent_post_14_revenue_per_day_change_pct"], 0
        )
        self.assertLess(
            global_result["adjacent_post_14_revenue_per_payer_day_change_pct"], -5
        )
        growth_booster = self.adjacent[
            self.adjacent["product_id"].eq("P007")
        ].iloc[0]
        self.assertTrue(growth_booster["launch_warning"])
        self.assertTrue(self.adjacent["post_14_warning"].all())

    def test_combined_adjacent_set_reconciles_with_global_guardrail(self) -> None:
        combined = self.adjacent[
            self.adjacent["product_id"].eq("ADJACENT_SET")
        ].iloc[0]
        global_result = self.evaluation[self.evaluation["scope"].eq("ALL")].iloc[0]
        self.assertAlmostEqual(
            combined["launch_change_pct"],
            global_result["adjacent_launch_revenue_per_payer_day_change_pct"],
        )
        self.assertAlmostEqual(
            combined["post_14_change_pct"],
            global_result["adjacent_post_14_revenue_per_payer_day_change_pct"],
        )

    def test_regional_launch_warning_is_specific_to_jp(self) -> None:
        regional = self.evaluation[~self.evaluation["scope"].eq("ALL")].set_index("scope")
        warning_regions = set(
            regional.index[regional["launch_adjacent_reallocation_warning"]]
        )
        self.assertEqual(warning_regions, {"JP"})
        self.assertTrue(regional["post_14_adjacent_reallocation_warning"].all())

    def test_retention_guardrail_does_not_fail(self) -> None:
        self.assertFalse(self.evaluation["retention_guardrail_failed"].any())

    def test_product_mix_becomes_less_concentrated(self) -> None:
        global_windows = self.windows[self.windows["scope"].eq("ALL")].set_index("window")
        self.assertLess(
            global_windows.loc["launch", "product_revenue_hhi"],
            global_windows.loc["local_baseline", "product_revenue_hhi"],
        )
        self.assertLess(
            global_windows.loc["launch", "top_3_product_revenue_share"],
            global_windows.loc["local_baseline", "top_3_product_revenue_share"],
        )
        outcome = self.evaluation[self.evaluation["scope"].eq("ALL")]["outcome"].iat[0]
        self.assertEqual(outcome, "Mixed: growth with guardrail warning")


if __name__ == "__main__":
    unittest.main()
