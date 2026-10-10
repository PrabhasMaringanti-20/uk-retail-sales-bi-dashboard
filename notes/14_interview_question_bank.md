# Notes 14 — Interview Question Bank (Phase 16)

How to practise: a friend reads the question and you answer **out loud without notes**. Then they ask the follow-up
("Why?" or "What would you do differently?"). The model answers are guides. Use your own words, because memorised
answers sound memorised.

---

## A. The project overall

**1. Tell me about a project you're proud of.** *(the most common question; use `15_project_explained_simply.md`)*

**2. Is this real data?**
No. A simulated UK retailer with synthetic data I generated, with realistic patterns built in. I say this upfront; the
skills and methods are real.

**3. What was the hardest part?**
Data quality decisions: deciding what to fix, flag or quarantine without guessing. For example, blank customer IDs
looked like errors but were legitimate guest shoppers, worth £1.36M of revenue.
→ *Follow-up: what would have happened if you'd deleted them?* Revenue understated by about 16%, and in-store
performance would look wrongly weak.

**4. What would you do differently?**
Start with real screenshots of the Power BI report earlier, add an inventory table, and automate refresh (scheduled
pipeline + Power BI Service gateway). I'd also add a few more automated tests to the Python cleaning.

**5. How long did it take, and how did you use AI?**
Be honest about how you actually built it. A good answer: *"I used AI as a mentor and code reviewer, like a senior
colleague. It helped me draft code and documentation faster, but I ran everything, checked every number against the
database, and I can explain every decision."* Then prove it by explaining any query they point at.

## B. Business analysis
**6. How did you define the problem?** Disconnected reports → no trusted view of profit. Objectives were written as measurable outcomes.
**7. Who were the stakeholders?** CEO/CFO (manage closely), retail ops, e-commerce, category managers, customer service, IT. Influence/interest grid.
**8. Which KPIs and why?** Revenue, gross profit, margin, orders, AOV, customers, return rate, YoY. Each defined in writing so SQL and Power BI agree.
**9. What was out of scope?** Inventory, marketing spend, overheads, so gross profit, not net profit.
**10. How would you gather requirements in a real job?** Stakeholder interviews, current report review, KPI definition workshop, mock-ups for sign-off, then iterate.

## C. SQL
**11. WHERE vs HAVING?** Rows before grouping vs groups after.
**12. INNER vs LEFT JOIN, with an example from your project?** Returns: LEFT JOIN, because most sales have no return.
**13. How do you count orders when the table is at line level?** `COUNT(DISTINCT order_id)`.
**14. Write top 3 products per category.** `RANK() OVER (PARTITION BY category ORDER BY revenue DESC)` in a CTE, then `WHERE rnk <= 3`.
**15. YoY growth in SQL?** Monthly CTE + `LAG(revenue, 12)`.
**16. Running total?** `SUM(revenue) OVER (PARTITION BY year ORDER BY month)`.
**17. RANK vs DENSE_RANK vs ROW_NUMBER?** Ties: 1,2,2,4 / 1,2,2,3 / 1,2,3,4.
**18. How did you find duplicates?** `GROUP BY order_id, line HAVING COUNT(*) > 1`; prevented with a UNIQUE constraint.
**19. What constraints did you use and did they help?** PK, FK, UNIQUE, NOT NULL, CHECK. Yes: they caught 3 real bugs (column width, a blank age band, sales before launch).
**20. Explain your RFM query.** NTILE(5) for recency, frequency and monetary, then CASE rules → Champions, Loyal, At risk…
**21. How would you speed up a slow query?** Check `EXPLAIN ANALYZE`, index the join/filter columns, pre-aggregate, avoid functions on indexed columns in WHERE.

## D. Data modelling
**22. Fact vs dimension?** Events with numbers vs descriptions.
**23. What's the grain of FactSales?** One product line per order.
**24. Why a star schema?** Fast, simple, what Power BI is optimised for; each description is stored once.
**25. How did you handle the two dates on returns?** Role-playing date: return date active, order date inactive + USERELATIONSHIP.
**26. Why not link FactReturns to FactSales?** Fact-to-fact relationships cause ambiguity; both connect through shared dimensions.
**27. What's a surrogate key?** An integer key we generate; fast and stable.
**28. How did you deal with ambiguous relationships?** Region only via the fact; no Store→Region path; single-direction filters.
**29. What's an SCD?** Slowly changing dimension. Type 1 overwrites; Type 2 keeps history with new rows and date ranges.

