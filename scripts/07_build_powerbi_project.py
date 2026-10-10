"""
Builds a ready-to-open Power BI Project (.pbip) in powerbi/:

  NorthStar_Retail_Dashboard.pbip                 <- double-click this in Power BI Desktop
  NorthStar_Retail_Dashboard.SemanticModel/       <- tables, Power Query (M), relationships, DAX measures
  NorthStar_Retail_Dashboard.Report/              <- 5 report pages and their visuals

Everything is generated from the clean CSVs and dax/measures.dax, so the model always matches
the data and the documented measures. A validation step at the end checks that every column and
measure used by a relationship, DAX expression or visual actually exists.

Run:  python scripts/07_build_powerbi_project.py
"""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "clean"
PBI = ROOT / "powerbi"
NAME = "NorthStar_Retail_Dashboard"
MODEL_DIR = PBI / f"{NAME}.SemanticModel"
REPORT_DIR = PBI / f"{NAME}.Report"
DEFAULT_FOLDER = "C:\\NorthStar\\uk-retail-sales-bi-dashboard\\data\\clean\\"

for d in (MODEL_DIR, REPORT_DIR):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)

# =============================================================================
# 1. SEMANTIC MODEL
# =============================================================================
TABLES = {  # model table name -> csv file
    "FactSales": "fact_sales.csv", "FactReturns": "fact_returns.csv", "DimDate": "dim_date.csv",
    "DimCustomer": "dim_customer.csv", "DimProduct": "dim_product.csv", "DimStore": "dim_store.csv",
    "DimRegion": "dim_region.csv", "DimChannel": "dim_channel.csv",
}
DATE_COLS = {"Date", "OpenDate", "SignupDate", "FirstPurchaseDate", "LaunchDate"}
DATETIME_COLS = {"OrderDateTime"}
MONEY_COLS = {"UnitPrice", "UnitCost", "GrossSales", "DiscountAmount", "NetSales", "CostAmount", "GrossProfit",
              "RefundAmount", "ListPrice"}
RATIO_COLS = {"DiscountPct", "StandardMarginPct"}
SORT_BY = {("DimDate", "MonthName"): "MonthNumber", ("DimDate", "MonthShort"): "MonthNumber",
           ("DimDate", "DayName"): "DayOfWeekNumber", ("DimDate", "YearMonth"): "YearMonthKey"}
# (sort-by needs exactly one sort value per label, so YearQuarter keeps its natural text order: 2024-Q1 < 2024-Q2 ...)


def col_type(name: str, dtype: str) -> tuple[str, str, str | None]:
    """-> (TOM dataType, M type, formatString)"""
    if name in DATE_COLS:
        return "dateTime", "type date", "dd/mm/yyyy"
    if name in DATETIME_COLS:
        return "dateTime", "type datetime", "dd/mm/yyyy hh:nn"
    if name in MONEY_COLS:
        return "decimal", "Currency.Type", "£#,0.00"
    if name in RATIO_COLS:
        return "double", "type number", "0.0%"
    if dtype.startswith("int"):
        return "int64", "Int64.Type", "0"
    if dtype.startswith("float"):
        return "double", "type number", None
    return "string", "type text", None


def m_query(table: str, csv: str, cols: list[tuple[str, str]]) -> list[str]:
    types = ", ".join(f'{{"{c}", {mt}}}' for c, mt in cols)
    return [
        "let",
        f'    Source = Csv.Document(File.Contents(DataFolder & "{csv}"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),',
        "    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),",
        "    // empty text -> null, so blank dates/numbers don't become errors when typed",
        '    Blanks = Table.TransformColumns(Promoted, {}, each if _ = "" then null else _),',
        f'    Typed = Table.TransformColumnTypes(Blanks, {{{types}}}, "en-GB")',
        "in",
        "    Typed",
    ]


