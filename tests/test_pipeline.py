"""Regression and scenario tests for the synthetic analytics pipeline."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analyze_game_data import (
    event_window_summary, prepare_metrics, validate_data, validate_derived_data,
)
from src.generate_synthetic_data import (
    RANDOM_SEED, REGIONS, events_frame, generate_activity_kpis,
    generate_boss_metrics, generate_product_sales,
    generate_retention_cohorts, product_frame,
)


def build_datasets(seed: int = RANDOM_SEED) -> tuple[pd.DataFrame, ...]:
    rng = np.random.default_rng(seed)
    activity = generate_activity_kpis(rng)
    daily, sales = generate_product_sales(rng, activity)
    retention = generate_retention_cohorts(rng, daily)
    events, products = events_frame(), product_frame()
    bosses = generate_boss_metrics(rng, daily)
    return daily, retention, events, products, sales, bosses


class SyntheticPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        (cls.daily, cls.retention, cls.events, cls.products,
         cls.sales, cls.bosses) = build_datasets()

    def test_generation_is_deterministic(self) -> None:
        second = build_datasets()
        for first_frame, second_frame in zip(
            (self.daily, self.retention, self.events, self.products, self.sales, self.bosses),
            second,
        ):
            pd.testing.assert_frame_equal(first_frame, second_frame)

    def test_daily_date_region_grain_is_complete(self) -> None:
        self.assertFalse(self.daily[["date", "region"]].duplicated().any())
        self.assertEqual(set(self.daily["region"]), set(REGIONS))
        expected_rows = self.daily["date"].nunique() * len(REGIONS)
        self.assertEqual(len(self.daily), expected_rows)

    def test_business_constraints_and_revenue_reconciliation(self) -> None:
        numeric = ["dau", "nru", "returned_users", "user_outflow", "pu", "revenue"]
        self.assertTrue((self.daily[numeric] >= 0).all().all())
        self.assertTrue((self.daily["pu"] <= self.daily["dau"]).all())
        sales_total = self.sales.groupby(["date", "region"])["gross_revenue_usd"].sum()
        daily_total = self.daily.set_index(["date", "region"])["revenue"]
        np.testing.assert_allclose(sales_total.sort_index(), daily_total.sort_index(), atol=.01)
        priced = self.sales.merge(
            self.products[["product_id", "price_usd"]], on="product_id"
        )
        np.testing.assert_allclose(
            priced["gross_revenue_usd"], priced["units_sold"] * priced["price_usd"],
            atol=.01,
        )
        self.assertTrue(
            {"Small Premium Currency Pack", "Standard Premium Currency Pack",
             "Large Premium Currency Pack"}.issubset(set(self.products["product_name"]))
        )

    def test_retention_and_boss_funnels(self) -> None:
        self.assertTrue((self.retention["d30_retained"] <= self.retention["d7_retained"]).all())
        self.assertTrue((self.retention["d7_retained"] <= self.retention["d1_retained"]).all())
        self.assertTrue((self.retention["d1_retained"] <= self.retention["cohort_size"]).all())
        self.assertTrue((self.bosses["clears"] <= self.bosses["participants"]).all())
        self.assertTrue((self.bosses["participants"] <= self.bosses["attempts"]).all())

    def test_metric_formulas_and_full_validation(self) -> None:
        report = validate_data(self.daily, self.retention, self.events,
                               self.products, self.sales, self.bosses)
        self.assertEqual(int(report["null_cells"].sum()), 0)
        daily, retention, bosses = prepare_metrics(self.daily, self.retention, self.bosses)
        np.testing.assert_allclose(daily["conversion_rate"], daily["pu"]/daily["dau"])
        np.testing.assert_allclose(daily["arppu"], daily["revenue"]/daily["pu"])
        self.assertTrue((retention["d30_retention"] <= retention["d7_retention"]).all())
        events = event_window_summary(daily, self.events)
        derived_report = validate_derived_data(daily, retention, events, bosses)
        self.assertEqual(int(derived_report["unexpected_nulls"].sum()), 0)
        self.assertFalse(bosses["participation_rate"].isna().any())

    def test_bm_launch_has_revenue_lift_and_adjacent_product_warning(self) -> None:
        products = self.products[["product_id", "product_type"]]
        sales = self.sales.merge(products, on="product_id")
        before = sales[sales["date"].between("2025-04-15", "2025-05-14")]
        after = sales[sales["date"].between("2025-05-15", "2025-06-14")]
        self.assertGreater(after["gross_revenue_usd"].sum(), before["gross_revenue_usd"].sum())
        adjacent = {"monthly_pass", "currency_subscription", "growth_booster"}
        before_share = (before[before["product_type"].isin(adjacent)]["gross_revenue_usd"].sum()
                        / before["gross_revenue_usd"].sum())
        after_share = (after[after["product_type"].isin(adjacent)]["gross_revenue_usd"].sum()
                       / after["gross_revenue_usd"].sum())
        self.assertLess(after_share, before_share)
        before_pu = self.daily[self.daily["date"].between("2025-04-15", "2025-05-14")]["pu"].sum()
        after_pu = self.daily[self.daily["date"].between("2025-05-15", "2025-06-14")]["pu"].sum()
        self.assertLess(
            after[after["product_type"].isin(adjacent)]["gross_revenue_usd"].sum()/after_pu,
            before[before["product_type"].isin(adjacent)]["gross_revenue_usd"].sum()/before_pu,
        )

    def test_outage_crash_and_partial_trust_recovery(self) -> None:
        baseline = self.daily[self.daily["date"].between("2025-07-31", "2025-08-11")]
        outage = self.daily[self.daily["date"].between("2025-08-12", "2025-08-16")]
        recovery = self.daily[self.daily["date"].between("2025-08-17", "2025-09-20")]
        full_outage = self.daily[self.daily["date"].eq("2025-08-12")]
        partial_restore = self.daily[self.daily["date"].eq("2025-08-13")]
        self.assertTrue((full_outage["service_availability"] == 0).all())
        self.assertTrue((full_outage[[
            "dau", "nru", "returned_users", "user_outflow", "pu", "revenue"
        ]] == 0).all().all())
        self.assertTrue((partial_restore["service_availability"] == .5).all())
        self.assertTrue((partial_restore["dau"] > 0).all())
        self.assertLess(outage["dau"].mean(), baseline["dau"].mean() * .70)
        self.assertGreater(recovery["dau"].mean(), baseline["dau"].mean() * .90)
        august = self.retention[self.retention["cohort_month"].eq("2025-08-01")]
        october = self.retention[self.retention["cohort_month"].eq("2025-10-01")]
        august_d30 = august["d30_retained"].sum()/august["cohort_size"].sum()
        october_d30 = october["d30_retained"].sum()/october["cohort_size"].sum()
        self.assertGreater(october_d30, august_d30)
        self.assertLess(october_d30, .085)

    def test_only_mature_retention_cohorts_are_published(self) -> None:
        self.assertLessEqual(
            self.retention["cohort_month"].max(), pd.Timestamp("2025-11-01")
        )

    def test_regions_have_distinct_behavior(self) -> None:
        correlations = self.daily.pivot(
            index="date", columns="region", values="dau"
        ).corr()
        off_diagonal = correlations.where(~np.eye(len(correlations), dtype=bool)).stack()
        self.assertLess(float(off_diagonal.max()), .995)

    def test_event_comparisons_use_correct_scope_and_baseline(self) -> None:
        daily, _, _ = prepare_metrics(self.daily, self.retention, self.bosses)
        summary = event_window_summary(daily, self.events)
        jp_event = summary[summary["event_name"].eq("JP Star Festival")].iloc[0]
        self.assertEqual(jp_event["regions"], "JP")
        compensation = summary[
            summary["event_name"].eq("Extraordinary Compensation")
        ].iloc[0]
        self.assertIn("stable pre-incident baseline", compensation["comparison_basis"])

    def test_successful_and_underperforming_collaborations_differ(self) -> None:
        good = self.retention[self.retention["cohort_month"].eq("2024-09-01")]
        poor = self.retention[self.retention["cohort_month"].eq("2025-07-01")]
        good_d30 = good["d30_retained"].sum()/good["cohort_size"].sum()
        poor_d30 = poor["d30_retained"].sum()/poor["cohort_size"].sum()
        self.assertGreater(good_d30, poor_d30)


if __name__ == "__main__":
    unittest.main()
