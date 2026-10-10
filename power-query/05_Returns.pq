// Query: Returns (raw\returns.csv -> clean returns fact, linked to the clean Sales query)
let
    Source   = Csv.Document(File.Contents(DataFolder & "raw\returns.csv"),
                   [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Trimmed  = Table.TransformColumns(Promoted, {}, each if _ is text then Text.Trim(_) else _),
    Distinct = Table.Distinct(Trimmed),                                            // RE-01
    Typed    = Table.TransformColumnTypes(Distinct, {{"LineNo", Int64.Type}, {"ReturnQty", Int64.Type},
                   {"RefundAmount", type number}, {"ReturnDate", type date}}, "en-GB"),
    // RE-02 keep only returns that match a valid sale (inner join = orphans drop out)
    Joined   = Table.NestedJoin(Typed, {"OrderID", "LineNo"}, Sales, {"OrderID", "LineNo"}, "S", JoinKind.Inner),
    Expanded = Table.ExpandTableColumn(Joined, "S", {"OrderDT", "Quantity", "CustomerIDClean", "SKU", "StoreCode", "Channel"}),
    // RE-03 return date must be on/after the order date
    ValidSeq = Table.SelectRows(Expanded, each [ReturnDate] >= Date.From([OrderDT])),
    // RE-04 cannot return more than was bought
    CapQty   = Table.ReplaceValue(ValidSeq, each [ReturnQty], each List.Min({[ReturnQty], [Quantity]}),
                   Replacer.ReplaceValue, {"ReturnQty"}),
    // RE-05/06 reason: unify "/" spacing and casing, blank -> Not stated
    Reasons  = {"Wrong size / fit", "Faulty / defective", "Damaged / defective item", "Not as described",
                "Changed mind", "Arrived late"},
    Reason   = Table.TransformColumns(CapQty, {{"ReturnReason", each
                   let k = Text.Lower(Text.Replace(Text.Replace(_ ?? "", " / ", "/"), "/", " / ")),
                       hit = List.Select(Reasons, (r) => Text.Lower(r) = k)
                   in if List.IsEmpty(hit) then "Not stated" else hit{0}, type text}}),
    // RE-07 duplicate ReturnID after standardisation
    Unique   = Table.Distinct(Reason, {"ReturnID"}),
    DaysTo   = Table.AddColumn(Unique, "DaysToReturn", each Duration.Days([ReturnDate] - Date.From([OrderDT])), Int64.Type),
    DateKeys = Table.AddColumn(DaysTo, "DateKey", each Number.From(Date.ToText([ReturnDate], "yyyyMMdd")), Int64.Type),
    OrderKey = Table.AddColumn(DateKeys, "OrderDateKey", each Number.From(DateTime.ToText([OrderDT], "yyyyMMdd")), Int64.Type)
in
    OrderKey
