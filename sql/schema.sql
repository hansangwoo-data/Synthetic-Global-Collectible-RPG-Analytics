-- SQLite 3.25+; UTC calendar dates, USD. Foreign keys enabled by the loader.
CREATE TABLE daily_kpis (
 date TEXT NOT NULL, region TEXT NOT NULL CHECK(region IN ('KR','JP','GLOBAL_WEST')),
 dau INTEGER NOT NULL CHECK(dau>=0), nru INTEGER NOT NULL CHECK(nru>=0),
 returned_users INTEGER NOT NULL CHECK(returned_users>=0), user_outflow INTEGER NOT NULL CHECK(user_outflow>=0),
 event_names TEXT NOT NULL, event_types TEXT NOT NULL,
 service_availability REAL NOT NULL CHECK(service_availability BETWEEN 0 AND 1),
 pu INTEGER NOT NULL CHECK(pu BETWEEN 0 AND dau), revenue REAL NOT NULL CHECK(revenue>=0),
 PRIMARY KEY(date,region));
CREATE TABLE products (
 product_id TEXT PRIMARY KEY NOT NULL, product_name TEXT NOT NULL, product_type TEXT NOT NULL,
 price_usd REAL NOT NULL CHECK(price_usd>0), available_from TEXT NOT NULL,
 purchase_cycle_days INTEGER NOT NULL CHECK(purchase_cycle_days>0));
CREATE TABLE daily_product_sales (
 date TEXT NOT NULL, region TEXT NOT NULL, product_id TEXT NOT NULL,
 purchasers INTEGER NOT NULL CHECK(purchasers>=0), units_sold INTEGER NOT NULL CHECK(units_sold>=purchasers),
 gross_revenue_usd REAL NOT NULL CHECK(gross_revenue_usd>=0), PRIMARY KEY(date,region,product_id),
 FOREIGN KEY(date,region) REFERENCES daily_kpis(date,region), FOREIGN KEY(product_id) REFERENCES products(product_id));
CREATE TABLE retention_cohorts (
 cohort_month TEXT NOT NULL, region TEXT NOT NULL CHECK(region IN ('KR','JP','GLOBAL_WEST')),
 cohort_size INTEGER NOT NULL CHECK(cohort_size>0),
 d1_retained INTEGER NOT NULL CHECK(d1_retained BETWEEN 0 AND cohort_size),
 d7_retained INTEGER NOT NULL CHECK(d7_retained BETWEEN 0 AND d1_retained),
 d30_retained INTEGER NOT NULL CHECK(d30_retained BETWEEN 0 AND d7_retained), PRIMARY KEY(cohort_month,region));
CREATE TABLE events (
 event_id TEXT NOT NULL, event_name TEXT NOT NULL, event_type TEXT NOT NULL,
 region TEXT NOT NULL CHECK(region IN ('KR','JP','GLOBAL_WEST')),
 start_date TEXT NOT NULL, end_date TEXT NOT NULL CHECK(end_date>=start_date), narrative TEXT NOT NULL,
 PRIMARY KEY(event_id,region));
CREATE TABLE boss_event_metrics (
 date TEXT NOT NULL, region TEXT NOT NULL, boss_id TEXT NOT NULL, boss_name TEXT NOT NULL,
 difficulty TEXT NOT NULL CHECK(difficulty IN ('NORMAL','HARD','NIGHTMARE')),
 participants INTEGER NOT NULL CHECK(participants>=0), attempts INTEGER NOT NULL CHECK(attempts>=participants),
 clears INTEGER NOT NULL CHECK(clears BETWEEN 0 AND participants), PRIMARY KEY(date,region,boss_id,difficulty),
 FOREIGN KEY(date,region) REFERENCES daily_kpis(date,region));
