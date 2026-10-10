# Notes 02 — Data Architecture & Data Modelling (Phases 2 and 8)

**Files:** `documentation/data_model.md`, `documentation/data_dictionary.md`, `sql/01_create_schema.sql`

## In one line
We organised the data as a **star schema**: one table of sales events in the middle, and description tables around it.

## Simple explanation
Think of a till receipt. Each line says: *on this date, this customer bought this product in this store, through this
channel, for this much money.*
- The **numbers** (quantity, price, profit) go into the **fact table** (`FactSales`).
- The **descriptions** (product name, category, store city, customer segment, month) go into **dimension tables**.
- The fact table only stores **ID numbers** (keys) that point to the dimensions.

```
            DimDate     DimProduct
                 \        /
  DimCustomer — FactSales — DimStore
                 /        \
          DimChannel     DimRegion
```
It looks like a star, hence the name.

## Key topics

### 1. Fact vs dimension
| Fact table | Dimension table |
| --- | --- |
| Events / transactions | Descriptions / context |
| Many rows (185,858) | Fewer rows (12 regions, 1,220 products) |
| Numbers you add up (NetSales, Quantity) | Text you filter or group by (Category, City) |
| Foreign keys to dimensions | Primary key + attributes |

### 2. Grain: the most important decision
**Grain = what one row means.** FactSales grain = *one product line in one order.*
- **Why that grain?** It's the lowest detail available. You can always add up (line → order → day → month), but you
  can never split an order back into products.
- **Interview line:** *"I always define the grain first, because every measure and join depends on it."*

### 3. Keys
- **Primary key (PK):** unique ID of a row (`ProductKey`).
- **Foreign key (FK):** a column in the fact that points to a PK in a dimension.
- **Surrogate key:** an integer we create (1, 2, 3…). Faster joins, and stable if the source changes its codes.
- **Business/natural key:** the source's own code (`SKU`, `CustomerID`), kept for traceability.
- **Degenerate dimension:** `OrderID` sits in the fact with no table of its own; used to count orders.
- **Unknown member:** `CustomerKey = -1` = "Guest", for shoppers who didn't scan a loyalty card. Every fact row then
  has a valid customer, so nothing disappears in joins or shows as "(Blank)" in Power BI.

### 4. Relationships and cardinality
- **One-to-many (1:*)**: one product → many sales lines. All our relationships are this type.
- **Filter direction: single.** Dimension filters the fact (pick "Electronics" → only Electronics sales). Never the
  other way round (bi-directional = confusing results and slow models).
- **Many-to-many**: avoided. It usually signals a modelling mistake.

### 5. Two fact tables (FactSales + FactReturns)
Returns are separate events (different date, different grain). Both facts share the same dimensions
(**conformed dimensions**), so you can put sales and returns side by side in one visual.
- We **don't** link FactReturns directly to FactSales (fact-to-fact links create ambiguity).

### 6. Role-playing date
A return has two dates: when it was **returned** and when it was **ordered**. One DimDate, two relationships:
return date = active, order date = inactive. DAX turns on the inactive one with `USERELATIONSHIP` when needed.

### 7. Why RegionKey is on the fact
Online orders ship from the e-commerce hub (no real region). Region = store region for in-store sales, and customer's
delivery region for online sales. Putting RegionKey on the fact gives **one clear path** for filters. There is no
Store→Region relationship, so Power BI never has two ways to filter region (no ambiguity).

### 8. Date dimension
A table with one row per day (731 days), no gaps. Holds Year, Quarter, Month, weekday, UK financial year, bank
holidays, trading periods (Black Friday week, January sale…). Power BI time intelligence (YTD, last year) **needs**
it, marked as a date table.

### 9. GDPR data minimisation
Names, emails, exact birth date and full postcode are **not** in the model, only age band and postcode district.
You don't need to know *who* someone is to analyse *how* customers behave.

## Interview questions and model answers

**Q: Why a star schema and not one big flat table?**
A: A flat table repeats product and customer details on every one of 185,000 rows, which wastes memory and is easy
to get inconsistent. A star schema stores each description once, is fast in Power BI (it's what the engine is
optimised for), and is easy for users: filter by dimensions, sum the facts.

**Q: What is the grain of your fact table?**
A: One row per order line, meaning one product within one order. Orders are counted with DISTINCTCOUNT(OrderID).

**Q: Star vs snowflake?**
A: A snowflake splits dimensions further (Product → SubCategory → Category tables). It saves a little space but adds
joins. For Power BI a star is recommended, so I kept categories as columns in DimProduct.

**Q: How did you handle anonymous customers?**
A: An "unknown member" row, CustomerKey −1 "Guest". Then every sale has a valid foreign key, guest sales still count in
revenue, and I exclude them only where it matters (customer counts, revenue per customer).

**Q: Why surrogate keys if the source already has SKUs?**
A: Integers join faster and compress better, and if the source system re-codes a SKU the history doesn't break.
I keep the SKU as an attribute for traceability.

**Q (follow-up): What would you add for slowly changing dimensions?**
A: If a customer changes segment or a store changes region, a Type 2 SCD adds a new row with valid-from and valid-to
dates, so old sales stay with the old attribute. In this project, attributes don't change over the two years, so
Type 1 (overwrite) is enough. I'd mention SCD2 as a next step.

**Q: Why is UnitCost stored on the fact and not only in DimProduct?**
A: Cost changes over time (supplier increases in 2025). The fact stores the cost *at the time of sale*, so historical
profit stays correct.

## Common mistakes
- Not defining the grain, then double counting (e.g. joining returns to sales and summing sales again).
- Bi-directional relationships "to make it work".
- Using the fact table's date column instead of a proper date table, which breaks YTD and previous-year measures.
- Leaving blank foreign keys, which creates a "(Blank)" row in every slicer.
