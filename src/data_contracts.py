"""Fail-closed contracts for the published, fixed two-year scenario."""
from __future__ import annotations
import numpy as np
import pandas as pd

REGIONS = ['KR', 'JP', 'GLOBAL_WEST']
START = pd.Timestamp('2024-01-01')
END = pd.Timestamp('2025-12-31')
BOSS_EVENTS = {'BOSS001': 'EVT002', 'BOSS002': 'EVT003',
               'BOSS003': 'EVT006', 'BOSS004': 'EVT009'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_keys(frame, columns, expected, name):
    require(not frame[columns].isna().any().any(), f'{name}: null key')
    require(not frame.duplicated(columns).any(), f'{name}: duplicate key')
    actual = pd.MultiIndex.from_frame(frame[columns])
    require(len(actual.difference(expected)) == 0 and
            len(expected.difference(actual)) == 0, f'{name}: incomplete or unexpected grain')


def require_window(frame, date_column, start, end, regions, name):
    expected = pd.MultiIndex.from_product(
        [pd.date_range(start, end), regions], names=[date_column, 'region'])
    selected = frame[frame[date_column].between(pd.Timestamp(start), pd.Timestamp(end))
                     & frame.region.isin(regions)]
    exact_keys(selected, [date_column, 'region'], expected, name)


def validate_contracts(daily, retention, events, products, sales, bosses):
    events = events.copy()
    events["start_date"] = pd.to_datetime(events["start_date"])
    events["end_date"] = pd.to_datetime(events["end_date"])
    products = products.copy()
    products["available_from"] = pd.to_datetime(products["available_from"])
    frames = [daily, retention, events, products, sales, bosses]
    for frame in frames:
        require(not frame.empty and not frame.isna().any().any(), 'empty table or null cell')
        numeric = frame.select_dtypes(include='number')
        require(np.isfinite(numeric).all().all() and numeric.ge(0).all().all(),
                'numeric fields must be finite and nonnegative')
        count_cols = set(frame.columns) & {'dau','nru','returned_users','user_outflow','pu',
            'cohort_size','d1_retained','d7_retained','d30_retained',
            'purchasers','units_sold','participants','attempts','clears','purchase_cycle_days'}
        for col in count_cols:
            require(frame[col].mod(1).eq(0).all(), f'{col}: counts must be integers')
        if 'region' in frame:
            require(frame.region.isin(REGIONS).all(), 'unknown region')
    grid = pd.MultiIndex.from_product([pd.date_range(START, END), REGIONS], names=['date','region'])
    exact_keys(daily, ['date','region'], grid, 'daily')
    mature = [m for m in pd.date_range(START, END, freq='MS')
              if m + pd.offsets.MonthEnd(0) + pd.Timedelta(days=30) <= END]
    exact_keys(retention, ['cohort_month','region'],
               pd.MultiIndex.from_product([mature, REGIONS]), 'retention')
    require(retention.cohort_size.gt(0).all(), 'cohort_size must be positive')
    monthly = daily.assign(cohort_month=daily.date.dt.to_period('M').dt.to_timestamp())
    monthly = monthly.groupby(['cohort_month','region']).nru.sum()
    cohorts = retention.set_index(['cohort_month','region']).cohort_size
    require(cohorts.eq(monthly.reindex(cohorts.index)).all(), 'cohort size must reconcile to NRU')
    require(not products.product_id.duplicated().any(), 'duplicate product')
    require(products.price_usd.gt(0).all() and products.purchase_cycle_days.ge(1).all(), 'invalid product')
    require(not events.duplicated(['event_id','region']).any(), 'duplicate event-region')
    require(events.start_date.le(events.end_date).all(), 'reversed event window')
    require(events.start_date.ge(START).all() and events.end_date.le(END).all(), 'event outside observation')
    for _, group in events.groupby('event_id'):
        require(group[['event_name','event_type','start_date','end_date']].nunique().le(1).all(),
                'event metadata differs across regions')
    # Event labels are denormalized convenience fields; reconcile them to the
    # event-region dimension so a removed event cannot silently change analysis.
    for row in daily.itertuples():
        active = events[events.region.eq(row.region) & events.start_date.le(row.date)
                        & events.end_date.ge(row.date)]
        expected_names = set(active.event_name) or {"No Event"}
        expected_types = set(active.event_type) or {"baseline"}
        require(set(row.event_names.split(" | ")) == expected_names and
                set(row.event_types.split(" | ")) == expected_types,
                "daily event labels do not reconcile to event dimension")
    expected_sales = daily[['date','region']].merge(products[['product_id','available_from']], how='cross')
    expected_sales = expected_sales[expected_sales.date.ge(expected_sales.available_from)]
    exact_keys(sales, ['date','region','product_id'],
               pd.MultiIndex.from_frame(expected_sales[['date','region','product_id']]), 'sales')
    require(sales.units_sold.ge(sales.purchasers).all(), 'units below purchasers')
    require(sales.units_sold.eq(0).eq(sales.purchasers.eq(0)).all(), 'units without purchasers')
    counts = sales.groupby(['date','region']).purchasers.agg(['max','sum'])
    payers = daily.set_index(['date','region']).pu.reindex(counts.index)
    require((counts['max'].le(payers) & counts['sum'].ge(payers)).all(),
            'PU must lie between maximum and sum of product purchasers')
    require(daily.pu.le(daily.dau).all(), 'PU exceeds DAU')
    require((daily.nru + daily.returned_users).le(daily.dau).all(), 'new + returned exceeds DAU')
    expected_bosses = []
    for boss_id, event_id in BOSS_EVENTS.items():
        event = events[events.event_id.eq(event_id)]
        require(set(event.region) == set(REGIONS), 'missing boss event-region')
        for row in event.itertuples():
            expected_bosses.extend((d, row.region, boss_id, difficulty)
                for d in pd.date_range(row.start_date, row.end_date)
                for difficulty in ['NORMAL','HARD','NIGHTMARE'])
    exact_keys(bosses, ['date','region','boss_id','difficulty'],
               pd.MultiIndex.from_tuples(expected_bosses), 'bosses')
    boss_dau = bosses.merge(daily[['date','region','dau']], on=['date','region'], validate='many_to_one')
    require(boss_dau.participants.le(boss_dau.dau).all(), 'boss participants exceed DAU')
