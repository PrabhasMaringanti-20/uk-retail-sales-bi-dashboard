"""
Phase 5 - builds excel/NorthStar_Excel_Analysis.xlsx: live formulas only, no pasted results,
so the workbook teaches XLOOKUP, INDEX/MATCH, SUMIFS, COUNTIFS, AVERAGEIFS, IFS,
conditional formatting and data-validation checks on real (simulated) data.

Sheets
  README        what each sheet teaches
  Sales_Dec25   December 2025 sales lines (clean) + formula columns
  Products      product lookup table
  Summary       SUMIFS / COUNTIFS business summary with conditional formatting
  Raw_DQ        a sample of RAW (messy) rows with data-quality check formulas
  Pivot_Steps   how to build the PivotTables by hand

Run:  python scripts/helpers/build_excel.py
"""

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

ROOT = Path(__file__).resolve().parents[2]
CLEAN, RAW = ROOT / "data" / "clean", ROOT / "data" / "raw"
OUT = ROOT / "excel" / "NorthStar_Excel_Analysis.xlsx"
OUT.parent.mkdir(exist_ok=True)

HEAD = PatternFill("solid", fgColor="2A78D6")
NOTE = PatternFill("solid", fgColor="F1F0EC")
BOLD_W = Font(bold=True, color="FFFFFF")
GBP = '£#,##0.00'
GBP0 = '£#,##0'
PCT = '0.0%'

fs = pd.read_csv(CLEAN / "fact_sales.csv")
dp = pd.read_csv(CLEAN / "dim_product.csv")
dst = pd.read_csv(CLEAN / "dim_store.csv")
dch = pd.read_csv(CLEAN / "dim_channel.csv")

dec = fs[(fs.DateKey >= 20251201) & (fs.DateKey <= 20251231)].copy()
dec = dec.merge(dp[["ProductKey", "SKU"]], on="ProductKey").merge(dst[["StoreKey", "StoreCode"]], on="StoreKey") \
         .merge(dch[["ChannelKey", "ChannelName"]], on="ChannelKey")
dec["OrderDate"] = pd.to_datetime(dec["OrderDateTime"]).dt.date
dec = dec.sort_values(["OrderDateTime", "OrderID", "OrderLineNumber"])

wb = Workbook()


def header(ws, row, cols, fill=HEAD):
    for i, c in enumerate(cols, 1):
        cell = ws.cell(row=row, column=i, value=c)
        cell.fill, cell.font = fill, BOLD_W
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def widths(ws, w):
    for i, x in enumerate(w, 1):
        ws.column_dimensions[get_column_letter(i)].width = x


# ------------------------------------------------------------------ README
ws = wb.active
ws.title = "README"
lines = [
    ("NorthStar Retail UK - Excel analysis (SIMULATED DATA, fictional company)", True),
    ("", False),
    ("Sheet", True),
    ("Sales_Dec25 - December 2025 order lines. Grey columns are formulas: INDEX/MATCH, XLOOKUP, IFS, maths.", False),
    ("Products - lookup table (one row per SKU). Formatted as an Excel Table called tblProducts.", False),
    ("Summary - SUMIFS / COUNTIFS / AVERAGEIFS summaries, a reconciliation check and conditional formatting.", False),
    ("Raw_DQ - 3,000 RAW rows as delivered by the source systems, with data-quality checks (COUNTBLANK, COUNTIFS...).", False),
    ("Pivot_Steps - step-by-step PivotTable exercises to do by hand.", False),
    ("", False),
    ("Notes", True),
    ("XLOOKUP needs Excel 2021 / Microsoft 365. INDEX/MATCH works in every version - both are used on purpose.", False),
    ("Reconciliation: Summary!B4 must equal the December 2025 revenue from SQL (see sql/README.md).", False),
    ("Never type over a formula column - change the inputs and let the formulas recalculate.", False),
]
for r, (txt, b) in enumerate(lines, 1):
    ws.cell(row=r, column=1, value=txt).font = Font(bold=b, size=13 if r == 1 else 11)
ws.column_dimensions["A"].width = 120

