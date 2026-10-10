-- =====================================================================
-- 04_business_questions.sql
-- 40 business questions, from basic SQL to advanced analysis.
--   psql -d northstar -f sql/04_business_questions.sql
--
-- Results:        sql/results/04_business_questions_output.txt
-- Explanations:   sql/README.md  (question -> logic -> result -> business meaning)
--
-- KPI definitions (agreed in business-analysis/01_business_case.md)
--   Revenue      = SUM(net_sales)           (after discount, ex VAT)
--   Gross profit = SUM(gross_profit)        (revenue - cost of goods)
--   Margin %     = gross profit / revenue
--   Orders       = COUNT(DISTINCT order_id)
--   AOV          = revenue / orders
--   Return rate  = refunds / revenue        (value basis)
-- =====================================================================
SET search_path TO northstar;
\pset footer off

-- #####################################################################
-- LEVEL 1 - FUNDAMENTALS: SELECT, WHERE, GROUP BY, HAVING, CASE, JOIN
-- #####################################################################

\echo '=== Q01. What are the headline KPIs for the whole period? ==='
SELECT ROUND(SUM(net_sales), 0)                                   AS revenue,
       ROUND(SUM(cost_amount), 0)                                 AS cost,
       ROUND(SUM(gross_profit), 0)                                AS gross_profit,
       ROUND(100 * SUM(gross_profit) / SUM(net_sales), 2)         AS margin_pct,
       COUNT(DISTINCT order_id)                                   AS orders,
       COUNT(DISTINCT customer_key) FILTER (WHERE customer_key <> -1) AS known_customers,
       ROUND(SUM(net_sales) / COUNT(DISTINCT order_id), 2)        AS aov,
       SUM(quantity)                                              AS units
FROM fact_sales;

\echo '=== Q02. How did revenue, profit and margin change between 2024 and 2025? ==='
SELECT d.year,
       ROUND(SUM(s.net_sales), 0)                              AS revenue,
       ROUND(SUM(s.gross_profit), 0)                           AS gross_profit,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 2)  AS margin_pct,
       COUNT(DISTINCT s.order_id)                              AS orders,
       ROUND(SUM(s.net_sales) / COUNT(DISTINCT s.order_id), 2) AS aov
FROM fact_sales s
JOIN dim_date d ON d.date_key = s.date_key
GROUP BY d.year
ORDER BY d.year;

\echo '=== Q03. Which categories drive revenue, and how profitable are they? ==='
SELECT p.category,
       ROUND(SUM(s.net_sales), 0)                                         AS revenue,
       ROUND(100 * SUM(s.net_sales) / SUM(SUM(s.net_sales)) OVER (), 1)   AS revenue_share_pct,
       ROUND(SUM(s.gross_profit), 0)                                      AS gross_profit,
       ROUND(100 * SUM(s.gross_profit) / SUM(SUM(s.gross_profit)) OVER (), 1) AS profit_share_pct,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1)             AS margin_pct
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.category
ORDER BY revenue DESC;

\echo '=== Q04. How is revenue split by channel, and which channels are growing? ==='
SELECT c.channel_name,
       ROUND(SUM(s.net_sales) FILTER (WHERE d.year = 2024), 0) AS revenue_2024,
       ROUND(SUM(s.net_sales) FILTER (WHERE d.year = 2025), 0) AS revenue_2025,
       ROUND(100 * (SUM(s.net_sales) FILTER (WHERE d.year = 2025)
                  / SUM(s.net_sales) FILTER (WHERE d.year = 2024) - 1), 1) AS growth_pct,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1) AS margin_pct
FROM fact_sales s
JOIN dim_channel c ON c.channel_key = s.channel_key
JOIN dim_date d    ON d.date_key = s.date_key
GROUP BY c.channel_name
ORDER BY revenue_2025 DESC;

\echo '=== Q05. What are the top 10 products by revenue? ==='
SELECT p.sku, p.product_name, p.category,
       SUM(s.quantity)                                        AS units,
       ROUND(SUM(s.net_sales), 0)                             AS revenue,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1) AS margin_pct
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.sku, p.product_name, p.category
ORDER BY revenue DESC
LIMIT 10;

