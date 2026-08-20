"""Tests for Analysis 6 cross-analysis regional strategy synthesis."""

from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from src.analyze_game_data import prepare_metrics
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
from src.analyze_regional import (
    REGION_ORDER,
    regional_action_plan,
    regional_evidence_summary,
    regional_guardrail_matrix,
)
from src.analyze_retention import regional_quality_summary, retention_monthly_summary
from src.generate_synthetic_data import (
    RANDOM_SEED,
    events_frame,
    generate_activity_kpis,
    generate_boss_metrics,
    generate_product_sales,
    generate_retention_cohorts,
    product_frame,
)


class RegionalAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        rng = np.random.default_rng(RANDOM_SEED)
        activity = generate_activity_kpis(rng)
        daily, sales = generate_product_sales(rng, activity)
        retention = generate_retention_cohorts(rng, daily)
        events = events_frame()
        bosses = generate_boss_metrics(rng, daily)

        daily_metrics, _, _ = prepare_metrics(daily, retention, bosses)
        dependency = event_dependency_summary(daily_metrics)
        monthly = retention_monthly_summary(retention, events)
        collaboration = pd.concat([
            regional_quality_summary(monthly, "fantasy_crossover_2024"),
            regional_quality_summary(monthly, "astra_crossover_2025"),
        ], ignore_index=True)
        regional_bosses = boss_regional_summary(prepare_boss_funnel(bosses, daily))
        sales_enriched = prepare_sales(sales, product_frame())
        monetization = bm_evaluation_summary(
            monetization_window_summary(daily, sales_enriched), retention
        )
        incident_windows = incident_window_summary(daily)
        incident_stages = incident_stage_evaluation(incident_windows)
        incident_retention = incident_retention_summary(retention)
        incident = incident_final_evaluation(incident_stages, incident_retention)

        cls.evidence = regional_evidence_summary(
            dependency, collaboration, regional_bosses, monetization, incident
        )
        cls.guardrails = regional_guardrail_matrix(cls.evidence)
        cls.actions = regional_action_plan(cls.evidence)

    def test_evidence_has_one_complete_row_per_region(self) -> None:
        self.assertEqual(self.evidence["region"].tolist(), REGION_ORDER)
        self.assertFalse(self.evidence["region"].duplicated().any())
        self.assertFalse(self.evidence.isna().any().any())

    def test_synthesis_does_not_create_a_composite_score(self) -> None:
        score_columns = [column for column in self.evidence if "score" in column]
        self.assertEqual(score_columns, [])

    def test_jp_is_the_only_immediate_bm_adjacency_warning(self) -> None:
        launch = self.guardrails[
            self.guardrails["guardrail_id"].eq("bm_launch")
        ]
        warning_regions = set(launch.loc[launch["status"].eq("Warning"), "region"])
        self.assertEqual(warning_regions, {"JP"})

    def test_shared_guardrail_pattern_is_consistent(self) -> None:
        warning_ids = {
            "astra_d30", "astra_entry", "bm_post_14", "incident_d30",
        }
        for guardrail_id in warning_ids:
            rows = self.guardrails[self.guardrails["guardrail_id"].eq(guardrail_id)]
            self.assertTrue(rows["status"].eq("Warning").all())
        operations = self.guardrails[
            self.guardrails["guardrail_id"].eq("incident_operations")
        ]
        self.assertTrue(operations["status"].eq("Pass").all())

    def test_global_west_combines_scale_upside_with_quality_risk(self) -> None:
        evidence = self.evidence.set_index("region")
        self.assertEqual(
            evidence["bm_launch_revenue_change_pct"].idxmax(), "GLOBAL_WEST"
        )
        self.assertEqual(
            evidence["liveops_revenue_share_2025"].idxmax(), "GLOBAL_WEST"
        )
        self.assertEqual(evidence["astra_d30_change_pp"].idxmin(), "GLOBAL_WEST")
        self.assertEqual(evidence["incident_d30_change_pp"].idxmin(), "GLOBAL_WEST")

    def test_jp_and_kr_local_patterns_are_preserved(self) -> None:
        evidence = self.evidence.set_index("region")
        self.assertEqual(evidence["fantasy_d30_change_pp"].idxmax(), "JP")
        self.assertEqual(evidence["incident_outflow_recovery_index"].idxmax(), "JP")
        self.assertEqual(evidence["incident_nru_recovery_index"].idxmin(), "KR")
        self.assertEqual(evidence["incident_d30_change_pp"].idxmax(), "KR")

    def test_guardrail_matrix_has_six_checks_for_each_region(self) -> None:
        counts = self.guardrails.groupby("region")["guardrail_id"].nunique()
        self.assertTrue((counts == 6).all())
        self.assertEqual(len(self.guardrails), 18)
        self.assertTrue(self.guardrails["display_value"].str.len().gt(0).all())

    def test_action_plan_separates_shared_and_local_priorities(self) -> None:
        self.assertEqual(len(self.actions[self.actions["scope"].eq("ALL")]), 3)
        for region in REGION_ORDER:
            self.assertEqual(len(self.actions[self.actions["scope"].eq(region)]), 2)
        self.assertFalse(self.actions[["scope", "priority"]].duplicated().any())


if __name__ == "__main__":
    unittest.main()
