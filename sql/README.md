# SQL — PostgreSQL database and 40 business questions

> Simulated data (fictional NorthStar Retail UK). All numbers come from `results/04_business_questions_output.txt`,
> produced by running the scripts below against PostgreSQL 16.

## Files

| File | What it does |
| --- | --- |
| `01_create_schema.sql` | Creates the `northstar` schema: 6 dimensions, 2 facts, PK / FK / CHECK constraints, indexes |
| `02_load_data.sql` | Loads `data/clean/*.csv` with `\copy` (dimensions first, then facts) |
| `03_data_quality_checks.sql` | 13 PASS/FAIL tests after loading + the reconciliation totals |
| `04_business_questions.sql` | 40 business questions, grouped from basic to advanced |
| `results/04_business_questions_output.txt` | The actual output of every query |

## How to run

```bash
createdb northstar
psql -d northstar -f sql/01_create_schema.sql
psql -d northstar -f sql/02_load_data.sql
psql -d northstar -f sql/03_data_quality_checks.sql
psql -d northstar -f sql/04_business_questions.sql
```
Run from the project root. In pgAdmin, open each file in the Query Tool. `\copy` is a psql command, so for
pgAdmin use *Import/Export* on each table instead.

## The reconciliation numbers

Every report (Excel, Power BI, presentation) must match these:

| Revenue | Gross profit | Margin | Orders |
| ---: | ---: | ---: | ---: |
| £8,545,887.73 | £3,595,003.75 | 42.07% | 89,528 |

## Constraints that caught real bugs

While building, the database itself rejected bad data, which is why constraints are worth it:
- `VARCHAR(5)` on postcode district rejected the value `Unknown`, so the column was widened.
- `NOT NULL` on `age_band` exposed a pandas bug where missing ages became blank instead of `Unknown`.
- Check *"no sales before product launch date"* failed for 356 rows and exposed a generator bug. It was fixed at source.

## Skill progression

| Level | SQL skills | Questions |
| --- | --- | --- |
| 1 Fundamentals | SELECT, WHERE, GROUP BY, HAVING, ORDER BY, CASE, JOIN, LEFT JOIN, FILTER | Q01–Q12 |
| 2 Intermediate | CTEs, scalar & correlated subqueries, conditional aggregation | Q13–Q23 |
| 3 Window functions | LAG, LEAD, RANK, ROW_NUMBER, NTILE, running totals, moving averages, ROLLUP | Q24–Q33 |
| 4 Analysis | cohort retention, RFM, break-even discount, margin decomposition, basket analysis | Q34–Q40 |

---

## Question by question

Format: **Business question → SQL technique → Result → What it means for the business**

### Level 1 — Fundamentals

**Q01 Headline KPIs.** Aggregates (`SUM`, `COUNT DISTINCT`), `FILTER` to exclude guests from the customer count.
→ Revenue £8.55M, gross profit £3.60M, margin 42.1%, 89,528 orders, 9,530 known customers, AOV £95.45.
→ This is the baseline every other number reconciles to.

**Q02 2024 vs 2025.** JOIN to `dim_date`, GROUP BY year.
→ Revenue £3.96M → £4.58M (**+15.7%**), but gross profit only £1.72M → £1.88M (**+9.4%**). Margin 43.3% → **41.0%**.
→ **The core story: growth is real, but each £ of sales earns less profit.**

**Q03 Category mix.** Window function `SUM(SUM(x)) OVER ()` for % of total without a subquery.
→ Electronics is the largest category (19.3% of revenue) but earns only 5.9% of gross profit (13.0% margin).
Beauty: 12.3% of revenue, 17.8% of profit (60.9% margin).
→ Revenue rank ≠ profit rank. Category decisions must look at profit.

**Q04 Channels.** Conditional aggregation with `FILTER (WHERE year = …)` to pivot years into columns.
→ Mobile App +49.0%, Click & Collect +23.8%, Website +22.4%, In-Store +4.4%.
→ Growth is coming from digital channels.

**Q05 Top 10 products.** GROUP BY + ORDER BY + LIMIT.
→ #1 is Pixelpoint Over-Ear Headphones (£297K) at only 15% margin; the Kids Tablet (#7, £63K) earns 3.6%.
→ Some best sellers barely make money.

**Q06 Weakest-margin products.** HAVING on revenue (≥ £10K) to ignore tiny sellers; `FILTER` for lines below cost.
→ All 12 weakest products are Electronics. 16–26% of their order lines were sold **below cost**.
**Q06b:** £41.8K of gross profit was lost on lines sold below cost, almost all in Electronics (13% of Electronics revenue).
→ Electronics discounts push prices under cost.