\echo '=== Q06. Which products have the weakest margins, and how often are they sold below cost? ==='
SELECT p.sku, p.product_name, p.category,
       ROUND(p.standard_margin_pct * 100, 1)                                AS list_margin_pct,
       ROUND(SUM(s.net_sales), 0)                                           AS revenue,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1)               AS actual_margin_pct,
       ROUND(100.0 * COUNT(*) FILTER (WHERE s.gross_profit < 0) / COUNT(*), 1) AS pct_lines_below_cost,
       ROUND(-SUM(s.gross_profit) FILTER (WHERE s.gross_profit < 0), 0)     AS loss_on_those_lines
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.sku, p.product_name, p.category, p.standard_margin_pct
HAVING SUM(s.net_sales) >= 10000                 -- ignore tiny sellers
ORDER BY actual_margin_pct
LIMIT 12;

\echo '=== Q06b. How much gross profit is lost on order lines sold BELOW cost? ==='
SELECT p.category,
       COUNT(*) FILTER (WHERE s.gross_profit < 0)                              AS lines_below_cost,
       ROUND(-SUM(s.gross_profit) FILTER (WHERE s.gross_profit < 0), 0)        AS profit_lost,
       ROUND(100 * SUM(s.net_sales) FILTER (WHERE s.gross_profit < 0) / SUM(s.net_sales), 1) AS pct_revenue_below_cost
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.category
ORDER BY profit_lost DESC NULLS LAST;

\echo '=== Q07. Which sub-categories have a margin below 30% (HAVING)? ==='
SELECT p.category, p.sub_category,
       ROUND(SUM(s.net_sales), 0)                             AS revenue,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1) AS margin_pct
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.category, p.sub_category
HAVING SUM(s.gross_profit) / SUM(s.net_sales) < 0.30
ORDER BY margin_pct;

\echo '=== Q08. How does each UK region perform? ==='
SELECT r.region_name, r.nation,
       ROUND(SUM(s.net_sales), 0)                                       AS revenue,
       ROUND(100 * SUM(s.net_sales) / SUM(SUM(s.net_sales)) OVER (), 1) AS revenue_share_pct,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1)           AS margin_pct,
       ROUND(SUM(s.net_sales) / COUNT(DISTINCT s.order_id), 2)          AS aov
FROM fact_sales s
JOIN dim_region r ON r.region_key = s.region_key
GROUP BY r.region_name, r.nation
ORDER BY revenue DESC;

\echo '=== Q09. How do discounts affect margin? (CASE to build discount bands) ==='
SELECT CASE
         WHEN discount_pct = 0     THEN '1. No discount'
         WHEN discount_pct <= 0.15 THEN '2. 5-15%'
         WHEN discount_pct <= 0.25 THEN '3. 20-25%'
         WHEN discount_pct <= 0.35 THEN '4. 30-35%'
         ELSE                           '5. 40%+'
       END                                                 AS discount_band,
       COUNT(*)                                            AS lines,
       ROUND(SUM(net_sales), 0)                            AS revenue,
       ROUND(SUM(discount_amount), 0)                      AS discount_given,
       ROUND(100 * SUM(gross_profit) / SUM(net_sales), 1)  AS margin_pct
FROM fact_sales
GROUP BY 1
ORDER BY 1;

\echo '=== Q10. Weekend vs weekday: how does shopping differ by channel? ==='
SELECT c.channel_name,
       CASE WHEN d.is_weekend = 'Y' THEN 'Weekend' ELSE 'Weekday' END AS day_type,
       COUNT(DISTINCT s.order_id)                                      AS orders,
       ROUND(COUNT(DISTINCT s.order_id)::numeric
             / COUNT(DISTINCT d.date_key), 1)                          AS orders_per_day
FROM fact_sales s
JOIN dim_date d    ON d.date_key = s.date_key
JOIN dim_channel c ON c.channel_key = s.channel_key
GROUP BY c.channel_name, day_type
ORDER BY c.channel_name, day_type;

\echo '=== Q11. Which payment methods do customers use in each channel? ==='
SELECT c.channel_name, s.payment_method,
       COUNT(DISTINCT s.order_id) AS orders,
       ROUND(100.0 * COUNT(DISTINCT s.order_id)
             / SUM(COUNT(DISTINCT s.order_id)) OVER (PARTITION BY c.channel_name), 1) AS share_pct
FROM fact_sales s
JOIN dim_channel c ON c.channel_key = s.channel_key
GROUP BY c.channel_name, s.payment_method
ORDER BY c.channel_name, orders DESC;

\echo '=== Q12. What is the return rate by category? ==='
SELECT p.category,
       ROUND(SUM(s.net_sales), 0)                                   AS revenue,
       ROUND(COALESCE(SUM(r.refund_amount), 0), 0)                  AS refunds,
       ROUND(100 * COALESCE(SUM(r.refund_amount), 0) / SUM(s.net_sales), 1) AS return_rate_pct