tables_json, columns_index = [], {}
for tname, csv in TABLES.items():
    df = pd.read_csv(CLEAN / csv, nrows=5000)
    cols, mcols = [], []
    for c, dt in df.dtypes.astype(str).items():
        tom, mt, fmt = col_type(c, dt)
        col = {"name": c, "dataType": tom, "sourceColumn": c}
        if fmt:
            col["formatString"] = fmt
        is_key = c.endswith("Key") or c in ("ISOWeek", "Year", "MonthNumber", "QuarterNumber", "DayOfMonth",
                                            "DayOfWeekNumber", "OrderLineNumber", "MergedRecords", "SizeSqFt")
        if tom in ("int64", "double", "decimal") and (is_key or c in RATIO_COLS or c in ("UnitPrice", "UnitCost", "ListPrice")):
            col["summarizeBy"] = "none"
        elif tom in ("int64", "double", "decimal"):
            col["summarizeBy"] = "sum"
        if tname.startswith("Fact") and c.endswith("Key"):
            col["isHidden"] = True
        if (tname, c) in SORT_BY:
            col["sortByColumn"] = SORT_BY[(tname, c)]
        if tname == "DimDate" and c == "Date":
            col["isKey"] = True
        if tname == "DimRegion" and c == "RegionName":
            col["dataCategory"] = "StateOrProvince"
        cols.append(col)
        mcols.append((c, mt))
    t = {"name": tname, "columns": cols,
         "partitions": [{"name": tname, "mode": "import", "source": {"type": "m", "expression": m_query(tname, csv, mcols)}}]}
    if tname == "DimDate":
        t["dataCategory"] = "Time"            # = "Mark as date table"
    tables_json.append(t)
    columns_index[tname] = {c["name"] for c in cols}

# Calculated column: discount band (for the profitability page)
fact = next(t for t in tables_json if t["name"] == "FactSales")
fact["columns"].append({
    "type": "calculated", "name": "Discount Band", "dataType": "string",
    "expression": ("SWITCH ( TRUE (), FactSales[DiscountPct] = 0, \"1 None\", FactSales[DiscountPct] <= 0.15, \"2 5-15%\", "
                   "FactSales[DiscountPct] <= 0.25, \"3 20-25%\", FactSales[DiscountPct] <= 0.35, \"4 30-35%\", \"5 40%+\" )")})
columns_index["FactSales"].add("Discount Band")

# Hierarchies for drill-down
next(t for t in tables_json if t["name"] == "DimDate")["hierarchies"] = [{"name": "Calendar", "levels": [
    {"name": "Year", "ordinal": 0, "column": "Year"}, {"name": "Quarter", "ordinal": 1, "column": "Quarter"},
    {"name": "Month", "ordinal": 2, "column": "MonthShort"}, {"name": "Date", "ordinal": 3, "column": "Date"}]}]
next(t for t in tables_json if t["name"] == "DimProduct")["hierarchies"] = [{"name": "Product Hierarchy", "levels": [
    {"name": "Category", "ordinal": 0, "column": "Category"}, {"name": "SubCategory", "ordinal": 1, "column": "SubCategory"},
    {"name": "Product", "ordinal": 2, "column": "ProductName"}]}]

# ---- measures, parsed from dax/measures.dax (the single source of truth)
dax_text = (ROOT / "dax" / "measures.dax").read_text()
heads = list(re.finditer(r"^([A-Z][^\n=/]*?) =\n", dax_text, flags=re.M))
measures = []
for i, h in enumerate(heads):
    body = dax_text[h.end(): heads[i + 1].start() if i + 1 < len(heads) else len(dax_text)]
    lines = body.rstrip().split("\n")
    while lines and (lines[-1].strip().startswith("//") or lines[-1].strip() == ""):  # section comments of the NEXT block
        lines.pop()
    measures.append((h.group(1).strip(), "\n".join(lines).strip()))


def measure_format(n: str) -> str | None:
    if n in ("Margin Colour", "YoY Arrow", "Selected Period Label"):
        return None
    if "(pts)" in n:
        return "+0.0;-0.0;0.0"
    if "%" in n:
        return "0.0%"
    if n in ("Orders", "Customers", "Units Sold", "Returned Units", "New Customers", "Returning Customers"):
        return "#,0"
    if "Rank" in n:
        return "0"
    if n in ("Average Order Value", "Units per Order", "Revenue per Customer"):
        return "£#,0.00" if n != "Units per Order" else "0.00"
    return "£#,0"


