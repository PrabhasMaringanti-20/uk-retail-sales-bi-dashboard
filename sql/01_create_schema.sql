-- =====================================================================
-- 01_create_schema.sql
-- NorthStar Retail UK (simulated) - star schema in PostgreSQL
--
-- Run from the project root:
--   createdb northstar
--   psql -d northstar -f sql/01_create_schema.sql
--
-- Design notes
--   * Dimensions get an integer surrogate key (xxxKey) + the business key (xxxID / code).
--   * Facts hold foreign keys to every dimension + numeric measures.
--   * Constraints (PK, FK, CHECK) make the database itself refuse bad data,
--     so data-quality rules are enforced, not just documented.
-- =====================================================================

DROP SCHEMA IF EXISTS northstar CASCADE;
CREATE SCHEMA northstar;
SET search_path TO northstar;

-- ---------------------------------------------------------------- DIMENSIONS

CREATE TABLE dim_date (
    date_key            INTEGER     PRIMARY KEY,          -- YYYYMMDD, e.g. 20250131
    full_date           DATE        NOT NULL UNIQUE,
    year                SMALLINT    NOT NULL,
    quarter             CHAR(2)     NOT NULL,             -- Q1..Q4
    quarter_number      SMALLINT    NOT NULL CHECK (quarter_number BETWEEN 1 AND 4),
    year_quarter        CHAR(7)     NOT NULL,             -- 2025-Q1
    month_number        SMALLINT    NOT NULL CHECK (month_number BETWEEN 1 AND 12),
    month_name          VARCHAR(10) NOT NULL,
    month_short         CHAR(3)     NOT NULL,
    year_month          CHAR(7)     NOT NULL,             -- 2025-01
    year_month_key      INTEGER     NOT NULL,             -- 202501
    iso_week            SMALLINT    NOT NULL,
    day_of_month        SMALLINT    NOT NULL,
    day_of_week_number  SMALLINT    NOT NULL CHECK (day_of_week_number BETWEEN 1 AND 7),  -- 1 = Monday
    day_name            VARCHAR(10) NOT NULL,
    is_weekend          CHAR(1)     NOT NULL CHECK (is_weekend IN ('Y','N')),
    is_uk_bank_holiday  CHAR(1)     NOT NULL CHECK (is_uk_bank_holiday IN ('Y','N')),
    uk_financial_year   VARCHAR(9)  NOT NULL,             -- FY2024/25 (April - March)
    trading_period      VARCHAR(20) NOT NULL
);

CREATE TABLE dim_customer (
    customer_key        INTEGER     PRIMARY KEY,          -- -1 = Guest (anonymous in-store sale)
    customer_id         VARCHAR(10) NOT NULL UNIQUE,
    gender              VARCHAR(25) NOT NULL,
    age_band            VARCHAR(10) NOT NULL,
    city                VARCHAR(40) NOT NULL,
    postcode_district   VARCHAR(8)  NOT NULL,             -- outward code only (GDPR minimisation)
    postcode_valid      CHAR(1)     NOT NULL CHECK (postcode_valid IN ('Y','N')),
    customer_region     VARCHAR(30) NOT NULL,
    segment             VARCHAR(12) NOT NULL CHECK (segment IN ('Value','Mainstream','Premium','Guest')),
    loyalty_member      CHAR(1)     NOT NULL CHECK (loyalty_member IN ('Y','N')),
    signup_date         DATE,
    first_purchase_date DATE,
    is_guest            CHAR(1)     NOT NULL CHECK (is_guest IN ('Y','N')),
    merged_records      SMALLINT    NOT NULL DEFAULT 0
);

CREATE TABLE dim_product (
    product_key         INTEGER      PRIMARY KEY,
    sku                 VARCHAR(15)  NOT NULL UNIQUE,
    product_name        VARCHAR(80)  NOT NULL,
    category            VARCHAR(20)  NOT NULL,
    sub_category        VARCHAR(20)  NOT NULL,
    brand               VARCHAR(25)  NOT NULL,
    unit_cost           NUMERIC(10,2) NOT NULL CHECK (unit_cost > 0),
    list_price          NUMERIC(10,2) NOT NULL CHECK (list_price > 0),
    launch_date         DATE         NOT NULL,
    is_own_label        CHAR(1)      NOT NULL CHECK (is_own_label IN ('Y','N')),
    standard_margin_pct NUMERIC(6,4) NOT NULL,
    price_band          VARCHAR(12)  NOT NULL
);

CREATE TABLE dim_region (
    region_key          INTEGER     PRIMARY KEY,
    region_code         VARCHAR(4)  NOT NULL UNIQUE,
    region_name         VARCHAR(30) NOT NULL UNIQUE,
    nation              VARCHAR(20) NOT NULL
);

