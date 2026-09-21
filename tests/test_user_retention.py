import unittest
import pandas as pd
from src.user_retention import generate, validate, sql_result, pandas_result, run, ROOT

class UserRetentionTests(unittest.TestCase):
    def fixture(self):
        users=pd.DataFrame([
            ('a','2024-02-22T23:59:59','KR'),
            ('b','2024-02-22T00:00:00','KR'),
            ('c','2024-03-25T00:00:00','KR'),
            ('future','2024-04-01T00:00:00','KR'),
        ],columns=['user_id','registered_at_utc','region'])
        logs=pd.DataFrame([
            ('1','a','2024-02-29T00:00:00','2024-02-29T00:00:00'),
            ('1','a','2024-02-29T00:00:00','2024-03-01T00:00:00'),
            ('2','a','2024-02-29T23:59:59','2024-02-29T23:59:59'),
            ('3','b','2024-03-23T00:00:00','2024-03-23T00:00:00'),
            ('4','a','2024-03-23T00:00:00','2024-04-01T00:00:00'),
            ('5','b','2024-03-01T00:00:00','2024-03-01T00:00:00'),
        ],columns=['event_id','user_id','occurred_at_utc','received_at_utc'])
        return users,logs

    def test_exact_day_leap_day_duplicate_late_and_immature(self):
        users,logs=self.fixture()
        result=sql_result(users,logs,'2024-03-31')
        pd.testing.assert_frame_equal(result,pandas_result(users,logs,'2024-03-31'),check_dtype=False)
        feb=result[result.cohort_month.eq('2024-02')]
        self.assertEqual(feb.eligible_users.tolist(),[2,2])
        self.assertEqual(feb.retained_users.tolist(),[1,1])
        self.assertEqual(feb.retention_rate.tolist(),[.5,.5])
        march=result[result.cohort_month.eq('2024-03')]
        self.assertEqual(march.eligible_users.tolist(),[0,0])
        self.assertTrue(march.retention_rate.isna().all())
        # Late event becomes visible at next snapshot; D30 need not imply D7.
        later=sql_result(users,logs,'2024-04-01')
        self.assertEqual(later.query("cohort_month == '2024-02' and day == 30").retained_users.iloc[0],2)

    def test_source_reproduces_and_report_matches(self):
        for expected,name in zip(generate(),['user_cohort_users','user_cohort_logins']):
            pd.testing.assert_frame_equal(expected,pd.read_csv(ROOT/f'data/synthetic/{name}.csv'))
        result=run()
        self.assertTrue((result.retained_users <= result.eligible_users).all())
        self.assertTrue((result.eligible_users <= result.cohort_users).all())

    def test_business_contract_failures(self):
        users,logs=self.fixture()
        invalid=logs.copy(); invalid.loc[0,'user_id']='orphan'
        with self.assertRaisesRegex(ValueError,'Orphan'): validate(users,invalid)
        invalid=logs.copy(); invalid.loc[1,'occurred_at_utc']='2024-02-28T00:00:00'
        with self.assertRaisesRegex(ValueError,'Conflicting'): validate(users,invalid)
        invalid=logs.copy(); invalid.loc[0,'occurred_at_utc']='2024-02-01T00:00:00'
        invalid=invalid.drop(index=1)
        with self.assertRaisesRegex(ValueError,'chronology'): validate(users,invalid)
        with self.assertRaisesRegex(ValueError,'Duplicate'): validate(pd.concat([users,users]),logs)

if __name__=='__main__': unittest.main()
