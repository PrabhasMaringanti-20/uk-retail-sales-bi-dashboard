# Notes 06 — Power Query (Phase 6)

**Files:** `power-query/*.pq`, `power-query/README.md`

## In one line
Power Query records cleaning steps once, so every refresh repeats them automatically.

## Simple explanation
Cleaning by hand in Excel works once. Next month the new file is messy again. Power Query is like a **recipe**: each
step ("trim spaces", "fix channel names", "remove duplicates") is saved. Drop in a new file, press Refresh, and the
recipe runs again. The language behind the buttons is called **M**.

## Steps / skills used
| Skill | M function | In the project |
| --- | --- | --- |
| Data types | `Table.TransformColumnTypes` | dates, money, keys (the #1 source of errors) |
| Locale | `"en-GB"` | UK dates (DD/MM/YYYY) and decimals |
| Trim all columns | `Table.TransformColumns(t, {}, Text.Trim)` | removes hidden spaces |
| Replace / map values | record lookup, `if…then…else` | 14 channel spellings → 4 |
| Remove duplicates | `Table.Distinct` | double-loaded batch |
| Conditional column | `Table.AddColumn(… each if …)` | AgeBand, PriceBand, DQ_Issue |
| Split text | `Text.BeforeDelimiter` | postcode district |
| Merge (join) | `Table.NestedJoin` | products ← transaction cost; returns ← sales |
| Group by | `Table.Group` + `List.Median` | median price per SKU per year |
| Append | `Table.Combine` | combining monthly files |
| Parameter | `DataFolder` | change one path for all queries |
| Custom function | `fnParseDateTime` | two date formats + `try … otherwise null` |
| Staging queries | "Enable load" off | helper queries not shown to users |

## Important ideas
- **Query folding:** with a database source, Power Query turns steps into SQL that runs in the database (fast). Custom
  functions break folding. That's fine for CSVs, but with big databases, push heavy work into SQL.
- **Reference vs duplicate:** *reference* builds on another query (it changes when the source changes);
  *duplicate* copies the steps (independent).
- **Circular dependency:** Products needed Sales (for missing costs) and Sales needed Products (for valid SKUs). Fixed by
  reading the SKU list from the raw file. A real problem we solved.
- **Quarantine pattern:** add a `DQ_Issue` column that says why a row fails; one query keeps the valid rows, another
  keeps the rejected rows so they stay visible.

## Interview questions

**Q: Power Query or SQL for cleaning?**
A: If the data is in a database, SQL (it runs on the server and is shared by every tool). Power Query for
self-service, file-based or refreshable report-level shaping. In this project, Python is the tested reference, and the
M scripts mirror the same rules so a business user can refresh without Python.

**Q: How do you make a Power Query solution easy to move between computers?**
A: A parameter for the folder path, so it's one change instead of editing every query.

**Q: What causes most Power Query refresh errors?**
A: Changed column names or types in the source, and locale problems with dates and decimals. Set types explicitly
with a locale and avoid hard-coded column lists where possible.