CREATE TABLE dim_store (
    store_key           INTEGER     PRIMARY KEY,
    store_code          CHAR(4)     NOT NULL UNIQUE,
    store_name          VARCHAR(40) NOT NULL,
    store_type          VARCHAR(20) NOT NULL,
    city                VARCHAR(30) NOT NULL,
    postcode            VARCHAR(8)  NOT NULL,
    store_region        VARCHAR(30) NOT NULL,             -- descriptive only; sales use fact.region_key
    size_sq_ft          INTEGER     NOT NULL CHECK (size_sq_ft >= 0),
    open_date           DATE        NOT NULL,
    is_online           CHAR(1)     NOT NULL CHECK (is_online IN ('Y','N')),
    is_like_for_like    CHAR(1)     NOT NULL CHECK (is_like_for_like IN ('Y','N'))
);

CREATE TABLE dim_channel (
    channel_key         INTEGER     PRIMARY KEY,
    channel_name        VARCHAR(20) NOT NULL UNIQUE,
    channel_type        VARCHAR(10) NOT NULL,
    description         VARCHAR(60) NOT NULL
);

-- ---------------------------------------------------------------- FACTS

-- Grain: ONE ROW PER ORDER LINE (one product within one order)
CREATE TABLE fact_sales (
    sales_line_key      INTEGER       PRIMARY KEY,
    order_id            VARCHAR(10)   NOT NULL,           -- degenerate dimension
    order_line_number   SMALLINT      NOT NULL,
    date_key            INTEGER       NOT NULL REFERENCES dim_date(date_key),
    order_datetime      TIMESTAMP     NOT NULL,
    customer_key        INTEGER       NOT NULL REFERENCES dim_customer(customer_key),
    product_key         INTEGER       NOT NULL REFERENCES dim_product(product_key),
    store_key           INTEGER       NOT NULL REFERENCES dim_store(store_key),
    channel_key         INTEGER       NOT NULL REFERENCES dim_channel(channel_key),
    region_key          INTEGER       NOT NULL REFERENCES dim_region(region_key),
    quantity            SMALLINT      NOT NULL CHECK (quantity BETWEEN 1 AND 20),
    unit_price          NUMERIC(10,2) NOT NULL CHECK (unit_price > 0),
    unit_cost           NUMERIC(10,2) NOT NULL CHECK (unit_cost > 0),
    discount_pct        NUMERIC(5,4)  NOT NULL CHECK (discount_pct BETWEEN 0 AND 0.6),
    gross_sales         NUMERIC(12,2) NOT NULL,
    discount_amount     NUMERIC(12,2) NOT NULL,
    net_sales           NUMERIC(12,2) NOT NULL,           -- = Revenue
    cost_amount         NUMERIC(12,2) NOT NULL,
    gross_profit        NUMERIC(12,2) NOT NULL,
    payment_method      VARCHAR(15)   NOT NULL,
    is_price_imputed    CHAR(1)       NOT NULL CHECK (is_price_imputed IN ('Y','N')),
    UNIQUE (order_id, order_line_number),
    CHECK (net_sales = gross_sales - discount_amount)
);

-- Grain: ONE ROW PER RETURNED ORDER LINE
CREATE TABLE fact_returns (
    return_key          INTEGER       PRIMARY KEY,
    return_id           VARCHAR(10)   NOT NULL UNIQUE,
    sales_line_key      INTEGER       NOT NULL REFERENCES fact_sales(sales_line_key),
    order_id            VARCHAR(10)   NOT NULL,
    order_line_number   SMALLINT      NOT NULL,
    date_key            INTEGER       NOT NULL REFERENCES dim_date(date_key),   -- return date
    order_date_key      INTEGER       NOT NULL REFERENCES dim_date(date_key),   -- original order date
    customer_key        INTEGER       NOT NULL REFERENCES dim_customer(customer_key),
    product_key         INTEGER       NOT NULL REFERENCES dim_product(product_key),
    store_key           INTEGER       NOT NULL REFERENCES dim_store(store_key),
    channel_key         INTEGER       NOT NULL REFERENCES dim_channel(channel_key),
    region_key          INTEGER       NOT NULL REFERENCES dim_region(region_key),
    return_qty          SMALLINT      NOT NULL CHECK (return_qty >= 1),
    refund_amount       NUMERIC(12,2) NOT NULL CHECK (refund_amount >= 0),
    return_reason       VARCHAR(30)   NOT NULL,
    return_method       VARCHAR(10)   NOT NULL,
    days_to_return      SMALLINT      NOT NULL CHECK (days_to_return >= 0)
);

-- ---------------------------------------------------------------- INDEXES
-- Foreign-key columns are what we filter and join on most.
CREATE INDEX ix_sales_date     ON fact_sales (date_key);
CREATE INDEX ix_sales_customer ON fact_sales (customer_key);
CREATE INDEX ix_sales_product  ON fact_sales (product_key);
CREATE INDEX ix_sales_store    ON fact_sales (store_key);
CREATE INDEX ix_sales_order    ON fact_sales (order_id);
CREATE INDEX ix_returns_date   ON fact_returns (date_key);
CREATE INDEX ix_returns_line   ON fact_returns (sales_line_key);
