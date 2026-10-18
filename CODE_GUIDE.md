# How to Read and Explain the Code

The project has about 4,600 lines of code. **You don't need to understand all of it.** A Data Analyst / BI Analyst
interview tests **SQL, DAX, data modelling and data cleaning decisions**, not every line of Python. This guide tells
you exactly what to read, in what order, and how to explain it.

---

## 1. What matters most: three tiers

| Tier | Files | Lines | What you need |
| --- | --- | ---: | --- |
| **1: Must understand** (asked in interviews) | `sql/04_business_questions.sql` · `dax/measures.dax` · `sql/01_create_schema.sql` | ~1,080 | Explain any query or measure line by line |
| **2: Should understand** (the decisions) | `scripts/03_clean_data.py` (2 sections only) · `documentation/validation_rules.md` | ~200 of 683 | Explain *what* each cleaning rule does and *why* |
| **3: Know what it does** (one sentence each) | `scripts/01_generate_data.py` · `scripts/02_inject_quality_issues.py` · `power-query/*.pq` · `scripts/helpers/*` | the rest | Say what goes in, what comes out, why it exists |

**Is there unnecessary code?** No dead code, but not every file is equally important:
- The 4 files in `scripts/helpers/` only **build output files** (charts, Excel workbook, slides, Power BI file).
  They are tools, not analysis, so they sit in their own folder. You never need to explain them line by line.
  Keep them: they rebuild those files automatically if the data changes.
- Every check, `assert` and `record(...)` line in the cleaning script is there on purpose. They prove the cleaning
  is correct and write the cleaning log.

---

## 2. How to read a long file in VS Code (the trick)

Never read a 700-line file top to bottom. Use the "map first, then zoom in" method:

1. **Read the box at the very top** (the text between `"""` … `"""` in Python, or `-- ===` comments in SQL). It says what
   the file does, what goes in and what comes out.
2. **Fold everything:** press `Ctrl + K`, then `Ctrl + 0` (zero). Now you only see the section headers.
   (`Ctrl + K`, then `Ctrl + J` unfolds again.)
3. **Open the Outline:** in the Explorer panel on the left, open **OUTLINE** at the bottom. It lists the sections and
   functions. Click one to jump there.
4. **Jump to a line:** `Ctrl + G`, type the line number from the tables below, Enter.
5. **Find a word:** `Ctrl + F` (e.g. search `Q19` or `Gross Margin %`).
6. **For each block, ask four questions:** *What goes in? What does it do? What comes out? Why?*
   If you can answer those four, you understand the block, even if you can't write every line yourself.

---

## 3. Tier 1: the files interviewers ask about

### `sql/01_create_schema.sql` (162 lines): the database design
| Lines (approx.) | What it does | Say this |
| --- | --- | --- |
| top | `DROP SCHEMA … CREATE SCHEMA northstar` | "Creates a clean, separate area for the project's tables." |
| `CREATE TABLE dim_…` | 6 description tables (date, customer, product, region, store, channel) | "Each dimension has a primary key and descriptive columns." |
| `CREATE TABLE fact_sales` | The main table: one row per order line | "The fact table holds the numbers and a foreign key to each dimension." |
| `REFERENCES …` | Foreign keys | "The database refuses a sale for a product that doesn't exist." |
| `CHECK (…)` | Business rules, e.g. quantity 1–20, net = gross − discount | "Rules are enforced by the database itself, not just written down." |
| `CREATE INDEX` | Indexes on join columns | "Makes joins and filters faster." |

### `sql/04_business_questions.sql` (686 lines, 40 questions): the analysis
It's not one long program. It's **40 small, separate queries**, each 8–25 lines long. Every query starts with a line
like `\echo '=== Q03. Which categories drive revenue… ==='`, which is the business question in plain English.
`sql/README.md` gives the result and the meaning of each one.

