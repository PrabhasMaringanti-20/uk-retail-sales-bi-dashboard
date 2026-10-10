"""
Phase 4a - Inject controlled data-quality problems into the source extracts.

Real source systems are messy. To practise data cleaning honestly, we take the
generated extracts (data/_truth) and deliberately break them in known, counted ways,
writing the result to data/raw/. Because we know exactly what was broken, we can later
prove the cleaning step (03_clean_data.py) fixed it.

Every injected problem is listed in data/raw/_injected_issues.csv (the "answer key").

Run:  python scripts/02_inject_quality_issues.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
ROOT = Path(__file__).resolve().parents[1]
TRUTH = ROOT / "data" / "_truth"
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

cust = pd.read_csv(TRUTH / "customers.csv", dtype=str)
prod = pd.read_csv(TRUTH / "products.csv", dtype=str)
stores = pd.read_csv(TRUTH / "stores.csv", dtype=str)
regions = pd.read_csv(TRUTH / "regions.csv", dtype=str)
sales = pd.read_csv(TRUTH / "sales_transactions.csv", dtype=str, keep_default_na=False)
rets = pd.read_csv(TRUTH / "returns.csv", dtype=str)

log: list[dict] = []


def note(table: str, issue: str, n: int, detail: str = "") -> None:
    log.append({"Table": table, "Issue": issue, "RowsAffected": n, "Detail": detail})


def pick(df: pd.DataFrame, n: int, mask=None) -> pd.Index:
    pool = df.index if mask is None else df.index[mask]
    return pd.Index(rng.choice(pool, size=min(n, len(pool)), replace=False))


# ---------------------------------------------------------------- customers
# 1) Duplicate customers: the same person re-registered with a new ID.
#    Email differs only by case/whitespace, name casing differs. Some sales use the new ID.
dup_src = pick(cust, 180)
dups = cust.loc[dup_src].copy()
next_id = 100000 + len(cust)
dups["CustomerID"] = [f"C{next_id + i}" for i in range(len(dups))]
dups["Email"] = [("  " + e.upper()) if i % 2 else e.title() for i, e in enumerate(dups["Email"])]
dups["FirstName"] = dups["FirstName"].str.upper()
dups["SignupDate"] = (pd.to_datetime(dups["SignupDate"]) + pd.Timedelta(days=200)).dt.strftime("%Y-%m-%d")
dup_map = dict(zip(cust.loc[dup_src, "CustomerID"], dups["CustomerID"]))
cust = pd.concat([cust, dups], ignore_index=True)
note("customers", "Duplicate customer (re-registered, new ID)", len(dups),
     "Email differs only by case/leading spaces; first name upper-cased")

# Point ~40% of the duplicated people's later sales at the duplicate ID
moved = 0
for orig, new in dup_map.items():
    m = sales.index[sales["CustomerID"] == orig]
    if len(m) > 1:
        take = m[len(m) // 2:]
        sales.loc[take, "CustomerID"] = new
        moved += len(take)
note("sales_transactions", "Sales recorded against duplicate customer ID", moved)

# 2) Missing values
for col, n in [("Postcode", 260), ("Gender", 600), ("DateOfBirth", 950), ("City", 120)]:
    idx = pick(cust, n)
    cust.loc[idx, col] = np.nan
    note("customers", f"Missing {col}", len(idx))

# 3) Invalid / badly formatted postcodes
idx = pick(cust, 150, cust["Postcode"].notna())
fixable = idx[:90]
cust.loc[fixable, "Postcode"] = cust.loc[fixable, "Postcode"].str.lower().str.replace(" ", "", regex=False)
note("customers", "Postcode badly formatted (lowercase, no space) - fixable", len(fixable))
broken = idx[90:]
cust.loc[broken, "Postcode"] = rng.choice(["XX1 1XX", "12345", "N/A", "M1", "SW1A 1", "000 000"], len(broken))
note("customers", "Postcode invalid - not recoverable", len(broken))

# 4) Inconsistent text values
idx = pick(cust, 400)
cust.loc[idx, "Segment"] = [rng.choice([s.upper(), s.lower(), s + " ", " " + s]) for s in cust.loc[idx, "Segment"]]
note("customers", "Segment inconsistent casing/whitespace", len(idx))
idx = pick(cust, 300, cust["City"].notna())
cust.loc[idx, "City"] = [rng.choice([c.lower(), c.upper(), c + "  "]) for c in cust.loc[idx, "City"]]
note("customers", "City inconsistent casing/whitespace", len(idx))
idx = pick(cust, 200)
cust.loc[idx, "LoyaltyMember"] = cust.loc[idx, "LoyaltyMember"].map({"Y": "Yes", "N": "No"})
note("customers", "LoyaltyMember coded Yes/No instead of Y/N", len(idx))
idx = pick(cust, 150)
cust.loc[idx, "Gender"] = cust.loc[idx, "Gender"].map({"Female": "F", "Male": "M"}).fillna(cust.loc[idx, "Gender"])
note("customers", "Gender coded F/M instead of Female/Male", len(idx))

# 5) Mixed date formats and impossible birth dates
idx = pick(cust, 500, cust["DateOfBirth"].notna())
cust.loc[idx, "DateOfBirth"] = pd.to_datetime(cust.loc[idx, "DateOfBirth"]).dt.strftime("%d/%m/%Y")
note("customers", "DateOfBirth in DD/MM/YYYY format", len(idx))
idx = pick(cust, 25, cust["DateOfBirth"].notna())
cust.loc[idx, "DateOfBirth"] = rng.choice(["1900-01-01", "2031-05-14", "2020-13-45"], len(idx))
note("customers", "DateOfBirth impossible (placeholder, future or invalid)", len(idx))

cust = cust.sample(frac=1, random_state=1).reset_index(drop=True)

# ---------------------------------------------------------------- products
cat_variants = {
    "Electronics": ["electronics", "ELECTRONICS", "Electronic", "Electronics "],
    "Home & Kitchen": ["Home and Kitchen", "home & kitchen", "Home & Kitchen "],
    "Clothing": ["clothing", "Clothes", "CLOTHING"],
    "Toys & Games": ["Toys and Games", "toys & games"],
    "Sports & Outdoors": ["Sports and Outdoors", "Sport & Outdoors"],
    "Beauty": ["beauty", "Beauty "],
    "Footwear": ["footwear", "Shoes"],
    "Accessories": ["accessories", "Accessory"],
}
idx = pick(prod, 160)
prod.loc[idx, "Category"] = [rng.choice(cat_variants[c]) for c in prod.loc[idx, "Category"]]
note("products", "Category inconsistent spelling/casing", len(idx))
idx = pick(prod, 14)
prod.loc[idx, "SubCategory"] = np.nan
note("products", "Missing SubCategory", len(idx))
idx = pick(prod, 12)
prod.loc[idx, "UnitCost"] = np.nan
note("products", "Missing UnitCost in product master", len(idx))
idx = pick(prod, 30)
prod.loc[idx, "ListPrice"] = "£" + prod.loc[idx, "ListPrice"]
note("products", "ListPrice stored as text with £ symbol", len(idx))
dupe_rows = prod.loc[pick(prod, 8)]
prod = pd.concat([prod, dupe_rows], ignore_index=True)
note("products", "Exact duplicate product rows", len(dupe_rows))

# ---------------------------------------------------------------- stores
stores.loc[stores["Region"] == "Yorkshire and the Humber", "Region"] = "Yorkshire & Humber"
note("stores", "Region name differs from region reference table", 2, "'Yorkshire & Humber'")
stores.loc[stores["StoreCode"] == "ST09", "Postcode"] = stores.loc[stores["StoreCode"] == "ST09", "Postcode"].str.lower()
note("stores", "Postcode lowercase", 1)

# ---------------------------------------------------------------- sales
n0 = len(sales)
# Channel label chaos from different source systems
ch_variants = {"In-Store": ["instore", "STORE", "In Store"], "Website": ["Web", "website", "WEB"],
               "Mobile App": ["App", "mobile app"], "Click & Collect": ["Click and Collect", "C&C"]}
idx = pick(sales, 9000)
sales.loc[idx, "Channel"] = [rng.choice(ch_variants[c]) for c in sales.loc[idx, "Channel"]]
note("sales_transactions", "Channel label variants", len(idx))

# Mixed date formats (UK style from the store till system)
idx = pick(sales, 6000, sales["Channel"].isin(["instore", "STORE", "In Store", "In-Store"]))
sales.loc[idx, "OrderDateTime"] = pd.to_datetime(sales.loc[idx, "OrderDateTime"]).dt.strftime("%d/%m/%Y %H:%M")
note("sales_transactions", "OrderDateTime in DD/MM/YYYY HH:MM format", len(idx))
# Impossible and out-of-range dates
idx = pick(sales, 22)
sales.loc[idx, "OrderDateTime"] = rng.choice(["2024-02-30 12:00:00", "2025-04-31 10:15:00", "2025-13-02 09:00:00"], len(idx))
note("sales_transactions", "OrderDateTime impossible (e.g. 30 Feb)", len(idx))
idx = pick(sales, 15)
sales.loc[idx, "OrderDateTime"] = rng.choice(["2026-03-11 14:00:00", "2027-01-05 11:30:00", "1999-12-31 23:59:00"], len(idx))
note("sales_transactions", "OrderDateTime outside the reporting window", len(idx))

# Missing unit price
idx = pick(sales, 340)
sales.loc[idx, "UnitPrice"] = ""
note("sales_transactions", "Missing UnitPrice", len(idx))
# Discount entered as whole number (20 instead of 0.20)
idx = pick(sales, 520, sales["DiscountPct"].astype(float) > 0)
sales.loc[idx, "DiscountPct"] = (sales.loc[idx, "DiscountPct"].astype(float) * 100).round().astype(int).astype(str)
note("sales_transactions", "DiscountPct entered as percentage number (20 not 0.20)", len(idx))
# Negative quantity (refund keyed as a negative sale) and absurd quantity
idx = pick(sales, 35)
sales.loc[idx, "Quantity"] = "-" + sales.loc[idx, "Quantity"]
note("sales_transactions", "Negative Quantity", len(idx))
idx = pick(sales, 6)
sales.loc[idx, "Quantity"] = rng.choice(["999", "250", "1000"], len(idx))
note("sales_transactions", "Quantity outlier (>= 250 units)", len(idx))
# Unknown SKU (orphan foreign key)
idx = pick(sales, 12)
sales.loc[idx, "SKU"] = rng.choice(["NS-XXX-99999", "TEST-SKU", "NS-ELE-0000"], len(idx))
note("sales_transactions", "SKU not found in product master", len(idx))
# Exact duplicate transaction rows (double-loaded batch)
dup_rows = sales.loc[pick(sales, 900)]
sales = pd.concat([sales, dup_rows], ignore_index=True)
note("sales_transactions", "Exact duplicate rows (double-loaded batch)", len(dup_rows))
sales = sales.sample(frac=1, random_state=3).reset_index(drop=True)

# ---------------------------------------------------------------- returns
dup_rows = rets.loc[pick(rets, 60)]
rets = pd.concat([rets, dup_rows], ignore_index=True)
note("returns", "Exact duplicate return rows", len(dup_rows))
idx = pick(rets, 400)
rets.loc[idx, "ReturnReason"] = np.nan
note("returns", "Missing ReturnReason", len(idx))
idx = pick(rets, 700, rets["ReturnReason"].notna())
rets.loc[idx, "ReturnReason"] = [rng.choice([r.upper(), r.lower(), r.replace(" / ", "/")]) for r in rets.loc[idx, "ReturnReason"]]
note("returns", "ReturnReason inconsistent casing/format", len(idx))
idx = pick(rets, 18)
rets.loc[idx, "OrderID"] = ["SO" + str(9_000_000 + i) for i in range(len(idx))]
note("returns", "Return references an order that does not exist", len(idx))
idx = pick(rets, 20, ~rets.index.isin(idx))
rets.loc[idx, "ReturnDate"] = "2023-06-01"
note("returns", "ReturnDate before the order date", len(idx))
idx = pick(rets, 10)
rets.loc[idx, "ReturnQty"] = "9"
note("returns", "ReturnQty greater than quantity sold", len(idx))

# ---------------------------------------------------------------- write
cust.to_csv(RAW / "customers.csv", index=False)
prod.to_csv(RAW / "products.csv", index=False)
stores.to_csv(RAW / "stores.csv", index=False)
regions.to_csv(RAW / "regions.csv", index=False)
sales.to_csv(RAW / "sales_transactions.csv", index=False)
rets.to_csv(RAW / "returns.csv", index=False)
pd.DataFrame(log).to_csv(RAW / "_injected_issues.csv", index=False)

print(pd.DataFrame(log).to_string(index=False))
print(f"\nsales rows {n0:,} -> {len(sales):,}")