FROM fact_sales s
JOIN dim_product p       ON p.product_key = s.product_key
LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key   -- LEFT: most lines are never returned
GROUP BY p.category
ORDER BY return_rate_pct DESC;

-- #####################################################################
-- LEVEL 2 - INTERMEDIATE: CTEs, SUBQUERIES, CONDITIONAL AGGREGATION
-- #####################################################################

\echo '=== Q13. Monthly KPI trend (CTE) ==='
WITH monthly AS (
    SELECT d.year_month,
           SUM(s.net_sales)          AS revenue,
           SUM(s.gross_profit)       AS gross_profit,
           COUNT(DISTINCT s.order_id) AS orders
    FROM fact_sales s
    JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year_month
)
SELECT year_month,
       ROUND(revenue, 0)                       AS revenue,
       ROUND(gross_profit, 0)                  AS gross_profit,
       ROUND(100 * gross_profit / revenue, 1)  AS margin_pct,
       orders,
       ROUND(revenue / orders, 2)              AS aov
FROM monthly
ORDER BY year_month;

\echo '=== Q14. Store league table (physical stores): revenue, margin, sales density ==='
WITH store_perf AS (
    SELECT st.store_name, st.store_type, st.store_region, st.size_sq_ft, st.open_date,
           SUM(s.net_sales)    AS revenue,
           SUM(s.gross_profit) AS gross_profit,
           AVG(s.discount_pct) AS avg_discount
    FROM fact_sales s
    JOIN dim_store st ON st.store_key = s.store_key
    WHERE st.is_online = 'N'
    GROUP BY st.store_name, st.store_type, st.store_region, st.size_sq_ft, st.open_date
)
SELECT store_name, store_type, store_region,
       ROUND(revenue, 0)                          AS revenue,
       ROUND(100 * gross_profit / revenue, 1)     AS margin_pct,
       ROUND(100 * avg_discount, 1)               AS avg_discount_pct,
       ROUND(revenue / size_sq_ft, 2)             AS revenue_per_sq_ft,
       open_date
FROM store_perf
ORDER BY margin_pct;

\echo '=== Q15. Which physical stores have a margin below the physical-store average? (subquery) ==='
SELECT st.store_name,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1) AS store_margin_pct,
       (SELECT ROUND(100 * SUM(s2.gross_profit) / SUM(s2.net_sales), 1)
          FROM fact_sales s2 JOIN dim_store x ON x.store_key = s2.store_key
         WHERE x.is_online = 'N')                             AS avg_store_margin_pct
FROM fact_sales s
JOIN dim_store st ON st.store_key = s.store_key
WHERE st.is_online = 'N'
GROUP BY st.store_name
HAVING SUM(s.gross_profit) / SUM(s.net_sales) <
       (SELECT SUM(s2.gross_profit) / SUM(s2.net_sales)
          FROM fact_sales s2 JOIN dim_store x ON x.store_key = s2.store_key
         WHERE x.is_online = 'N')
ORDER BY store_margin_pct;

\echo '=== Q16. Return rate by channel and year (is it rising?) ==='
SELECT c.channel_name, d.year,
       ROUND(100 * COALESCE(SUM(r.refund_amount), 0) / SUM(s.net_sales), 2) AS return_rate_pct,
       ROUND(100.0 * COUNT(r.return_key) / COUNT(*), 2)                     AS lines_returned_pct
FROM fact_sales s
JOIN dim_channel c       ON c.channel_key = s.channel_key
JOIN dim_date d          ON d.date_key = s.date_key
LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key
GROUP BY c.channel_name, d.year
ORDER BY c.channel_name, d.year;

\echo '=== Q17. Why are customers returning items? Top reasons per category ==='
WITH reasons AS (
    SELECT p.category, r.return_reason,
           COUNT(*)              AS returns,
           SUM(r.refund_amount)  AS refunds
    FROM fact_returns r
    JOIN dim_product p ON p.product_key = r.product_key
    GROUP BY p.category, r.return_reason
)
SELECT category, return_reason, returns,
       ROUND(100.0 * returns / SUM(returns) OVER (PARTITION BY category), 1) AS share_of_category_returns_pct
FROM reasons
WHERE returns >= 20
ORDER BY category, returns DESC;

