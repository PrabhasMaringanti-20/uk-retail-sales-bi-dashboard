# Validation Rules & Cleaning Decisions

Each rule has an ID used in `scripts/03_clean_data.py`, `data/clean/_cleaning_log.csv` and the
[data quality report](data_quality_report.md).

**Decision principle:** *Fix* when the correct value is certain. *Flag* when it is uncertain but usable. *Quarantine*
when the row can't be trusted. *Never guess silently.*

| Rule | Table | Check | Action | Why this decision |
| --- | --- | --- | --- | --- |
| ST-01 | stores | Region name in reference list | Map aliases (`Yorkshire & Humber`) | Same region, different spelling, so the fix is certain |
| ST-02 | stores | Postcode format | Upper-case + standard space | Formatting only |
| PR-01 | products | Exact duplicate rows | Remove | Identical rows add nothing |
| PR-02 | products | Category in the 8 allowed values | Mapping table (`electronic` → Electronics) | Mapping table is auditable; unmapped values stop the pipeline |
| PR-03 | products | SubCategory present | `Unclassified` + flag | Guessing a classification could mislead category managers |
| PR-04 | products | ListPrice numeric | Strip `£`, convert | Formatting only |
| PR-05/06/07 | products | UnitCost present | Fill from 2024 transaction cost → 2025 cost ÷ measured uplift → category ratio | Transaction cost is the best evidence; fallbacks are logged |
| CU-01/02/03 | customers | Segment / Loyalty / Gender codes | Standardise (Title Case, Y/N, Female/Male) | Same meaning, different code |
| CU-04 | customers | Gender present | `Unknown` | Can't be inferred, and shouldn't be |
| CU-05/06 | customers | UK postcode regex `^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$` | Re-format if possible; else blank + `PostcodeValid = N` | Keep the customer, flag the field |
| CU-07/08/09 | customers | City | Standard casing; infer from postcode district when unambiguous; else `Unknown` | Postcode district → city is a reliable lookup |
| CU-10/11 | customers | DOB parseable, age 16–100 | Parse DD/MM/YYYY; impossible dates → blank (`AgeBand = Unknown`) | 1900-01-01 is a placeholder, not a birthday |
| CU-12 | customers | One record per email (trimmed, lower-case) | Merge into earliest record; re-point sales | Duplicate people inflate customer counts and break retention |
| SA-01 | sales | Exact duplicate rows | Remove | Double-loaded batch would double revenue |
| SA-02 | sales | Channel in 4 allowed values | Mapping table | 14 spellings → 4 channels |
| SA-03 | sales | Date format | Parse ISO and UK formats explicitly | Never let a tool guess day/month order |
| SA-04 | sales | Date is a real date | **Quarantine** | 30 Feb can't be corrected with certainty |
| SA-05 | sales | Date in 2024–2025 | **Quarantine** | Out-of-window rows belong to another extract |
| SA-06 | sales | Quantity > 0 | **Quarantine** | Negative quantities are refunds keyed as sales; returns come from the returns system |
| SA-07 | sales | Quantity ≤ 20 | **Quarantine** | 999 units is a keying error for a retail till |
| SA-08 | sales | SKU exists in product master | **Quarantine** | Orphan: no category, cost or name |
| SA-09 | sales | Discount 0–0.60 | Values > 1 divided by 100 | `20` clearly means 20% |
| SA-10 | sales | UnitPrice present | Impute same SKU's price in the same year + flag | Prices are fixed per SKU per year, so the imputation is near-certain and flagged |
| SA-11 | sales | Customer exists | Re-point duplicate IDs to the master | Follows CU-12 |
| SA-12 | sales | CustomerID blank | Keep as Guest (-1) | **Legitimate blank**: anonymous in-store sale, not an error |
| RE-01 | returns | Exact duplicates | Remove | |
| RE-02 | returns | Links to a valid sales line | **Quarantine** | A refund with no sale can't be analysed |
| RE-03 | returns | Return date ≥ order date | **Quarantine** | Impossible sequence |
| RE-04 | returns | ReturnQty ≤ quantity sold | Cap at quantity sold | Refund amount was already within the amount paid |
| RE-05/06 | returns | Reason in allowed list | Standardise; blank → `Not stated` | |
| RE-07 | returns | ReturnID unique | Remove duplicates found after standardisation | Some duplicates differed only in casing |

## Data-quality dimensions measured

| Dimension | Meaning | How it's measured here |
| --- | --- | --- |
| Completeness | Is the data there? | % of required fields populated |
| Validity | Does it follow the rules? | Date in window, quantity 1–20, discount 0–60%, postcode regex, allowed codes |
| Consistency | Is the same thing written the same way? | Distinct labels vs the target (e.g. 14 channel labels → 4) |
| Uniqueness | Is each thing recorded once? | Duplicate rows, duplicate business keys, duplicate emails |
| Integrity | Do references point to something real? | SKU in product master; return linked to a sale |
| Accuracy | Is it correct? | Recomputed totals match (SQL checks) and, uniquely here, comparison to the generator's answer key |

## Where the rules are enforced

1. **Python** (`03_clean_data.py`): applies the rules and asserts that nothing unmapped is left.
2. **PostgreSQL** (`01_create_schema.sql`): PK, FK, UNIQUE, NOT NULL and CHECK constraints reject bad loads.
3. **SQL tests** (`03_data_quality_checks.sql`): 13 PASS/FAIL checks after every load.
4. **Power Query** (`power-query/`): the same rules as repeatable M steps for the Power BI path.