# ------------------------------------------------------------------ Products
wp = wb.create_sheet("Products")
pcols = ["SKU", "ProductName", "Category", "SubCategory", "Brand", "UnitCost", "ListPrice"]
header(wp, 1, pcols)
for r, row in enumerate(dp[pcols].itertuples(index=False), 2):
    for c, v in enumerate(row, 1):
        wp.cell(row=r, column=c, value=v)
np_ = len(dp) + 1
for r in range(2, np_ + 1):
    wp.cell(row=r, column=6).number_format = GBP
    wp.cell(row=r, column=7).number_format = GBP
tab = Table(displayName="tblProducts", ref=f"A1:G{np_}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight9", showRowStripes=True)
wp.add_table(tab)
widths(wp, [15, 48, 18, 18, 22, 11, 11])
wp.freeze_panes = "A2"

# ------------------------------------------------------------------ Sales_Dec25
wsd = wb.create_sheet("Sales_Dec25")
inputs = ["OrderID", "LineNo", "OrderDate", "SKU", "StoreCode", "Channel", "Quantity", "UnitPrice", "UnitCost", "DiscountPct"]
formulas = ["Category", "Brand", "GrossSales", "DiscountAmount", "NetSales", "CostAmount", "GrossProfit", "Margin",
            "DiscountBand", "LossLine"]
header(wsd, 1, inputs + formulas)
n = len(dec)
last = n + 1
prod_rng = f"Products!$A$2:$A${np_}"
for r, row in enumerate(dec.itertuples(index=False), 2):
    vals = [row.OrderID, row.OrderLineNumber, row.OrderDate, row.SKU, row.StoreCode, row.ChannelName, row.Quantity,
            row.UnitPrice, row.UnitCost, row.DiscountPct]
    for c, v in enumerate(vals, 1):
        wsd.cell(row=r, column=c, value=v)
    f = {
        # K: INDEX/MATCH - classic lookup, exact match (0)
        11: f"=INDEX(Products!$C$2:$C${np_},MATCH(D{r},{prod_rng},0))",
        # L: XLOOKUP - modern lookup with a 'not found' value
        12: f'=_xlfn.XLOOKUP(D{r},{prod_rng},Products!$E$2:$E${np_},"Not found")',
        13: f"=G{r}*H{r}",
        14: f"=ROUND(M{r}*J{r},2)",
        15: f"=M{r}-N{r}",
        16: f"=G{r}*I{r}",
        17: f"=O{r}-P{r}",
        18: f'=IF(O{r}=0,"",Q{r}/O{r})',
        19: f'=_xlfn.IFS(J{r}=0,"1 None",J{r}<=0.15,"2 5-15%",J{r}<=0.25,"3 20-25%",J{r}<=0.35,"4 30-35%",TRUE,"5 40%+")',
        20: f'=IF(Q{r}<0,"LOSS","")',
    }
    for c, v in f.items():
        wsd.cell(row=r, column=c, value=v)
for r in range(2, last + 1):
    wsd.cell(row=r, column=3).number_format = "dd/mm/yyyy"
    for c in (8, 9, 13, 14, 15, 16, 17):
        wsd.cell(row=r, column=c).number_format = GBP
    wsd.cell(row=r, column=10).number_format = "0%"
    wsd.cell(row=r, column=18).number_format = PCT
for c in range(11, 21):
    wsd.cell(row=1, column=c).fill = PatternFill("solid", fgColor="52514E")
tab = Table(displayName="tblSales", ref=f"A1:T{last}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleLight1", showRowStripes=True)
wsd.add_table(tab)
# Conditional formatting: highlight loss-making lines red, deep discounts amber
red = PatternFill("solid", fgColor="F8D0D0")
amber = PatternFill("solid", fgColor="FBE6B3")
wsd.conditional_formatting.add(f"Q2:Q{last}", CellIsRule(operator="lessThan", formula=["0"], fill=red))
wsd.conditional_formatting.add(f"J2:J{last}", CellIsRule(operator="greaterThanOrEqual", formula=["0.3"], fill=amber))
widths(wsd, [11, 7, 11, 14, 9, 15, 8, 10, 10, 9, 17, 20, 11, 11, 11, 11, 11, 8, 10, 8])
wsd.freeze_panes = "A2"