| Lines | Level | What it shows |
| --- | --- | --- |
| 21–177 | Level 1, Q01–Q12 | SELECT, JOIN, GROUP BY, HAVING, CASE: the basics |
| 178–362 | Level 2, Q13–Q23 | CTEs (`WITH …`), subqueries |
| 363–536 | Level 3, Q24–Q33 | Window functions: `LAG`, `RANK`, `ROW_NUMBER`, running totals |
| 537–686 | Level 4, Q34–Q40 | Cohorts, RFM, break-even discount, margin breakdown |

**Learn these 10 really well** (they cover every skill): Q02, Q03, Q09, Q12, Q13, Q19, Q24, Q25, Q27, Q35.

**How to explain a query, example Q03 (line 47):**
```sql
SELECT p.category,
       SUM(s.net_sales) AS revenue,                                    -- add up sales per category
       SUM(s.net_sales) * 100 / SUM(SUM(s.net_sales)) OVER () AS share -- category ÷ grand total
FROM fact_sales s
JOIN dim_product p ON p.product_key = s.product_key                    -- get the category name
GROUP BY p.category                                                    -- one row per category
ORDER BY revenue DESC;
```
> "I join the sales table to the product table to get each sale's category, group by category, and sum the sales.
> The `OVER ()` window gives the grand total on every row, so I can show each category's share without a second
> query. Result: Electronics is 19% of revenue but only 6% of profit."

### `dax/measures.dax` (231 lines, 52 measures): the Power BI formulas
Each measure is just **2–8 lines**, written as `Name =` followed by the formula, and grouped in 9 numbered sections.

| Section | Measures | Learn |
| --- | --- | --- |
| 1. Base | Revenue, Cost, Gross Profit, Units | `SUM` |
| 2. Ratios | Gross Margin %, Discount Rate % | `DIVIDE` (safe division) |
| 3. Counts | Orders, Customers, Average Order Value | `DISTINCTCOUNT`, `CALCULATE` |
| 4. Returns | Return Rate %, Refunds by Order Date | `USERELATIONSHIP` |
| 5. Time | Revenue PY, YoY %, YTD, MoM, Running Total | `SAMEPERIODLASTYEAR`, `TOTALYTD`, `DATEADD` |
| 6. Share | % of Total, Company Margin | `ALL` |
| 7. Row-by-row | Revenue (SUMX check), Profit Lost Below Cost | `SUMX`, `FILTER` |
| 8. Customers | New, Returning, Repeat % | `VALUES`, `FILTER` |
| 9. Display | Ranks, colours, arrows | `RANKX`, `SWITCH` |

**Must know by heart:** Revenue, Gross Profit, Gross Margin %, Orders, Average Order Value, Customers, Revenue PY,
Revenue YoY %, Revenue YTD, Return Rate % (Order Cohort). `dax/README.md` explains each function.

---

## 4. Tier 2: the cleaning script, only 2 sections

`scripts/03_clean_data.py` is 683 lines, but it's built from the same small pattern repeated:
**check → fix or quarantine → `record(...)` a log line.** Read only these two sections:

### Section A: SALES cleaning (lines ~307–364)
| Code | Plain English | Why |
| --- | --- | --- |
| `s.drop_duplicates()` | Remove rows that are exact copies | A batch was loaded twice, which would double revenue |
| `CHANNEL_MAP = {...}` then `.map()` | "web", "WEB", "Website" → "Website" | 14 spellings → 4 channels |
| `parse_dt(...)` | Read both `2024-03-15` and `15/03/2024` dates | Never let the computer guess day vs month |
| `quarantine(... OrderDateTime.isna() ...)` | Set aside rows with impossible dates (30 Feb) | Can't be fixed with certainty |
| `quarantine(... Quantity <= 0 ...)` | Set aside negative quantities | They're refunds typed as sales; returns are counted elsewhere |
| `DiscountPct > 1` → `/ 100` | "20" becomes 0.20 | Someone typed the percentage as a whole number |
| `ref_price = …median()` | Fill a missing price with the same product's price that year, and flag it | Nearly certain, and marked `IsPriceImputed = Y` |
| `.replace(id_map)` | Point duplicate customers to their master ID | One person, one customer |
| `assert ...` | Stop the program if anything unexpected is left | A safety net |
| `record("SA-0x", ...)` | Write one line to the cleaning log | Every change is documented |