\echo '=== Q18. Which products have a return rate above 25% (min 40 units sold)? ==='
WITH prod AS (
    SELECT s.product_key,
           SUM(s.quantity)                     AS units_sold,
           COALESCE(SUM(r.return_qty), 0)      AS units_returned
    FROM fact_sales s
    LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key
    GROUP BY s.product_key
)
SELECT p.sku, p.product_name, p.brand, p.sub_category, units_sold, units_returned,
       ROUND(100.0 * units_returned / units_sold, 1) AS unit_return_rate_pct
FROM prod
JOIN dim_product p ON p.product_key = prod.product_key
WHERE units_sold >= 40
  AND units_returned::numeric / units_sold > 0.25
ORDER BY unit_return_rate_pct DESC
LIMIT 15;

\echo '=== Q19. Brand return rates 2024 vs 2025 (conditional aggregation with FILTER) ==='
WITH brand_year AS (
    SELECT p.brand,
           SUM(r.refund_amount) FILTER (WHERE d.year = 2024) / SUM(s.net_sales) FILTER (WHERE d.year = 2024) AS rr_2024,
           SUM(r.refund_amount) FILTER (WHERE d.year = 2025) / SUM(s.net_sales) FILTER (WHERE d.year = 2025) AS rr_2025,
           SUM(s.net_sales) AS revenue
    FROM fact_sales s
    JOIN dim_product p       ON p.product_key = s.product_key
    JOIN dim_date d          ON d.date_key = s.date_key
    LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key
    WHERE p.category IN ('Clothing', 'Footwear', 'Electronics')
    GROUP BY p.brand
)
-- A column alias cannot be used inside an expression in ORDER BY, so we compute in a CTE first
SELECT brand,
       ROUND(100 * rr_2024, 1)             AS return_rate_2024,
       ROUND(100 * rr_2025, 1)             AS return_rate_2025,
       ROUND(100 * (rr_2025 - rr_2024), 1) AS change_pts,
       ROUND(revenue, 0)                   AS revenue
FROM brand_year
ORDER BY change_pts DESC;

\echo '=== Q20. How do promotional trading periods perform? ==='
SELECT d.trading_period,
       COUNT(DISTINCT d.date_key)                                    AS days,
       ROUND(SUM(s.net_sales) / COUNT(DISTINCT d.date_key), 0)       AS revenue_per_day,
       ROUND(100 * SUM(s.discount_amount) / SUM(s.gross_sales), 1)   AS discount_rate_pct,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1)        AS margin_pct
FROM fact_sales s
JOIN dim_date d ON d.date_key = s.date_key
GROUP BY d.trading_period
ORDER BY revenue_per_day DESC;

\echo '=== Q21. New vs returning customers by quarter ==='
WITH first_order AS (
    SELECT customer_key, MIN(date_key) AS first_date_key
    FROM fact_sales
    WHERE customer_key <> -1
    GROUP BY customer_key
),
orders AS (
    SELECT DISTINCT s.order_id, s.customer_key, d.year_quarter,
           CASE WHEN s.date_key = f.first_date_key THEN 'New' ELSE 'Returning' END AS customer_type
    FROM fact_sales s
    JOIN first_order f ON f.customer_key = s.customer_key
    JOIN dim_date d    ON d.date_key = s.date_key
)
SELECT year_quarter,
       COUNT(DISTINCT customer_key) FILTER (WHERE customer_type = 'New')       AS new_customers,
       COUNT(DISTINCT customer_key) FILTER (WHERE customer_type = 'Returning') AS returning_customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE customer_type = 'Returning') / COUNT(*), 1) AS returning_order_share_pct
FROM orders
GROUP BY year_quarter
ORDER BY year_quarter;
-- Note: "New" in Q1 2024 is overstated - customers who bought before 2024 look new (data starts Jan 2024).

\echo '=== Q22. What is each customer segment worth? ==='
SELECT c.segment,
       COUNT(DISTINCT s.customer_key)                                   AS customers,
       ROUND(SUM(s.net_sales), 0)                                       AS revenue,
       ROUND(SUM(s.net_sales) / NULLIF(COUNT(DISTINCT s.customer_key), 0), 0) AS revenue_per_customer,
       ROUND(COUNT(DISTINCT s.order_id)::numeric / NULLIF(COUNT(DISTINCT s.customer_key), 0), 2) AS orders_per_customer,
       ROUND(SUM(s.net_sales) / COUNT(DISTINCT s.order_id), 2)          AS aov,
       ROUND(100 * SUM(s.gross_profit) / SUM(s.net_sales), 1)           AS margin_pct