fact["measures"] = []
for n, expr in measures:
    m = {"name": n, "expression": expr.split("\n")}
    f = measure_format(n)
    if f:
        m["formatString"] = f
    if "%" in n or "(pts)" in n:
        m["displayFolder"] = "Ratios"
    elif "PY" in n or "YoY" in n or "YTD" in n or "PM" in n or "MoM" in n or "Running" in n or "Moving" in n:
        m["displayFolder"] = "Time intelligence"
    elif "Refund" in n or "Return" in n:
        m["displayFolder"] = "Returns"
    elif "Customer" in n or "Guest" in n:
        m["displayFolder"] = "Customers"
    else:
        m["displayFolder"] = "Core"
    fact["measures"].append(m)
measure_names = {n for n, _ in measures}

# ---- relationships (all many-to-one, single direction)
rels = []
for k, dim in [("DateKey", "DimDate"), ("CustomerKey", "DimCustomer"), ("ProductKey", "DimProduct"),
               ("StoreKey", "DimStore"), ("ChannelKey", "DimChannel"), ("RegionKey", "DimRegion")]:
    for f in ("FactSales", "FactReturns"):
        rels.append({"name": f"{f}_{k}", "fromTable": f, "fromColumn": k, "toTable": dim, "toColumn": k})
rels.append({"name": "FactReturns_OrderDateKey", "fromTable": "FactReturns", "fromColumn": "OrderDateKey",
             "toTable": "DimDate", "toColumn": "DateKey", "isActive": False})

model = {
    "compatibilityLevel": 1567,
    "model": {
        "culture": "en-GB",
        "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
        "defaultPowerBIDataSourceVersion": "powerBI_V3",
        "sourceQueryCulture": "en-GB",
        "expressions": [{
            "name": "DataFolder", "kind": "m",
            "expression": [f'"{DEFAULT_FOLDER}" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]'],
            "annotations": [{"name": "PBI_ResultType", "value": "Text"}]}],
        "tables": tables_json,
        "relationships": rels,
        "annotations": [{"name": "PBI_QueryOrder", "value": json.dumps(["DataFolder"] + list(TABLES))},
                        {"name": "__PBI_TimeIntelligenceEnabled", "value": "0"}],
    },
}
(MODEL_DIR / "model.bim").write_text(json.dumps(model, indent=2, ensure_ascii=False))
(MODEL_DIR / "definition.pbism").write_text(json.dumps({"version": "1.0", "settings": {}}, indent=2))

# =============================================================================
# 2. REPORT (PBIR-Legacy report.json)
# =============================================================================
ALIAS = {"FactSales": "f", "FactReturns": "r", "DimDate": "d", "DimCustomer": "c", "DimProduct": "p",
         "DimStore": "s", "DimRegion": "g", "DimChannel": "ch"}
used_refs: list[tuple[str, str, str]] = []


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def field(ref: str):
    """'DimDate.Year' -> column ref; 'm:Revenue' -> measure ref (all measures live on FactSales)."""
    if ref.startswith("m:"):
        name = ref[2:]
        used_refs.append(("measure", "FactSales", name))
        return ("FactSales", {"Measure": {"Expression": {"SourceRef": {"Source": ALIAS["FactSales"]}}, "Property": name}},
                f"FactSales.{name}")
    table, col = ref.split(".", 1)
    used_refs.append(("column", table, col))
    return (table, {"Column": {"Expression": {"SourceRef": {"Source": ALIAS[table]}}, "Property": col}}, f"{table}.{col}")


vid = 0


def visual(vtype, x, y, w, h, roles: dict, title=None, order=None, objects=None, extra=None):
    global vid
    vid += 1
    entities, select, projections = [], [], {}
    for role, refs in roles.items():
        projections[role] = []
        for r in refs:
            t, expr, qref = field(r)
            if t not in entities:
                entities.append(t)
            if not any(s["Name"] == qref for s in select):
                select.append({**expr, "Name": qref})
            projections[role].append({"queryRef": qref} | ({"active": True} if role == "Category" else {}))
    query = {"Version": 2, "From": [{"Name": ALIAS[e], "Entity": e, "Type": 0} for e in entities], "Select": select}
    if order:
        ref, direction = order
        _, expr, _ = field(ref)
        query["OrderBy"] = [{"Direction": 2 if direction == "desc" else 1, "Expression": expr}]
    sv = {"visualType": vtype, "projections": projections, "prototypeQuery": query, "drillFilterOtherVisuals": True}
    if objects:
        sv["objects"] = objects
    vc = {}
    if title:
        vc["title"] = [{"properties": {"show": lit("true"), "text": lit(f"'{title}'")}}]
    if vc:
        sv["vcObjects"] = vc
    cfg = {"name": f"visual{vid:03d}", "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": vid, "width": w, "height": h}}],
           "singleVisual": sv}
    if extra:
        cfg.update(extra)
    return {"x": x, "y": y, "z": vid, "width": w, "height": h, "config": json.dumps(cfg), "filters": "[]"}