## E. Power BI & DAX
**30. Explain filter context.** The set of filters (slicers, visual rows, CALCULATE) a measure is evaluated in.
**31. What does CALCULATE do?** Changes the filter context, then evaluates.
**32. Measure vs calculated column?** Query time vs refresh time; aggregate vs slice.
**33. YoY % in DAX?** SAMEPERIODLASTYEAR inside CALCULATE, then DIVIDE.
**34. Why mark a date table?** Time intelligence needs a complete, contiguous date column.
**35. How did you check your numbers were right?** Reconciliation table (Year × Revenue/GP/Orders) against SQL; SUMX check measure.
**36. Import or DirectQuery?** Import: small data, fastest, full DAX.
**37. How do you secure a report for store managers?** Row-level security roles; dynamic RLS with USERPRINCIPALNAME and a user-store table.
**38. How did you design the pages?** One audience and question per page; KPIs with comparisons at the top; trend + breakdowns; synced slicers.

## F. Data quality
**39. Name the data-quality dimensions.** Completeness, validity, consistency, uniqueness, integrity (referential), accuracy.
**40. Fix, flag or quarantine: give an example of each.** Channel spelling (fix); imputed price (flag); 30 Feb date (quarantine).
**41. How do you de-duplicate customers?** Normalise email (trim, lower case), keep the earliest record, re-point transactions. Risks: shared family emails → also check name/postcode in real life.
**42. How do you make cleaning repeatable?** Script it (Python/Power Query), log every rule, and run checks on every load.

## G. Business case / thinking
**43. Revenue is up but profit is down. What do you look at?** Mix (category/channel), price vs cost changes, discount depth, returns, one-off events. Decompose margin.
**44. The CEO wants a 30%-off Black Friday on everything. What do you say?** Electronics breaks even at about 19% off, so 30% off loses money on every unit. Propose category-specific caps and test.
**45. Online returns are 12%. Should we charge for returns?** Maybe, but first fix the causes: sizing (Stride Lab), faulty products (Voltix), and fit guidance. A charge risks losing customers; test it on a segment first.
**46. Which store would you close?** I wouldn't decide from gross margin alone: no rent or staff costs are in the data. Newcastle's problem is discounting (fixable); the outlet's low margin is by design. I'd need full store P&L data.
**47. How would you measure if the discount cap worked?** A/B test: regions with the cap vs without; compare margin, revenue and units over the same period, with like-for-like stores.
**48. What's the biggest risk in your recommendations?** Volume loss when cutting discounts. Mitigation: pilot, measure, then roll out.

## H. Behavioural (use STAR: Situation, Task, Action, Result)
**49. Tell me about a time you found an error in your own work.** The generator produced sales before product launch dates; my SQL check failed for 356 rows. I traced it to month-end vs month-start logic, fixed it at source and re-ran the whole pipeline. Lesson: automated checks catch your own bugs.
**50. Tell me about explaining something technical to a non-technical audience.** The margin bridge: instead of formulas, "we lost 2.4p per £1 of sales: 1.6p because suppliers charged more, 0.8p because we gave bigger discounts."

---

## Tough follow-ups to practise
- "Why 30% volume loss in your estimate? Where did that come from?" → *It's an assumption, stated openly; I'd test it.*
- "Your data is synthetic, so you designed the answers. Isn't that circular?" → *I designed the behaviours, but I still
  had to find, measure and size them correctly with SQL. Several things I didn't plan came out too: the hero headphones
  product at 15% margin and Click & Collect turning loss-making at 40%+ discount in December 2025. The skill being shown is the method.*
- "What would a real retailer's data look like differently?" → *Messier keys, more systems, VAT, multi-currency,
  promotions tables, stock, and much bigger volumes.*
