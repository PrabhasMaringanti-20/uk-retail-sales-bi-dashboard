// Function query: fnParseDateTime
// Parses the two formats found in the source (ISO from the web system, UK from the store tills).
// Anything else (e.g. 2024-02-30) returns null, so it can be quarantined - never guessed.
// Explicit formats avoid the classic bug where 03/04/2024 is read as 4 March by a US locale.
(t as nullable text) as nullable datetime =>
let
    txt = if t = null then null else Text.Trim(t),
    result =
        if txt = null or txt = "" then null
        else if Text.Contains(txt, "/") then
            try DateTime.FromText(txt, [Format = "dd/MM/yyyy HH:mm", Culture = "en-GB"])
            otherwise try DateTime.From(Date.FromText(txt, [Format = "dd/MM/yyyy", Culture = "en-GB"]))
            otherwise null
        else
            try DateTime.FromText(txt, [Format = "yyyy-MM-dd HH:mm:ss", Culture = "en-GB"])
            otherwise try DateTime.From(Date.FromText(txt, [Format = "yyyy-MM-dd", Culture = "en-GB"]))
            otherwise null
in
    result