def textbox(x, y, w, h, text, size="20pt", bold=True, color="#0B0B0B"):
    global vid
    vid += 1
    style = {"fontSize": size, "color": color}
    if bold:
        style["fontWeight"] = "bold"
    cfg = {"name": f"visual{vid:03d}", "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": vid, "width": w, "height": h}}],
           "singleVisual": {"visualType": "textbox", "drillFilterOtherVisuals": True,
                            "objects": {"general": [{"properties": {"paragraphs": [
                                {"textRuns": [{"value": text, "textStyle": style}]}]}}]}}}
    return {"x": x, "y": y, "z": vid, "width": w, "height": h, "config": json.dumps(cfg), "filters": "[]"}


LABELS = {"labels": [{"properties": {"show": lit("true")}}]}


def card(x, y, w, h, measure):
    return visual("card", x, y, w, h, {"Values": [f"m:{measure}"]},
                  objects={"labels": [{"properties": {"fontSize": lit("20D")}}],
                           "categoryLabels": [{"properties": {"show": lit("true")}}]})


def slicer(x, y, w, h, ref, group):
    return visual("slicer", x, y, w, h, {"Values": [ref]},
                  objects={"data": [{"properties": {"mode": lit("'Dropdown'")}}],
                           "header": [{"properties": {"show": lit("true")}}]},
                  extra={"syncGroup": {"groupName": group, "fieldChanges": True, "filterChanges": True}})


def header(title, subtitle):
    return [
        textbox(20, 8, 600, 40, title),
        textbox(20, 44, 620, 24, subtitle + "  ·  NorthStar Retail UK (fictional) · simulated data", "10pt", False, "#52514E"),
        slicer(650, 8, 150, 60, "DimDate.Year", "Year"),
        slicer(805, 8, 150, 60, "DimRegion.RegionName", "Region"),
        slicer(960, 8, 150, 60, "DimChannel.ChannelName", "Channel"),
        slicer(1115, 8, 150, 60, "DimProduct.Category", "Category"),
    ]


def card_row(names, y=78, h=82):
    w = (1240 - 10 * (len(names) - 1)) / len(names)
    return [card(round(20 + i * (w + 10)), y, round(w), h, n) for i, n in enumerate(names)]


pages = []

# ---- Page 1: Executive Overview
v = header("Executive Overview", "How are we doing vs last year?")
v += card_row(["Revenue", "Gross Profit", "Gross Margin %", "Orders", "Average Order Value", "Customers",
               "Return Rate % (Order Cohort)"])
v.append(visual("lineChart", 20, 170, 760, 270, {"Category": ["DimDate.MonthShort"], "Y": ["m:Revenue"], "Series": ["DimDate.Year"]},
                "Revenue by month, 2024 vs 2025"))
v.append(visual("tableEx", 20, 450, 760, 260, {"Values": ["DimDate.Year", "m:Revenue", "m:Revenue YoY %", "m:Gross Profit",
                                                           "m:Gross Profit YoY %", "m:Gross Margin %", "m:Gross Margin Change (pts)", "m:Orders"]},
                "Year comparison (must match SQL: revenue £8,545,888 total)"))
v.append(visual("clusteredBarChart", 790, 170, 470, 270, {"Category": ["DimChannel.ChannelName"], "Y": ["m:Revenue"]},
                "Revenue by channel", order=("m:Revenue", "desc"), objects=LABELS))
v.append(visual("clusteredBarChart", 790, 450, 470, 260, {"Category": ["DimProduct.Category"], "Y": ["m:Gross Margin %"]},
                "Gross margin % by category", order=("m:Gross Margin %", "desc"), objects=LABELS))
