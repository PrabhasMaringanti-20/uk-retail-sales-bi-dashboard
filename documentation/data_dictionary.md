# Data Dictionary

All tables live in `data/clean/` (CSV) and in PostgreSQL schema `northstar` (same columns in snake_case).
Money is GBP excluding VAT, at 2 decimal places.

## FactSales — one row per order line

| Column | Type | Description / rule |
| --- | --- | --- |
| SalesLineKey | int, PK | Surrogate key |
| OrderID | text | Order number (degenerate dimension). Count DISTINCT for orders |
| OrderLineNumber | int | Line within the order (1..n). (OrderID, line) is unique |
| DateKey | int, FK → DimDate | Order date as YYYYMMDD |
| OrderDateTime | timestamp | Order timestamp (till/web log) |
| CustomerKey | int, FK → DimCustomer | -1 = Guest (anonymous in-store) |
| ProductKey | int, FK → DimProduct | |
| StoreKey | int, FK → DimStore | Physical store, or the E-commerce Hub for website/app orders |
| ChannelKey | int, FK → DimChannel | |
| RegionKey | int, FK → DimRegion | Store region (in-store, C&C) or delivery region (website/app) |
| Quantity | int | 1–20 (validated) |
| UnitPrice | money | List price at time of sale |
| UnitCost | money | Cost price at time of sale (changes over time, so it is stored on the fact) |
| DiscountPct | decimal | 0–0.60, in 5% steps |
| GrossSales | money | Quantity × UnitPrice |
| DiscountAmount | money | GrossSales × DiscountPct |
| NetSales | money | **Revenue** = GrossSales − DiscountAmount |
| CostAmount | money | Quantity × UnitCost |
| GrossProfit | money | NetSales − CostAmount |
| PaymentMethod | text | Contactless, Chip & PIN, Cash, Mobile Wallet, Debit/Credit Card, PayPal, Klarna |
| IsPriceImputed | Y/N | Y = UnitPrice was missing in the source and was imputed (rule SA-10) |

## FactReturns — one row per returned order line

| Column | Type | Description / rule |
| --- | --- | --- |
| ReturnKey | int, PK | Surrogate key |
| ReturnID | text | Business key from the returns system (unique) |
| SalesLineKey | int | The original sale line (lineage; not a Power BI relationship) |
| OrderID, OrderLineNumber | | Original order line |
| DateKey | int, FK → DimDate | **Return date** (active relationship) |
| OrderDateKey | int, FK → DimDate | Original order date (inactive relationship) |
| CustomerKey … RegionKey | FKs | Copied from the original sale so returns slice the same way as sales |
| ReturnQty | int | ≤ quantity sold (rule RE-04) |
| RefundAmount | money | ≤ amount paid for the line |
| ReturnReason | text | Wrong size / fit, Faulty / defective, Damaged / defective item, Not as described, Changed mind, Arrived late, Not stated |
| ReturnMethod | text | In-Store or Post |
| DaysToReturn | int | Return date − order date (≥ 0) |

## DimDate — one row per day, 2024-01-01 to 2025-12-31

DateKey (PK, YYYYMMDD), Date, Year, Quarter (Q1–Q4), QuarterNumber, YearQuarter (2025-Q1), MonthNumber, MonthName,
MonthShort, YearMonth (2025-01), YearMonthKey (202501, for sorting), ISOWeek, DayOfMonth, DayOfWeekNumber
(1 = Monday), DayName, IsWeekend (Y/N), IsUKBankHoliday (Y/N, England & Wales), UKFinancialYear (FY2024/25 = April–March),
TradingPeriod (Regular Trading, January Sale, Summer Sale, Black Friday Week, Christmas Trading, Boxing Day Sale).

## DimCustomer — one row per de-duplicated customer + Guest

| Column | Description |
| --- | --- |
| CustomerKey | PK. -1 = Guest |
| CustomerID | Business key (master ID after merging duplicates) |
| Gender | Female, Male, Other/Prefer not to say, Unknown |
| AgeBand | 16-24 … 65+, Unknown (age at 31-Dec-2025; date of birth itself is not kept) |
| City | Standardised city name |
| PostcodeDistrict | Outward code only, e.g. `M14` (GDPR minimisation) |
| PostcodeValid | N = the source postcode was missing or invalid |
| CustomerRegion | Home region (descriptive only) |
| Segment | Value, Mainstream, Premium (Guest for -1) |
| LoyaltyMember | Y/N |
| SignupDate | Registration date |
| FirstPurchaseDate | First order in the data window (blank = registered but never purchased) |
| IsGuest | Y only for -1 |
| MergedRecords | Number of duplicate records merged into this customer |

## DimProduct — one row per SKU

ProductKey (PK), SKU, ProductName, Category (8), SubCategory (32 + "Unclassified"), Brand, UnitCost (current standard
cost), ListPrice (2024 list price), LaunchDate, IsOwnLabel (Y/N, NorthStar Essentials), StandardMarginPct
((ListPrice − UnitCost) ÷ ListPrice), PriceBand (Under £15, £15-£40, £40-£100, Over £100).

## DimStore — one row per store

StoreKey (PK), StoreCode, StoreName, StoreType (Flagship, Shopping Centre, High Street, Retail Park, Outlet, Online),
City, Postcode, StoreRegion (text only), SizeSqFt (0 for online), OpenDate, IsOnline (Y/N),
IsLikeForLike (Y = open before 1 Jan 2024, so comparable in both years).

## DimRegion — 12 UK regions

RegionKey (PK), RegionCode, RegionName, Nation (England, Scotland, Wales, Northern Ireland).

## DimChannel — 4 channels

| ChannelKey | ChannelName | ChannelType |
| --- | --- | --- |
| 1 | In-Store | Physical |
| 2 | Website | Digital |
| 3 | Mobile App | Digital |
| 4 | Click & Collect | Hybrid (ordered online, collected in store) |
