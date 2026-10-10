# Notes 15 — Explain the Project (scripts to say out loud)

## The 30-second version (for "tell me about yourself")
> "I built an end-to-end retail analytics project for a simulated UK retailer, NorthStar. I generated two years of
> realistic data (185,000 order lines across 24 stores and online), cleaned it with 40 documented rules, modelled it as a
> star schema in PostgreSQL, answered 40 business questions in SQL, and built a Power BI dashboard with DAX. The main
> finding was that revenue grew 15.7% but profit only 9.4%, because of discounting and Electronics margins. I turned
> that into prioritised recommendations worth about £120–140K of gross profit a year, as an illustrative estimate."

## The 2-minute version (STAR)
**Situation:** NorthStar (fictional) had stores and e-commerce, but four reports that disagreed. Revenue was growing, but
nobody knew where profit was lost.

**Task:** Build one trusted source of truth and explain what's happening, why, and what to do.

**Action:**
1. **Business analysis:** problem statement, stakeholders, KPI definitions (e.g. AOV = revenue ÷ distinct orders).
2. **Data:** simulated realistic data, then deliberately added messy problems: duplicates, 14 channel spellings, bad dates.
3. **Cleaning:** 40 rules; fix if certain, flag if uncertain, quarantine if untrustworthy. Validity went from 92% to 100%.
4. **Modelling:** star schema with two fact tables (sales and returns) and six dimensions, loaded into PostgreSQL with
   constraints.
5. **SQL:** 40 questions, from GROUP BY to window functions, cohorts and RFM.
6. **Power BI + DAX:** measures like margin, YoY and return rate; 5 pages for different audiences.

**Result:** Found that margin fell 2.4 points (1.6 cost inflation, 0.8 discounting), that Electronics sells below cost
above a ~19% discount, and that one footwear supplier tripled its return rate. Recommended discount guardrails, supplier
action and a win-back campaign, prioritised on an impact/effort matrix.

## Explain it to a non-technical person (your family)
"Imagine a shop chain that sells more every year but doesn't make more money. I built a system that collects all
their sales, cleans up the mistakes, and shows on one screen where money is made and lost. It showed they give away too
much in discounts, especially on electronics, and that one brand of shoes keeps getting sent back because the sizes
are wrong."

## How each skill maps to the job advert
| Job asks for | Where it is in this project |
| --- | --- |
| SQL | 40 queries, window functions, constraints, data-quality checks |
| Power BI / DAX | model, 40+ measures, 5-page design, RLS concept |
| Excel | XLOOKUP, SUMIFS, pivots, reconciliation |
| Data cleaning | 40 rules, before/after metrics, quarantine |
| Data modelling | star schema, grain, keys, role-playing date |
| Stakeholder / business skills | problem statement, stakeholder map, KPI definitions, recommendations |
| Communication | insight report, 10-slide deck |
| Python (bonus) | data generation, cleaning pipeline, charts |

## The honest-limitations line (say it before they ask)
"It's a simulated project, so it shows capability, not professional experience. I can't claim real financial
impact, and gross profit excludes overheads. But every number reconciles across SQL, Excel and Power BI, and I can
explain every decision."
