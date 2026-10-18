"""
Builds every chart used in the insight report, presentation and README, plus
design mockups of the five Power BI pages, straight from the clean star schema.

Output: screenshots/*.png

The dashboard mockups are rendered with matplotlib to show the intended layout.
They are NOT Power BI screenshots - replace them with real screenshots once the
.pbix is built (see powerbi/01_build_guide.md).

Run:  python scripts/helpers/build_charts.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, PercentFormatter

ROOT = Path(__file__).resolve().parents[2]
CLEAN = ROOT / "data" / "clean"
OUT = ROOT / "screenshots"
OUT.mkdir(exist_ok=True)

# Colour-blind-validated categorical palette (fixed order) + neutral ink
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN, VIOLET, RED = (
    "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948")
GREY, SURFACE, INK, INK2, GRID = "#b9b8b2", "#fcfcfb", "#0b0b0b", "#52514e", "#e6e5e0"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK2, "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlelocation": "left", "axes.titlepad": 10,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "legend.frameon": False, "legend.fontsize": 9, "axes.axisbelow": True,
})
GBP = FuncFormatter(lambda v, _: f"£{v / 1e6:.1f}M" if abs(v) >= 1e6 else f"£{v / 1e3:.0f}K")

# ------------------------------------------------------------------ load
fs = pd.read_csv(CLEAN / "fact_sales.csv")
fr = pd.read_csv(CLEAN / "fact_returns.csv")
dd = pd.read_csv(CLEAN / "dim_date.csv")
dp = pd.read_csv(CLEAN / "dim_product.csv")
dst = pd.read_csv(CLEAN / "dim_store.csv")
dch = pd.read_csv(CLEAN / "dim_channel.csv")
dc = pd.read_csv(CLEAN / "dim_customer.csv")
dr = pd.read_csv(CLEAN / "dim_region.csv")

s = (fs.merge(dd[["DateKey", "Year", "YearMonth", "MonthNumber", "MonthShort", "TradingPeriod"]], on="DateKey")
       .merge(dp[["ProductKey", "Category", "Brand", "SubCategory"]], on="ProductKey")
       .merge(dst[["StoreKey", "StoreName", "StoreType", "IsOnline"]], on="StoreKey")
       .merge(dch[["ChannelKey", "ChannelName"]], on="ChannelKey")
       .merge(dc[["CustomerKey", "Segment"]], on="CustomerKey")
       .merge(dr[["RegionKey", "RegionName"]], on="RegionKey"))
s = s.merge(fr[["SalesLineKey", "RefundAmount"]], on="SalesLineKey", how="left")
s["RefundAmount"] = s["RefundAmount"].fillna(0)


def save(fig, name):
    fig.savefig(OUT / name, dpi=160, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def kpi(df):
    rev = df["NetSales"].sum()
    return dict(rev=rev, gp=df["GrossProfit"].sum(), margin=df["GrossProfit"].sum() / rev,
                orders=df["OrderID"].nunique(), aov=rev / df["OrderID"].nunique(),
                customers=df.loc[df["CustomerKey"] != -1, "CustomerKey"].nunique(),
                rr=df["RefundAmount"].sum() / rev)


# ================================================================== insight charts
# 1. Monthly revenue and margin, 2024 vs 2025 (two panels - never a dual axis)
m = s.groupby(["Year", "MonthNumber"]).agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum")).reset_index()
m["margin"] = m["gp"] / m["rev"]
months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6.4), sharex=True, gridspec_kw={"hspace": 0.35})
for yr, col in [(2024, GREY), (2025, BLUE)]:
    d = m[m["Year"] == yr]
    a1.plot(d["MonthNumber"], d["rev"], color=col, lw=2, marker="o", ms=5, label=str(yr))
    a2.plot(d["MonthNumber"], d["margin"], color=col, lw=2, marker="o", ms=5, label=str(yr))
a1.set_title("Revenue by month: 2025 above 2024 every month")
a1.yaxis.set_major_formatter(GBP)
a1.legend(loc="upper left")
a2.set_title("Gross margin by month: 2025 below 2024, worst in sale months")
a2.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
a2.set_xticks(range(1, 13), months)
for mn in (1, 7, 11):
    v = m[(m.Year == 2025) & (m.MonthNumber == mn)]["margin"].iloc[0]
    a2.annotate(f"{v:.0%}", (mn, v), textcoords="offset points", xytext=(0, -16), ha="center", color=INK2, fontsize=9)
save(fig, "01_monthly_revenue_margin.png")

# 2. Category: share of revenue vs share of profit
c = s.groupby("Category").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
c["rev_share"], c["gp_share"], c["margin"] = c.rev / c.rev.sum(), c.gp / c.gp.sum(), c.gp / c.rev
c = c.sort_values("rev_share")
fig, ax = plt.subplots(figsize=(10, 5.2))
y = np.arange(len(c))
ax.barh(y + 0.2, c["rev_share"], height=0.38, color=BLUE, label="Share of revenue")
ax.barh(y - 0.2, c["gp_share"], height=0.38, color=ORANGE, label="Share of gross profit")
ax.set_yticks(y, [f"{n}  ({mg:.0%} margin)" for n, mg in zip(c.index, c.margin)])
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Electronics: biggest share of revenue, smallest share of profit per £")
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
save(fig, "02_category_revenue_vs_profit.png")

# 3. Discount band vs margin
bands = pd.cut(s["DiscountPct"], [-0.01, 0, 0.15, 0.25, 0.35, 1], labels=["None", "5-15%", "20-25%", "30-35%", "40%+"])
b = s.groupby(bands, observed=True).agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
b["margin"] = b.gp / b.rev
fig, ax = plt.subplots(figsize=(8.5, 4.6))
cols = [BLUE, BLUE, BLUE, ORANGE, ORANGE]
bars = ax.bar(b.index.astype(str), b["margin"], color=cols, width=0.6)
for bar, v, r in zip(bars, b["margin"], b["rev"]):
    ax.text(bar.get_x() + bar.get_width() / 2, v + 0.01, f"{v:.0%}", ha="center", color=INK, fontsize=10)
    ax.text(bar.get_x() + bar.get_width() / 2, 0.012, (f"£{r / 1e6:.1f}M" if r >= 1e6 else f"£{r / 1e3:.0f}K"), ha="center", color="white", fontsize=8)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Gross margin by discount level: deep discounts leave almost no profit")
ax.set_xlabel("Discount on the order line")
ax.grid(axis="x", visible=False)
save(fig, "03_discount_vs_margin.png")

# 4. Channel growth
ch = s.groupby(["ChannelName", "Year"])["NetSales"].sum().unstack()
ch["growth"] = ch[2025] / ch[2024] - 1
ch = ch.sort_values("growth")
fig, ax = plt.subplots(figsize=(8.5, 4))
ax.barh(ch.index, ch["growth"], color=[GREY if g < 0.1 else BLUE for g in ch["growth"]], height=0.55)
for i, (g, r) in enumerate(zip(ch["growth"], ch[2025])):
    ax.text(g + 0.01, i, f"+{g:.0%}  (£{r / 1e6:.2f}M in 2025)", va="center", color=INK, fontsize=9)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_xlim(0, ch["growth"].max() * 1.6)
ax.set_title("Revenue growth 2025 vs 2024 by channel: digital is driving growth")
ax.grid(axis="y", visible=False)
save(fig, "04_channel_growth.png")

# 5. Return rate and margin-after-returns by channel
rc = s.groupby("ChannelName").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"), ref=("RefundAmount", "sum"))
rc["m"] = rc.gp / rc.rev
rc["m_after"] = (rc.gp - rc.ref) / rc.rev
rc = rc.sort_values("m_after")
fig, ax = plt.subplots(figsize=(8.5, 4.2))
y = np.arange(len(rc))
ax.barh(y + 0.2, rc["m"], height=0.38, color=GREY, label="Gross margin")
ax.barh(y - 0.2, rc["m_after"], height=0.38, color=BLUE, label="Margin after refunds")
for i, (a, b_) in enumerate(zip(rc["m"], rc["m_after"])):
    ax.text(b_ + 0.005, i - 0.2, f"{b_:.0%}", va="center", fontsize=9)
ax.set_yticks(y, rc.index)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Refunds remove 10-12 margin points online vs 4 in store")
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
save(fig, "05_margin_after_returns_by_channel.png")

# 6. Online apparel return rate trend
ap = s[s.Category.isin(["Clothing", "Footwear"]) & s.ChannelName.isin(["Website", "Mobile App"])]
t = ap.groupby("YearMonth").agg(rev=("NetSales", "sum"), ref=("RefundAmount", "sum"))
t["rr"] = t.ref / t.rev
fig, ax = plt.subplots(figsize=(10, 4.2))
ax.plot(range(len(t)), t["rr"], color=BLUE, lw=2, marker="o", ms=5)
ax.plot(len(t) - 1, t["rr"].iloc[-1], marker="o", ms=8, color=SURFACE, mec=GREY, mew=2)
ax.annotate("Dec 2025: incomplete\n(return window still open)", (len(t) - 1, t["rr"].iloc[-1]),
            xytext=(-150, -8), textcoords="offset points", fontsize=8, color=INK2,
            arrowprops=dict(arrowstyle="-", color=GREY))
ax.set_xticks(range(len(t)), [ym[2:] if ym.endswith(("01", "07")) else "" for ym in t.index])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_ylim(0, t["rr"].max() * 1.2)
ax.set_title("Online clothing & footwear return rate (by order month): ~16% to ~27%")
save(fig, "06_online_apparel_return_trend.png")

# 7. Brand return rates 2024 vs 2025 (apparel/footwear brands)
br = s[s.Category.isin(["Clothing", "Footwear"])].groupby(["Brand", "Year"]).agg(rev=("NetSales", "sum"), ref=("RefundAmount", "sum"))
br["rr"] = br.ref / br.rev
br = br["rr"].unstack().sort_values(2025)
fig, ax = plt.subplots(figsize=(8.5, 4.2))
y = np.arange(len(br))
for i, (a, b_) in enumerate(zip(br[2024], br[2025])):
    col = ORANGE if b_ - a > 0.08 else BLUE
    ax.plot([a, b_], [i, i], color=GRID, lw=3, zorder=1)
    ax.scatter([a], [i], color=GREY, s=60, zorder=2)
    ax.scatter([b_], [i], color=col, s=60, zorder=3)
    ax.text(b_ + 0.006, i, f"{b_:.0%}", va="center", fontsize=9)
ax.set_yticks(y, br.index)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.scatter([], [], color=GREY, label="2024")
ax.scatter([], [], color=BLUE, label="2025")
ax.legend(loc="lower right")
ax.set_title("Clothing & footwear return rate by brand: Stride Lab jumps in 2025")
ax.grid(axis="y", visible=False)
save(fig, "07_brand_return_rates.png")

# 8. Store margin league
st = s[s.IsOnline == "N"].groupby("StoreName").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"), disc=("DiscountPct", "mean"))
st["m"] = st.gp / st.rev
st = st.sort_values("m")
fig, ax = plt.subplots(figsize=(9, 7.5))
cols = [ORANGE if n in ("Bluewater Outlet", "Newcastle Eldon Square") else BLUE for n in st.index]
ax.barh(st.index, st["m"], color=cols, height=0.65)
for i, (mg, dsc) in enumerate(zip(st["m"], st["disc"])):
    ax.text(mg + 0.004, i, f"{mg:.0%}  (avg disc {dsc:.0%})", va="center", fontsize=8, color=INK2)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_xlim(0, 0.6)
ax.set_title("Gross margin by store: two stores sit far below the pack")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8)
save(fig, "08_store_margin.png")

# 9. Margin bridge 2024 -> 2025
y24 = s[s.Year == 2024]
y25 = s[s.Year == 2025]
c24, d24 = y24.CostAmount.sum() / y24.GrossSales.sum(), y24.DiscountAmount.sum() / y24.GrossSales.sum()
c25, d25 = y25.CostAmount.sum() / y25.GrossSales.sum(), y25.DiscountAmount.sum() / y25.GrossSales.sum()
m24, m_disc, m25 = 1 - c24 / (1 - d24), 1 - c24 / (1 - d25), 1 - c25 / (1 - d25)
steps = [("2024 margin", m24, None), ("More discounting", m_disc - m24, m24), ("Cost up faster\nthan prices", m25 - m_disc, m_disc), ("2025 margin", m25, None)]
fig, ax = plt.subplots(figsize=(8.5, 4.4))
for i, (lab, v, base) in enumerate(steps):
    if base is None:
        ax.bar(i, v, color=BLUE, width=0.55)
        ax.text(i, v + 0.004, f"{v:.1%}", ha="center", fontsize=10)
    else:
        ax.bar(i, v, bottom=base, color=ORANGE, width=0.55)
        ax.text(i, base + 0.004, f"{v * 100:+.1f} pts", ha="center", fontsize=10)
ax.set_xticks(range(4), [x[0] for x in steps])
ax.set_ylim(0.36, 0.45)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Why gross margin fell 2.4 points (axis starts at 36%)")
ax.grid(axis="x", visible=False)
save(fig, "09_margin_bridge.png")

# 10. RFM segment share
rfm = pd.DataFrame({"Segment": ["Champions", "Loyal", "At risk", "Lapsed", "New / promising", "Needs attention"]})
base = s[s.CustomerKey != -1].groupby("CustomerKey").agg(last=("DateKey", "max"), f=("OrderID", "nunique"), m=("NetSales", "sum"))
base["recency"] = (pd.Timestamp("2025-12-31") - pd.to_datetime(base["last"].astype(str))).dt.days
base["r"] = pd.qcut(base["recency"].rank(method="first", ascending=False), 5, labels=False) + 1
base["fq"] = pd.qcut(base["f"].rank(method="first"), 5, labels=False) + 1
base["mq"] = pd.qcut(base["m"].rank(method="first"), 5, labels=False) + 1


def lab(r):
    if r.r >= 4 and r.fq >= 4 and r.mq >= 4: return "Champions"
    if r.r >= 3 and r.fq >= 3: return "Loyal"
    if r.r >= 4 and r.fq <= 2: return "New / promising"
    if r.r <= 2 and r.fq >= 3: return "At risk"
    if r.r <= 2 and r.fq <= 2: return "Lapsed"
    return "Needs attention"


base["seg"] = base.apply(lab, axis=1)
g = base.groupby("seg").agg(cust=("m", "size"), rev=("m", "sum"))
g = g.reindex(rfm.Segment)
g["cust_share"], g["rev_share"] = g.cust / g.cust.sum(), g.rev / g.rev.sum()
fig, ax = plt.subplots(figsize=(9, 4.4))
y = np.arange(len(g))[::-1]
ax.barh(y + 0.2, g["cust_share"], height=0.38, color=GREY, label="Share of customers")
ax.barh(y - 0.2, g["rev_share"], height=0.38, color=BLUE, label="Share of revenue")
for yy, v in zip(y, g["rev_share"]):
    ax.text(v + 0.005, yy - 0.2, f"{v:.0%}", va="center", fontsize=9)
ax.set_yticks(y, g.index)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("RFM segments: 'At risk' customers still hold ~15% of revenue")
ax.legend(loc="lower right")
ax.grid(axis="y", visible=False)
save(fig, "10_rfm_segments.png")

# 11. Impact vs effort matrix (scores from insights/02_recommendations.md)
recs = [  # id, label, impact 1-5, effort 1-5
    ("R1", "Discount guardrails", 4.6, 2.0), ("R2", "Electronics price/mix", 4.2, 3.0),
    ("R3", "Fix Stride Lab sizing", 3.8, 1.8), ("R4", "Size guide & fit tool", 3.4, 3.6),
    ("R5", "Voltix supplier claim", 2.8, 1.5), ("R6", "Newcastle promo review", 2.4, 1.2),
    ("R7", "Win back 'At risk'", 3.6, 2.4), ("R8", "Capture guest shoppers", 3.0, 3.2),
    ("R9", "Grow app, check returns", 3.2, 3.8), ("R10", "Outlet role review", 1.8, 2.6),
]
fig, ax = plt.subplots(figsize=(8.5, 6.5))
ax.axhline(3, color=GRID, lw=1.5)
ax.axvline(3, color=GRID, lw=1.5)
for txt, (x, yq) in {"QUICK WINS": (1.1, 4.85), "MAJOR PROJECTS": (4.9, 4.85), "FILL-INS": (1.1, 1.15),
                     "DEPRIORITISE": (4.9, 1.15)}.items():
    ax.text(x, yq, txt, color=INK2, fontsize=9, fontweight="bold", ha="left" if x < 3 else "right")
for rid, labl, imp, eff in recs:
    ax.scatter(eff, imp, s=90, color=BLUE if (imp >= 3 and eff < 3) else (ORANGE if imp >= 3 else GREY),
               edgecolor=SURFACE, linewidth=2, zorder=3)
    ax.annotate(f"{rid} {labl}", (eff, imp), xytext=(7, 4), textcoords="offset points", fontsize=8.5, color=INK)
ax.set_xlim(1, 5)
ax.set_ylim(1, 5)
ax.set_xlabel("Effort (1 = days, 5 = multi-quarter)")
ax.set_ylabel("Impact (1 = minor, 5 = major profit impact)")
ax.set_title("Impact vs effort: where to start")
ax.grid(False)
save(fig, "11_impact_effort_matrix.png")


# ================================================================== Power BI page mockups
def tiles(fig, items, top=0.825, height=0.075):
    n = len(items)
    w = 0.94 / n
    for i, (label, value, sub) in enumerate(items):
        ax = fig.add_axes([0.03 + i * w, top, w - 0.01, height])
        ax.set_axis_off()
        ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, color="#f1f0ec", zorder=0))
        ax.text(0.06, 0.70, label, fontsize=8.5, color=INK2, transform=ax.transAxes)
        ax.text(0.06, 0.22, value, fontsize=15, fontweight="bold", color=INK, transform=ax.transAxes)
        if sub:
            ax.text(0.94, 0.25, sub, fontsize=8, color=INK2, ha="right", transform=ax.transAxes)


def page(title, subtitle):
    fig = plt.figure(figsize=(16, 9))
    fig.text(0.03, 0.955, title, fontsize=18, fontweight="bold")
    fig.text(0.03, 0.925, subtitle, fontsize=9.5, color=INK2)
    fig.text(0.97, 0.955, "Slicers:  Year | Quarter | Region | Channel | Category", fontsize=9, color=INK2, ha="right")
    fig.text(0.97, 0.012, "Design mockup rendered in Python - layout reference for the Power BI build (simulated data)",
             fontsize=8, color=INK2, ha="right", style="italic")
    return fig


k24, k25 = kpi(y24), kpi(y25)


def delta(a, b, pts=False):
    return f"{(b - a) * 100:+.1f} pts vs LY" if pts else f"{b / a - 1:+.1%} vs LY"


# Page 1 - Executive overview
fig = page("Executive Overview — FY 2025", "NorthStar Retail UK (fictional) · all channels · gross profit = revenue − cost of goods")
tiles(fig, [("Revenue", f"£{k25['rev'] / 1e6:.2f}M", delta(k24["rev"], k25["rev"])),
            ("Gross profit", f"£{k25['gp'] / 1e6:.2f}M", delta(k24["gp"], k25["gp"])),
            ("Gross margin", f"{k25['margin']:.1%}", delta(k24["margin"], k25["margin"], True)),
            ("Orders", f"{k25['orders']:,}", delta(k24["orders"], k25["orders"])),
            ("AOV", f"£{k25['aov']:.2f}", delta(k24["aov"], k25["aov"])),
            ("Customers", f"{k25['customers']:,}", delta(k24["customers"], k25["customers"])),
            ("Return rate", f"{k25['rr']:.1%}", delta(k24["rr"], k25["rr"], True))])
ax = fig.add_axes([0.04, 0.45, 0.55, 0.33])
for yr, col in [(2024, GREY), (2025, BLUE)]:
    d = m[m.Year == yr]
    ax.plot(d.MonthNumber, d.rev, color=col, lw=2, marker="o", ms=4, label=f"Revenue {yr}")
ax.set_xticks(range(1, 13), months)
ax.yaxis.set_major_formatter(GBP)
ax.set_title("Revenue by month vs last year")
ax.legend(loc="upper left")
ax = fig.add_axes([0.04, 0.07, 0.55, 0.28])
for yr, col in [(2024, GREY), (2025, BLUE)]:
    d = m[m.Year == yr]
    ax.plot(d.MonthNumber, d.margin, color=col, lw=2, marker="o", ms=4, label=f"Margin {yr}")
ax.set_xticks(range(1, 13), months)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Gross margin % by month vs last year")
ax = fig.add_axes([0.67, 0.45, 0.30, 0.33])
cc = y25.groupby("ChannelName")["NetSales"].sum().sort_values()
ax.barh(cc.index, cc.values, color=BLUE, height=0.55)
ax.xaxis.set_major_formatter(GBP)
ax.set_title("Revenue by channel (2025)")
ax.grid(axis="y", visible=False)
ax = fig.add_axes([0.67, 0.07, 0.30, 0.28])
cat = y25.groupby("Category").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
cat["m"] = cat.gp / cat.rev
cat = cat.sort_values("m")
ax.barh(cat.index, cat.m, color=[ORANGE if v < 0.3 else BLUE for v in cat.m], height=0.6)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Gross margin by category (2025)")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8)
save(fig, "mockup_page1_executive_overview.png")

# Page 2 - Sales performance
fig = page("Sales Performance", "Where revenue comes from: products, stores, regions, channels")
tiles(fig, [("Revenue", f"£{k25['rev'] / 1e6:.2f}M", delta(k24["rev"], k25["rev"])),
            ("Units", f"{y25.Quantity.sum():,}", delta(y24.Quantity.sum(), y25.Quantity.sum())),
            ("LFL store growth", "+5.3%", "stores open both years"),
            ("Online share", f"{y25[y25.ChannelName.isin(['Website', 'Mobile App'])].NetSales.sum() / k25['rev']:.0%}", "web + app")])
ax = fig.add_axes([0.04, 0.45, 0.42, 0.33])
rg = y25.groupby("RegionName")["NetSales"].sum().sort_values()
ax.barh(rg.index, rg.values, color=BLUE, height=0.6)
ax.xaxis.set_major_formatter(GBP)
ax.set_title("Revenue by region (2025)")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8)
ax = fig.add_axes([0.56, 0.45, 0.41, 0.33])
mc = s.pivot_table(index="YearMonth", columns="ChannelName", values="NetSales", aggfunc="sum")
for col_, name in zip([BLUE, ORANGE, AQUA, VIOLET], ["In-Store", "Website", "Mobile App", "Click & Collect"]):
    ax.plot(range(len(mc)), mc[name], color=col_, lw=2, label=name)
ax.set_xticks(range(len(mc)), [ym[2:] if ym.endswith(("01", "07")) else "" for ym in mc.index])
ax.yaxis.set_major_formatter(GBP)
ax.legend(loc="upper left", ncol=2)
ax.set_title("Monthly revenue by channel")
ax = fig.add_axes([0.04, 0.07, 0.42, 0.29])
tp = y25.groupby("StoreName")["NetSales"].sum().sort_values().tail(10)
ax.barh(tp.index, tp.values, color=BLUE, height=0.6)
ax.xaxis.set_major_formatter(GBP)
ax.set_title("Top 10 physical stores by revenue (2025)")
ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8)
ax = fig.add_axes([0.56, 0.07, 0.41, 0.29])
ax.set_axis_off()
ax.set_title("Top products (table visual with conditional formatting)")
tpp = y25.merge(dp[["ProductKey", "ProductName"]], on="ProductKey").groupby("ProductName").agg(
    rev=("NetSales", "sum"), gp=("GrossProfit", "sum")).sort_values("rev", ascending=False).head(8)
rows = [[n[:42], f"£{r / 1e3:,.0f}K", f"{g / r:.0%}"] for n, (r, g) in zip(tpp.index, tpp.values)]
tb = ax.table(cellText=rows, colLabels=["Product", "Revenue", "Margin"], loc="upper left", cellLoc="left",
              colWidths=[0.7, 0.15, 0.15])
tb.auto_set_font_size(False)
tb.set_fontsize(8.5)
for (r_, c_), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    if r_ == 0:
        cell.set_text_props(fontweight="bold")
save(fig, "mockup_page2_sales_performance.png")

# Page 3 - Profitability
fig = page("Profitability", "Margin, discount cost and low-margin products")
disc25 = y25.DiscountAmount.sum()
tiles(fig, [("Gross margin", f"{k25['margin']:.1%}", delta(k24["margin"], k25["margin"], True)),
            ("Discount given", f"£{disc25 / 1e3:,.0f}K", delta(y24.DiscountAmount.sum(), disc25)),
            ("Discount rate", f"{d25:.1%}", f"{(d25 - d24) * 100:+.1f} pts vs LY"),
            ("Profit lost below cost", f"£{-y25.loc[y25.GrossProfit < 0, 'GrossProfit'].sum() / 1e3:,.0f}K", "lines sold under cost")])
ax = fig.add_axes([0.04, 0.45, 0.42, 0.33])
bb = y25.groupby(pd.cut(y25.DiscountPct, [-0.01, 0, 0.15, 0.25, 0.35, 1], labels=["None", "5-15%", "20-25%", "30-35%", "40%+"]),
                 observed=True).agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
ax.bar(bb.index.astype(str), bb.gp / bb.rev, color=[BLUE, BLUE, BLUE, ORANGE, ORANGE], width=0.6)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Margin by discount band (2025)")
ax.grid(axis="x", visible=False)
ax = fig.add_axes([0.56, 0.45, 0.41, 0.33])
xs = y25.merge(dp[["ProductKey", "ProductName"]], on="ProductKey").groupby(["ProductName", "Category"]).agg(
    rev=("NetSales", "sum"), gp=("GrossProfit", "sum")).reset_index()
xs["m"] = xs.gp / xs.rev
ax.scatter(xs.rev, xs.m, s=12, color=[ORANGE if c_ == "Electronics" else BLUE for c_ in xs.Category], alpha=0.6)
ax.axhline(k25["margin"], color=INK2, lw=1, ls="--")
ax.xaxis.set_major_formatter(GBP)
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.scatter([], [], color=ORANGE, label="Electronics")
ax.scatter([], [], color=BLUE, label="Other categories")
ax.legend(loc="lower right")
ax.set_title("Product revenue vs margin (dashed = company margin)")
ax = fig.add_axes([0.04, 0.07, 0.42, 0.29])
sub = y25[y25.Category == "Electronics"].groupby("SubCategory").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
sub = (sub.gp / sub.rev).sort_values()
ax.barh(sub.index, sub.values, color=ORANGE, height=0.55)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Electronics margin by sub-category")
ax.grid(axis="y", visible=False)
ax = fig.add_axes([0.56, 0.07, 0.41, 0.29])
tpm = y25.groupby("TradingPeriod").agg(rev=("NetSales", "sum"), gp=("GrossProfit", "sum"))
tpm = (tpm.gp / tpm.rev).sort_values()
ax.barh(tpm.index, tpm.values, color=[ORANGE if v < 0.35 else BLUE for v in tpm.values], height=0.55)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Margin by trading period (2025)")
ax.grid(axis="y", visible=False)
save(fig, "mockup_page3_profitability.png")

# Page 4 - Customers
fig = page("Customer Analytics", "Known customers only (guest in-store sales excluded) · segments, retention, value")
kn25 = y25[y25.CustomerKey != -1]
tiles(fig, [("Active customers", f"{k25['customers']:,}", delta(k24["customers"], k25["customers"])),
            ("Revenue / customer", f"£{kn25.NetSales.sum() / k25['customers']:,.0f}", ""),
            ("Orders / customer", f"{kn25.OrderID.nunique() / k25['customers']:.1f}", ""),
            ("Guest share of in-store", f"{y25[(y25.ChannelName == 'In-Store') & (y25.CustomerKey == -1)].NetSales.sum() / y25[y25.ChannelName == 'In-Store'].NetSales.sum():.0%}", "not identifiable")])
ax = fig.add_axes([0.04, 0.45, 0.42, 0.33])
sg = kn25.groupby("Segment").agg(rev=("NetSales", "sum"), c=("CustomerKey", "nunique"), o=("OrderID", "nunique"))
sg["rpc"] = sg.rev / sg.c
ax.bar(sg.index, sg.rpc, color=BLUE, width=0.5)
for i, v in enumerate(sg.rpc):
    ax.text(i, v + 15, f"£{v:,.0f}", ha="center", fontsize=9)
ax.set_title("Revenue per customer by segment (2025)")
ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"£{v:,.0f}"))
ax.grid(axis="x", visible=False)
ax = fig.add_axes([0.56, 0.45, 0.41, 0.33])
fo = s[s.CustomerKey != -1].groupby("CustomerKey")["DateKey"].min()
s2 = s[s.CustomerKey != -1].assign(first=lambda d: d.CustomerKey.map(fo))
s2["type"] = np.where(s2.DateKey == s2["first"], "New", "Returning")
q = s2.groupby(["YearMonth", "type"])["CustomerKey"].nunique().unstack()
q = q[q.index >= "2024-04"]
ax.bar(range(len(q)), q["Returning"], color=BLUE, width=0.7, label="Returning")
ax.bar(range(len(q)), q["New"], bottom=q["Returning"], color=ORANGE, width=0.7, label="New")
ax.set_xticks(range(len(q)), [ym[2:] if ym.endswith(("01", "04", "07", "10")) else "" for ym in q.index])
ax.legend(loc="upper left")
ax.set_title("Customers per month: new vs returning (from Apr 2024)")
ax = fig.add_axes([0.04, 0.07, 0.42, 0.29])
ax.barh(g.index[::-1], g["rev_share"][::-1], color=BLUE, height=0.55)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Revenue share by RFM segment (2 years)")
ax.grid(axis="y", visible=False)
ax = fig.add_axes([0.56, 0.07, 0.41, 0.29])
ag = kn25.merge(dc[["CustomerKey", "AgeBand"]], on="CustomerKey").groupby(["AgeBand", "ChannelName"])["NetSales"].sum().unstack().fillna(0)
ag = ag.div(ag.sum(axis=1), axis=0)
left = np.zeros(len(ag))
for col_, name in zip([BLUE, ORANGE, AQUA, VIOLET], ["In-Store", "Website", "Mobile App", "Click & Collect"]):
    ax.barh(ag.index, ag[name], left=left, color=col_, height=0.6, label=name, edgecolor=SURFACE, linewidth=1)
    left += ag[name].values
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.legend(loc="lower right", ncol=4, bbox_to_anchor=(1.0, 1.0), fontsize=7.5, handlelength=1)
ax.set_title("Channel mix by age band (2025)")
ax.grid(axis="y", visible=False)
save(fig, "mockup_page4_customers.png")

# Page 5 - Returns
fig = page("Returns", "Return rate = refunds ÷ revenue · returns linked to the original sale")
r25 = fr.merge(dd[["DateKey", "Year"]], on="DateKey")
tiles(fig, [("Refunds (by return date)", f"£{r25[r25.Year == 2025].RefundAmount.sum() / 1e3:,.0f}K", ""),
            ("Return rate", f"{k25['rr']:.1%}", delta(k24["rr"], k25["rr"], True)),
            ("Online return rate", f"{y25[y25.ChannelName.isin(['Website', 'Mobile App'])].RefundAmount.sum() / y25[y25.ChannelName.isin(['Website', 'Mobile App'])].NetSales.sum():.1%}", "web + app"),
            ("Avg days to return", f"{fr.DaysToReturn.mean():.0f}", "")])
ax = fig.add_axes([0.04, 0.45, 0.42, 0.33])
ax.plot(range(len(t)), t["rr"], color=BLUE, lw=2, marker="o", ms=4)
ax.set_xticks(range(len(t)), [ym[2:] if ym.endswith(("01", "07")) else "" for ym in t.index])
ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Online clothing & footwear return rate by order month")
ax = fig.add_axes([0.56, 0.45, 0.41, 0.33])
rcat = s.groupby("Category").agg(rev=("NetSales", "sum"), ref=("RefundAmount", "sum"))
rcat = (rcat.ref / rcat.rev).sort_values()
ax.barh(rcat.index, rcat.values, color=BLUE, height=0.6)
ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
ax.set_title("Return rate by category")
ax.grid(axis="y", visible=False)
ax = fig.add_axes([0.04, 0.07, 0.42, 0.29])
rs = fr["ReturnReason"].value_counts().sort_values()
ax.barh(rs.index, rs.values, color=BLUE, height=0.6)
ax.set_title("Returns by reason (count)")
ax.grid(axis="y", visible=False)
ax = fig.add_axes([0.56, 0.07, 0.41, 0.29])
ax.set_axis_off()
ax.set_title("Highest-return products (min 40 units)")
pr = s.groupby("ProductKey").agg(u=("Quantity", "sum"), rev=("NetSales", "sum"), ref=("RefundAmount", "sum"))
pr = pr[pr.u >= 40]
pr["rr"] = pr.ref / pr.rev
pr = pr.sort_values("rr", ascending=False).head(7).join(dp.set_index("ProductKey")[["ProductName"]])
tb = ax.table(cellText=[[n[:44], f"{v:.0%}"] for n, v in zip(pr.ProductName, pr.rr)], colLabels=["Product", "Return rate"],
              loc="upper left", cellLoc="left", colWidths=[0.8, 0.2])
tb.auto_set_font_size(False)
tb.set_fontsize(8.5)
for (r_, c_), cell in tb.get_celld().items():
    cell.set_edgecolor(GRID)
    if r_ == 0:
        cell.set_text_props(fontweight="bold")
save(fig, "mockup_page5_returns.png")
