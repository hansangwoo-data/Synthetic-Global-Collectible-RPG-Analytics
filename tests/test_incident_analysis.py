"""Tests for Analysis 5 outage impact and staged recovery analysis."""

from __future__ import annotations

import unittest

import numpy as np

from src.analyze_incident import (
    INCIDENT_WINDOWS,
    incident_final_evaluation,
    incident_retention_summary,
    incident_stage_evaluation,
    incident_window_summary,
)
from src.generate_synthetic_data import (
    RANDOM_SEED,
    generate_activity_kpis,
    generate_product_sales,
    generate_retention_cohorts,
)


class IncidentAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        cls.daily, _ = generate_product_sales(rng, activity)
        cls.retention = generate_retention_cohorts(rng, cls.daily)
        cls.windows = incident_window_summary(cls.daily)
        cls.stages = incident_stage_evaluation(cls.windows)
        cls.retention_summary = incident_retention_summary(cls.retention)
        cls.final = incident_final_evaluation(cls.stages, cls.retention_summary)

    def test_incident_windows_are_complete_and_non_overlapping(self) -> None:
        global_windows = self.windows[self.windows["scope"].eq("ALL")]
        expected_days = [12, 1, 1, 3, 7, 28, 10]
        actual_days = global_windows.sort_values("window_order")["days"].tolist()
        self.assertEqual(actual_days, expected_days)
        self.assertEqual(set(global_windows["window"]), set(INCIDENT_WINDOWS))
        self.assertFalse(self.windows[["scope", "window"]].duplicated().any())

    def test_full_outage_has_zero_observed_activity_and_commerce(self) -> None:
        outage = self.windows[
            self.windows["scope"].eq("ALL")
            & self.windows["window"].eq("full_outage")
        ].iloc[0]
        self.assertEqual(outage["service_availability"], 0)
        for metric in ["dau_per_day", "nru_per_day", "returned_users_per_day",
                       "user_outflow_per_day", "pu_per_day", "revenue_per_day"]:
            self.assertEqual(outage[metric], 0)
        self.assertFalse(outage["outflow_observable"])
        self.assertTrue(np.isnan(outage["user_outflow_recovery_index"]))

    def test_technical_availability_precedes_behavioral_recovery(self) -> None:
        global_windows = self.windows[self.windows["scope"].eq("ALL")].set_index("window")
        self.assertEqual(global_windows.loc["partial_restoration", "service_availability"], .5)
        self.assertEqual(global_windows.loc["delayed_response", "service_availability"], .82)
        compensation_availability = global_windows.loc[
            "extraordinary_compensation", "service_availability"
        ]
        self.assertEqual(compensation_availability, 1)
        self.assertLess(
            global_windows.loc["extraordinary_compensation", "dau_recovery_index"], 95
        )

    def test_compensation_reactivates_without_commercial_recovery(self) -> None:
        compensation = self.stages[
            self.stages["scope"].eq("ALL")
            & self.stages["window"].eq("extraordinary_compensation")
        ].iloc[0]
        self.assertGreater(compensation["returned_users_recovery_index"], 250)
        self.assertLess(compensation["revenue_recovery_index"], 90)
        self.assertFalse(compensation["operational_thresholds_met"])

    def test_postmortem_recovers_activity_before_revenue(self) -> None:
        remediation = self.stages[
            self.stages["scope"].eq("ALL")
            & self.stages["window"].eq("postmortem_remediation")
        ].iloc[0]
        self.assertTrue(remediation["dau_pass"])
        self.assertTrue(remediation["pu_pass"])
        self.assertFalse(remediation["revenue_pass"])

    def test_residual_window_meets_operational_thresholds_in_every_region(self) -> None:
        residual = self.stages[
            self.stages["window"].eq("residual_post_recovery")
        ]
        self.assertEqual(len(residual), 4)
        self.assertTrue(residual["operational_thresholds_met"].all())

    def test_july_is_not_used_as_clean_retention_reference(self) -> None:
        global_retention = self.retention_summary[
            self.retention_summary["scope"].eq("ALL")
        ].set_index("period")
        self.assertEqual(global_retention.loc["june_reference", "d30_change_pp"], 0)
        self.assertLess(global_retention.loc["july_overlap", "d30_change_pp"], -.5)
        self.assertLess(
            global_retention.loc["august_incident", "d30_retention"],
            global_retention.loc["july_overlap", "d30_retention"],
        )

    def test_residual_d30_guardrail_fails_in_every_region(self) -> None:
        residual = self.retention_summary[
            self.retention_summary["period"].eq("residual_oct_nov_pooled")
        ]
        self.assertEqual(len(residual), 4)
        self.assertTrue(residual["d30_guardrail_failed"].all())

    def test_each_post_recovery_month_fails_guardrail_in_every_region(self) -> None:
        post_recovery = self.retention_summary[
            self.retention_summary["period"].isin([
                "october_residual", "november_residual",
            ])
        ]
        self.assertEqual(len(post_recovery), 8)
        failures_by_period = post_recovery.groupby("period")[
            "d30_guardrail_failed"
        ].all()
        self.assertTrue(failures_by_period.all())

    def test_final_outcome_separates_operations_from_retention(self) -> None:
        self.assertTrue(self.final["operational_thresholds_met"].all())
        self.assertTrue(self.final["d30_guardrail_failed"].all())
        self.assertTrue(self.final["outflow_above_baseline"].all())
        self.assertEqual(
            set(self.final["final_outcome"]),
            {"Mixed: operational recovery, retention gap remains"},
        )


if __name__ == "__main__":
    unittest.main()
