# DAX — measures and how they work

All measures are in [`measures.dax`](measures.dax). Expected FY2025 values are written next to them so you can check
the model reconciles with SQL.

## Two ideas that explain almost all of DAX

### 1. Filter context
Every visual cell is calculated with a set of filters, such as *Year = 2025* and *Category = Electronics*. Slicers, rows,
columns and relationships all add filters. A measure is a formula evaluated **inside** that context.
`[Revenue] = SUM(FactSales[NetSales])` gives £879K in the Electronics/2025 cell and £4.58M in the total, from the same formula.

### 2. Row context
An **iterator** (`SUMX`, `FILTER`, `RANKX`, `AVERAGEX`) walks a table one row at a time. Inside it you can read columns of
the current row. A row context **is not** a filter; `CALCULATE` converts it into one (*context transition*).

## The functions used, and why

| Function | What it does | Where we use it |
| --- | --- | --- |
| `SUM` | Adds a column in the current filter context | Revenue, Cost, Refund Amount |
| `DIVIDE(a, b)` | a ÷ b, returns BLANK instead of an error when b = 0 | Every ratio: margin, AOV, return rate |
| `DISTINCTCOUNT` | Counts unique values | Orders (OrderID), Customers |
| `CALCULATE(expr, filters…)` | Evaluates `expr` after **changing** the filter context. The most important DAX function | Customers (exclude Guest), YoY, deep-discount margin |
| `FILTER(table, condition)` | Returns the rows meeting a condition (row-by-row) | Profit lost below cost, running total, repeat customers |
| `ALL(table/column)` | Removes filters | % of total, company benchmark, running total |
| `SUMX(table, expr)` | Calculates `expr` for each row, then sums | Revenue check, loss below cost |
| `USERELATIONSHIP` | Uses an inactive relationship for one calculation | Refunds by **order** date |
| `TOTALYTD` | Year-to-date total | Revenue YTD |
| `SAMEPERIODLASTYEAR` | Shifts the dates back 1 year | Revenue PY, YoY % |
| `DATEADD` | Shifts the dates by N intervals | Previous month, MoM % |
| `DATESINPERIOD` | A window of dates | 3-month moving average |
| `RANKX` | Ranks items by a measure | Product and store rank |
| `VAR … RETURN` | Stores an intermediate result. Easier to read, and calculated once | YoY %, YoY arrow |
| `SWITCH(TRUE(), …)` | Readable if/else-if chain | Conditional colour |
| `SELECTEDVALUE` | The single value selected in a slicer, or a default | Dynamic titles |

## Patterns worth explaining in an interview

**Why `Gross Margin % = DIVIDE([Gross Profit], [Revenue])` and not a calculated column averaged?**
An average of line margins gives every line the same weight: a £2 cable counts as much as a £300 headphone. Margin must be
total profit ÷ total revenue, calculated *after* aggregation, which is exactly what a measure does.

**Why does `Customers` use CALCULATE?**
Anonymous in-store sales all point at the Guest member (-1). Without the filter, 15,156 guest orders would count as
one customer and distort revenue per customer. `CALCULATE` adds `IsGuest = "N"` to whatever filters already exist.

**How does `Revenue PY` work?**
In a 2025 context, `SAMEPERIODLASTYEAR(DimDate[Date])` returns the same dates in 2024. `CALCULATE` replaces the date filter
with those dates and recalculates Revenue. This needs a complete, contiguous date table marked as a date table.

**Why are there two return rates?**
- `Return Rate %` uses the **return date**: refunds processed this month ÷ revenue this month (the finance view).
- `Return Rate % (Order Cohort)` uses the **order date** through `USERELATIONSHIP`: of what we sold in March, how much came
  back? This is the right measure for product and supplier quality, and it matches SQL Q16/Q39.

**Running total with `FILTER(ALL(DimDate[Date]), DimDate[Date] <= LastDate)`**
`ALL` removes the month filter, so we can see every date. `FILTER` keeps only dates up to the last date in the current
cell. `CALCULATE` sums revenue over that set. Compare with `TOTALYTD`, which resets every January.

**Margin change in points, not percent.** 43.3% → 41.0% is −2.4 *points*. As a percentage change it would be −5.5%.
Mixing these up is a common reporting mistake.

**Measures vs calculated columns**
- *Calculated column:* calculated once at refresh, stored per row, uses row context. Use it for slicing and grouping
  (e.g. PriceBand). It costs memory.
- *Measure:* calculated at query time in filter context. Use it for any number you aggregate. Not stored.

## Reconciliation check (do this after building the model)

Put these in a table visual with **Year** on rows:

| Year | Revenue | Gross Profit | Margin | Orders |
| --- | ---: | ---: | ---: | ---: |
| 2024 | 3,961,750 | 1,716,939 | 43.3% | 42,639 |
| 2025 | 4,584,138 | 1,878,065 | 41.0% | 46,889 |
| Total | 8,545,888 | 3,595,004 | 42.1% | 89,528 |

If Power BI shows anything different, a relationship or data type is wrong. Fix it before building visuals.
Also check `Revenue (SUMX check)` against `Revenue`. They differ by only about £43 in £8.5M, because the stored
discount amount is rounded to the penny on each line while SUMX doesn't round. Explaining a tiny, known
difference like this is exactly what reconciliation is about.