FROM fact_sales s
JOIN dim_customer c ON c.customer_key = s.customer_key
WHERE c.is_guest = 'N'                -- the single Guest row would distort per-customer averages
GROUP BY c.segment
ORDER BY revenue DESC;

\echo '=== Q23. How much in-store revenue comes from unidentified (guest) shoppers? ==='
SELECT st.store_name,
       ROUND(SUM(s.net_sales), 0)                                                   AS in_store_revenue,
       ROUND(100 * SUM(s.net_sales) FILTER (WHERE s.customer_key = -1) / SUM(s.net_sales), 1) AS guest_share_pct
FROM fact_sales s
JOIN dim_store st  ON st.store_key = s.store_key
JOIN dim_channel c ON c.channel_key = s.channel_key
WHERE c.channel_name = 'In-Store'
GROUP BY st.store_name
ORDER BY guest_share_pct DESC
LIMIT 10;

-- #####################################################################
-- LEVEL 3 - WINDOW FUNCTIONS: LAG/LEAD, RANK, ROW_NUMBER, RUNNING TOTALS
-- #####################################################################

\echo '=== Q24. Month-over-month revenue growth (LAG) ==='
WITH m AS (
    SELECT d.year_month, SUM(s.net_sales) AS revenue
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year_month
)
SELECT year_month,
       ROUND(revenue, 0)                                              AS revenue,
       ROUND(LAG(revenue) OVER (ORDER BY year_month), 0)              AS prev_month,
       ROUND(100 * (revenue / LAG(revenue) OVER (ORDER BY year_month) - 1), 1) AS mom_growth_pct
FROM m
ORDER BY year_month;

\echo '=== Q25. Year-over-year growth for each month (LAG over 12 rows) ==='
WITH m AS (
    SELECT d.year, d.month_number, d.month_short,
           SUM(s.net_sales) AS revenue, SUM(s.gross_profit) AS gross_profit
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year, d.month_number, d.month_short
),
w AS (
    SELECT *,
           LAG(revenue, 12)      OVER (ORDER BY year, month_number) AS revenue_ly,
           LAG(gross_profit, 12) OVER (ORDER BY year, month_number) AS profit_ly
    FROM m
)
SELECT month_short,
       ROUND(revenue_ly, 0)                          AS revenue_2024,
       ROUND(revenue, 0)                             AS revenue_2025,
       ROUND(100 * (revenue / revenue_ly - 1), 1)    AS revenue_yoy_pct,
       ROUND(100 * (gross_profit / profit_ly - 1), 1) AS profit_yoy_pct
FROM w
WHERE year = 2025
ORDER BY month_number;

\echo '=== Q26. Year-to-date running total revenue (SUM OVER with PARTITION) ==='
WITH m AS (
    SELECT d.year, d.month_number, SUM(s.net_sales) AS revenue
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year, d.month_number
)
SELECT year, month_number,
       ROUND(revenue, 0) AS revenue,
       ROUND(SUM(revenue) OVER (PARTITION BY year ORDER BY month_number
                                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW), 0) AS ytd_revenue
FROM m
ORDER BY year, month_number;

\echo '=== Q27. Top 3 products in each category (RANK inside a partition) ==='
WITH ranked AS (
    SELECT p.category, p.product_name,
           SUM(s.net_sales) AS revenue,
           RANK() OVER (PARTITION BY p.category ORDER BY SUM(s.net_sales) DESC) AS rnk
    FROM fact_sales s
    JOIN dim_product p ON p.product_key = s.product_key
    GROUP BY p.category, p.product_name
)
SELECT category, rnk, product_name, ROUND(revenue, 0) AS revenue
FROM ranked
WHERE rnk <= 3
ORDER BY category, rnk;

\echo '=== Q28. Best store in each region (ROW_NUMBER) ==='
WITH s AS (
    SELECT st.store_region, st.store_name, SUM(f.gross_profit) AS gross_profit,
           ROW_NUMBER() OVER (PARTITION BY st.store_region ORDER BY SUM(f.gross_profit) DESC) AS rn,
           COUNT(*) OVER (PARTITION BY st.store_region) AS stores_in_region
    FROM fact_sales f
    JOIN dim_store st ON st.store_key = f.store_key
    WHERE st.is_online = 'N'
    GROUP BY st.store_region, st.store_name
)
SELECT store_region, store_name AS top_store_by_profit, ROUND(gross_profit, 0) AS gross_profit, stores_in_region
FROM s
WHERE rn = 1
ORDER BY gross_profit DESC;

