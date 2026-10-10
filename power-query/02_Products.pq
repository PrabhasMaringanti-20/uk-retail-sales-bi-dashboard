// Query: Products  (raw\products.csv -> clean product dimension)
let
    Source    = Csv.Document(File.Contents(DataFolder & "raw\products.csv"),
                    [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted  = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    // Trim every text column (default transformation applies to all columns)
    Trimmed   = Table.TransformColumns(Promoted, {}, each if _ is text then Text.Trim(_) else _),
    // PR-01 exact duplicate rows
    Distinct  = Table.Distinct(Trimmed),
    // PR-02 category mapping table (lower-case variant -> standard name)
    CategoryMap = [
        #"clothing" = "Clothing", #"clothes" = "Clothing",
        #"footwear" = "Footwear", #"shoes" = "Footwear",
        #"home & kitchen" = "Home & Kitchen", #"home and kitchen" = "Home & Kitchen",
        #"electronics" = "Electronics", #"electronic" = "Electronics",
        #"beauty" = "Beauty",
        #"toys & games" = "Toys & Games", #"toys and games" = "Toys & Games",
        #"sports & outdoors" = "Sports & Outdoors", #"sports and outdoors" = "Sports & Outdoors",
        #"sport & outdoors" = "Sports & Outdoors",
        #"accessories" = "Accessories", #"accessory" = "Accessories"
    ],
    Category  = Table.TransformColumns(Distinct, {{"Category",
                    each Record.FieldOrDefault(CategoryMap, Text.Lower(_), "UNMAPPED"), type text}}),
    // PR-03 missing sub-category is flagged, not guessed
    SubCat    = Table.ReplaceValue(Category, "", "Unclassified", Replacer.ReplaceValue, {"SubCategory"}),
    // PR-04 '£19.99' -> 19.99
    Price     = Table.TransformColumns(SubCat, {{"ListPrice",
                    each Number.FromText(Text.Replace(_, "£", ""), "en-GB"), type number}}),
    Cost      = Table.TransformColumns(Price, {{"UnitCost",
                    each if _ = "" or _ = null then null else Number.FromText(_, "en-GB"), type nullable number}}),
    // PR-05 missing cost: use the median 2024 transaction cost for the SKU (query SalesCost2024 below)
    Joined    = Table.NestedJoin(Cost, {"SKU"}, SalesCost2024, {"SKU"}, "Tx", JoinKind.LeftOuter),
    Expanded  = Table.ExpandTableColumn(Joined, "Tx", {"MedianCost"}),
    FilledCost = Table.AddColumn(Expanded, "UnitCostClean",
                    each if [UnitCost] = null then [MedianCost] else [UnitCost], type number),
    Tidy      = Table.RemoveColumns(FilledCost, {"UnitCost", "MedianCost"}),
    Renamed   = Table.RenameColumns(Tidy, {{"UnitCostClean", "UnitCost"}}),
    Typed     = Table.TransformColumnTypes(Renamed, {{"LaunchDate", type date}}, "en-GB"),
    // Derived columns
    Margin    = Table.AddColumn(Typed, "StandardMarginPct",
                    each ([ListPrice] - [UnitCost]) / [ListPrice], Percentage.Type),
    PriceBand = Table.AddColumn(Margin, "PriceBand", each
                    if [ListPrice] <= 15 then "Under £15"
                    else if [ListPrice] <= 40 then "£15-£40"
                    else if [ListPrice] <= 100 then "£40-£100"
                    else "Over £100", type text)
in
    PriceBand

// ----------------------------------------------------------------------------
// Helper query: SalesCost2024  (disable load: right-click > uncheck "Enable load")
// let
//     S      = SalesStaging,
//     Y2024  = Table.SelectRows(S, each Date.Year([OrderDT]) = 2024),
//     Grp    = Table.Group(Y2024, {"SKU"}, {{"MedianCost", each List.Median([UnitCost]), type number}})
// in
//     Grp
