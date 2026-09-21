-- Parameters: :as_of = last fully observed UTC calendar date.
-- Two independent denominators: only users whose exact target day has elapsed.
WITH ranked AS (
 SELECT *, ROW_NUMBER() OVER (PARTITION BY event_id ORDER BY received_at_utc) AS rn
 FROM user_logins WHERE date(received_at_utc) <= :as_of
), login_days AS (
 SELECT DISTINCT user_id, date(occurred_at_utc) AS login_date
 FROM ranked WHERE rn = 1 AND date(occurred_at_utc) <= :as_of
), horizons(day) AS (VALUES (7),(30)), user_targets AS (
 SELECT u.user_id, u.region, strftime('%Y-%m', u.registered_at_utc) AS cohort_month,
 h.day, date(u.registered_at_utc, '+' || h.day || ' days') AS target_date
 FROM cohort_users u CROSS JOIN horizons h
 WHERE date(u.registered_at_utc) <= :as_of
), outcomes AS (
 SELECT t.*, CASE WHEN t.target_date <= :as_of THEN 1 ELSE 0 END AS eligible,
 CASE WHEN t.target_date <= :as_of AND l.user_id IS NOT NULL THEN 1 ELSE 0 END AS retained
 FROM user_targets t LEFT JOIN login_days l
 ON t.user_id = l.user_id AND t.target_date = l.login_date
)
SELECT cohort_month, region, day, COUNT(*) AS cohort_users,
 SUM(eligible) AS eligible_users, SUM(retained) AS retained_users,
 1.0 * SUM(retained) / NULLIF(SUM(eligible), 0) AS retention_rate
FROM outcomes GROUP BY cohort_month, region, day
ORDER BY cohort_month, region, day;
