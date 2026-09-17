-- Aggregate product facts BEFORE joining service facts to avoid multiplying DAU/PU.
CREATE VIEW daily_reconciliation AS
WITH sales AS (
 SELECT date,region,SUM(gross_revenue_usd) AS product_revenue,
        MAX(purchasers) AS min_feasible_pu,SUM(purchasers) AS max_feasible_pu
 FROM daily_product_sales GROUP BY date,region
)
SELECT d.*,s.product_revenue,d.revenue-s.product_revenue AS revenue_difference,
       s.min_feasible_pu,s.max_feasible_pu
FROM daily_kpis d JOIN sales s USING(date,region);

CREATE VIEW daily_metrics_sql AS
SELECT *,1.0*pu/NULLIF(dau,0) AS conversion_rate,
 revenue/NULLIF(dau,0) AS arpu,revenue/NULLIF(pu,0) AS arppu,
 AVG(dau) OVER(PARTITION BY region ORDER BY date ROWS BETWEEN 6 PRECEDING AND CURRENT ROW) AS dau_7d
FROM daily_kpis;

CREATE VIEW retention_monthly_sql AS
SELECT cohort_month,region AS scope,cohort_size,d1_retained,d7_retained,d30_retained,
 1.0*d30_retained/cohort_size AS d30_retention FROM retention_cohorts
UNION ALL
SELECT cohort_month,'ALL',SUM(cohort_size),SUM(d1_retained),SUM(d7_retained),SUM(d30_retained),
 1.0*SUM(d30_retained)/SUM(cohort_size)
FROM retention_cohorts GROUP BY cohort_month;

-- Calendar windows are explicit; rates use ratio of sums, not mean of daily rates.
CREATE VIEW monetization_windows_sql AS
WITH windows(window,start_date,end_date) AS (VALUES
 ('february_reference','2025-02-01','2025-02-28'),
 ('local_baseline','2025-04-15','2025-05-14'),
 ('launch','2025-05-15','2025-06-14'),('post_14','2025-06-15','2025-06-28')),
 product_day AS (
 SELECT s.date,s.region,SUM(s.gross_revenue_usd) AS revenue,
 SUM(CASE WHEN p.product_type IN ('monthly_pass','currency_subscription','growth_booster')
          THEN s.gross_revenue_usd ELSE 0 END) AS adjacent,
 SUM(CASE WHEN s.product_id='P008' THEN s.gross_revenue_usd ELSE 0 END) AS new_bm
 FROM daily_product_sales s JOIN products p USING(product_id) GROUP BY s.date,s.region
), daily_scope AS (
 SELECT d.date,d.region AS scope,d.dau,d.pu,p.revenue,p.adjacent,p.new_bm
 FROM daily_kpis d JOIN product_day p USING(date,region)
 UNION ALL
 SELECT d.date,'ALL',SUM(d.dau),SUM(d.pu),SUM(p.revenue),SUM(p.adjacent),SUM(p.new_bm)
 FROM daily_kpis d JOIN product_day p USING(date,region) GROUP BY d.date
)
SELECT d.scope,w.window,COUNT(*) AS days,SUM(d.dau) AS dau,SUM(d.pu) AS pu,SUM(d.revenue) AS revenue,
 1.0*SUM(d.pu)/COUNT(*) AS pu_per_day,SUM(d.revenue)/COUNT(*) AS revenue_per_day,
 1.0*SUM(d.pu)/NULLIF(SUM(d.dau),0) AS conversion_rate,
 SUM(d.revenue)/NULLIF(SUM(d.pu),0) AS revenue_per_payer_day,
 SUM(d.adjacent)/NULLIF(SUM(d.pu),0) AS adjacent_revenue_per_payer_day,
 SUM(d.new_bm)/COUNT(*) AS new_bm_revenue_per_day
FROM daily_scope d JOIN windows w ON d.date BETWEEN w.start_date AND w.end_date
GROUP BY d.scope,w.window;

CREATE VIEW boss_summary_sql AS
SELECT b.boss_id,b.difficulty,SUM(b.participants) AS participants,SUM(b.clears) AS clears,
 SUM(b.attempts) AS attempts,SUM(d.dau) AS dau,
 1.0*SUM(b.participants)/NULLIF(SUM(d.dau),0) AS participation_rate,
 1.0*SUM(b.clears)/NULLIF(SUM(b.participants),0) AS clear_rate,
 1.0*SUM(b.attempts)/NULLIF(SUM(b.participants),0) AS attempts_per_participant
FROM boss_event_metrics b JOIN daily_kpis d USING(date,region)
GROUP BY b.boss_id,b.difficulty;