### Section B: BUILD THE STAR SCHEMA (lines ~401–573)
Creates each table: `dim_region`, `dim_channel`, `dim_store`, `dim_product`, `dim_customer` (with the **Guest**
row = −1, and with names and emails removed for GDPR), `dim_date` (one row per day with UK bank holidays and trading
periods), then `fact_sales` (calculates GrossSales, DiscountAmount, NetSales, CostAmount, GrossProfit) and `fact_returns`.

The rest of the file (data-quality measurement and the report) just writes `documentation/data_quality_report.md`.
Know that it exists; you don't need to explain it line by line.

---

## 5. Tier 3: one sentence each

| File | Say this |
| --- | --- |
| `scripts/01_generate_data.py` | "Creates 2 years of realistic pretend sales, with patterns built in: Christmas peaks, online growth, costs rising faster than prices, over-discounting at one store, a shoe brand with sizing problems. The 10 numbered sections build stores, products, customers, orders, discounts and returns." |
| `scripts/02_inject_quality_issues.py` | "Deliberately breaks the data in 37 counted ways (duplicates, bad dates, typos) so the cleaning can be tested against a known answer key." |
| `power-query/*.pq` | "The same cleaning rules written in Power Query, so a business user can refresh in Power BI without Python." |
| `scripts/helpers/build_charts.py` | "Draws the charts and dashboard mockup images." |
| `scripts/helpers/build_excel.py` | "Builds the Excel workbook with live formulas." |
| `scripts/helpers/build_presentation.py` | "Builds the 10-slide PowerPoint." |
| `scripts/helpers/build_powerbi_project.py` | "Builds the Power BI file from the data and the DAX file, and checks every field exists." |
| `scripts/run_pipeline.sh` | "Runs everything in order with one command (Mac/Linux)." |

---

## 6. How to explain the code to your brother (a 1-hour session)

1. **10 min: the flow, no code.** Draw on paper: *generate → mess up → clean → database → SQL → Power BI → findings*.
   Point to the file for each arrow.
2. **10 min: the data model.** Open `sql/01_create_schema.sql`, show `fact_sales` and one `dim_` table, and the
   `REFERENCES` line that links them.
3. **15 min: three SQL queries.** Q03 (GROUP BY + JOIN), Q09 (CASE), Q25 (LAG). For each one, read the question, run
   it, and look at the result in `sql/results/04_business_questions_output.txt`.
4. **10 min: four DAX measures.** Revenue → Gross Margin % → Customers (CALCULATE) → Revenue YoY %.
5. **10 min: two cleaning rules.** The CHANNEL_MAP and the negative-quantity quarantine. Ask: "fix, flag or quarantine?"
6. **5 min: homework.** He re-types Q03 and the Gross Margin % measure from memory.

---

## 7. What interviewers ask about code (and short answers)

| Question | Answer |
| --- | --- |
| "Did you write all this yourself?" | "I used AI as a coding assistant, but I ran every step, checked every number, and can explain any part. Pick a query and I'll walk you through it." |
| "Why Python for cleaning, not Excel?" | "It's repeatable: same input, same output, every time, with a log of every change. Excel cleaning by hand can't be repeated next month." |
| "What does `assert` do?" | "It stops the program if a condition is false, so bad data can't slip through silently." |
| "Why so many lines?" | "Most of it is logging and checks. The core logic is a few small rules repeated per table." |
| "Walk me through one query." | Use the Q03 explanation above. |
