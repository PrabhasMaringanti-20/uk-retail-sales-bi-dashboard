"""
Phase 4b - Validate, clean and model the raw extracts into a star schema.

Input : data/raw/*.csv            (messy source extracts)
Output: data/clean/*.csv          (star schema: dimensions + facts, ready for SQL and Power BI)
        data/quarantine/*.csv     (rows that failed validation and could not be safely fixed)
        data/clean/_cleaning_log.csv
        documentation/data_quality_report.md

Principles
  1. Never silently change data: every rule has an ID, and every fix is counted in the log.
  2. Fix only what can be fixed with certainty (formats, casing, known codes).
  3. Quarantine what cannot be fixed (impossible dates, orphans), never guess.
  4. Distinguish *legitimate* blanks (guest shoppers) from *errors*.

Run:  python scripts/03_clean_data.py
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
CLEAN = ROOT / "data" / "clean"
QUAR = ROOT / "data" / "quarantine"
DOCS = ROOT / "documentation"
for p in (CLEAN, QUAR, DOCS):
    p.mkdir(parents=True, exist_ok=True)

WINDOW_START, WINDOW_END = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31 23:59:59")
UK_POSTCODE = re.compile(r"^[A-Z]{1,2}[0-9][A-Z0-9]? [0-9][A-Z]{2}$")
CANON_CATEGORIES = ["Clothing", "Footwear", "Home & Kitchen", "Electronics", "Beauty",
                    "Toys & Games", "Sports & Outdoors", "Accessories"]
CANON_CHANNELS = ["In-Store", "Website", "Mobile App", "Click & Collect"]
CANON_REASONS = ["Wrong size / fit", "Faulty / defective", "Damaged / defective item", "Not as described",
                 "Changed mind", "Arrived late"]

log: list[dict] = []


def record(rule: str, table: str, action: str, rows: int) -> None:
    log.append({"RuleID": rule, "Table": table, "Action": action, "RowsAffected": int(rows)})


def quarantine(df: pd.DataFrame, mask: pd.Series, table: str, rule: str, reason: str) -> pd.DataFrame:
    bad = df[mask].copy()
    bad["QuarantineRule"] = rule
    bad["QuarantineReason"] = reason
    path = QUAR / f"{table}_quarantine.csv"
    bad.to_csv(path, mode="a", header=not path.exists(), index=False)
    record(rule, table, f"Quarantined: {reason}", mask.sum())
    return df[~mask].copy()


for f in QUAR.glob("*.csv"):
    f.unlink()

raw = {n: pd.read_csv(RAW / f"{n}.csv", dtype=str, keep_default_na=False, na_values=[""])
       for n in ["customers", "products", "stores", "regions", "sales_transactions", "returns"]}

# ===========================================================================
# Data-quality measurement (run on raw *and* clean data for a before/after view)
# ===========================================================================


def parse_dt(s: pd.Series) -> pd.Series:
    """Parse ISO (YYYY-MM-DD[ HH:MM:SS]) and UK (DD/MM/YYYY[ HH:MM]) formats; invalid -> NaT."""
    iso = pd.to_datetime(s, format="%Y-%m-%d %H:%M:%S", errors="coerce")
    iso_d = pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
    uk = pd.to_datetime(s, format="%d/%m/%Y %H:%M", errors="coerce")
    uk_d = pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    return iso.fillna(iso_d).fillna(uk).fillna(uk_d)


def pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def measure_sales(df: pd.DataFrame, products: pd.DataFrame) -> dict:
    req = ["OrderID", "LineNo", "OrderDateTime", "SKU", "StoreCode", "Channel", "Quantity", "UnitPrice",
           "UnitCost", "DiscountPct"]
    dtv = pd.to_datetime(df["OrderDateTime"], format="ISO8601", errors="coerce") if "OrderDateTime" in df else None
    qty = pd.to_numeric(df["Quantity"], errors="coerce")
    disc = pd.to_numeric(df["DiscountPct"], errors="coerce")
    valid = (dtv.between(WINDOW_START, WINDOW_END) & qty.between(1, 20) & disc.between(0, 0.6)
             & df["Channel"].isin(CANON_CHANNELS))
    return {
        "Completeness (required fields populated)": df[req].notna().all(axis=1).mean(),
        "Validity (ISO date in window, qty 1-20, discount 0-60%, known channel)": valid.mean(),
        "Consistency (distinct channel labels; target 4)": df["Channel"].nunique(),
        "Uniqueness (rows not exact duplicates)": 1 - df.duplicated().mean(),
        "Uniqueness (OrderID+LineNo unique)": 1 - df.duplicated(["OrderID", "LineNo"]).mean(),
        "Integrity (SKU exists in product master)": df["SKU"].isin(products["SKU"]).mean(),
    }


def measure_customers(df: pd.DataFrame) -> dict:
    email = df["Email"].str.strip().str.lower()
    pc = df["Postcode"].fillna("")
    return {
        "Completeness (Postcode, Gender, DOB, City populated)":
            df[["Postcode", "Gender", "DateOfBirth", "City"]].notna().all(axis=1).mean(),
        "Validity (postcode matches UK format)": pc.str.match(UK_POSTCODE).mean(),
        "Consistency (distinct Segment labels; target 3)": df["Segment"].nunique(),
        "Consistency (distinct LoyaltyMember codes; target 2)": df["LoyaltyMember"].nunique(),
        "Uniqueness (one record per email address)": 1 - email.duplicated().mean(),
    }


def measure_products(df: pd.DataFrame) -> dict:
    return {
        "Completeness (SubCategory, UnitCost populated)": df[["SubCategory", "UnitCost"]].notna().all(axis=1).mean(),
        "Validity (ListPrice numeric)": pd.to_numeric(df["ListPrice"], errors="coerce").notna().mean(),
        "Consistency (distinct Category labels; target 8)": df["Category"].nunique(),
        "Uniqueness (SKU unique)": 1 - df.duplicated("SKU").mean(),
    }


def measure_returns(df: pd.DataFrame, sales: pd.DataFrame) -> dict:
    key = df["OrderID"] + "|" + df["LineNo"].astype(str)
    skey = set(sales["OrderID"] + "|" + sales["LineNo"].astype(str))
    return {
        "Completeness (ReturnReason populated)": df["ReturnReason"].notna().mean(),
        "Consistency (distinct reason labels; target <= 7)": df["ReturnReason"].nunique(),
        "Uniqueness (ReturnID unique)": 1 - df.duplicated("ReturnID").mean(),
        "Integrity (return links to a sales line)": key.isin(skey).mean(),
    }


before = {
    "sales_transactions": measure_sales(raw["sales_transactions"], raw["products"]),
    "customers": measure_customers(raw["customers"]),
    "products": measure_products(raw["products"]),
    "returns": measure_returns(raw["returns"], raw["sales_transactions"]),
}
row_counts_before = {k: len(v) for k, v in raw.items()}

# ===========================================================================
# REGIONS
# ===========================================================================
regions = raw["regions"].copy()
regions = regions.apply(lambda c: c.str.strip())
REGION_ALIASES = {"yorkshire & humber": "Yorkshire and the Humber", "yorkshire and humber": "Yorkshire and the Humber"}
region_by_name = {n.lower(): n for n in regions["RegionName"]}


def canon_region(x):
    if pd.isna(x):
        return x
    k = x.strip().lower()
    return REGION_ALIASES.get(k, region_by_name.get(k, x.strip()))


# ===========================================================================
# STORES
# ===========================================================================
stores = raw["stores"].copy().apply(lambda c: c.str.strip())
n = (~stores["Region"].map(canon_region).eq(stores["Region"])).sum()
stores["Region"] = stores["Region"].map(canon_region)
record("ST-01", "stores", "Region names mapped to the region reference table", n)


def format_postcode(pc):
    if pd.isna(pc):
        return pc
    s = re.sub(r"\s+", "", str(pc)).upper()
    if len(s) >= 5:
        s = s[:-3] + " " + s[-3:]
    return s


n = (stores["Postcode"] != stores["Postcode"].map(format_postcode)).sum()
stores["Postcode"] = stores["Postcode"].map(format_postcode)
record("ST-02", "stores", "Postcode upper-cased and spaced", n)

# ===========================================================================
# PRODUCTS
# ===========================================================================
prod = raw["products"].copy().apply(lambda c: c.str.strip())
n0 = len(prod)
prod = prod.drop_duplicates()
record("PR-01", "products", "Exact duplicate rows removed", n0 - len(prod))
assert prod["SKU"].is_unique, "SKU still duplicated after removing exact duplicates"

CATEGORY_MAP = {c.lower(): c for c in CANON_CATEGORIES}
CATEGORY_MAP.update({"electronic": "Electronics", "home and kitchen": "Home & Kitchen", "clothes": "Clothing",
                     "toys and games": "Toys & Games", "sports and outdoors": "Sports & Outdoors",
                     "sport & outdoors": "Sports & Outdoors", "shoes": "Footwear", "accessory": "Accessories"})
mapped = prod["Category"].str.lower().map(CATEGORY_MAP)
record("PR-02", "products", "Category standardised via mapping table", (mapped != prod["Category"]).sum())
unmapped = prod.loc[mapped.isna(), "Category"].unique()
assert len(unmapped) == 0, f"Unmapped categories: {unmapped}"
prod["Category"] = mapped

n = prod["SubCategory"].isna().sum()
prod["SubCategory"] = prod["SubCategory"].fillna("Unclassified")
record("PR-03", "products", "Missing SubCategory set to 'Unclassified' (not guessed; flagged for merchandising)", n)

n = prod["ListPrice"].str.contains("£", na=False).sum()
prod["ListPrice"] = pd.to_numeric(prod["ListPrice"].str.replace("£", "", regex=False))
record("PR-04", "products", "ListPrice '£' symbol removed and converted to number", n)

# Missing master cost: take the cost recorded on the product's own 2024 sales lines
# (the master holds the *original* cost, so 2024 transactions are the right reference)
s_raw = raw["sales_transactions"].assign(UnitCost=lambda d: pd.to_numeric(d["UnitCost"], errors="coerce"),
                                         Yr=lambda d: parse_dt(d["OrderDateTime"]).dt.year)
cost_2024 = s_raw[s_raw["Yr"] == 2024].groupby("SKU")["UnitCost"].median()
cost_2025 = s_raw[s_raw["Yr"] == 2025].groupby("SKU")["UnitCost"].median()
prod["UnitCost"] = pd.to_numeric(prod["UnitCost"])
missing_cost = prod["UnitCost"].isna()
from_2024 = missing_cost & prod["SKU"].isin(cost_2024.index)
prod.loc[from_2024, "UnitCost"] = prod.loc[from_2024, "SKU"].map(cost_2024)
record("PR-05", "products", "Missing UnitCost filled from median 2024 transaction cost for the SKU", from_2024.sum())
# Products launched in 2025 only have 2025 costs: back out the 2025 supplier increase measured on other SKUs
both = cost_2024.index.intersection(cost_2025.index)
cost_uplift = float((cost_2025[both] / cost_2024[both]).median())
from_2025 = prod["UnitCost"].isna() & prod["SKU"].isin(cost_2025.index)
prod.loc[from_2025, "UnitCost"] = (prod.loc[from_2025, "SKU"].map(cost_2025) / cost_uplift).round(2)
record("PR-06", "products", f"Missing UnitCost (2025-only SKU) = 2025 cost / measured uplift {cost_uplift:.3f}",
       from_2025.sum())
# No sales at all: use the category's median cost-to-price ratio
ratio = (prod["UnitCost"] / prod["ListPrice"]).groupby(prod["Category"]).median()
from_cat = prod["UnitCost"].isna()
prod.loc[from_cat, "UnitCost"] = (prod.loc[from_cat, "ListPrice"] * prod.loc[from_cat, "Category"].map(ratio)).round(2)
record("PR-07", "products", "Missing UnitCost (never sold) estimated from category median cost ratio", from_cat.sum())
assert prod["UnitCost"].notna().all()

# ===========================================================================
# CUSTOMERS
# ===========================================================================
cust = raw["customers"].copy().apply(lambda c: c.str.strip())

seg = cust["Segment"].str.title()
record("CU-01", "customers", "Segment standardised to Title Case", (seg != cust["Segment"]).sum())
cust["Segment"] = seg

loy = cust["LoyaltyMember"].replace({"Yes": "Y", "No": "N"})
record("CU-02", "customers", "LoyaltyMember Yes/No recoded to Y/N", (loy != cust["LoyaltyMember"]).sum())
cust["LoyaltyMember"] = loy

g = cust["Gender"].replace({"F": "Female", "M": "Male"})
record("CU-03", "customers", "Gender F/M recoded to Female/Male", (g != cust["Gender"]).sum() - cust["Gender"].isna().sum())
record("CU-04", "customers", "Missing Gender set to 'Unknown'", g.isna().sum())
cust["Gender"] = g.fillna("Unknown")

pc = cust["Postcode"].map(format_postcode)
record("CU-05", "customers", "Postcode upper-cased and spaced",
       ((pc != cust["Postcode"]) & cust["Postcode"].notna()).sum())
valid_pc = pc.fillna("").str.match(UK_POSTCODE)
record("CU-06", "customers", "Invalid postcode set to blank and flagged (PostcodeValid = N)",
       (~valid_pc & pc.notna()).sum())
cust["Postcode"] = pc.where(valid_pc)
cust["PostcodeValid"] = np.where(valid_pc, "Y", "N")

# City: canonical spelling from the most common spelling (case-insensitive);
# if missing, infer from the postcode district where that mapping is unambiguous
city_key = cust["City"].str.lower()
canon_city = (cust.dropna(subset=["City"]).assign(k=city_key.dropna())
              .groupby("k")["City"].agg(lambda s: s.value_counts().index[0]))
new_city = city_key.map(canon_city)
record("CU-07", "customers", "City casing/whitespace standardised",
       ((new_city != cust["City"]) & cust["City"].notna()).sum())
cust["City"] = new_city
district = cust["Postcode"].str.split(" ").str[0]
d2c = (pd.DataFrame({"d": district, "c": cust["City"]}).dropna().groupby("d")["c"]
       .agg(lambda s: s.mode().iloc[0] if s.nunique() == 1 else np.nan))
infer = cust["City"].isna() & district.map(d2c).notna()
cust.loc[infer, "City"] = district[infer].map(d2c)
record("CU-08", "customers", "Missing City inferred from postcode district", infer.sum())
record("CU-09", "customers", "Missing City (no valid postcode) set to 'Unknown'", cust["City"].isna().sum())
cust["City"] = cust["City"].fillna("Unknown")

dob = parse_dt(cust["DateOfBirth"])
age = (pd.Timestamp("2025-12-31") - dob).dt.days / 365.25
bad_dob = cust["DateOfBirth"].notna() & (dob.isna() | (age < 16) | (age > 100))
record("CU-10", "customers", "DateOfBirth DD/MM/YYYY parsed to a date",
       (cust["DateOfBirth"].str.contains("/", na=False) & ~bad_dob).sum())
record("CU-11", "customers", "Impossible DateOfBirth (unparseable, age <16 or >100) set to blank", bad_dob.sum())
dob[bad_dob] = pd.NaT
cust["DateOfBirth"] = dob
cust["SignupDate"] = pd.to_datetime(cust["SignupDate"])

# Duplicate customers: same normalised email -> keep the earliest registration as master
cust["EmailNorm"] = cust["Email"].str.strip().str.lower()
cust = cust.sort_values(["EmailNorm", "SignupDate", "CustomerID"])
cust["MasterID"] = cust.groupby("EmailNorm")["CustomerID"].transform("first")
dupes = cust[cust["CustomerID"] != cust["MasterID"]]
id_map = dict(zip(dupes["CustomerID"], dupes["MasterID"]))
# Fill gaps in the master record from the duplicate where the master is blank
for col in ["Postcode", "City", "DateOfBirth", "Gender"]:
    donor = dupes.set_index("MasterID")[col]
    donor = donor[~donor.index.duplicated()]
    mrows = cust["CustomerID"].isin(donor.index)
    blank = mrows & (cust[col].isna() | cust[col].eq("Unknown"))
    cust.loc[blank, col] = cust.loc[blank, "CustomerID"].map(donor)
merged_counts = dupes.groupby("MasterID").size()
cust = cust[cust["CustomerID"] == cust["MasterID"]].copy()
cust["MergedRecords"] = cust["CustomerID"].map(merged_counts).fillna(0).astype(int)
record("CU-12", "customers", "Duplicate customers merged into earliest record (matched on normalised email)", len(dupes))

# ===========================================================================
# SALES
# ===========================================================================
s = raw["sales_transactions"].copy().apply(lambda c: c.str.strip())
n0 = len(s)
s = s.drop_duplicates()
record("SA-01", "sales_transactions", "Exact duplicate rows removed (double-loaded batch)", n0 - len(s))

CHANNEL_MAP = {"in-store": "In-Store", "instore": "In-Store", "store": "In-Store", "in store": "In-Store",
               "website": "Website", "web": "Website", "mobile app": "Mobile App", "app": "Mobile App",
               "click & collect": "Click & Collect", "click and collect": "Click & Collect", "c&c": "Click & Collect"}
ch = s["Channel"].str.lower().map(CHANNEL_MAP)
assert ch.notna().all(), s.loc[ch.isna(), "Channel"].unique()
record("SA-02", "sales_transactions", "Channel labels mapped to 4 standard channels", (ch != s["Channel"]).sum())
s["Channel"] = ch

dtp = parse_dt(s["OrderDateTime"])
record("SA-03", "sales_transactions", "UK-format OrderDateTime parsed",
       (s["OrderDateTime"].str.contains("/") & dtp.notna()).sum())
s["OrderDateTime"] = dtp
s = quarantine(s, s["OrderDateTime"].isna(), "sales_transactions", "SA-04", "Impossible/unparseable order date")
s = quarantine(s, ~s["OrderDateTime"].between(WINDOW_START, WINDOW_END), "sales_transactions", "SA-05",
               "Order date outside reporting window")

s["Quantity"] = pd.to_numeric(s["Quantity"])
s = quarantine(s, s["Quantity"] <= 0, "sales_transactions", "SA-06",
               "Negative/zero quantity (refund keyed as sale; returns live in returns table)")
s = quarantine(s, s["Quantity"] > 20, "sales_transactions", "SA-07", "Quantity outlier > 20 units")
s = quarantine(s, ~s["SKU"].isin(prod["SKU"]), "sales_transactions", "SA-08", "SKU not in product master")

s["DiscountPct"] = pd.to_numeric(s["DiscountPct"])
fix = s["DiscountPct"] > 1
s.loc[fix, "DiscountPct"] = s.loc[fix, "DiscountPct"] / 100
record("SA-09", "sales_transactions", "DiscountPct entered as whole number divided by 100", fix.sum())
assert s["DiscountPct"].between(0, 0.6).all()

s["UnitPrice"] = pd.to_numeric(s["UnitPrice"])
s["UnitCost"] = pd.to_numeric(s["UnitCost"])
s["Year"] = s["OrderDateTime"].dt.year
miss = s["UnitPrice"].isna()
ref_price = s.groupby(["SKU", "Year"])["UnitPrice"].median()
s.loc[miss, "UnitPrice"] = [ref_price.get((k, y), np.nan) for k, y in zip(s.loc[miss, "SKU"], s.loc[miss, "Year"])]
still = s["UnitPrice"].isna()
lp = prod.set_index("SKU")["ListPrice"]
s.loc[still, "UnitPrice"] = (s.loc[still, "SKU"].map(lp) * np.where(s.loc[still, "Year"] == 2025, 1.03, 1.0)).round(2)
s["IsPriceImputed"] = np.where(miss, "Y", "N")
record("SA-10", "sales_transactions", "Missing UnitPrice imputed from same SKU's price in the same year "
       "(list price fallback) and flagged IsPriceImputed = Y", miss.sum())

s["CustomerID"] = s["CustomerID"].replace(id_map)
record("SA-11", "sales_transactions", "CustomerID re-pointed from duplicate to master customer",
       raw["sales_transactions"]["CustomerID"].isin(id_map.keys()).sum())
record("SA-12", "sales_transactions", "Blank CustomerID kept as Guest (-1): legitimate in-store anonymous sale",
       s["CustomerID"].isna().sum())
assert s["CustomerID"].dropna().isin(cust["CustomerID"]).all()
assert s["StoreCode"].isin(stores["StoreCode"]).all()
assert not s.duplicated(["OrderID", "LineNo"]).any()

# ===========================================================================
# RETURNS
# ===========================================================================
r = raw["returns"].copy().apply(lambda c: c.str.strip())
n0 = len(r)
r = r.drop_duplicates()
record("RE-01", "returns", "Exact duplicate rows removed", n0 - len(r))
r["LineNo"] = r["LineNo"].astype(str)
s["LineNo"] = s["LineNo"].astype(str)
line = s[["OrderID", "LineNo", "OrderDateTime", "Quantity", "UnitPrice", "DiscountPct"]]
r = r.merge(line, on=["OrderID", "LineNo"], how="left", validate="m:1")
r = quarantine(r, r["OrderDateTime"].isna(), "returns", "RE-02",
               "No matching (valid) sales line - orphan return")
r["ReturnDate"] = pd.to_datetime(r["ReturnDate"])
r = quarantine(r, r["ReturnDate"] < r["OrderDateTime"].dt.normalize(), "returns", "RE-03",
               "Return date before order date")
r["ReturnQty"] = pd.to_numeric(r["ReturnQty"])
over = r["ReturnQty"] > r["Quantity"]
r.loc[over, "ReturnQty"] = r.loc[over, "Quantity"]
record("RE-04", "returns", "ReturnQty capped at quantity sold", over.sum())
r["RefundAmount"] = pd.to_numeric(r["RefundAmount"])
max_refund = (r["Quantity"] * r["UnitPrice"] * (1 - r["DiscountPct"])).round(2)
assert (r["RefundAmount"] <= max_refund + 0.02).all(), "Refund larger than the amount paid"  # 1p rounding tolerance

REASON_MAP = {re.sub(r"\s*/\s*", "/", x.lower()): x for x in CANON_REASONS}
reason_new = r["ReturnReason"].str.lower().str.replace(r"\s*/\s*", "/", regex=True).map(REASON_MAP)
record("RE-05", "returns", "ReturnReason casing/format standardised",
       ((reason_new != r["ReturnReason"]) & r["ReturnReason"].notna()).sum())
record("RE-06", "returns", "Missing ReturnReason set to 'Not stated'", r["ReturnReason"].isna().sum())
r["ReturnReason"] = reason_new.fillna("Not stated")

# Some duplicates differ only in formatting, so they only become identical after standardising
n0 = len(r)
r = r.sort_values("ReturnID", kind="stable").drop_duplicates("ReturnID", keep="first")
record("RE-07", "returns", "Duplicate ReturnID removed after standardisation (kept first)", n0 - len(r))

# ===========================================================================
# BUILD THE STAR SCHEMA
# ===========================================================================
# DimRegion
dim_region = regions.reset_index(drop=True)
dim_region.insert(0, "RegionKey", range(1, len(dim_region) + 1))
region_key = dict(zip(dim_region["RegionName"], dim_region["RegionKey"]))

# DimChannel
dim_channel = pd.DataFrame({
    "ChannelKey": [1, 2, 3, 4],
    "ChannelName": CANON_CHANNELS,
    "ChannelType": ["Physical", "Digital", "Digital", "Hybrid"],
    "Description": ["Purchased and paid at a store till", "Ordered on northstar website, home delivery",
                    "Ordered in the NorthStar app, home delivery", "Ordered online, collected from a store"],
})
channel_key = dict(zip(dim_channel["ChannelName"], dim_channel["ChannelKey"]))

# DimStore
dim_store = stores.sort_values("StoreCode").reset_index(drop=True)
dim_store.insert(0, "StoreKey", range(1, len(dim_store) + 1))
dim_store = dim_store.rename(columns={"Region": "StoreRegion"})
dim_store["SizeSqFt"] = pd.to_numeric(dim_store["SizeSqFt"])
dim_store["OpenDate"] = pd.to_datetime(dim_store["OpenDate"])
dim_store["IsOnline"] = np.where(dim_store["StoreType"].eq("Online"), "Y", "N")
dim_store["IsLikeForLike"] = np.where(dim_store["OpenDate"] < pd.Timestamp("2024-01-01"), "Y", "N")
store_key = dict(zip(dim_store["StoreCode"], dim_store["StoreKey"]))
store_region = dict(zip(dim_store["StoreCode"], dim_store["StoreRegion"]))

# DimProduct
dim_product = prod.sort_values("SKU").reset_index(drop=True)
dim_product.insert(0, "ProductKey", range(1, len(dim_product) + 1))
dim_product["StandardMarginPct"] = ((dim_product["ListPrice"] - dim_product["UnitCost"]) / dim_product["ListPrice"]).round(4)
dim_product["PriceBand"] = pd.cut(dim_product["ListPrice"], [0, 15, 40, 100, 10_000],
                                  labels=["Under £15", "£15-£40", "£40-£100", "Over £100"]).astype(str)
dim_product["LaunchDate"] = pd.to_datetime(dim_product["LaunchDate"])
product_key = dict(zip(dim_product["SKU"], dim_product["ProductKey"]))

# DimCustomer (GDPR data minimisation: names, email, full DOB and full postcode are NOT carried into the model)
first_purchase = s.dropna(subset=["CustomerID"]).groupby("CustomerID")["OrderDateTime"].min()
c = cust.sort_values("CustomerID").reset_index(drop=True)
age = ((pd.Timestamp("2025-12-31") - c["DateOfBirth"]).dt.days / 365.25)
c["AgeBand"] = pd.cut(age, [0, 24, 34, 44, 54, 64, 120],
                      labels=["16-24", "25-34", "35-44", "45-54", "55-64", "65+"]).astype("string").fillna("Unknown")
c["PostcodeDistrict"] = c["Postcode"].str.split(" ").str[0].fillna("Unknown")
c["CustomerRegion"] = c["Region"].map(canon_region)
c["FirstPurchaseDate"] = c["CustomerID"].map(first_purchase).dt.normalize()
dim_customer = pd.DataFrame({
    "CustomerKey": range(1, len(c) + 1),
    "CustomerID": c["CustomerID"],
    "Gender": c["Gender"],
    "AgeBand": c["AgeBand"],
    "City": c["City"],
    "PostcodeDistrict": c["PostcodeDistrict"],
    "PostcodeValid": c["PostcodeValid"],
    "CustomerRegion": c["CustomerRegion"],
    "Segment": c["Segment"],
    "LoyaltyMember": c["LoyaltyMember"],
    "SignupDate": c["SignupDate"].dt.date,
    "FirstPurchaseDate": c["FirstPurchaseDate"].dt.date,
    "IsGuest": "N",
    "MergedRecords": c["MergedRecords"],
})
guest = pd.DataFrame([{"CustomerKey": -1, "CustomerID": "GUEST", "Gender": "Unknown", "AgeBand": "Unknown",
                       "City": "Unknown", "PostcodeDistrict": "Unknown", "PostcodeValid": "N",
                       "CustomerRegion": "Unknown", "Segment": "Guest", "LoyaltyMember": "N",
                       "SignupDate": None, "FirstPurchaseDate": None, "IsGuest": "Y", "MergedRecords": 0}])
dim_customer = pd.concat([guest, dim_customer], ignore_index=True)
customer_key = dict(zip(dim_customer["CustomerID"], dim_customer["CustomerKey"]))
customer_region = dict(zip(c["CustomerID"], c["CustomerRegion"]))

# DimDate - one row per day, full calendar years (required by Power BI time intelligence)
dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
UK_BANK_HOLIDAYS = pd.to_datetime([  # England & Wales
    "2024-01-01", "2024-03-29", "2024-04-01", "2024-05-06", "2024-05-27", "2024-08-26", "2024-12-25", "2024-12-26",
    "2025-01-01", "2025-04-18", "2025-04-21", "2025-05-05", "2025-05-26", "2025-08-25", "2025-12-25", "2025-12-26"])


def black_friday(y: int) -> pd.Timestamp:
    nov30 = pd.Timestamp(y, 11, 30)
    return nov30 - pd.Timedelta(days=(nov30.weekday() - 4) % 7)


def trading_period(d: pd.Timestamp) -> str:
    bf = black_friday(d.year)
    if bf - pd.Timedelta(days=6) <= d <= bf + pd.Timedelta(days=3):
        return "Black Friday Week"
    if d.month == 1:
        return "January Sale"
    if (d.month == 6 and d.day >= 20) or d.month == 7:
        return "Summer Sale"
    if d.month == 12 and d.day >= 26:
        return "Boxing Day Sale"
    if d.month == 12 or (d.month == 11 and d > bf + pd.Timedelta(days=3)):
        return "Christmas Trading"
    return "Regular Trading"


iso = dates.isocalendar()
dim_date = pd.DataFrame({
    "DateKey": dates.strftime("%Y%m%d").astype(int),
    "Date": dates.date,
    "Year": dates.year,
    "Quarter": "Q" + dates.quarter.astype(str),
    "QuarterNumber": dates.quarter,
    "YearQuarter": dates.year.astype(str) + "-Q" + dates.quarter.astype(str),
    "MonthNumber": dates.month,
    "MonthName": dates.strftime("%B"),
    "MonthShort": dates.strftime("%b"),
    "YearMonth": dates.strftime("%Y-%m"),
    "YearMonthKey": (dates.year * 100 + dates.month),
    "ISOWeek": iso.week.to_numpy(),
    "DayOfMonth": dates.day,
    "DayOfWeekNumber": dates.dayofweek + 1,
    "DayName": dates.strftime("%A"),
    "IsWeekend": np.where(dates.dayofweek >= 5, "Y", "N"),
    "IsUKBankHoliday": np.where(dates.isin(UK_BANK_HOLIDAYS), "Y", "N"),
    "UKFinancialYear": [f"FY{y}/{str(y + 1)[2:]}" if m >= 4 else f"FY{y - 1}/{str(y)[2:]}"
                        for y, m in zip(dates.year, dates.month)],
    "TradingPeriod": [trading_period(d) for d in dates],
})

# FactSales - grain: one row per order line
s = s.sort_values(["OrderDateTime", "OrderID", "LineNo"]).reset_index(drop=True)
fs = pd.DataFrame({"SalesLineKey": range(1, len(s) + 1)})
fs["OrderID"] = s["OrderID"]
fs["OrderLineNumber"] = s["LineNo"].astype(int)
fs["DateKey"] = s["OrderDateTime"].dt.strftime("%Y%m%d").astype(int)
fs["OrderDateTime"] = s["OrderDateTime"]
fs["CustomerKey"] = s["CustomerID"].map(customer_key).fillna(-1).astype(int)
fs["ProductKey"] = s["SKU"].map(product_key)
fs["StoreKey"] = s["StoreCode"].map(store_key)
fs["ChannelKey"] = s["Channel"].map(channel_key)
# Sales region: store region for physical/C&C sales, customer's home region for delivered online orders
reg_name = np.where(s["StoreCode"].eq("ST99"), s["CustomerID"].map(customer_region), s["StoreCode"].map(store_region))
fs["RegionKey"] = pd.Series(reg_name).map(region_key)
fs["Quantity"] = s["Quantity"].astype(int)
fs["UnitPrice"] = s["UnitPrice"].round(2)
fs["UnitCost"] = s["UnitCost"].round(2)
fs["DiscountPct"] = s["DiscountPct"].round(4)
fs["GrossSales"] = (fs["Quantity"] * fs["UnitPrice"]).round(2)
fs["DiscountAmount"] = (fs["GrossSales"] * fs["DiscountPct"]).round(2)
fs["NetSales"] = (fs["GrossSales"] - fs["DiscountAmount"]).round(2)
fs["CostAmount"] = (fs["Quantity"] * fs["UnitCost"]).round(2)
fs["GrossProfit"] = (fs["NetSales"] - fs["CostAmount"]).round(2)
fs["PaymentMethod"] = s["PaymentMethod"]
fs["IsPriceImputed"] = s["IsPriceImputed"]
assert fs[["ProductKey", "StoreKey", "ChannelKey", "RegionKey"]].notna().all().all()

# FactReturns - grain: one row per returned order line
line_key = fs.set_index(["OrderID", "OrderLineNumber"])
r["LineNo"] = r["LineNo"].astype(int)
r = r.sort_values(["ReturnDate", "ReturnID"]).reset_index(drop=True)
lk = line_key.loc[list(zip(r["OrderID"], r["LineNo"]))].reset_index()
fr = pd.DataFrame({
    "ReturnKey": range(1, len(r) + 1),
    "ReturnID": r["ReturnID"],
    "SalesLineKey": lk["SalesLineKey"],
    "OrderID": r["OrderID"],
    "OrderLineNumber": r["LineNo"],
    "DateKey": r["ReturnDate"].dt.strftime("%Y%m%d").astype(int),
    "OrderDateKey": lk["DateKey"],
    "CustomerKey": lk["CustomerKey"],
    "ProductKey": lk["ProductKey"],
    "StoreKey": lk["StoreKey"],
    "ChannelKey": lk["ChannelKey"],
    "RegionKey": lk["RegionKey"],
    "ReturnQty": r["ReturnQty"].astype(int),
    "RefundAmount": r["RefundAmount"].round(2),
    "ReturnReason": r["ReturnReason"],
    "ReturnMethod": r["ReturnMethod"],
    "DaysToReturn": (r["ReturnDate"] - r["OrderDateTime"].dt.normalize()).dt.days,
})

# ---------------------------------------------------------------------------
# Write outputs
# ---------------------------------------------------------------------------
outputs = {"dim_date": dim_date, "dim_customer": dim_customer, "dim_product": dim_product,
           "dim_store": dim_store, "dim_region": dim_region, "dim_channel": dim_channel,
           "fact_sales": fs, "fact_returns": fr}
for name, df in outputs.items():
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            fmt = "%Y-%m-%d %H:%M:%S" if col == "OrderDateTime" else "%Y-%m-%d"
            out[col] = out[col].dt.strftime(fmt)
    out.to_csv(CLEAN / f"{name}.csv", index=False)
pd.DataFrame(log).to_csv(CLEAN / "_cleaning_log.csv", index=False)

# ===========================================================================
# AFTER metrics + accuracy check against the generator's answer key
# ===========================================================================
s_after = fs.assign(OrderDateTime=fs["OrderDateTime"].dt.strftime("%Y-%m-%d %H:%M:%S"),
                    LineNo=fs["OrderLineNumber"], SKU=fs["ProductKey"].map(dict(zip(dim_product["ProductKey"], dim_product["SKU"]))),
                    StoreCode=fs["StoreKey"].map(dict(zip(dim_store["StoreKey"], dim_store["StoreCode"]))),
                    Channel=fs["ChannelKey"].map(dict(zip(dim_channel["ChannelKey"], dim_channel["ChannelName"]))))
cust_after = cust.assign(Postcode=cust["Postcode"].fillna("MISSING"))
after = {
    "sales_transactions": measure_sales(s_after, dim_product),
    "customers": measure_customers(cust.assign(Postcode=cust["Postcode"].where(cust["PostcodeValid"].eq("Y"), "VALID-BLANK")
                                               .replace("VALID-BLANK", np.nan), Gender=cust["Gender"],
                                               DateOfBirth=cust["DateOfBirth"])),
    "products": measure_products(dim_product),
    "returns": measure_returns(r.assign(LineNo=r["LineNo"].astype(str)), s.assign(LineNo=s["LineNo"].astype(str))),
}

accuracy_lines = []
truth_dir = ROOT / "data" / "_truth"
if truth_dir.exists():
    t = pd.read_csv(truth_dir / "sales_transactions.csv", keep_default_na=False)
    t["NetSales"] = (t["Quantity"] * t["UnitPrice"] * (1 - t["DiscountPct"])).round(2)
    t["key"] = t["OrderID"] + "|" + t["LineNo"].astype(str)
    fs_key = fs["OrderID"] + "|" + fs["OrderLineNumber"].astype(str)
    cmp = pd.DataFrame({"key": fs_key, "NetSales": fs["NetSales"]}).merge(t[["key", "NetSales"]], on="key",
                                                                         suffixes=("", "_truth"))
    exact = (cmp["NetSales"] - cmp["NetSales_truth"]).abs() < 0.02
    accuracy_lines = [
        f"| Sales lines in answer key | {len(t):,} |",
        f"| Sales lines after cleaning | {len(fs):,} |",
        f"| Lines quarantined (could not be trusted) | {len(t) - len(fs):,} ({(len(t) - len(fs)) / len(t):.3%}) |",
        f"| Cleaned lines whose NetSales exactly matches the answer key | {exact.mean():.3%} |",
        f"| Revenue after cleaning vs answer key | £{fs['NetSales'].sum():,.2f} vs £{t['NetSales'].sum():,.2f} "
        f"({fs['NetSales'].sum() / t['NetSales'].sum() - 1:+.3%}) |",
    ]
    tc = pd.read_csv(truth_dir / "customers.csv")
    accuracy_lines.append(f"| Customers in answer key vs after de-duplication | {len(tc):,} vs {len(cust):,} |")

# ---------------------------------------------------------------------------
# Data-quality report (markdown)
# ---------------------------------------------------------------------------


def fmt(v):
    return pct(v) if isinstance(v, float) else f"{v}"


lines_md = [
    "# Data Quality Report — NorthStar Retail UK (simulated)",
    "",
    "_Generated by `scripts/03_clean_data.py`. Do not edit by hand; re-run the script._",
    "",
    "## 1. Row counts",
    "",
    "| Table | Raw rows | Clean rows | Quarantined |",
    "| --- | ---: | ---: | ---: |",
]
q_counts = {f.stem.replace("_quarantine", ""): len(pd.read_csv(f)) for f in QUAR.glob("*.csv")}
for raw_name, clean_name in [("sales_transactions", "fact_sales"), ("returns", "fact_returns"),
                             ("customers", "dim_customer"), ("products", "dim_product"), ("stores", "dim_store"),
                             ("regions", "dim_region")]:
    lines_md.append(f"| {raw_name} → {clean_name} | {row_counts_before[raw_name]:,} | {len(outputs[clean_name]):,} | "
                    f"{q_counts.get(raw_name, 0):,} |")
lines_md += ["", "> `dim_customer` includes one extra row: the **Guest** member (CustomerKey = -1).", "",
             "## 2. Data-quality dimensions: before vs after", ""]
for table in before:
    lines_md += [f"### {table}", "", "| Check | Before | After |", "| --- | ---: | ---: |"]
    for k in before[table]:
        lines_md.append(f"| {k} | {fmt(before[table][k])} | {fmt(after[table][k])} |")
    lines_md.append("")
lines_md += [
    "Notes",
    "- **Customer completeness stays below 100% on purpose.** Missing date of birth or an unrecoverable postcode cannot be",
    "  invented; they are left blank (AgeBand = 'Unknown', PostcodeValid = 'N') and the gap is reported.",
    "- **Validity** for sales is measured against the business rules in `documentation/validation_rules.md`.",
    "",
    "## 3. Accuracy check against the answer key",
    "",
    "Because the data is synthetic, the generator keeps an uncorrupted copy. This lets us *prove* the cleaning",
    "is correct, which you cannot normally do. In a real job you would reconcile to finance totals instead.",
    "",
    "| Measure | Result |",
    "| --- | --- |",
    *accuracy_lines,
    "",
    "## 4. Cleaning log (every rule, every row count)",
    "",
    "| Rule | Table | Action | Rows |",
    "| --- | --- | --- | ---: |",
]
for e in log:
    lines_md.append(f"| {e['RuleID']} | {e['Table']} | {e['Action']} | {e['RowsAffected']:,} |")
(DOCS / "data_quality_report.md").write_text("\n".join(lines_md) + "\n")

print("\n".join(lines_md))
