# START HERE — Study Notes for the UK Retail Sales & BI Dashboard

These notes explain **every step of the project in simple words**: what was done, why, and how to talk about it in
an interview. Read them in order. Each file follows the same pattern:

1. **In one line**: the idea in a sentence
2. **Simple explanation**: no jargon
3. **What we did**: the actual steps and files
4. **Why**: the reasoning (interviewers care most about this)
5. **Interview questions + model answers**
6. **Common mistakes**

## Study order (about 2–3 weeks at 1–2 hours a day)

| Day | Read | Then do |
| --- | --- | --- |
| 1 | `15_project_explained_simply.md` | Say the 2-minute pitch out loud 3 times |
| 2 | `01_business_analysis_notes.md` | Re-write the problem statement in your own words |
| 3 | `02_data_model_notes.md` | Draw the star schema on paper from memory |
| 4 | `03_data_generation_notes.md` | Open `scripts/01_generate_data.py`, find each planted pattern |
| 5 | `04_data_quality_notes.md` | Open `documentation/data_quality_report.md`, explain 5 rules |
| 6 | `05_excel_notes.md` | Open the workbook, rebuild one PivotTable |
| 7 | `06_power_query_notes.md` | Paste one `.pq` script into Power BI |
| 8–10 | `07_sql_notes.md` | Run the SQL yourself; re-type 10 queries without looking |
| 11–13 | `09_power_bi_notes.md` + `10_dax_notes.md` | **Build the .pbix** following `powerbi/01_build_guide.md` |
| 14 | `11_insights_and_decisions_notes.md` | Explain 3 insights using Finding → Evidence → … |
| 15 | `13_presentation_notes.md` | Present the 10 slides in 8 minutes |
| 16+ | `14_interview_question_bank.md` | Practise with a friend; answer without reading |

> **Golden rule:** this is a **simulated** project. Always say so: *"I built a simulated end-to-end retail analytics
> project with synthetic data designed to behave like a real retailer."* Honesty is a strength in interviews.
> Never claim it was a real company or that you saved real money.

## The project in one picture

```
Business problem → Raw messy data → Cleaning (40 rules) → PostgreSQL star schema
     → 40 SQL questions → Power BI model + DAX → 5-page dashboard
     → 10 insights → 10 prioritised recommendations → 10-slide executive deck
```

## Key numbers to remember (they come up in every interview)

| Number | Meaning |
| --- | --- |
| £8.55M | Total revenue over 2 years (£3.96M in 2024 → £4.58M in 2025, +15.7%) |
| +9.4% | Gross profit growth, slower than revenue: **the core story** |
| 43.3% → 41.0% | Gross margin fell 2.4 points |
| 185,858 | Order lines (fact table rows); 89,528 orders |
| 12,500 | Customers (after removing 180 duplicates) |
| 1,220 / 24 / 12 | Products / stores (+ online hub) / UK regions |
| 19% vs 6% | Electronics' share of revenue vs its share of gross profit |
| 18.7% | Discount at which Electronics starts losing money |
| 10% → 28% | Stride Lab (footwear brand) return rate, 2024 → 2025 |
| 40 / 13 / 40 | Cleaning rules / SQL data checks / SQL business questions |

## Glossary (simple meanings)

| Word | Meaning |
| --- | --- |
| KPI | Key Performance Indicator: a number that shows if the business is doing well (e.g. revenue) |
| Revenue / Net sales | Money from sales after discounts (no VAT) |
| Gross profit | Revenue − cost of the goods sold |
| Gross margin % | Gross profit ÷ revenue: how many pence of profit per £1 of sales |
| AOV | Average Order Value = revenue ÷ number of orders |
| Return rate | Refunds ÷ revenue |
| YoY / MoM | Year-over-year / month-over-month change |
| LFL | Like-for-like: compare only stores open in both periods |
| Fact table | The table of events/transactions with numbers (sales lines) |
| Dimension table | The descriptive "who/what/where/when" tables (product, customer, date…) |
| Grain | What one row of a fact table means (here: one product line in one order) |
| Star schema | One fact table in the middle, dimensions around it, like a star |
| Surrogate key | A simple ID number we create (ProductKey = 17) instead of the source code |
| ETL / pipeline | Extract → Transform → Load: getting data from source to the report |
| DAX | The formula language of Power BI |
| Power Query (M) | Power BI/Excel tool for cleaning and shaping data |
| RFM | Recency, Frequency, Monetary: a way to group customers by behaviour |
| Cohort | A group of customers who started in the same period |
