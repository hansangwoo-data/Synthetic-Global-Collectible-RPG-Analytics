"""Independent CSV, adversarial-contract and SQL parity checks."""
import unittest
import sqlite3
import pandas as pd
import numpy as np
from src.analyze_game_data import load_data,project_root,validate_data
from src.analyze_monetization import monetization_window_summary,prepare_sales
from src.analyze_incident import incident_window_summary
from src.analyze_lifecycle import _evaluate_immediate
from src.analyze_regional import regional_guardrail_matrix
from src.verify_sql import verify,build_database
from src.generate_synthetic_data import (RANDOM_SEED,generate_activity_kpis,generate_product_sales,
    generate_retention_cohorts,generate_boss_metrics,events_frame,product_frame)

class AuditContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_data(project_root())

    def test_checked_in_csvs_match_generator(self):
        rng=np.random.default_rng(RANDOM_SEED)
        d,s=generate_product_sales(rng,generate_activity_kpis(rng))
        r=generate_retention_cohorts(rng,d);b=generate_boss_metrics(rng,d)
        for actual,expected in zip([d,r,events_frame(),product_frame(),s,b],self.data):
            for col in expected.select_dtypes('datetime').columns:actual[col]=pd.to_datetime(actual[col])
            pd.testing.assert_frame_equal(actual,expected,check_dtype=False,rtol=0,atol=1e-9)

    def test_sql_python_parity(self):
        self.assertTrue(verify().status.eq('PASS').all())
        from src.build_evidence import main
        main(check=True)

    def test_orphan_product_rejected(self):
        data=[f.copy() for f in self.data];data[4].loc[0,'product_id']='UNKNOWN'
        with self.assertRaises(ValueError):validate_data(*data)
        with self.assertRaises(ValueError):prepare_sales(data[4],data[3])

    def test_missing_zero_sale_rejected(self):
        data=[f.copy() for f in self.data]
        data[4]=data[4].drop(data[4].query('units_sold==0').index[0])
        with self.assertRaises(ValueError):validate_data(*data)

    def test_missing_entire_region_rejected(self):
        data=[f[f.region!='KR'] if 'region' in f else f for f in self.data]
        with self.assertRaises(ValueError):validate_data(*data)

    def test_missing_boundary_date_rejected(self):
        data=[f.copy() for f in self.data];data[0]=data[0][data[0].date!=data[0].date.min()]
        with self.assertRaises(ValueError):validate_data(*data)

    def test_invalid_numeric_values_rejected(self):
        for table,col,value in [(1,'d30_retained',-1),(5,'participants',-.5),(4,'units_sold',np.inf),
                                (0,'dau',np.nan),(0,'pu',1.5)]:
            with self.subTest(table=table,col=col,value=value):
                data=[f.copy() for f in self.data];data[table][col]=data[table][col].astype(float)
                data[table].loc[0,col]=value
                with self.assertRaises(ValueError):validate_data(*data)

    def test_cohort_nru_mismatch_rejected(self):
        data=[f.copy() for f in self.data];data[1].loc[0,'cohort_size']+=1
        with self.assertRaises(ValueError):validate_data(*data)

    def test_impossible_payer_union_rejected(self):
        data=[f.copy() for f in self.data]
        row=data[0].iloc[0];sales=data[4].query('date==@row.date and region==@row.region')
        data[0].loc[0,'pu']=sales.purchasers.sum()+1
        with self.assertRaises(ValueError):validate_data(*data)

    def test_cent_reconciliation_has_no_relative_tolerance(self):
        data=[f.copy() for f in self.data]
        idx=data[4].gross_revenue_usd.idxmax();data[4].loc[idx,'gross_revenue_usd']+=.02
        with self.assertRaises(ValueError):validate_data(*data)

    def test_incomplete_analysis_windows_rejected(self):
        d,r,e,p,s,b=self.data
        for function in [lambda x:monetization_window_summary(x,prepare_sales(s,p)),incident_window_summary]:
            with self.assertRaises(ValueError):function(d[d.region!='KR'])

    def test_sql_constraints_survive_loading(self):
        conn,_=build_database()
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE daily_product_sales SET product_id='UNKNOWN' WHERE rowid=1")
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute("UPDATE retention_cohorts SET d30_retained=-1 WHERE rowid=1")
        conn.close()

    def test_threshold_equality_matches_source_analyses(self):
        evidence=pd.DataFrame([dict(region='KR',astra_d30_change_pp=-1,
            astra_normal_participation_index=90,bm_adjacent_launch_change_pct=-5,
            bm_adjacent_post_14_change_pct=-5,incident_d30_change_pp=-.5,
            incident_operational_thresholds_met=True)])
        result=regional_guardrail_matrix(evidence).set_index('guardrail_id').status
        self.assertEqual(result['astra_d30'],'Warning');self.assertEqual(result['bm_launch'],'Warning')
        self.assertEqual(result['bm_post_14'],'Warning');self.assertEqual(result['incident_d30'],'Pass')
        self.assertEqual(result['astra_entry'],'Pass')

    def test_incomplete_baseline_cannot_receive_success(self):
        self.assertIn('Not evaluable',_evaluate_immediate({'baseline_incomplete':True,'event_type':'seasonal'}))

if __name__=='__main__':unittest.main()
