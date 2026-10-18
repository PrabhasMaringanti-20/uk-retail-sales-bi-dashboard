# Notes 05 — Excel (Phase 5)

**Files:** `excel/NorthStar_Excel_Analysis.xlsx`, `excel/README.md`, built by `scripts/helpers/build_excel.py`

## In one line
Excel is used for quick exploration and validation of a sample: lookups, conditional sums, checks and pivots.

## Simple explanation
Before building a big system, an analyst opens a month of data in Excel to understand it: *Which categories sell?
Are there blanks? Does the total match?* Excel is the fastest way to "look at the data".

## The functions used (with the exact formula style from the workbook)

| Function | What it does | Example |
| --- | --- | --- |
| `INDEX/MATCH` | Lookup that works in every Excel version | `=INDEX(Products!C:C, MATCH(D2, Products!A:A, 0))` → Category |
| `XLOOKUP` | Modern lookup with a "not found" value | `=XLOOKUP(D2, Products!A:A, Products!E:E, "Not found")` → Brand |
| `SUMIFS` | Sum with conditions | `=SUMIFS(NetSales, Category, "Electronics")` |
| `COUNTIFS` | Count with conditions | `=COUNTIFS(Category, A16, LossLine, "LOSS")` |
| `AVERAGEIFS` | Average with conditions | average line value per category |
| `IFS` | Many conditions without nested IFs | discount band |
| `IFERROR` | Show "" instead of #DIV/0! | channel × band matrix |
| `SUMPRODUCT(1/COUNTIF(r,r))` | **Distinct** count (orders, not lines) | Orders = 6,539 |
| `ROUND` | Round money to pennies | discount amount |
| Conditional formatting | Colour cells by rules | red = loss line, amber = 30%+ discount, data bars, colour scale |
| Excel Table | Named, auto-expanding range | `tblSales`, `tblProducts` |
| PivotTable | Drag-and-drop summary | `Pivot_Steps` sheet exercises |

## What the workbook found (December 2025)
- Revenue £634,047, margin 40.5%, 6,539 orders, AOV £96.96.
- Electronics: 9.7% margin, and 417 of the 641 loss-making lines.
- At 40%+ discount, margin is under 5% in every channel and **negative** for Click & Collect.
- **Reconciliation:** Excel total vs SQL total differ by £2.29. That was explained, not hidden: Excel's ROUND rounds
  halves away from zero, while Python rounds halves to even.

## Why reconciliation matters
If Excel says £634,047 and Power BI says £640,000, the CFO trusts neither. Always prove that two tools give the same
number, or explain the difference exactly.

## Interview questions

**Q: VLOOKUP vs INDEX/MATCH vs XLOOKUP?**
A: VLOOKUP can only look to the right and breaks if a column is inserted. INDEX/MATCH looks in any direction and
works everywhere. XLOOKUP is the modern, simplest version, with a built-in not-found value and exact match by default.

**Q: How do you count distinct orders in Excel?**
A: In Excel 365, `=COUNTA(UNIQUE(range))`. In older versions, `=SUMPRODUCT(1/COUNTIF(range,range))`.

**Q: What does a PivotTable calculated field do, and why is margin a trap?**
A: It calculates on the summed values, so Margin = SUM(GrossProfit)/SUM(NetSales), which is correct. Averaging a
margin column is wrong because small and big lines get equal weight.

**Q: When would you NOT use Excel?**
A: For 185,000 rows across 2 years, refreshed every week for many users, I'd use a database and Power BI. Excel is
for exploration, validation and one-off analysis.

## Practice tasks
1. Build a PivotTable: Category × Channel, values NetSales, shown as % of row total.
2. Add a slicer on StoreCode and a timeline on OrderDate.
3. In Raw_DQ, add a check: UnitCost greater than UnitPrice.
