# Power BI — Step-by-step Build Guide (Phase 9)

> **Shortcut:** a ready-made Power BI Project already exists: `powerbi/NorthStar_Retail_Dashboard.pbip`.
> Simple instructions for opening it (and a beginner version of this guide) are in [`00_SIMPLE_STEPS.md`](00_SIMPLE_STEPS.md).
> This file is the detailed reference for building everything by hand.

Power BI Desktop is free and runs on Windows. This guide builds the full report from the clean data in about 4–6 hours.
Layout references: `screenshots/mockup_page*.png` (Python mockups). **When finished, replace them with real screenshots
of the report** and save the `.pbix` as `powerbi/NorthStar_Retail_Dashboard.pbix`.

## Step 0 — Get the data
Unzip `data/clean_data.zip` (or run `bash scripts/run_pipeline.sh`). You need the 8 CSVs in `data/clean/`.

Two connection options. Know both for interviews:
- **A. CSV (simplest):** Home → Get data → Text/CSV, for each file.
- **B. PostgreSQL:** Home → Get data → PostgreSQL database → server `localhost`, database `northstar`, then pick the
  `northstar.*` tables. A database is the "real-world" option: one governed source for SQL and BI.

Choose **Import** mode (data is small and fast). DirectQuery is for very large or real-time data.

## Step 1 — Power Query (Transform data)
For each table, open **Transform data** and:
1. Check the **data types** (the most common source of errors):
   - Keys = Whole number. Money columns = **Fixed decimal number** (currency). DiscountPct = Decimal.
   - `DimDate[Date]`, `OpenDate`, `SignupDate`, `LaunchDate` = Date. `OrderDateTime` = Date/Time.
2. Rename the queries to `FactSales`, `FactReturns`, `DimDate`, `DimCustomer`, `DimProduct`, `DimStore`, `DimRegion`,
   `DimChannel`.
3. Paste the M scripts from `power-query/` if you want the full raw-to-clean path (see `power-query/README.md`).
4. **Close & Apply.**

## Step 2 — Model view (relationships)
Delete any relationships Power BI auto-detected, then create these (drag key onto key):

| From | To | Cardinality | Direction | Active |
| --- | --- | --- | --- | --- |
| FactSales[DateKey] | DimDate[DateKey] | *:1 | Single | Yes |
| FactSales[CustomerKey] | DimCustomer[CustomerKey] | *:1 | Single | Yes |
| FactSales[ProductKey] | DimProduct[ProductKey] | *:1 | Single | Yes |
| FactSales[StoreKey] | DimStore[StoreKey] | *:1 | Single | Yes |
| FactSales[ChannelKey] | DimChannel[ChannelKey] | *:1 | Single | Yes |
| FactSales[RegionKey] | DimRegion[RegionKey] | *:1 | Single | Yes |
| FactReturns[DateKey] | DimDate[DateKey] | *:1 | Single | Yes |
| FactReturns[OrderDateKey] | DimDate[DateKey] | *:1 | Single | **No (inactive)** |
| FactReturns[CustomerKey], [ProductKey], [StoreKey], [ChannelKey], [RegionKey] | matching Dim | *:1 | Single | Yes |

Then:
- **Mark DimDate as date table:** select DimDate → Table tools → Mark as date table → `Date`.
- **Sort by column:** `MonthName` and `MonthShort` sort by `MonthNumber`; `DayName` by `DayOfWeekNumber`;
  `YearMonth` by `YearMonthKey`.
- **Hide** all key columns in the facts (`…Key`) so report users only see dimension attributes.
- Set the **format** of money columns to £ (Currency, English (United Kingdom)).
- Create a **hierarchy** in DimDate: Year → Quarter → MonthShort → Date (for drill-down), and in DimProduct:
  Category → SubCategory → ProductName.

Take a screenshot of the model view for the README (`screenshots/powerbi_model_view.png`).

## Step 3 — Measures
Home → Enter data → name the table `_Measures` → Load. Add every measure from `dax/measures.dax`
(New measure → paste). Format: Revenue/Profit as £ with 0 decimals, % measures as Percentage with 1 decimal.

**Reconcile before building visuals:** a table with Year + Revenue + Gross Profit + Gross Margin % + Orders must match
the table in `dax/README.md`.

## Step 4 — Theme and canvas
View → Themes → Browse for themes → `powerbi/northstar_theme.json`.
Canvas 16:9 (1280 × 720). Each page gets: title text box (top left), a slicer bar (top right), a row of KPI cards, then
2×2 visuals.

**Slicers (sync across all pages):** View → Sync slicers. Year, Quarter, Region (`DimRegion[RegionName]`),
Channel, Category. Use the *Dropdown* style to save space.

## Step 5 — The pages

### Page 1 · Executive Overview (`mockup_page1_executive_overview.png`)
| Visual | Fields |
| --- | --- |
| 7 KPI cards (new Card visual, reference label = YoY) | Revenue, Gross Profit, Gross Margin %, Orders, Average Order Value, Customers, Return Rate % (Order Cohort); reference labels: Revenue YoY %, Gross Profit YoY %, Gross Margin Change (pts) |
| Line chart | X: DimDate[MonthShort]; Y: Revenue; Legend: DimDate[Year] |
| Line chart | X: MonthShort; Y: Gross Margin %; Legend: Year |
| Bar chart | Y: DimChannel[ChannelName]; X: Revenue |
| Bar chart | Y: DimProduct[Category]; X: Gross Margin %; conditional colour: `Margin Colour` (fx → Field value) |

