-- =====================================================================
-- 03_data_quality_checks.sql
-- Post-load checks. Every check returns a row with a PASS/FAIL status,
-- so the whole file reads as a test report.
--   psql -d northstar -f sql/03_data_quality_checks.sql
-- =====================================================================
SET search_path TO northstar;

WITH checks AS (
    -- 1. Uniqueness: no duplicate order lines
    SELECT 'Uniqueness: order_id + line unique' AS check_name,
           COUNT(*) - COUNT(DISTINCT (order_id, order_line_number)) AS failures
    FROM fact_sales
    UNION ALL
    -- 2. Completeness: every sale has a valid date in the reporting window
    SELECT 'Validity: order date inside 2024-2025',
           COUNT(*) FILTER (WHERE order_datetime < '2024-01-01' OR order_datetime >= '2026-01-01')
    FROM fact_sales
    UNION ALL
    -- 3. Accuracy: stored measures recompute correctly
    SELECT 'Accuracy: net_sales = qty * price - discount',
           COUNT(*) FILTER (WHERE ABS(net_sales - (quantity * unit_price - discount_amount)) > 0.01)
    FROM fact_sales
    UNION ALL
    SELECT 'Accuracy: gross_profit = net_sales - cost',
           COUNT(*) FILTER (WHERE ABS(gross_profit - (net_sales - cost_amount)) > 0.01)
    FROM fact_sales
    UNION ALL
    -- 4. Consistency: date_key matches the timestamp
    SELECT 'Consistency: date_key matches order_datetime',
           COUNT(*) FILTER (WHERE date_key <> TO_CHAR(order_datetime, 'YYYYMMDD')::INT)
    FROM fact_sales
    UNION ALL
    -- 5. Integrity: guest sales only happen in store
    SELECT 'Business rule: guest customers only in In-Store channel',
           COUNT(*)
    FROM fact_sales s JOIN dim_channel c USING (channel_key)
    WHERE s.customer_key = -1 AND c.channel_name <> 'In-Store'
    UNION ALL
    -- 6. Returns cannot be refunded for more than was paid
    SELECT 'Business rule: refund <= amount paid for the line',
           COUNT(*)
    FROM fact_returns r JOIN fact_sales s USING (sales_line_key)
    WHERE r.refund_amount > s.net_sales + 0.02
    UNION ALL
    SELECT 'Business rule: return qty <= qty sold',
           COUNT(*)
    FROM fact_returns r JOIN fact_sales s USING (sales_line_key)
    WHERE r.return_qty > s.quantity
    UNION ALL
    SELECT 'Business rule: return date on/after order date',
           COUNT(*) FROM fact_returns WHERE date_key < order_date_key
    UNION ALL
    -- 7. Returns carry the same dimension keys as the sale they reverse
    SELECT 'Consistency: return keys match original sale',
           COUNT(*)
    FROM fact_returns r JOIN fact_sales s USING (sales_line_key)
    WHERE (r.product_key, r.customer_key, r.store_key, r.channel_key, r.region_key)
       <> (s.product_key, s.customer_key, s.store_key, s.channel_key, s.region_key)
    UNION ALL
    -- 8. Date dimension is contiguous (required for time intelligence in Power BI)
    SELECT 'Completeness: date dimension has no gaps',
           (MAX(full_date) - MIN(full_date) + 1) - COUNT(*)
    FROM dim_date
    UNION ALL
    -- 9. Products sold before they launched
    SELECT 'Validity: no sales before product launch date',
           COUNT(*)
    FROM fact_sales s JOIN dim_product p USING (product_key)
    WHERE s.order_datetime::date < p.launch_date
    UNION ALL
    -- 10. Stores trading before they opened
    SELECT 'Validity: no sales before store open date',
           COUNT(*)
    FROM fact_sales s JOIN dim_store st USING (store_key)
    WHERE s.order_datetime::date < st.open_date
)
SELECT check_name, failures, CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks
ORDER BY status, check_name;

-- Informational: how much of the data relied on imputation or 'Unknown' values?
SELECT 'Sales lines with imputed price' AS measure,
       COUNT(*) FILTER (WHERE is_price_imputed = 'Y') AS rows_affected,
       ROUND(100.0 * COUNT(*) FILTER (WHERE is_price_imputed = 'Y') / COUNT(*), 3) AS pct
FROM fact_sales
UNION ALL
SELECT 'Customers with unknown age band',
       COUNT(*) FILTER (WHERE age_band = 'Unknown' AND is_guest = 'N'),
       ROUND(100.0 * COUNT(*) FILTER (WHERE age_band = 'Unknown' AND is_guest = 'N') / COUNT(*), 3)
FROM dim_customer
UNION ALL
SELECT 'Products with unclassified sub-category',
       COUNT(*) FILTER (WHERE sub_category = 'Unclassified'),
       ROUND(100.0 * COUNT(*) FILTER (WHERE sub_category = 'Unclassified') / COUNT(*), 3)
FROM dim_product;

-- Reconciliation total: the number every report must agree with
SELECT ROUND(SUM(net_sales), 2)   AS total_revenue,
       ROUND(SUM(gross_profit), 2) AS total_gross_profit,
       COUNT(DISTINCT order_id)    AS total_orders
FROM fact_sales;
