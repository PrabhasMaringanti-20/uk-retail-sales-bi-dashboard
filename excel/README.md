# Excel (Phase 5) — `NorthStar_Excel_Analysis.xlsx`

Built by `scripts/05_build_excel.py`. Every number in the workbook is a **live formula**: change an input and it
recalculates. Opened and recalculated in LibreOffice to check the results (XLOOKUP needs Excel 2021/365 or
LibreOffice 24.8+).

| Sheet | Skills | What to look at |
| --- | --- | --- |
| Sales_Dec25 | `INDEX/MATCH`, `XLOOKUP`, `IFS`, `ROUND`, Excel Tables, conditional formatting | 13,744 December 2025 order lines. Red = sold below cost; amber = discount ≥ 30% |
| Products | Lookup table (`tblProducts`) | One row per SKU |
| Summary | `SUM`, `SUMIFS`, `COUNTIFS`, `AVERAGEIFS`, `SUMPRODUCT(1/COUNTIF())` distinct count, `IFERROR`, data bars, colour scales | KPIs, category table, channel × discount-band margin matrix, **reconciliation to SQL** |
| Raw_DQ | `ISBLANK`, `MATCH` against an allowed list, `SEARCH`, `COUNTIFS` duplicates | 3,000 raw rows with 7 data-quality checks |
| Pivot_Steps | PivotTables, calculated fields, slicers, timelines | Exercises to build by hand |

## What it shows (December 2025)
- Revenue £634,047, gross profit £256,835, **margin 40.5%**, 6,539 orders, AOV £96.96.
- Electronics: 19.5% of revenue but a **9.7% margin**, and 417 of the 641 loss-making lines.
- The channel × discount matrix shows margin falling below 5% at 40%+ discount in every channel, and turning
  **negative** for Click & Collect.
- The reconciliation cell says **MATCH**, with a £2.29 difference explained by rounding (Excel's `ROUND` rounds halves
  away from zero; the Python pipeline rounds halves to even).

## Raw data checks (3,000-row sample)
| Check | Rows |
| --- | ---: |
| Missing unit price | 5 |
| Channel not a standard label | 118 |
| Discount typed as a whole number (20 instead of 0.20) | 20 |
| Quantity outside 1–20 | 1 |
| UK-format date (DD/MM/YYYY) | 74 |
| Duplicate OrderID + LineNo (both copies flagged) | 22 |
| Guest / blank customer (**legitimate**, not an error) | 564 |

## Interview points
- **XLOOKUP vs INDEX/MATCH vs VLOOKUP:** VLOOKUP breaks when columns are inserted and can't look left. INDEX/MATCH
  works everywhere. XLOOKUP is simplest and has a built-in "not found" value.
- **Why `SUMPRODUCT(1/COUNTIF())`?** Lines are not orders. Each order's lines add up to 1, which gives a distinct count.
  In Excel 365, `=COUNTA(UNIQUE(range))` is simpler.
- **Why margin = total profit ÷ total revenue, not AVERAGE(Margin)?** An average of ratios gives every line equal
  weight regardless of size.
- **When not to use Excel:** 185,000 lines over 2 years, refreshed weekly, used by many people → database + Power BI.
