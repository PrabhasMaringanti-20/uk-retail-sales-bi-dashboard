// Query: DimDate - generated in M (no source file needed). Mark as date table after loading.
let
    StartDate = #date(2024, 1, 1),
    EndDate   = #date(2025, 12, 31),
    Dates     = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    ToTable   = Table.FromList(Dates, Splitter.SplitByNothing(), {"Date"}),
    Typed     = Table.TransformColumnTypes(ToTable, {{"Date", type date}}),
    AddCols   = Table.AddColumn(Typed, "Attrs", each [
        DateKey         = Date.Year([Date]) * 10000 + Date.Month([Date]) * 100 + Date.Day([Date]),
        Year            = Date.Year([Date]),
        QuarterNumber   = Date.QuarterOfYear([Date]),
        Quarter         = "Q" & Text.From(Date.QuarterOfYear([Date])),
        MonthNumber     = Date.Month([Date]),
        MonthName       = Date.MonthName([Date], "en-GB"),
        MonthShort      = Text.Start(Date.MonthName([Date], "en-GB"), 3),
        YearMonth       = Date.ToText([Date], "yyyy-MM"),
        YearMonthKey    = Date.Year([Date]) * 100 + Date.Month([Date]),
        DayOfWeekNumber = Date.DayOfWeek([Date], Day.Monday) + 1,
        DayName         = Date.DayOfWeekName([Date], "en-GB"),
        IsWeekend       = if Date.DayOfWeek([Date], Day.Monday) >= 5 then "Y" else "N",
        // UK financial year runs April to March
        UKFinancialYear = let y = Date.Year([Date]), s = if Date.Month([Date]) >= 4 then y else y - 1
                          in "FY" & Text.From(s) & "/" & Text.End(Text.From(s + 1), 2)
    ]),
    Expanded  = Table.ExpandRecordColumn(AddCols, "Attrs",
                    {"DateKey", "Year", "QuarterNumber", "Quarter", "MonthNumber", "MonthName", "MonthShort",
                     "YearMonth", "YearMonthKey", "DayOfWeekNumber", "DayName", "IsWeekend", "UKFinancialYear"}),
    Types     = Table.TransformColumnTypes(Expanded, {{"DateKey", Int64.Type}, {"Year", Int64.Type},
                    {"QuarterNumber", Int64.Type}, {"MonthNumber", Int64.Type}, {"YearMonthKey", Int64.Type},
                    {"DayOfWeekNumber", Int64.Type}})
in
    Types
