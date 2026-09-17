"""Descriptive robustness checks, not confidence intervals or causal estimates."""
import pandas as pd
from src.analyze_game_data import load_data, project_root
from src.analyze_monetization import prepare_sales,monetization_window_summary,bm_evaluation_summary


def sensitivity_tables():
    d,r,e,p,s,b=load_data(project_root())
    bounds=s.groupby(['date','region']).purchasers.agg(['max','sum'])
    rows=[]
    for assumption in ['published_feasible_union','maximum_overlap','no_overlap_capped_at_dau']:
        daily=d.copy()
        if assumption!='published_feasible_union':
            values=bounds['max' if assumption=='maximum_overlap' else 'sum']
            daily['pu']=pd.MultiIndex.from_frame(daily[['date','region']]).map(values)
            daily['pu']=daily[['pu','dau']].min(axis=1)
        result=bm_evaluation_summary(monetization_window_summary(daily,prepare_sales(s,p)),r)
        result['payer_assumption']=assumption;rows.append(result)
    windows=[]
    agg=d.groupby('date')[['dau','pu','revenue','returned_users']].sum()
    for start,end,label in [('2025-05-15','2025-06-14','subscription'),
                            ('2025-08-17','2025-08-23','compensation')]:
        start,end=pd.Timestamp(start),pd.Timestamp(end)
        for days in [7,14,28]:
            # Incident baselines always end BEFORE the outage, not before compensation.
            base_end=pd.Timestamp('2025-08-11') if label=='compensation' else start-pd.Timedelta(days=1)
            base_start=base_end-pd.Timedelta(days=days-1)
            before=agg.loc[base_start:base_end].mean();after=agg.loc[start:end].mean()
            overlap=e[e.start_date.le(base_end)&e.end_date.ge(base_start)].event_name.unique()
            for metric in agg:
                windows.append({'context':label,'baseline_days':days,'baseline_start':base_start,
                    'baseline_end':base_end,'overlaps':' | '.join(sorted(overlap)) or 'None',
                    'metric':metric,'change_pct':(after[metric]/before[metric]-1)*100})
    return pd.concat(rows,ignore_index=True),pd.DataFrame(windows)

if __name__=='__main__':
    payer,windows=sensitivity_tables();out=project_root()/'outputs';out.mkdir(exist_ok=True)
    payer.to_csv(out/'payer_assumption_sensitivity.csv',index=False)
    windows.to_csv(out/'baseline_sensitivity.csv',index=False)
    print(payer[['scope','payer_assumption','adjacent_launch_revenue_per_payer_day_change_pct','outcome']].to_string(index=False))
