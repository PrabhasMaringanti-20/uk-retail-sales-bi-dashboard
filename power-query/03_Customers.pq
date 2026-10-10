// Query: Customers  (raw\customers.csv -> de-duplicated customer dimension)
let
    Source   = Csv.Document(File.Contents(DataFolder & "raw\customers.csv"),
                   [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Trimmed  = Table.TransformColumns(Promoted, {}, each if _ is text then Text.Trim(_) else _),

    // CU-01..03 standardise codes
    Segment  = Table.TransformColumns(Trimmed, {{"Segment", Text.Proper, type text}}),
    Loyalty  = Table.ReplaceValue(Segment, each [LoyaltyMember], each
                   if [LoyaltyMember] = "Yes" then "Y" else if [LoyaltyMember] = "No" then "N" else [LoyaltyMember],
                   Replacer.ReplaceValue, {"LoyaltyMember"}),
    Gender   = Table.TransformColumns(Loyalty, {{"Gender", each
                   if _ = "F" then "Female" else if _ = "M" then "Male"
                   else if _ = "" or _ = null then "Unknown" else _, type text}}),

    // CU-05/06 postcode: upper-case, remove spaces, re-insert one space before the last 3 characters, validate
    PcFormat = Table.TransformColumns(Gender, {{"Postcode", each
                   let s = Text.Upper(Text.Remove(_ ?? "", {" "}))
                   in if Text.Length(s) >= 5 then Text.Start(s, Text.Length(s) - 3) & " " & Text.End(s, 3) else s,
                   type text}}),
    // Simple structural check (M has no regex): outward 2-4 chars starting with a letter, inward = digit + 2 letters
    PcValid  = Table.AddColumn(PcFormat, "PostcodeValid", each
                   let parts = Text.Split([Postcode], " "),
                       out   = if List.Count(parts) = 2 then parts{0} else "",
                       inw   = if List.Count(parts) = 2 then parts{1} else ""
                   in if Text.Length(out) >= 2 and Text.Length(out) <= 4
                         and Text.Length(inw) = 3
                         and List.Contains({"A".."Z"}, Text.Start(out, 1))
                         and List.Contains({"0".."9"}, Text.Start(inw, 1))
                         and List.ContainsAll({"A".."Z"}, Text.ToList(Text.End(inw, 2)))
                      then "Y" else "N", type text),
    PcClean  = Table.ReplaceValue(PcValid, each [Postcode], each if [PostcodeValid] = "Y" then [Postcode] else null,
                   Replacer.ReplaceValue, {"Postcode"}),
    District = Table.AddColumn(PcClean, "PostcodeDistrict",
                   each if [Postcode] = null then "Unknown" else Text.BeforeDelimiter([Postcode], " "), type text),

    // CU-07 city casing (Text.Proper would turn "upon" into "Upon", so fix that exception)
    City     = Table.TransformColumns(District, {{"City", each
                   if _ = "" or _ = null then "Unknown"
                   else Text.Replace(Text.Proper(_), " Upon ", " upon "), type text}}),

    // CU-10/11 date of birth: two formats, impossible values -> null
    Dob      = Table.TransformColumns(City, {{"DateOfBirth", each
                   let d = try Date.From(fnParseDateTime(_)) otherwise null
                   in if d = null or d < #date(1925, 1, 1) or d > #date(2009, 12, 31) then null else d,
                   type nullable date}}),
    AgeBand  = Table.AddColumn(Dob, "AgeBand", each
                   let a = if [DateOfBirth] = null then null
                           else Number.RoundDown(Duration.Days(#date(2025, 12, 31) - [DateOfBirth]) / 365.25)
                   in if a = null then "Unknown" else if a <= 24 then "16-24" else if a <= 34 then "25-34"
                      else if a <= 44 then "35-44" else if a <= 54 then "45-54" else if a <= 64 then "55-64" else "65+",
                   type text),
    Signup   = Table.TransformColumnTypes(AgeBand, {{"SignupDate", type date}}, "en-GB"),

    // CU-12 duplicates: same e-mail (trimmed, lower case) -> keep the earliest registration
    EmailKey = Table.AddColumn(Signup, "EmailNorm", each Text.Lower(Text.Trim([Email])), type text),
    Sorted   = Table.Buffer(Table.Sort(EmailKey, {{"EmailNorm", Order.Ascending}, {"SignupDate", Order.Ascending}})),
    // Table.Distinct keeps the FIRST row per key - Table.Buffer guarantees the sort order is respected
    Masters  = Table.Distinct(Sorted, {"EmailNorm"}),
    // GDPR minimisation: drop direct identifiers before loading to the model
    Final    = Table.RemoveColumns(Masters, {"FirstName", "LastName", "Email", "EmailNorm", "DateOfBirth", "Postcode"})
in
    Final

// ----------------------------------------------------------------------------
// Helper query: CustomerIdMap (disable load) - maps every duplicate CustomerID to its master
// let
//     All     = Sorted,                                   // reference the step above via a staging query
//     Grouped = Table.Group(All, {"EmailNorm"}, {{"Ids", each [CustomerID]}, {"MasterID", each List.First([CustomerID])}}),
//     Expand  = Table.ExpandListColumn(Grouped, "Ids"),
//     Map     = Table.RenameColumns(Table.SelectColumns(Expand, {"Ids", "MasterID"}), {{"Ids", "CustomerID"}})
// in
//     Map
