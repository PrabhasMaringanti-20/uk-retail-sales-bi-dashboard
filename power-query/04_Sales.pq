// Query: SalesStaging (disable load) -> Sales (valid rows) and Sales_Quarantine (rejected rows)
let
    Source   = Csv.Document(File.Contents(DataFolder & "raw\sales_transactions.csv"),
                   [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Trimmed  = Table.TransformColumns(Promoted, {}, each if _ is text then Text.Trim(_) else _),

    // SA-01 exact duplicate rows (double-loaded batch)
    Distinct = Table.Distinct(Trimmed),

    // SA-02 channel mapping: 14 spellings -> 4 channels
    Channel  = Table.TransformColumns(Distinct, {{"Channel", each
                   let l = Text.Lower(_) in
                   if List.Contains({"in-store", "instore", "store", "in store"}, l) then "In-Store"
                   else if List.Contains({"website", "web"}, l) then "Website"
                   else if List.Contains({"mobile app", "app"}, l) then "Mobile App"
                   else if List.Contains({"click & collect", "click and collect", "c&c"}, l) then "Click & Collect"
                   else "UNMAPPED", type text}}),

    // SA-03 parse both date formats
    OrderDT  = Table.AddColumn(Channel, "OrderDT", each fnParseDateTime([OrderDateTime]), type nullable datetime),

    // Numbers (en-GB culture so "." is the decimal point)
    Numbers  = Table.TransformColumns(OrderDT, {
                   {"Quantity",    each Number.FromText(_, "en-GB"), Int64.Type},
                   {"UnitPrice",   each if _ = "" or _ = null then null else Number.FromText(_, "en-GB"), type nullable number},
                   {"UnitCost",    each Number.FromText(_, "en-GB"), type number},
                   // SA-09 "20" means 20% -> 0.20
                   {"DiscountPct", each let d = Number.FromText(_, "en-GB") in if d > 1 then d / 100 else d, type number}}),

    // SA-04..08 validation: one column says WHY a row fails (null = valid)
    // SKU list read straight from the raw product file. Referencing the Products query here would create a
    // circular dependency (Products fills missing costs from SalesStaging -> SalesStaging -> Products).
    RawProducts = Table.PromoteHeaders(Csv.Document(File.Contents(DataFolder & "raw\products.csv"),
                      [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv])),
    SkuList  = List.Buffer(List.Transform(RawProducts[SKU], Text.Trim)),
    Issue    = Table.AddColumn(Numbers, "DQ_Issue", each
                   if [OrderDT] = null then "SA-04 invalid date"
                   else if [OrderDT] < #datetime(2024, 1, 1, 0, 0, 0) or [OrderDT] >= #datetime(2026, 1, 1, 0, 0, 0)
                        then "SA-05 outside window"
                   else if [Quantity] <= 0 then "SA-06 negative quantity"
                   else if [Quantity] > 20 then "SA-07 quantity outlier"
                   else if not List.Contains(SkuList, [SKU]) then "SA-08 unknown SKU"
                   else if [Channel] = "UNMAPPED" then "SA-02 unknown channel"
                   else null, type nullable text),
    Year     = Table.AddColumn(Issue, "Year", each if [OrderDT] = null then null else Date.Year([OrderDT]), Int64.Type)
in
    Year

// ============================================================================
// Query: Sales_Quarantine   (load it to a hidden table so the rejected rows stay visible and countable)
// let Source = Table.SelectRows(SalesStaging, each [DQ_Issue] <> null) in Source
//
// ============================================================================
// Query: Sales   (the clean fact table)
// let
//     Valid      = Table.SelectRows(SalesStaging, each [DQ_Issue] = null),
//     // SA-10 missing price: median price of the same SKU in the same year
//     RefPrice   = Table.Group(Table.SelectRows(Valid, each [UnitPrice] <> null), {"SKU", "Year"},
//                      {{"RefPrice", each List.Median([UnitPrice]), type number}}),
//     Joined     = Table.NestedJoin(Valid, {"SKU", "Year"}, RefPrice, {"SKU", "Year"}, "R", JoinKind.LeftOuter),
//     Expanded   = Table.ExpandTableColumn(Joined, "R", {"RefPrice"}),
//     Imputed    = Table.AddColumn(Expanded, "IsPriceImputed", each if [UnitPrice] = null then "Y" else "N", type text),
//     Price      = Table.AddColumn(Imputed, "UnitPriceClean", each [UnitPrice] ?? [RefPrice], type number),
//     // SA-11 duplicate customers -> master ID;  SA-12 blank customer = GUEST (legitimate)
//     Cust       = Table.NestedJoin(Price, {"CustomerID"}, CustomerIdMap, {"CustomerID"}, "M", JoinKind.LeftOuter),
//     CustX      = Table.ExpandTableColumn(Cust, "M", {"MasterID"}),
//     CustomerID = Table.AddColumn(CustX, "CustomerIDClean", each
//                      if [CustomerID] = "" or [CustomerID] = null then "GUEST" else [MasterID] ?? [CustomerID], type text),
//     // Measures-to-be as columns (row level)
//     Gross      = Table.AddColumn(CustomerID, "GrossSales", each [Quantity] * [UnitPriceClean], Currency.Type),
//     Disc       = Table.AddColumn(Gross, "DiscountAmount", each Number.Round([GrossSales] * [DiscountPct], 2), Currency.Type),
//     Net        = Table.AddColumn(Disc, "NetSales", each [GrossSales] - [DiscountAmount], Currency.Type),
//     CostAmt    = Table.AddColumn(Net, "CostAmount", each [Quantity] * [UnitCost], Currency.Type),
//     GP         = Table.AddColumn(CostAmt, "GrossProfit", each [NetSales] - [CostAmount], Currency.Type),
//     DateKey    = Table.AddColumn(GP, "DateKey", each Number.From(DateTime.ToText([OrderDT], "yyyyMMdd")), Int64.Type),
//     Keep       = Table.SelectColumns(DateKey, {"OrderID", "LineNo", "DateKey", "OrderDT", "CustomerIDClean", "SKU",
//                      "StoreCode", "Channel", "Quantity", "UnitPriceClean", "UnitCost", "DiscountPct", "GrossSales",
//                      "DiscountAmount", "NetSales", "CostAmount", "GrossProfit", "PaymentMethod", "IsPriceImputed"})
// in
//     Keep