### Page 2 · Sales Performance
| Visual | Fields |
| --- | --- |
| Cards | Revenue, Units Sold, Revenue YoY %, Revenue % of Channel Total (filtered to Website + Mobile App) |
| Bar chart | DimRegion[RegionName] × Revenue (sorted descending) |
| Line chart | YearMonth × Revenue, Legend = ChannelName |
| Bar chart | Top 10 stores: StoreName × Revenue, filter pane → Top N = 10 by Revenue; DimStore[IsOnline] = N |
| Table | ProductName, Revenue, Gross Margin %, Product Revenue Rank; conditional formatting data bars on Revenue |
| Optional | Filled map on DimRegion[RegionName] (set data category = State or Province) |

### Page 3 · Profitability
| Visual | Fields |
| --- | --- |
| Cards | Gross Margin %, Discount Amount, Discount Rate %, Profit Lost Below Cost |
| Column chart | Discount band (create a calculated column, below) × Gross Margin % |
| Scatter | Values: ProductName; X: Revenue; Y: Gross Margin %; Legend: Category. Add a constant line at company margin |
| Bar chart | Electronics SubCategory × Gross Margin % (visual filter Category = Electronics) |
| Bar chart | DimDate[TradingPeriod] × Gross Margin % |

Calculated column (in FactSales) for the discount band:
```DAX
Discount Band =
SWITCH ( TRUE (),
    FactSales[DiscountPct] = 0,     "1 None",
    FactSales[DiscountPct] <= 0.15, "2 5-15%",
    FactSales[DiscountPct] <= 0.25, "3 20-25%",
    FactSales[DiscountPct] <= 0.35, "4 30-35%",
    "5 40%+" )
```

### Page 4 · Customer Analytics
| Visual | Fields |
| --- | --- |
| Cards | Customers, Revenue per Customer, Repeat Customer %, Guest Share of In-Store Revenue % |
| Column chart | Segment × Revenue per Customer (page filter IsGuest = N) |
| Stacked column | YearMonth × New Customers and Returning Customers |
| 100% stacked bar | AgeBand × Revenue, Legend = ChannelName |
| Matrix | Segment (rows) × Year (columns): Customers, AOV, Revenue |

### Page 5 · Returns
| Visual | Fields |
| --- | --- |
| Cards | Refund Amount, Return Rate % (Order Cohort), Returned Units, Margin after Returns % |
| Line chart | YearMonth × Return Rate % (Order Cohort), filter Category in (Clothing, Footwear), Channel in (Website, Mobile App) |
| Bar chart | Category × Return Rate % (Order Cohort) |
| Bar chart | FactReturns[ReturnReason] × Returned Units |
| Table | ProductName, Brand, Units Sold, Returned Units, Return Rate % (Order Cohort); filter Units Sold ≥ 40; sort desc |
| Bar chart | ChannelName × Gross Margin % and Margin after Returns % |

### Optional Page 6 · Inventory
Not built: no inventory data exists in scope. Say this honestly in interviews; it's listed as a next phase.

## Step 6 — Interactivity
- **Drill-through:** create a hidden page "Product Detail" with ProductName as the drill-through field (cards + monthly
  trend + returns by reason). Right-click any product → Drill through.
- **Tooltips:** a small tooltip page (Page information → Allow use as tooltip) showing Revenue, Margin, Return rate;
  assign it to the category bar charts.
- **Bookmarks + buttons:** a "Reset filters" button (bookmark with no filters).
- **Edit interactions:** stop the KPI cards from being cross-filtered by the trend charts if that confuses users.
- **Dynamic title:** use `Selected Period Label` as a measure-driven title (Format → Title → fx).

## Step 7 — Performance & publishing
- View → Performance analyzer: every visual should load in under 1 second at this size.
- Remove unused columns (e.g. OrderDateTime if not used) to reduce model size.
- Publish to Power BI Service (free account) or export to PDF for the portfolio. For GitHub, add screenshots
  of every page to `screenshots/`.
- **Row-level security (talking point):** Modeling → Manage roles → a static role such as "Newcastle" with the filter
  `DimStore[StoreName] = "Newcastle Eldon Square"`, tested with *View as*. In production you would make it dynamic: a
  small UserStore table (email → StoreKey) filtered by `USERPRINCIPALNAME()`. This shows you know how one report can
  serve every store manager safely.

## Step 8 — Final checklist
- [ ] Totals reconcile with SQL (Revenue £8,545,888; GP £3,595,004; Orders 89,528)
- [ ] DimDate marked as a date table; months sort Jan→Dec
- [ ] No bi-directional relationships; one inactive relationship (OrderDateKey)
- [ ] Every page has a title, consistent slicers, and "simulated data" in the footer
- [ ] Colours from the theme only; red/amber/green used only for status and always with a label
- [ ] Real screenshots in `screenshots/`