S = "Sales_Dec25"
NET, GP, CAT, CH, QTY, DB, DISC, LOSS = (f"{S}!$O$2:$O${last}", f"{S}!$Q$2:$Q${last}", f"{S}!$K$2:$K${last}",
                                         f"{S}!$F$2:$F${last}", f"{S}!$G$2:$G${last}", f"{S}!$S$2:$S${last}",
                                         f"{S}!$N$2:$N${last}", f"{S}!$T$2:$T${last}")
ORD = f"{S}!$A$2:$A${last}"

# ------------------------------------------------------------------ Summary
sm = wb.create_sheet("Summary")
sm["A1"] = "December 2025 summary - every number is a live formula"
sm["A1"].font = Font(bold=True, size=14)
kpis = [
    ("Revenue", f"=SUM({NET})", GBP0),
    ("Gross profit", f"=SUM({GP})", GBP0),
    ("Gross margin", "=B5/B4", PCT),
    ("Order lines", f"=COUNTA({ORD})", "#,##0"),
    ("Orders (distinct)", f"=SUMPRODUCT(1/COUNTIF({ORD},{ORD}))", "#,##0"),
    ("Average order value", "=B4/B8", GBP),
    ("Units", f"=SUM({QTY})", "#,##0"),
    ("Discount given", f"=SUM({DISC})", GBP0),
    ("Loss-making lines", f'=COUNTIF({LOSS},"LOSS")', "#,##0"),
]
sm["A3"], sm["B3"] = "KPI", "Value"
header(sm, 3, ["KPI", "Value"])
for i, (k, f, fmt) in enumerate(kpis, 4):
    sm.cell(row=i, column=1, value=k)
    c = sm.cell(row=i, column=2, value=f)
    c.number_format = fmt
sm["C8"] = "<- SUMPRODUCT(1/COUNTIF()) counts distinct orders (lines are not orders!)"
sm["C8"].font = Font(italic=True, color="52514E")

# Reconciliation check against the SQL figure computed when the workbook was built
sql_rev = round(dec["NetSales"].sum(), 2)
sm["D3"], sm["E3"] = "Reconciliation", ""
header_cells = sm["D3"]
header_cells.font = Font(bold=True)
sm["D4"], sm["E4"] = "Revenue in SQL (Dec 2025)", sql_rev
sm["E4"].number_format = GBP
sm["D5"], sm["E5"] = "Difference", "=B4-E4"
sm["E5"].number_format = GBP
sm["D6"], sm["E6"] = "Status", '=IF(ABS(E5)<5,"MATCH","CHECK")'
sm["D7"] = ("Tolerance £5: Excel ROUND() rounds halves away from zero, Python/SQL pipeline rounded halves to even, "
            "so ~13,700 lines differ by a few pence in total. Explain known differences - don't hide them.")
sm["D7"].font = Font(italic=True, color="52514E")
sm["D7"].alignment = Alignment(wrap_text=True, vertical="top")
sm.merge_cells("D7:H10")
sm.conditional_formatting.add("E6", CellIsRule(operator="equal", formula=['"MATCH"'], fill=PatternFill("solid", fgColor="CDEFDF")))
sm.conditional_formatting.add("E6", CellIsRule(operator="equal", formula=['"CHECK"'], fill=red))

# By category (SUMIFS / COUNTIFS / AVERAGEIFS)
r0 = 15
sm.cell(row=r0 - 1, column=1, value="By category").font = Font(bold=True, size=12)
header(sm, r0, ["Category", "Revenue", "Gross profit", "Margin", "Lines", "Avg line value", "Share of revenue", "Loss lines"])
cats = sorted(dp["Category"].unique())
for i, cat in enumerate(cats, r0 + 1):
    sm.cell(row=i, column=1, value=cat)
    sm.cell(row=i, column=2, value=f"=SUMIFS({NET},{CAT},A{i})").number_format = GBP0
    sm.cell(row=i, column=3, value=f"=SUMIFS({GP},{CAT},A{i})").number_format = GBP0
    sm.cell(row=i, column=4, value=f'=IF(B{i}=0,"",C{i}/B{i})').number_format = PCT
    sm.cell(row=i, column=5, value=f"=COUNTIFS({CAT},A{i})").number_format = "#,##0"
    sm.cell(row=i, column=6, value=f"=AVERAGEIFS({NET},{CAT},A{i})").number_format = GBP
    sm.cell(row=i, column=7, value=f"=B{i}/$B$4").number_format = PCT
    sm.cell(row=i, column=8, value=f'=COUNTIFS({CAT},A{i},{LOSS},"LOSS")').number_format = "#,##0"