\echo '=== Q29. 3-month moving average of revenue (smooths seasonality) ==='
WITH m AS (
    SELECT d.year_month, SUM(s.net_sales) AS revenue
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year_month
)
SELECT year_month,
       ROUND(revenue, 0) AS revenue,
       ROUND(AVG(revenue) OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW), 0) AS moving_avg_3m
FROM m
ORDER BY year_month;

\echo '=== Q30. How long until customers buy again? (LAG on each customer''s orders) ==='
WITH cust_orders AS (
    SELECT DISTINCT s.customer_key, s.order_id, s.order_datetime::date AS order_date
    FROM fact_sales s
    WHERE s.customer_key <> -1
),
gaps AS (
    SELECT customer_key,
           order_date - LAG(order_date) OVER (PARTITION BY customer_key ORDER BY order_date, order_id) AS days_since_prev
    FROM cust_orders
)
SELECT c.segment,
       COUNT(*)                                                         AS repeat_orders,
       ROUND(AVG(days_since_prev), 0)                                   AS avg_days_between_orders,
       PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY days_since_prev)     AS median_days
FROM gaps g
JOIN dim_customer c ON c.customer_key = g.customer_key
WHERE days_since_prev IS NOT NULL
GROUP BY c.segment
ORDER BY avg_days_between_orders;

\echo '=== Q31. After a first order, how many customers come back within 90 days? (LEAD) by first channel ==='
WITH cust_orders AS (
    SELECT s.customer_key, s.order_id,
           MIN(s.order_datetime) AS order_ts,
           MIN(c.channel_name)   AS channel_name
    FROM fact_sales s
    JOIN dim_channel c ON c.channel_key = s.channel_key
    WHERE s.customer_key <> -1
    GROUP BY s.customer_key, s.order_id
),
seq AS (
    SELECT customer_key, channel_name, order_ts,
           ROW_NUMBER() OVER (PARTITION BY customer_key ORDER BY order_ts, order_id) AS n,
           LEAD(order_ts) OVER (PARTITION BY customer_key ORDER BY order_ts, order_id) AS next_order_ts
    FROM cust_orders
)
SELECT channel_name AS first_order_channel,
       COUNT(*) AS first_time_customers,
       ROUND(100.0 * COUNT(*) FILTER (WHERE next_order_ts <= order_ts + INTERVAL '90 days') / COUNT(*), 1)
           AS repurchase_within_90d_pct
FROM seq
WHERE n = 1
  AND order_ts >= '2024-04-01' AND order_ts < '2025-10-01'   -- skip "fake new" Q1-2024 and give 90 days to observe
GROUP BY channel_name
ORDER BY repurchase_within_90d_pct DESC;