pages.append(("Executive Overview", v))

# ---- Page 2: Sales Performance
v = header("Sales Performance", "Where does revenue come from?")
v += card_row(["Revenue", "Revenue YoY %", "Units Sold", "Orders", "Average Order Value"])
v.append(visual("clusteredBarChart", 20, 170, 420, 540, {"Category": ["DimRegion.RegionName"], "Y": ["m:Revenue"]},
                "Revenue by region", order=("m:Revenue", "desc"), objects=LABELS))
v.append(visual("lineChart", 450, 170, 810, 260, {"Category": ["DimDate.YearMonth"], "Y": ["m:Revenue"], "Series": ["DimChannel.ChannelName"]},
                "Monthly revenue by channel"))
v.append(visual("clusteredBarChart", 450, 440, 400, 270, {"Category": ["DimStore.StoreName"], "Y": ["m:Revenue (Physical Stores)"]},
                "Physical stores by revenue", order=("m:Revenue (Physical Stores)", "desc")))
v.append(visual("tableEx", 860, 440, 400, 270, {"Values": ["DimProduct.ProductName", "m:Revenue", "m:Gross Margin %", "m:Units Sold"]},
                "Products (sorted by revenue)", order=("m:Revenue", "desc")))
pages.append(("Sales Performance", v))

# ---- Page 3: Profitability
v = header("Profitability", "Where is margin lost?")
v += card_row(["Gross Margin %", "Gross Margin Change (pts)", "Discount Amount", "Discount Rate %", "Profit Lost Below Cost"])
v.append(visual("clusteredColumnChart", 20, 170, 600, 270, {"Category": ["FactSales.Discount Band"], "Y": ["m:Gross Margin %"]},
                "Gross margin % by discount band", order=("FactSales.Discount Band", "asc"), objects=LABELS))
v.append(visual("clusteredBarChart", 630, 170, 630, 270, {"Category": ["DimDate.TradingPeriod"], "Y": ["m:Gross Margin %"]},
                "Gross margin % by trading period", order=("m:Gross Margin %", "desc"), objects=LABELS))
v.append(visual("clusteredBarChart", 20, 450, 600, 260, {"Category": ["DimStore.StoreName"], "Y": ["m:Gross Margin % (Physical Stores)"]},
                "Store margin league (physical stores)", order=("m:Gross Margin % (Physical Stores)", "asc")))
v.append(visual("tableEx", 630, 450, 630, 260, {"Values": ["DimProduct.Category", "DimProduct.SubCategory", "m:Revenue",
                                                            "m:Gross Margin %", "m:Profit Lost Below Cost"]},
                "Sub-categories (lowest margin first)", order=("m:Gross Margin %", "asc")))
pages.append(("Profitability", v))

# ---- Page 4: Customer Analytics
v = header("Customer Analytics", "Who are our valuable customers, and are they staying?")
v += card_row(["Customers", "Revenue per Customer", "Repeat Customer %", "Guest Share of In-Store Revenue %"])
v.append(visual("clusteredColumnChart", 20, 170, 600, 270, {"Category": ["DimCustomer.Segment"], "Y": ["m:Revenue per Customer"]},
                "Revenue per customer by segment", order=("m:Revenue per Customer", "desc"), objects=LABELS))
v.append(visual("clusteredColumnChart", 630, 170, 630, 270, {"Category": ["DimDate.YearMonth"], "Y": ["m:New Customers", "m:Returning Customers"]},
                "New vs returning customers by month"))
v.append(visual("hundredPercentStackedBarChart", 20, 450, 600, 260, {"Category": ["DimCustomer.AgeBand"], "Y": ["m:Revenue"],
                                                                     "Series": ["DimChannel.ChannelName"]},
                "Channel mix by age band"))
v.append(visual("tableEx", 630, 450, 630, 260, {"Values": ["DimCustomer.Segment", "m:Customers", "m:Average Order Value",
                                                            "m:Revenue", "m:Gross Margin %"]},
                "Segment summary"))
pages.append(("Customer Analytics", v))

# ---- Page 5: Returns
v = header("Returns", "What comes back, why, and from which supplier?")
v += card_row(["Refund Amount", "Return Rate % (Order Cohort)", "Returned Units", "Margin after Returns %"])
v.append(visual("lineChart", 20, 170, 600, 270, {"Category": ["DimDate.YearMonth"], "Y": ["m:Return Rate % (Order Cohort)"]},
                "Return rate by order month (latest month incomplete)"))