end = r0 + len(cats)
sm.cell(row=end + 1, column=1, value="Total").font = Font(bold=True)
sm.cell(row=end + 1, column=2, value=f"=SUM(B{r0 + 1}:B{end})").number_format = GBP0
sm.cell(row=end + 1, column=3, value=f"=SUM(C{r0 + 1}:C{end})").number_format = GBP0
sm.cell(row=end + 1, column=4, value=f"=C{end + 1}/B{end + 1}").number_format = PCT
sm.conditional_formatting.add(f"B{r0 + 1}:B{end}", DataBarRule(start_type="min", end_type="max", color="2A78D6"))
sm.conditional_formatting.add(f"D{r0 + 1}:D{end}", ColorScaleRule(start_type="min", start_color="EB6834",
                                                                     mid_type="percentile", mid_value=50, mid_color="FFFFFF",
                                                                     end_type="max", end_color="2A78D6"))

# By channel x discount band (2-condition SUMIFS)
r1 = end + 4
sm.cell(row=r1 - 1, column=1, value="Margin by channel and discount band (SUMIFS with 2 conditions)").font = Font(bold=True, size=12)
bands = ["1 None", "2 5-15%", "3 20-25%", "4 30-35%", "5 40%+"]
header(sm, r1, ["Channel"] + bands)
for i, ch in enumerate(["In-Store", "Website", "Mobile App", "Click & Collect"], r1 + 1):
    sm.cell(row=i, column=1, value=ch)
    for j, b in enumerate(bands, 2):
        col = get_column_letter(j)
        sm.cell(row=i, column=j, value=f'=IFERROR(SUMIFS({GP},{CH},$A{i},{DB},{col}${r1})/SUMIFS({NET},{CH},$A{i},{DB},{col}${r1}),"")').number_format = PCT
rng = f"B{r1 + 1}:F{r1 + 4}"
sm.conditional_formatting.add(rng, CellIsRule(operator="lessThan", formula=["0"], fill=red))
sm.conditional_formatting.add(rng, CellIsRule(operator="between", formula=["0", "0.2"], fill=amber))
widths(sm, [26, 16, 16, 12, 12, 16, 16, 12])

# ------------------------------------------------------------------ Raw_DQ
rq = wb.create_sheet("Raw_DQ")
raw = (pd.read_csv(RAW / "sales_transactions.csv", dtype=str, keep_default_na=False)
         .sort_values(["OrderID", "LineNo"], kind="stable").head(3000))   # sorted, so duplicate pairs sit together
rcols = list(raw.columns)
checks = ["DQ_PriceBlank", "DQ_ChannelValid", "DQ_DiscountWhole", "DQ_QtyInvalid", "DQ_UKDate", "DQ_DupKey", "DQ_Guest"]
header(rq, 1, rcols + checks)
nr = len(raw) + 1
for r, row in enumerate(raw.itertuples(index=False), 2):
    for c, v in enumerate(row, 1):
        if rcols[c - 1] in ("Quantity", "UnitPrice", "UnitCost", "DiscountPct", "LineNo") and v != "":
            v = float(v) if "." in v else int(v)
        rq.cell(row=r, column=c, value=v if v != "" else None)
    rq.cell(row=r, column=13, value=f'=IF(ISBLANK(I{r}),1,0)')
    rq.cell(row=r, column=14, value=f'=IF(ISNUMBER(MATCH(G{r},{{"In-Store","Website","Mobile App","Click & Collect"}},0)),0,1)')
    rq.cell(row=r, column=15, value=f"=IF(K{r}>1,1,0)")
    rq.cell(row=r, column=16, value=f"=IF(OR(H{r}<1,H{r}>20),1,0)")
    rq.cell(row=r, column=17, value=f'=IF(ISNUMBER(SEARCH("/",C{r})),1,0)')
    rq.cell(row=r, column=18, value=f"=IF(COUNTIFS($A$2:$A${nr},A{r},$B$2:$B${nr},B{r})>1,1,0)")
    rq.cell(row=r, column=19, value=f"=IF(ISBLANK(D{r}),1,0)")