**Q07 Sub-categories under 30% margin.** `HAVING` on a ratio.
→ Only Electronics sub-categories qualify (11.9%–15.3%).

**Q08 Regions.** JOIN `dim_region`. Note: region = store region for store sales, delivery region for online sales.
→ London 19.6% of revenue. North East has the lowest margin (38.6%) and South East is next (39.8%).
→ Both low-margin regions are explained by a single store each (see Q14).

**Q09 Discount bands.** `CASE` to bucket a continuous value.
→ Margin by discount band: none 46.2%, 5–15% 38.4%, 20–25% 28.9%, 30–35% 18.4%, 40%+ **5.6%**.
→ Deep discounts (30%+) bring in £0.7M of revenue at very little profit.

**Q10 Weekend vs weekday.** CASE on `is_weekend`; orders per day (divide by distinct days, not total orders).
→ In-store: 81 orders/day at weekends vs 61 on weekdays (+33%). Online is flat across the week.
→ Store staffing should follow weekends; online promotions can run any day.

**Q11 Payment mix.** Window `PARTITION BY channel` for share within channel.
→ Contactless is 52% of in-store orders; Klarna (buy-now-pay-later) is about 14% of online orders.

**Q12 Return rate by category.** `LEFT JOIN` returns (most lines are never returned, so an INNER JOIN would drop them).
→ Footwear 14.8%, Clothing 12.6%, Electronics 7.6% … Beauty 1.5%.

### Level 2 — Intermediate

**Q13 Monthly KPI trend.** CTE to aggregate first, then calculate ratios.
→ Peaks in Nov–Dec. **January 2025 margin was only 28.2%** (January sale), with July and November next lowest.

**Q14 Store league table.** CTE + `revenue / size_sq_ft` (sales density).
→ Two outliers: **Bluewater Outlet at 24.7% margin** (29% average discount; it is an outlet) and
**Newcastle Eldon Square at 37.0%** (15.3% average discount vs about 5% elsewhere). All other stores are 43–45%.
→ Newcastle is a full-price store discounting like an outlet. That is a management issue, not a market one.

**Q15 Stores below average.** Subquery in `SELECT` and `HAVING` (compare each group to the overall figure).
→ Only Bluewater, Newcastle and (marginally) Reading are below the 43.3% average.

**Q16 Return rate by channel and year.** Two-level GROUP BY with LEFT JOIN.
→ Website 11.0% → 12.5%, App 10.1% → 12.2%, In-Store 4.2% → 4.5%.
→ Online returns are 2.5–3× store returns and rising.

**Q17 Return reasons.** CTE + window share within category.
→ Footwear: 63% "wrong size / fit". Clothing: 51%. Electronics: 53% "faulty / defective".
→ Different categories need different fixes (fit guidance vs supplier quality).

**Q18 High-return products.** HAVING-style filter on a ratio with a minimum volume.
→ The top items are **Voltix** smart-home devices (doorbell 30%, camera 29%, smart bulb 25.5% of units returned) and
**Stride Lab** boots.