\echo '=== Q32. Pareto: what share of customers generates 80% of known-customer revenue? ==='
WITH cust AS (
    SELECT customer_key, SUM(net_sales) AS revenue
    FROM fact_sales
    WHERE customer_key <> -1
    GROUP BY customer_key
),
cum AS (
    SELECT revenue,
           SUM(revenue) OVER (ORDER BY revenue DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
             / SUM(revenue) OVER () AS cum_share,
           ROW_NUMBER() OVER (ORDER BY revenue DESC) AS rn,
           COUNT(*) OVER () AS n
    FROM cust
)
SELECT ROUND(100.0 * MIN(rn) FILTER (WHERE cum_share >= 0.5) / MAX(n), 1) AS pct_customers_for_50pct_revenue,
       ROUND(100.0 * MIN(rn) FILTER (WHERE cum_share >= 0.8) / MAX(n), 1) AS pct_customers_for_80pct_revenue,
       MAX(n) AS active_customers
FROM cum;

\echo '=== Q33. Like-for-like (LFL) growth: stores open the whole of both years vs all stores ==='
SELECT CASE WHEN st.is_online = 'Y' THEN 'Online hub'
            WHEN st.is_like_for_like = 'Y' THEN 'LFL stores'
            ELSE 'New stores (non-LFL)' END                           AS store_group,
       ROUND(SUM(s.net_sales) FILTER (WHERE d.year = 2024), 0)        AS revenue_2024,
       ROUND(SUM(s.net_sales) FILTER (WHERE d.year = 2025), 0)        AS revenue_2025,
       ROUND(100 * (SUM(s.net_sales) FILTER (WHERE d.year = 2025)
                  / SUM(s.net_sales) FILTER (WHERE d.year = 2024) - 1), 1) AS growth_pct
FROM fact_sales s
JOIN dim_store st ON st.store_key = s.store_key
JOIN dim_date d   ON d.date_key = s.date_key
GROUP BY ROLLUP (1)
ORDER BY 1;

-- #####################################################################
-- LEVEL 4 - ADVANCED BUSINESS ANALYSIS
-- #####################################################################

\echo '=== Q34. Customer cohort retention: % of each acquisition quarter still buying later ==='
WITH first_q AS (
    SELECT s.customer_key, MIN(d.year * 4 + d.quarter_number - 1) AS cohort_idx
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    WHERE s.customer_key <> -1
    GROUP BY s.customer_key
),
activity AS (
    SELECT DISTINCT s.customer_key, d.year * 4 + d.quarter_number - 1 AS q_idx
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    WHERE s.customer_key <> -1
)
SELECT (f.cohort_idx / 4) || '-Q' || (f.cohort_idx % 4 + 1)              AS cohort,
       COUNT(DISTINCT f.customer_key)                                     AS cohort_size,
       -- NULL (blank) when that later quarter is after the end of the data (2025-Q4 = index 8103)
       CASE WHEN f.cohort_idx + 1 <= 2025 * 4 + 3 THEN
       ROUND(100.0 * COUNT(DISTINCT a.customer_key) FILTER (WHERE a.q_idx = f.cohort_idx + 1)
             / COUNT(DISTINCT f.customer_key), 1) END AS next_q_pct,
       CASE WHEN f.cohort_idx + 2 <= 2025 * 4 + 3 THEN
       ROUND(100.0 * COUNT(DISTINCT a.customer_key) FILTER (WHERE a.q_idx = f.cohort_idx + 2)
             / COUNT(DISTINCT f.customer_key), 1) END AS q_plus_2_pct,
       CASE WHEN f.cohort_idx + 4 <= 2025 * 4 + 3 THEN
       ROUND(100.0 * COUNT(DISTINCT a.customer_key) FILTER (WHERE a.q_idx = f.cohort_idx + 4)
             / COUNT(DISTINCT f.customer_key), 1) END AS q_plus_4_pct
FROM first_q f
JOIN activity a ON a.customer_key = f.customer_key
WHERE f.cohort_idx >= 2024 * 4 + 1          -- from 2024-Q2 (Q1 mixes in pre-2024 customers)
GROUP BY f.cohort_idx
ORDER BY f.cohort_idx;

\echo '=== Q35. RFM segmentation (NTILE scores for Recency, Frequency, Monetary) ==='
WITH base AS (
    SELECT customer_key,
           DATE '2025-12-31' - MAX(order_datetime::date) AS recency_days,
           COUNT(DISTINCT order_id)                      AS frequency,
           SUM(net_sales)                                AS monetary
    FROM fact_sales
    WHERE customer_key <> -1
    GROUP BY customer_key
),
scored AS (
    SELECT *,
           NTILE(5) OVER (ORDER BY recency_days DESC) AS r,   -- 5 = most recent
           NTILE(5) OVER (ORDER BY frequency)         AS f,
           NTILE(5) OVER (ORDER BY monetary)          AS m
    FROM base
),
labelled AS (
    SELECT *,
           CASE
             WHEN r >= 4 AND f >= 4 AND m >= 4 THEN '1. Champions'
             WHEN r >= 3 AND f >= 3              THEN '2. Loyal'
             WHEN r >= 4 AND f <= 2              THEN '3. New / promising'
             WHEN r <= 2 AND f >= 3              THEN '4. At risk (were loyal)'
             WHEN r <= 2 AND f <= 2              THEN '5. Lapsed'
             ELSE                                     '6. Needs attention'
           END AS rfm_segment
    FROM scored
)
SELECT rfm_segment,
       COUNT(*)                                                     AS customers,
       ROUND(AVG(recency_days), 0)                                  AS avg_recency_days,
       ROUND(AVG(frequency), 1)                                     AS avg_orders,
       ROUND(SUM(monetary), 0)                                      AS revenue,
       ROUND(100 * SUM(monetary) / SUM(SUM(monetary)) OVER (), 1)   AS revenue_share_pct
FROM labelled
GROUP BY rfm_segment
ORDER BY rfm_segment;

\echo '=== Q36. At what discount does each category stop making money? ==='
SELECT p.category,
       ROUND(100 * SUM(s.gross_profit) FILTER (WHERE s.discount_pct = 0)
                 / SUM(s.net_sales)    FILTER (WHERE s.discount_pct = 0), 1)                 AS margin_no_disc,
       ROUND(100 * SUM(s.gross_profit) FILTER (WHERE s.discount_pct BETWEEN 0.05 AND 0.15)
                 / SUM(s.net_sales)    FILTER (WHERE s.discount_pct BETWEEN 0.05 AND 0.15), 1) AS margin_5_15,
       ROUND(100 * SUM(s.gross_profit) FILTER (WHERE s.discount_pct BETWEEN 0.20 AND 0.30)
                 / SUM(s.net_sales)    FILTER (WHERE s.discount_pct BETWEEN 0.20 AND 0.30), 1) AS margin_20_30,
       ROUND(100 * SUM(s.gross_profit) FILTER (WHERE s.discount_pct >= 0.35)
                 / SUM(s.net_sales)    FILTER (WHERE s.discount_pct >= 0.35), 1)              AS margin_35_plus,
       ROUND(100 * (1 - SUM(s.cost_amount) / SUM(s.gross_sales)), 1)                         AS break_even_discount_pct
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key
GROUP BY p.category
ORDER BY break_even_discount_pct;
-- break-even discount = the discount at which net price equals cost = 1 - cost / list price

\echo '=== Q37. Why did margin fall? Decompose 2024 vs 2025 (discount rate vs cost ratio) ==='
WITH y AS (
    SELECT d.year,
           SUM(s.gross_sales)     AS gross,
           SUM(s.discount_amount) AS discount,
           SUM(s.net_sales)       AS net,
           SUM(s.cost_amount)     AS cost
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year
)
SELECT year,
       ROUND(100 * discount / gross, 2)   AS discount_rate_pct_of_gross,
       ROUND(100 * cost / gross, 2)       AS cost_pct_of_gross_sales,
       ROUND(100 * (net - cost) / net, 2) AS margin_pct
FROM y
ORDER BY year;

\echo '=== Q38. Profit after returns by channel (refunded goods assumed not resold) ==='
WITH line AS (
    SELECT s.channel_key, s.net_sales, s.gross_profit, COALESCE(r.refund_amount, 0) AS refund
    FROM fact_sales s
    LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key
)
SELECT c.channel_name,
       ROUND(SUM(net_sales), 0)                                         AS revenue,
       ROUND(100 * SUM(gross_profit) / SUM(net_sales), 1)               AS margin_pct,
       ROUND(SUM(refund), 0)                                            AS refunds,
       ROUND(SUM(gross_profit) - SUM(refund), 0)                        AS profit_after_returns,
       ROUND(100 * (SUM(gross_profit) - SUM(refund)) / SUM(net_sales), 1) AS margin_after_returns_pct
FROM line
JOIN dim_channel c ON c.channel_key = line.channel_key
GROUP BY c.channel_name
ORDER BY margin_after_returns_pct;

\echo '=== Q39. Online clothing & footwear return rate by order month (is the trend real?) ==='
SELECT d.year_month,
       ROUND(100 * COALESCE(SUM(r.refund_amount), 0) / SUM(s.net_sales), 1) AS return_rate_pct
FROM fact_sales s
JOIN dim_date d          ON d.date_key = s.date_key
JOIN dim_product p       ON p.product_key = s.product_key
JOIN dim_channel c       ON c.channel_key = s.channel_key
LEFT JOIN fact_returns r ON r.sales_line_key = s.sales_line_key
WHERE p.category IN ('Clothing', 'Footwear')
  AND c.channel_name IN ('Website', 'Mobile App')
GROUP BY d.year_month
ORDER BY d.year_month;
-- Caution: Dec 2025 orders have had little time to be returned (data ends 31 Dec) - "return lag".

\echo '=== Q40. Which categories are bought together? (self-join on order) ==='
WITH order_cats AS (
    SELECT DISTINCT s.order_id, p.category
    FROM fact_sales s JOIN dim_product p ON p.product_key = s.product_key
)
SELECT a.category AS category_a, b.category AS category_b,
       COUNT(*) AS orders_together,
       ROUND(100.0 * COUNT(*) / (SELECT COUNT(DISTINCT order_id) FROM order_cats), 2) AS pct_of_all_orders
FROM order_cats a
JOIN order_cats b ON a.order_id = b.order_id AND a.category < b.category
GROUP BY a.category, b.category
ORDER BY orders_together DESC
LIMIT 10;
