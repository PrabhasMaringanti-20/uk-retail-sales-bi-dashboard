# Notes 07 — SQL & PostgreSQL (Phase 7)

**Files:** `sql/01_create_schema.sql` … `sql/04_business_questions.sql`, `sql/README.md` (every query explained with its
real result), `sql/results/04_business_questions_output.txt`

## In one line
We built a PostgreSQL database with rules (constraints) and answered 40 business questions, from simple totals to
cohort retention.

## Simple explanation
A database is a set of tables that **enforce rules**: no duplicate IDs, no sale for a product that doesn't exist, no
negative quantity. SQL is the language for asking questions of it: *"What was revenue by category in 2025?"*

## Part A — Building the database
| Concept | Example | Why |
| --- | --- | --- |
| `CREATE SCHEMA` | `northstar` | Keeps project tables together |
| `PRIMARY KEY` | `product_key` | Unique row ID |
| `FOREIGN KEY … REFERENCES` | `fact_sales.product_key → dim_product` | No orphan sales |
| `UNIQUE` | `(order_id, order_line_number)` | No duplicate lines |
| `NOT NULL` | `age_band` | Caught a real pandas bug |
| `CHECK` | `quantity BETWEEN 1 AND 20`, `net_sales = gross_sales - discount_amount` | Business rules in the database |
| `INDEX` | on foreign keys | Faster joins and filters |
| `\copy` | load CSV from the client | No superuser needed |

**Load order:** dimensions first, then facts. The facts' foreign keys need the dimension rows to exist already.

## Part B — Query skills, from basic to advanced

### Level 1: Fundamentals
```sql
SELECT p.category,
       SUM(s.net_sales)                         AS revenue,
       SUM(s.gross_profit) / SUM(s.net_sales)   AS margin
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key   -- JOIN: bring in descriptions
WHERE s.discount_pct > 0                              -- WHERE: filter ROWS before grouping
GROUP BY p.category                                   -- one result row per category
HAVING SUM(s.net_sales) > 100000                      -- HAVING: filter GROUPS after grouping
ORDER BY revenue DESC;
```
- **Logical order SQL runs in:** FROM → JOIN → WHERE → GROUP BY → HAVING → SELECT → ORDER BY → LIMIT.
  That's why you can't use a SELECT alias inside WHERE.
- **CASE**: makes buckets, e.g. discount bands (Q09).
- **LEFT JOIN vs INNER JOIN**: returns are a LEFT JOIN (Q12), because most sales are never returned and an INNER JOIN
  would drop them.
- **FILTER**: `SUM(x) FILTER (WHERE year = 2025)` is PostgreSQL's neat way to pivot years into columns (Q04).
  It's the same as `SUM(CASE WHEN year = 2025 THEN x END)`, which works in every database.

### Level 2: CTEs and subqueries
```sql
WITH monthly AS (                       -- CTE = a named temporary result
    SELECT d.year_month, SUM(s.net_sales) AS revenue
    FROM fact_sales s JOIN dim_date d ON d.date_key = s.date_key
    GROUP BY d.year_month
)
SELECT * FROM monthly WHERE revenue > 400000;
```
- **CTE vs subquery:** same power. A CTE is easier to read and can be reused within the query.
- **Subquery in HAVING** (Q15): compare each store with the overall average.

### Level 3: Window functions (very common in interviews)
A window function calculates **across rows without collapsing them** (unlike GROUP BY).
```sql
SELECT year_month, revenue,
       LAG(revenue)     OVER (ORDER BY year_month)          AS prev_month,     -- Q24
       LAG(revenue, 12) OVER (ORDER BY year_month)          AS same_month_ly,  -- Q25
       SUM(revenue)     OVER (PARTITION BY year ORDER BY year_month)  AS ytd, -- Q26 running total
       AVG(revenue)     OVER (ORDER BY year_month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3  -- Q29
FROM monthly;
```
| Function | Use | Query |
| --- | --- | --- |
| `LAG` / `LEAD` | previous / next row | MoM, YoY, days between orders, next purchase |
| `RANK` | 1,2,2,4 (gaps after ties) | top 3 per category (Q27) |
| `DENSE_RANK` | 1,2,2,3 (no gaps) | |
| `ROW_NUMBER` | 1,2,3,4 (always unique) | one best store per region (Q28) |
| `NTILE(5)` | split into 5 equal groups | RFM scores (Q35) |
| `SUM() OVER (ORDER BY …)` | running total | Pareto (Q32) |
| `PARTITION BY` | restart for each group | per category, per customer, per year |

### Level 4: Business analysis patterns
- **Cohort retention (Q34):** group customers by first purchase quarter, then the % active N quarters later.
- **RFM (Q35):** Recency, Frequency, Monetary scores → Champions, Loyal, At risk, Lapsed.
- **Break-even discount (Q36):** 1 − cost ÷ list price. Electronics = 18.7%.
- **Margin decomposition (Q37):** separate the discount effect from the cost effect.
- **Basket analysis (Q40):** self-join on order_id with `a.category < b.category` so each pair counts once.

## The 7 traps (interviewers love these)
1. **Lines ≠ orders:** `COUNT(*)` counts lines. Orders = `COUNT(DISTINCT order_id)`. AOV uses distinct orders.
2. **Average of ratios:** margin = `SUM(profit)/SUM(revenue)`, never `AVG(margin)`.
3. **INNER JOIN drops rows:** use LEFT JOIN when the right side may be missing.
4. **Divide by zero:** `NULLIF(x, 0)`.
5. **NULL comparisons:** `= NULL` never works; use `IS NULL`.
6. **Incomplete periods:** December 2025 return rate looks low because returns haven't come back yet.
7. **Data window bias:** Q1 2024 "new customers" includes people who bought before 2024.

## Interview questions

**Q: WHERE vs HAVING?** WHERE filters rows before grouping; HAVING filters groups after aggregation.

**Q: RANK vs DENSE_RANK vs ROW_NUMBER?** With ties at 2nd place: RANK 1,2,2,4; DENSE_RANK 1,2,2,3; ROW_NUMBER 1,2,3,4.

**Q: How did you calculate YoY growth?** Aggregate by month in a CTE, then `LAG(revenue, 12) OVER (ORDER BY year, month)`
gives the same month last year, and growth = revenue ÷ last year − 1.

**Q: How do you find the top N per group?** `RANK()` or `ROW_NUMBER()` with `PARTITION BY group ORDER BY measure DESC`
in a CTE, then `WHERE rnk <= N`.

**Q: What is a CTE and why use one?** A named temporary result defined with WITH. It makes multi-step logic readable,
and you can use calculated columns in the next step, e.g. ordering by an expression on aliases (Q19).

**Q: How did you make sure your SQL was right?** A reconciliation total that every tool must match, 13 automated
PASS/FAIL checks, and sanity checks: shares add to 100%, and lines vs orders are consistent.

**Q (practical): Write a query for the top 3 products by revenue in each category.** See Q27. Practise writing it
from memory.

## Practice (do these without looking)
1. Revenue and margin by region for 2025 only.
2. The month with the highest revenue in each year (ROW_NUMBER).
3. Customers whose 2025 revenue fell versus 2024 (FILTER or CASE + HAVING).
4. Return rate by payment method (is Klarna higher?).