**Q19 Brand returns 2024 vs 2025.** `FILTER` inside a CTE (an alias can't be used inside an ORDER BY expression).
→ **Stride Lab: 10.2% → 28.2% (+18 points)**. All other brands moved by less than 4 points.
→ A single supplier problem, most likely a sizing change in 2025 (83% of its 2025 returns are "wrong size / fit").

**Q20 Trading periods.** GROUP BY a `dim_date` attribute. This is why a rich date dimension is useful.
→ Black Friday week sells £23.2K/day but at 30.1% margin; the January sale earns 31.3%. Regular trading earns 44.7%.

**Q21 New vs returning customers.** CTE for first order date, then CASE.
→ Returning customers place about 93% of orders. Q1 2024 looks "new-heavy" only because the data starts in Jan 2024
(a **data-window bias**).

**Q22 Segment value.** Excludes the Guest row, because one "customer" with 15,000 orders would distort averages.
→ Premium: £1,380 per customer, 10.7 orders, AOV £128.70. Value: £508 per customer, AOV £75.

**Q23 Guest share.** `FILTER` ratio.
→ About 32–34% of in-store revenue in every store is from unidentified shoppers (no loyalty card scanned).

### Level 3 — Window functions

**Q24 MoM growth.** `LAG(revenue) OVER (ORDER BY month)`.
→ MoM swings ±50% because of seasonality (Nov +45%, Jan −50%), so MoM alone is a misleading KPI here.

**Q25 YoY by month.** `LAG(revenue, 12)` (the same month last year).
→ Revenue grew every month (+8% to +24%), but **profit fell YoY in January (−11.3%) and July (−3.9%)**, both sale months.

**Q26 YTD running total.** `SUM() OVER (PARTITION BY year ORDER BY month ROWS UNBOUNDED PRECEDING)`.
→ 2025 YTD passed the full 2024 total (£3.96M) during December; at end-November it was £3.95M.

**Q27 Top 3 per category.** `RANK() OVER (PARTITION BY category ORDER BY revenue DESC)`.
→ Interview point: RANK vs DENSE_RANK vs ROW_NUMBER differ only when there are ties.

**Q28 Best store per region.** `ROW_NUMBER()` = exactly one winner per region.

**Q29 3-month moving average.** `AVG() OVER (ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)`. Smooths the seasonal noise.

**Q30 Days between orders.** `LAG(order_date) OVER (PARTITION BY customer)`.
→ Median gap: Premium 20 days, Mainstream 27, Value 31.

**Q31 90-day repurchase.** `LEAD()` to look at each customer's next order.
→ About 49–52% of new customers buy again within 90 days. The App is highest (52%), In-Store lowest (48.6%).

**Q32 Pareto.** Running cumulative share with `SUM() OVER (ORDER BY revenue DESC)`.
→ **14% of customers generate 50% of known-customer revenue; 38% generate 80%.**

**Q33 Like-for-like growth.** `GROUP BY ROLLUP` adds a total row.
→ LFL stores +5.3%, online hub +29.0%, new Sheffield store +56% (it only opened in July 2024).
→ Headline growth (+15.7%) flatters the store estate. Always report LFL.

### Level 4 — Advanced analysis

**Q34 Cohort retention.** Customers grouped by first-purchase quarter; % active N quarters later. Future quarters
return NULL (not 0%) because they haven't happened yet.
→ Roughly 40–57% of a cohort buy again in the next quarter; about 42–48% are still active a year later.

**Q35 RFM segmentation.** `NTILE(5)` scores for Recency, Frequency, Monetary, then CASE rules.
→ Champions (23% of customers) = 55% of revenue. **At risk: 1,450 customers who were loyal, holding 14.6% of revenue,
with no purchase for about 8 months.**

**Q36 Break-even discount.** Break-even discount = 1 − cost ÷ list price.
→ **Electronics breaks even at an 18.7% discount**, so any Electronics discount of 20%+ loses money
(−10% margin at 20–30%, −32% at 35%+). Beauty can absorb 62%.
→ Discount rules must be set per category, not as one blanket "30% off".

**Q37 Why margin fell.** Margin = 1 − cost% ÷ (1 − discount%).
→ Discount rate 5.85% → 7.12% of gross sales; cost 53.4% → 54.8% of gross sales.
→ Roughly −0.8 pts from more discounting and −1.6 pts from supplier cost inflation not passed on to prices
(see `screenshots/09_margin_bridge.png`).

**Q38 Profit after returns.** Assumes returned goods are not resold (conservative).
→ Website margin falls from 40.1% to **28.3%** after refunds; In-Store from 43.6% to 39.3%.
→ Online looks almost as profitable as stores until returns are counted.

**Q39 Online apparel returns by order month.**
→ About 16% in 2024 → **27–28% in H2 2025**. December 2025 shows 14.9% only because those orders have had little time
to be returned (**return-lag bias**). Never read the most recent month at face value.

**Q40 Basket pairs.** Self-join on `order_id` with `a.category < b.category` to avoid counting each pair twice.
→ Beauty + Clothing appear together in 8.2% of all orders, the strongest pair, so they are good for cross-promotion.

---

## Common SQL interview traps shown here
1. **COUNT(\*) vs COUNT(DISTINCT order_id)**: lines are not orders (AOV must divide by distinct orders).
2. **INNER vs LEFT JOIN** for returns: an INNER JOIN silently drops lines that were never returned.
3. **WHERE vs HAVING**: WHERE filters rows *before* grouping; HAVING filters groups *after*.
4. **Averages of ratios**: margin = SUM(profit) / SUM(revenue), never AVG(margin per line).
5. **Division by zero**: `NULLIF(x, 0)`.
6. **Aliases** can't be used in WHERE or inside ORDER BY expressions, so use a CTE.
7. **Incomplete periods**: the latest month's return rate and the first quarter's "new customers" are both biased.
