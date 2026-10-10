# Power Query (M) — repeatable cleaning inside Power BI / Excel (Phase 6)

The Python script `scripts/03_clean_data.py` is the reference cleaning implementation. These M scripts apply **the
same rule IDs** inside Power BI or Excel, so a business user can refresh the raw extracts and get the same result
without Python. Rule IDs match `documentation/validation_rules.md`.

> Honest note: these scripts were written to mirror the tested Python rules, but they could not be executed here
> (Power BI runs on Windows). When you run them, compare the row counts with `documentation/data_quality_report.md`:
> Sales 185,858 valid rows + 90 quarantined, Returns 14,120, Customers 12,500 (+ Guest), Products 1,220.
> A difference means a rule needs checking. Reconciling two implementations is itself a good interview story.

## Query order and dependencies

```
DataFolder (parameter)
fnParseDateTime (function)
raw products.csv (SKU list) ──► SalesStaging
SalesStaging ──► Sales ──► Returns
SalesStaging ──► Sales_Quarantine
SalesStaging ──► SalesCost2024 ──► Products
Customers    ──► CustomerIdMap ──► Sales
DimDate (generated)
```
Staging and helper queries: right-click → uncheck **Enable load** so they don't appear in the model.

## How to use
1. Power BI → Transform data → Home → Manage Parameters → create `DataFolder` (`00_DataFolder_parameter.pq`).
2. New Source → Blank Query → Advanced Editor → paste each `.pq` file. Rename each query to the name in its header.
   The helper queries shown in comments at the bottom of some files (`SalesCost2024`, `CustomerIdMap`, `Sales`,
   `Sales_Quarantine`) are separate blank queries: paste the code inside the comment.
3. Close & Apply. In this path, relationships use the **business keys** (SKU, CustomerID, StoreCode, Channel), which is
   simpler. The Python/SQL path creates integer surrogate keys. Both are valid; be ready to explain the difference.

## Power Query skills demonstrated

| Skill | Where |
| --- | --- |
| Parameters (one place to change the file path) | `00_DataFolder_parameter.pq` |
| Custom function, `try … otherwise` error handling | `01_fnParseDateTime.pq` |
| Data types and locale (`en-GB` dates and decimals) | every query |
| Trim / clean all columns at once | `Table.TransformColumns(t, {}, Text.Trim)` |
| Remove duplicates (all columns, or by key) | `Table.Distinct` |
| Replace values / mapping table (record lookup) | Products `CategoryMap`, Sales channel |
| Conditional columns (`if … then … else`) | AgeBand, PriceBand, DQ_Issue |
| Split / extract text | Postcode district (`Text.BeforeDelimiter`) |
| Merge queries (joins: left outer, inner, anti) | Products ← SalesCost2024, Returns ← Sales |
| Group by (median price/cost) | SalesCost2024, RefPrice |
| Append (combine sources) | e.g. append monthly extracts with `Table.Combine({Jan, Feb, …})` |
| Reference vs duplicate queries; disabling load | staging pattern |
| Quarantine pattern (flag column, then split valid/invalid) | Sales `DQ_Issue` |
| Generating a date table in M | `06_DimDate.pq` |

## Excel version
The same queries work in Excel: Data → Get Data → From Other Sources → Blank Query. Load the result to a table or to
the Data Model for PivotTables.

## Interview points
- **Power Query vs SQL vs Python for cleaning?** Use SQL when the data lives in a database (server-side, scalable).
  Power Query for self-service, refreshable BI transformations. Python for complex logic, large files or
  reproducible pipelines like the generator. Here, Python is the reference and Power Query is the refreshable BI path.
- **Query folding:** when the source is PostgreSQL, simple steps (filter, select, group) are translated into SQL and run
  in the database. Custom functions like `fnParseDateTime` stop folding. That's fine for CSV sources, and a reason
  to do heavy cleaning in SQL when using a database.
- **Why `Table.Buffer` before `Table.Distinct`:** it fixes the sort order in memory so "keep first" really keeps the
  earliest record.
