# Notes 10 — DAX (Phase 10)

**Files:** `dax/measures.dax` (all measures), `dax/README.md` (explanations)

## In one line
DAX measures are formulas that recalculate for whatever the user has filtered.

## Simple explanation
`Revenue = SUM(FactSales[NetSales])` is written **once**. In a chart by category, Power BI calculates it separately for
each category; with the 2025 slicer, only for 2025. That "what's currently filtered" is called **filter context**.
Understanding filter context = understanding DAX.

## The core measures (know them by heart)
```DAX
Revenue            = SUM ( FactSales[NetSales] )
Cost               = SUM ( FactSales[CostAmount] )
Gross Profit       = [Revenue] - [Cost]
Gross Margin %     = DIVIDE ( [Gross Profit], [Revenue] )
Orders             = DISTINCTCOUNT ( FactSales[OrderID] )
Average Order Value = DIVIDE ( [Revenue], [Orders] )
Customers          = CALCULATE ( DISTINCTCOUNT ( FactSales[CustomerKey] ), DimCustomer[IsGuest] = "N" )
Return Rate %      = DIVIDE ( [Refund Amount], [Revenue] )
Revenue PY         = CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( DimDate[Date] ) )
Revenue YoY %      = DIVIDE ( [Revenue] - [Revenue PY], [Revenue PY] )
Revenue YTD        = TOTALYTD ( [Revenue], DimDate[Date] )
Revenue PM         = CALCULATE ( [Revenue], DATEADD ( DimDate[Date], -1, MONTH ) )
```

## Each function explained simply
| Function | Simple meaning |
| --- | --- |
| `SUM` | Add up a column for what's filtered |
| `DIVIDE(a,b)` | a ÷ b, but returns blank instead of an error when b is 0 |
| `DISTINCTCOUNT` | Count unique values (orders, customers) |
| `CALCULATE` | "Calculate this, **but change the filters** like this." The most important function |
| `FILTER` | Go row by row and keep the rows that meet a condition |
| `ALL` | Ignore filters on this table/column (for % of total) |
| `SUMX` | For each row, calculate something, then add up the results |
| `SAMEPERIODLASTYEAR` | The same dates, one year back |
| `TOTALYTD` | Year-to-date total |
| `DATEADD` | Shift dates (e.g. −1 month) |
| `USERELATIONSHIP` | Use the inactive relationship (order date for returns) |
| `RANKX` | Rank items by a measure |
| `VAR … RETURN` | Save a step in a variable; easier to read, calculated once |

## Filter context vs row context
- **Filter context:** the filters applied to a calculation (slicers, rows/columns of a visual, CALCULATE).
- **Row context:** "the current row" while an iterator like SUMX or FILTER walks a table.
- **Context transition:** CALCULATE inside a row context turns the current row into a filter.

## Measure vs calculated column
| | Measure | Calculated column |
| --- | --- | --- |
| Calculated | When a visual asks (filter context) | At refresh, per row (row context) |
| Stored | No | Yes (uses memory) |
| Use for | Numbers you aggregate: revenue, margin % | Things you slice by: discount band, price band |

## Typical interview tasks

**Q: Explain CALCULATE.** It evaluates an expression with modified filters. `CALCULATE([Revenue], DimProduct[Category]
= "Electronics")` gives Electronics revenue regardless of the category slicer, but still respects the year slicer.

**Q: Why DIVIDE and not "/"?** DIVIDE handles division by zero safely (returns BLANK), so visuals don't show errors.

**Q: How do you calculate YoY %?** `Revenue PY = CALCULATE([Revenue], SAMEPERIODLASTYEAR(DimDate[Date]))`, then
`DIVIDE([Revenue] - [Revenue PY], [Revenue PY])`. It needs a marked date table with continuous dates.

**Q: What does ALL do in % of total?** `DIVIDE([Revenue], CALCULATE([Revenue], ALL(DimProduct)))`: the denominator ignores
the product filter, so it's the total across all products.

**Q: SUM vs SUMX?** SUM adds a column. SUMX calculates an expression row by row first (e.g. quantity × price × (1 −
discount)), then adds. Use SUMX when the value doesn't exist as a column.

**Q: Why are there two return-rate measures?** By return date (finance view: refunds processed this month) and by order
date via USERELATIONSHIP (quality view: of what we sold in March, how much came back). They answer different questions.

**Q: Margin went from 43.3% to 41.0%. Is that −2.4% or −5.5%?** −2.4 **points**. As a relative change it's −5.5%.
Always say "points" for changes in percentages.

## Common mistakes
- Calculated columns for ratios (wrong when aggregated).
- Forgetting to mark the date table, so time intelligence returns blanks.
- Counting rows instead of distinct orders.
- Bi-directional relationships instead of writing a correct measure.
