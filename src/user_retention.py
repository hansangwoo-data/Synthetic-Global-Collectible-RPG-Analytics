"""Independent supplemental synthetic login cohort; never backs the aggregate scenario."""
from pathlib import Path
import sqlite3
import random
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
AS_OF = '2025-03-31'
KEYS = ['cohort_month', 'region', 'day']

def generate():
    rng = random.Random(730)
    users, logs = [], []
    cutoff = pd.Timestamp(AS_OF)
    for i in range(360):
        uid = f'u{i:04d}'
        start = pd.Timestamp('2025-01-01') + pd.Timedelta(days=i % 90)
        users.append((uid, start.isoformat(), ['KR', 'JP', 'GLOBAL_WEST'][i % 3]))
        for day in range((cutoff - start).days + 1):
            # Full daily activity process, including returns after missed days.
            if day == 0 or rng.random() < .12 + .58 * (0.94 ** day):
                occurred = start + pd.Timedelta(days=day, hours=rng.randrange(24))
                event = (f'e{len(logs):06d}', uid, occurred.isoformat(), occurred.isoformat())
                logs.append(event)
                if rng.random() < .08:  # repeated delivery, same event identity
                    logs.append((*event[:3], (occurred + pd.Timedelta(hours=2)).isoformat()))
                if rng.random() < .15:  # second genuine session, count user only once
                    logs.append((f'e{len(logs):06d}', uid, occurred.isoformat(), occurred.isoformat()))
    return (pd.DataFrame(users, columns=['user_id','registered_at_utc','region']),
            pd.DataFrame(logs, columns=['event_id','user_id','occurred_at_utc','received_at_utc']))

def validate(users, logs):
    if users.isna().any().any() or logs.isna().any().any():
        raise ValueError('Null source field')
    if users.user_id.duplicated().any():
        raise ValueError('Duplicate user')
    if not users.region.isin(['KR','JP','GLOBAL_WEST']).all():
        raise ValueError('Unknown region')
    if not logs.user_id.isin(users.user_id).all():
        raise ValueError('Orphan login')
    for frame, cols in [(users,['registered_at_utc']), (logs,['occurred_at_utc','received_at_utc'])]:
        for col in cols:
            # Canonical UTC ISO strings make SQLite and pandas date interpretation identical.
            parsed = pd.to_datetime(frame[col], errors='raise')
            if not parsed.dt.strftime('%Y-%m-%dT%H:%M:%S').eq(frame[col]).all():
                raise ValueError('Expected canonical UTC timestamp without offset')
    if (logs.groupby('event_id')[['user_id','occurred_at_utc']].nunique() > 1).any().any():
        raise ValueError('Conflicting event redelivery')
    joined = logs.merge(users, on='user_id', validate='many_to_one')
    if ((joined.occurred_at_utc < joined.registered_at_utc) |
        (joined.received_at_utc < joined.occurred_at_utc)).any():
        raise ValueError('Invalid event chronology')

def sql_result(users, logs, as_of=AS_OF):
    validate(users, logs)
    with sqlite3.connect(':memory:') as db:
        users.to_sql('cohort_users', db, index=False)
        logs.to_sql('user_logins', db, index=False)
        return pd.read_sql_query((ROOT/'sql/user_retention.sql').read_text(), db,
                                 params={'as_of':as_of})

def pandas_result(users, logs, as_of=AS_OF):
    validate(users, logs)
    cutoff = pd.Timestamp(as_of)
    events = logs[pd.to_datetime(logs.received_at_utc).dt.normalize() <= cutoff]
    events = events.sort_values('received_at_utc').drop_duplicates('event_id').copy()
    events['date'] = pd.to_datetime(events.occurred_at_utc).dt.normalize()
    seen = set(zip(events.user_id, events.date))
    people = users.copy()
    people['registration'] = pd.to_datetime(people.registered_at_utc).dt.normalize()
    people = people[people.registration <= cutoff]
    people['cohort_month'] = people.registration.dt.strftime('%Y-%m')
    rows = []
    for (month, region), group in people.groupby(['cohort_month','region']):
        for day in (7,30):
            eligible = group[group.registration + pd.Timedelta(days=day) <= cutoff]
            count = sum((u, d + pd.Timedelta(days=day)) in seen
                        for u,d in zip(eligible.user_id, eligible.registration))
            rows.append((month,region,day,len(group),len(eligible),count,
                         count/len(eligible) if len(eligible) else float('nan')))
    return pd.DataFrame(rows, columns=KEYS+['cohort_users','eligible_users','retained_users','retention_rate'])

def run(regenerate=False, check_docs=True):
    folder = ROOT/'data/synthetic'
    if regenerate:
        for frame, name in zip(generate(), ['user_cohort_users','user_cohort_logins']):
            frame.to_csv(folder/f'{name}.csv',index=False)
    users, logs = [pd.read_csv(folder/f'{name}.csv') for name in ['user_cohort_users','user_cohort_logins']]
    result = sql_result(users,logs)
    pd.testing.assert_frame_equal(result,pandas_result(users,logs),check_dtype=False,atol=1e-12,rtol=0)
    (ROOT/'outputs').mkdir(exist_ok=True)
    result.to_csv(ROOT/'outputs/user_exact_day_retention.csv',index=False)
    lines = ['# Exact-day login cohort results', '',
             'Generated from the independent supplemental synthetic population; not evidence about the six aggregate scenario tables.', '',
             f'As of the end of {AS_OF} UTC. Rates are fractions. Zero eligible users produces NA.', '',
             '| Month | Region | Day | All registered | Eligible | Logged in on exact day | Rate |',
             '|---|---|---:|---:|---:|---:|---:|']
    for r in result.itertuples(index=False):
        rate = 'NA' if pd.isna(r.retention_rate) else f'{r.retention_rate:.4f}'
        lines.append(f'| {r.cohort_month} | {r.region} | {r.day} | {r.cohort_users} | {r.eligible_users} | {r.retained_users} | {rate} |')
    lines += ['', 'Small synthetic cohorts and an authored activity process cannot establish a regional advantage. Compare mature cohorts only; March uses partial eligible subsets; March D30 has zero or very few eligible users depending on region. Use this output to validate instrumentation before designing a real retention experiment.', '']
    content = '\n'.join(lines)
    path = ROOT/'docs/user_retention_results.md'
    if check_docs:
        if not path.exists() or path.read_text() != content:
            raise AssertionError('Stale user retention report; regenerate explicitly')
    else:
        path.write_text(content)
    return result

if __name__ == '__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--regenerate',action='store_true')
    p.add_argument('--refresh-docs',action='store_true')
    args=p.parse_args()
    print(run(args.regenerate,not args.refresh_docs).to_string(index=False))