for c in range(13, 20):
    rq.cell(row=1, column=c).fill = PatternFill("solid", fgColor="52514E")
rq.conditional_formatting.add(f"M2:R{nr}", CellIsRule(operator="equal", formula=["1"], fill=red))
# Summary of checks at the top-right
rq["V1"], rq["W1"], rq["X1"] = "Check", "Rows failing", "% of rows"
for c in ("V1", "W1", "X1"):
    rq[c].font = Font(bold=True)
labels = ["Missing unit price", "Channel not one of 4 standard labels", "Discount typed as whole number",
          "Quantity outside 1-20", "Date in UK DD/MM/YYYY format", "Duplicate OrderID+LineNo",
          "Guest (blank customer) - legitimate, not an error"]
for i, (lab, col) in enumerate(zip(labels, "MNOPQRS"), 2):
    rq.cell(row=i, column=22, value=lab)
    rq.cell(row=i, column=23, value=f"=SUM({col}2:{col}{nr})")
    rq.cell(row=i, column=24, value=f"=W{i}/COUNTA($A$2:$A${nr})").number_format = "0.00%"
rq.cell(row=10, column=22, value="Total rows checked")
rq.cell(row=10, column=23, value=f"=COUNTA(A2:A{nr})")
rq.cell(row=11, column=22, value="COUNTIFS flags BOTH copies of a duplicate: 2 flags = 1 extra row to remove.").font = Font(italic=True)
widths(rq, [11, 6, 18, 9, 14, 9, 15, 7, 9, 9, 9, 13, 8, 8, 8, 8, 8, 8, 8, 2, 2, 46, 13, 10])
rq.freeze_panes = "A2"

# ------------------------------------------------------------------ Pivot_Steps
pv = wb.create_sheet("Pivot_Steps")
steps = [
    "PivotTable exercises (do these by hand - building them is the skill)",
    "",
    "1. Click any cell in Sales_Dec25 > Insert > PivotTable > New worksheet.",
    "2. Rows: Category. Values: NetSales (Sum), GrossProfit (Sum). Check the total equals Summary!B4.",
    "3. Add a calculated field: PivotTable Analyze > Fields, Items & Sets > Calculated Field > Margin = GrossProfit / NetSales.",
    "   Why not average the Margin column? Because an average of ratios weights a £2 cable like a £300 headphone.",
    "4. Columns: Channel. Show Values As > % of Row Total -> channel mix per category.",
    "5. Rows: DiscountBand, Values: NetSales, GrossProfit, Margin -> the deeper the discount, the lower the margin.",
    "6. Insert > Slicer > StoreCode. Insert > Timeline > OrderDate (filter by day/week).",
    "7. Rows: Brand, Filter: Category = Electronics; sort by GrossProfit ascending to find weak brands.",
    "8. Conditional formatting on the pivot: Home > Conditional Formatting > Color Scales on the Margin field.",
    "9. Refresh: change a UnitPrice in Sales_Dec25, then PivotTable Analyze > Refresh - see the pivot update.",
    "",
    "Interview point: Excel is ideal for quick exploration and validation of a sample;",
    "for 185,000 rows across 2 years, the database + Power BI model is the right tool.",
]
for i, s in enumerate(steps, 1):
    pv.cell(row=i, column=1, value=s).font = Font(bold=(i == 1), size=13 if i == 1 else 11)
pv.column_dimensions["A"].width = 120

wb.save(OUT)
print(f"wrote {OUT}  ({n:,} December lines)  SQL Dec-2025 revenue £{sql_rev:,.2f}")
