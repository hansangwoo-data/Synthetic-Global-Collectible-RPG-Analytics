"""Execute independent SQL metrics on the checked-in CSVs and reconcile to pandas."""
from pathlib import Path
import sqlite3
import pandas as pd
import numpy as np
from src.analyze_game_data import load_data, project_root, validate_data, prepare_metrics
from src.analyze_monetization import prepare_sales, monetization_window_summary
from src.analyze_retention import retention_monthly_summary
from src.analyze_pve import prepare_boss_funnel, boss_performance_summary


def build_database(root=None):
    root = root or project_root()
    data = load_data(root)
    validate_data(*data)
    conn = sqlite3.connect(':memory:')
    conn.execute('PRAGMA foreign_keys=ON')
    conn.executescript((root/'sql/schema.sql').read_text())
    names = ['daily_kpis','retention_cohorts','events','products','daily_product_sales','boss_event_metrics']
    # Explicit DDL survives ingestion; do not use to_sql(if_exists='replace').
    for i in [0,3,1,2,4,5]:
        frame = data[i].copy()
        for col in frame.select_dtypes('datetime').columns:
            frame[col] = frame[col].dt.strftime('%Y-%m-%d')
        frame.to_sql(names[i],conn,if_exists='append',index=False)
    conn.executescript((root/'sql/metrics.sql').read_text())
    return conn, data


def verify(root=None):
    conn, data = build_database(root)
    d,r,e,p,s,b = data
    dm,_,_ = prepare_metrics(d,r,b)
    cases = [
        ('daily_metrics_sql',dm,['date','region'],['conversion_rate','arpu','arppu','dau_7d']),
        ('retention_monthly_sql',retention_monthly_summary(r,e),['cohort_month','scope'],
         ['cohort_size','d1_retained','d7_retained','d30_retained','d30_retention']),
        ('monetization_windows_sql',monetization_window_summary(d,prepare_sales(s,p)),['scope','window'],
         ['days','dau','pu','revenue','pu_per_day','revenue_per_day','conversion_rate',
          'revenue_per_payer_day','adjacent_revenue_per_payer_day','new_bm_revenue_per_day']),
        ('boss_summary_sql',boss_performance_summary(prepare_boss_funnel(b,d)),['boss_id','difficulty'],
         ['participants','clears','attempts','dau','participation_rate','clear_rate','attempts_per_participant']),
    ]
    results=[]
    for view,python,keys,columns in cases:
        sql=pd.read_sql_query(f'SELECT * FROM {view}',conn)
        python=python.copy()
        for col in python.select_dtypes('datetime').columns:
            python[col]=python[col].dt.strftime('%Y-%m-%d')
        left=sql.set_index(keys).sort_index()[columns]
        right=python.set_index(keys).sort_index()[columns]
        pd.testing.assert_index_equal(left.index,right.index)
        np.testing.assert_allclose(left,right,rtol=0,atol=1e-7,equal_nan=True)
        results.append({'view':view,'rows':len(left),'metrics':len(columns),'status':'PASS'})
    rec=pd.read_sql_query('SELECT * FROM daily_reconciliation',conn)
    assert rec.revenue_difference.abs().le(.005).all()
    assert rec.pu.between(rec.min_feasible_pu,rec.max_feasible_pu).all()
    conn.close()
    return pd.DataFrame(results)

if __name__=='__main__':
    result=verify()
    output=project_root()/'outputs';output.mkdir(exist_ok=True)
    result.to_csv(output/'sql_python_parity.csv',index=False)
    print(result.to_string(index=False))
