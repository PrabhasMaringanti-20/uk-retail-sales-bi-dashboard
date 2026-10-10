# Notes 04 — Data Quality & Cleaning (Phase 4)

**Files:** `scripts/02_inject_quality_issues.py` (breaks the data), `scripts/03_clean_data.py` (fixes it),
`documentation/validation_rules.md`, `documentation/data_quality_report.md`, `data/clean/_cleaning_log.csv`,
`data/raw/_injected_issues.csv`

## In one line
Real data is messy, so we **measured** the mess, **fixed** what we could with certainty, **quarantined** what we couldn't,
and **documented** every decision.

## Simple explanation
Imagine 4 shop systems typed by different people: one writes "Web", another "website", another "WEB". Some dates are
"15/03/2024", others "2024-03-15". Someone typed 999 instead of 1. A batch was loaded twice. If you build a dashboard on
that, revenue is wrong and nobody trusts it.

So we:
1. Broke clean data in **known, counted ways** (37 types of problems), which acts as an answer key.
2. Wrote rules to detect and fix them.
3. Measured quality **before and after**.
4. Proved it worked: **100% of cleaned sales lines match the answer key exactly.**

## The six data-quality dimensions (memorise these)
| Dimension | Question | Example from the project |
| --- | --- | --- |
| **Completeness** | Is the data there? | 600 customers missing gender → "Unknown" |
| **Validity** | Does it follow the rules? | Quantity 999, date "30 Feb 2024" |
| **Consistency** | Is the same thing written the same way? | 14 spellings of 4 channels; 28 of 8 categories |
| **Uniqueness** | Is each thing recorded once? | 900 duplicate sales rows; 180 duplicate customers |
| **Integrity** | Do references point to something real? | 12 sales with SKUs that don't exist |
| **Accuracy** | Is it correct? | Totals recompute; matches the answer key |

## Decision framework: Fix / Flag / Quarantine
| Action | When | Example |
| --- | --- | --- |
| **Fix** | The correct value is certain | "WEB" → "Website"; discount "20" → 0.20; "£19.99" → 19.99 |
| **Flag** | Usable but uncertain | Missing price imputed and marked `IsPriceImputed = Y`; invalid postcode → `PostcodeValid = N` |
| **Quarantine** | Can't be trusted | Date "2024-02-30", quantity −3, unknown SKU, return before the order date |
| **Keep (not an error!)** | The blank is legitimate | Blank customer on an in-store sale = guest shopper |

> **Never silently change data.** Every rule has an ID (SA-01, CU-12…) and a row count in the cleaning log.

## The trickiest decisions (great to explain)
1. **Duplicate customers:** same email with different capitals or spaces → merged into the earliest registration,
   and their sales re-pointed to that master ID. *Why email?* It's the most reliable personal identifier available.
   Names repeat; postcodes change.
2. **Missing price:** prices are fixed per SKU per year, so we used the same SKU's price that year. That's nearly
   certain, and it's flagged.
3. **Missing product cost:** took the cost from the product's own 2024 transactions. For a product only sold in 2025, we
   divided by the measured 2025 cost increase (+6%). That's evidence-based, not a guess.
4. **Negative quantities:** these were refunds typed as sales. The returns system already records returns, so keeping
   them would double-count. Quarantined.
5. **Mixed date formats:** parsed with **explicit** formats. If a tool guesses, 03/04/2024 might become 4 March
   (US style) instead of 3 April (UK style).
6. **Duplicates that only appear after cleaning:** some duplicate returns differed only in capital letters, so we
   de-duplicated again after standardising (rule RE-07).

## Results (from the data quality report)
| | Before | After |
| --- | ---: | ---: |
| Sales validity | 91.7% | 100% |
| Channel labels | 14 | 4 |
| Category labels | 28 | 8 |
| Duplicate sales rows | 900 | 0 |
| Customers | 12,680 | 12,500 (+ Guest) |
| Sales rows quarantined | n/a | 90 (0.05%) |

## Where quality is enforced (defence in depth)
1. Python cleaning rules + `assert` statements (the pipeline stops if something unexpected appears).
2. PostgreSQL constraints (PK, FK, UNIQUE, NOT NULL, CHECK): the database rejects bad rows.
3. 13 SQL PASS/FAIL tests after loading (`sql/03_data_quality_checks.sql`).
4. Reconciliation: the same totals in SQL, Excel and Power BI.

## Interview questions

**Q: Tell me about a data-quality issue you handled.**
A (STAR): *Situation:* sales came from several systems with 14 different channel labels, two date formats and a batch
that was loaded twice. *Task:* make revenue trustworthy. *Action:* I wrote rule-based cleaning: a mapping table for
channels, explicit date parsing, duplicate removal, and quarantine for impossible rows. Each rule has an ID and a row
count in a log. *Result:* validity went from 91.7% to 100%, only 0.05% of rows were quarantined, and the cleaned revenue
matched the answer key to the penny.

**Q: How do you decide between deleting, fixing and keeping bad data?**
A: Fix only when the right value is certain, flag when it's a reasonable estimate, quarantine when it can't be trusted,
and never delete silently. Quarantined rows are kept in a file so they can be reviewed with the data owner.

**Q: Isn't a blank customer ID an error?**
A: Not always. For in-store sales it means the shopper didn't scan a loyalty card. That's a legitimate unknown, so I
mapped it to a "Guest" member instead of deleting £1.36M of real sales.

**Q: How would you do this in a real job without an answer key?**
A: Reconcile to an independent source, such as finance's monthly revenue figures, do row-count checks between source and
target, review samples with the business owner, and set up automated checks on every refresh.

## Common mistakes
- Dropping rows with *any* blank, which can delete legitimate data (guests).
- Fixing values by guessing (e.g. inventing a category).
- Cleaning once by hand in Excel, so it isn't repeatable next month.
- Not telling anyone what you changed.