v.append(visual("clusteredBarChart", 630, 170, 630, 270, {"Category": ["DimProduct.Category"], "Y": ["m:Return Rate % (Order Cohort)"]},
                "Return rate by category", order=("m:Return Rate % (Order Cohort)", "desc"), objects=LABELS))
v.append(visual("clusteredBarChart", 20, 450, 400, 260, {"Category": ["FactReturns.ReturnReason"], "Y": ["m:Returned Units"]},
                "Returned units by reason", order=("m:Returned Units", "desc"), objects=LABELS))
v.append(visual("clusteredBarChart", 430, 450, 400, 260, {"Category": ["DimChannel.ChannelName"], "Y": ["m:Gross Margin %", "m:Margin after Returns %"]},
                "Margin before vs after refunds"))
v.append(visual("tableEx", 840, 450, 420, 260, {"Values": ["DimProduct.Brand", "m:Return Rate % (Order Cohort)", "m:Refunds by Order Date"]},
                "Brands by return rate", order=("m:Return Rate % (Order Cohort)", "desc")))
pages.append(("Returns", v))

sections = []
for i, (pname, vcs) in enumerate(pages):
    sections.append({"name": f"ReportSection{i + 1:02d}", "displayName": pname, "displayOption": 1, "width": 1280, "height": 720,
                     "ordinal": i, "config": "{}", "filters": "[]", "visualContainers": vcs})
report = {
    "config": json.dumps({"version": "5.43", "themeCollection": {"baseTheme": {"name": "CY24SU06", "version": "5.55", "type": 2}},
                          "activeSectionIndex": 0, "defaultDrillFilterOtherVisuals": True,
                          "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": 1}}),
    "layoutOptimization": 0,
    "sections": sections,
    "resourcePackages": [],
}
(REPORT_DIR / "report.json").write_text(json.dumps(report, indent=2))
(REPORT_DIR / "definition.pbir").write_text(json.dumps(
    {"version": "1.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}, "byConnection": None}}, indent=2))
(PBI / f"{NAME}.pbip").write_text(json.dumps(
    {"version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}], "settings": {"enableAutoRecovery": True}}, indent=2))

# =============================================================================
# 3. VALIDATION - every reference must exist
# =============================================================================
errors = []
for kind, t, n in used_refs:
    if kind == "measure" and n not in measure_names:
        errors.append(f"visual uses unknown measure [{n}]")
    if kind == "column" and n not in columns_index.get(t, set()):
        errors.append(f"visual uses unknown column {t}[{n}]")
for r in rels:
    for side in ("from", "to"):
        if r[f"{side}Column"] not in columns_index[r[f"{side}Table"]]:
            errors.append(f"relationship {r['name']} uses unknown column")
all_dax = [(n, e) for n, e in measures] + [("Discount Band", fact["columns"][-1]["expression"])]
for n, expr in all_dax:
    code = re.sub(r"//[^\n]*", "", expr)
    code = re.sub(r'"[^"]*"', '""', code)
    for t, c in re.findall(r"\b(Fact\w+|Dim\w+)\[([^\]]+)\]", code):
        if t not in columns_index or c not in columns_index[t]:
            errors.append(f"measure [{n}] references unknown column {t}[{c}]")
    for m in re.findall(r"(?<![\w\]])\[([^\]]+)\]", code):
        if m not in measure_names:
            errors.append(f"measure [{n}] references unknown measure [{m}]")
    if code.count("(") != code.count(")"):
        errors.append(f"measure [{n}] has unbalanced parentheses")
for t in TABLES:
    if t not in ALIAS:
        errors.append(f"no alias for {t}")

print(f"tables: {len(tables_json)}  relationships: {len(rels)}  measures: {len(measures)}  "
      f"pages: {len(sections)}  visuals: {sum(len(s['visualContainers']) for s in sections)}")
if errors:
    print("VALIDATION FAILED:\n  " + "\n  ".join(sorted(set(errors))))
    raise SystemExit(1)
print("validation: all columns, measures and relationships referenced exist")
