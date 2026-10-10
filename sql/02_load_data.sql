-- =====================================================================
-- 02_load_data.sql  -  load the cleaned star schema CSVs
--
-- Run from the project root (paths are relative to where psql is started):
--   psql -d northstar -f sql/02_load_data.sql
--
-- \copy runs on the client, so it works without superuser rights.
-- Load order matters: dimensions first, then facts (foreign keys).
-- =====================================================================
SET search_path TO northstar;

\copy dim_date     FROM 'data/clean/dim_date.csv'     WITH (FORMAT csv, HEADER true)
\copy dim_customer FROM 'data/clean/dim_customer.csv' WITH (FORMAT csv, HEADER true)
\copy dim_product  FROM 'data/clean/dim_product.csv'  WITH (FORMAT csv, HEADER true)
\copy dim_region   FROM 'data/clean/dim_region.csv'   WITH (FORMAT csv, HEADER true)
\copy dim_store    FROM 'data/clean/dim_store.csv'    WITH (FORMAT csv, HEADER true)
\copy dim_channel  FROM 'data/clean/dim_channel.csv'  WITH (FORMAT csv, HEADER true)
\copy fact_sales   FROM 'data/clean/fact_sales.csv'   WITH (FORMAT csv, HEADER true)
\copy fact_returns FROM 'data/clean/fact_returns.csv' WITH (FORMAT csv, HEADER true)

ANALYZE;

SELECT 'dim_date' AS table_name, COUNT(*) AS row_count FROM dim_date
UNION ALL SELECT 'dim_customer', COUNT(*) FROM dim_customer
UNION ALL SELECT 'dim_product',  COUNT(*) FROM dim_product
UNION ALL SELECT 'dim_region',   COUNT(*) FROM dim_region
UNION ALL SELECT 'dim_store',    COUNT(*) FROM dim_store
UNION ALL SELECT 'dim_channel',  COUNT(*) FROM dim_channel
UNION ALL SELECT 'fact_sales',   COUNT(*) FROM fact_sales
UNION ALL SELECT 'fact_returns', COUNT(*) FROM fact_returns;
