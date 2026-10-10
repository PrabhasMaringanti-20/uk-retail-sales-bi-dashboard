"""
Phase 3 - Synthetic data generator for NorthStar Retail UK (fictional).

Produces the *raw source extracts* in data/raw/ exactly as messy source systems
would deliver them (the data-quality problems are injected by 02_inject_quality_issues.py).

Design principle: the data is NOT purely random. Every pattern below is a deliberate,
documented business behaviour so that the analysis has something real to discover:

  * Seasonality: Q4 peak, Black Friday spike, January sale, summer for sports/sandals,
    Christmas for toys/fragrance, January fitness bump.
  * Channel shift: in-store roughly flat, website and app growing fast in 2025.
  * Margin squeeze: 2025 cost prices rise ~6% but selling prices only ~3%.
  * Discounting: sale periods + more promotions in 2025; one store (Newcastle) over-discounts;
    the outlet store discounts by design.
  * Category economics: Electronics = big revenue, thin margin; Beauty/Accessories = rich margin.
  * Returns: online >> in-store; clothing/footwear highest; one footwear brand has a 2025
    sizing problem; one electronics brand has a faulty smart-home line.
  * Customers: Pareto-like activity, segments with different price sensitivity,
    new customers acquired over time, some customers lapse, ~30% of in-store sales are guests.
  * A new store opens in July 2024 (like-for-like comparison trap).

Run:  python scripts/01_generate_data.py
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

START = dt.date(2024, 1, 1)
END = dt.date(2025, 12, 31)
DAYS = pd.date_range(START, END, freq="D")

# ---------------------------------------------------------------------------
# 1. Regions and stores
# ---------------------------------------------------------------------------
REGIONS = [
    # code, name, nation
    ("LDN", "London", "England"),
    ("SE", "South East", "England"),
    ("SW", "South West", "England"),
    ("EE", "East of England", "England"),
    ("EM", "East Midlands", "England"),
    ("WM", "West Midlands", "England"),
    ("YH", "Yorkshire and the Humber", "England"),
    ("NW", "North West", "England"),
    ("NE", "North East", "England"),
    ("WAL", "Wales", "Wales"),
    ("SCO", "Scotland", "Scotland"),
    ("NI", "Northern Ireland", "Northern Ireland"),
]
REGION_CODES = [r[0] for r in REGIONS]

# Postcode areas used to create realistic customer/store postcodes per region
POSTCODE_AREAS = {
    "LDN": [("London", ["E1", "E14", "N1", "N7", "SE1", "SE15", "SW11", "SW19", "W5", "NW3", "EC2A", "WC1E"])],
    "SE": [("Brighton", ["BN1", "BN2"]), ("Reading", ["RG1", "RG2"]), ("Oxford", ["OX1", "OX4"]), ("Guildford", ["GU1", "GU2"])],
    "SW": [("Bristol", ["BS1", "BS8"]), ("Exeter", ["EX1", "EX4"]), ("Plymouth", ["PL1", "PL4"])],
    "EE": [("Cambridge", ["CB1", "CB2"]), ("Norwich", ["NR1", "NR2"]), ("Chelmsford", ["CM1", "CM2"])],
    "EM": [("Nottingham", ["NG1", "NG7"]), ("Leicester", ["LE1", "LE2"]), ("Derby", ["DE1", "DE22"])],
    "WM": [("Birmingham", ["B1", "B15", "B29"]), ("Coventry", ["CV1", "CV4"]), ("Wolverhampton", ["WV1", "WV3"])],
    "YH": [("Leeds", ["LS1", "LS6"]), ("Sheffield", ["S1", "S10"]), ("York", ["YO1", "YO10"])],
    "NW": [("Manchester", ["M1", "M14", "M20"]), ("Liverpool", ["L1", "L17"]), ("Preston", ["PR1", "PR2"])],
    "NE": [("Newcastle upon Tyne", ["NE1", "NE6"]), ("Sunderland", ["SR1", "SR2"]), ("Durham", ["DH1"])],
    "WAL": [("Cardiff", ["CF10", "CF24"]), ("Swansea", ["SA1", "SA2"])],
    "SCO": [("Glasgow", ["G1", "G12"]), ("Edinburgh", ["EH1", "EH8"]), ("Aberdeen", ["AB10", "AB24"])],
    "NI": [("Belfast", ["BT1", "BT7", "BT9"])],
}
# Relative population weight of each region for customers
REGION_POP = {"LDN": 16, "SE": 14, "SW": 8, "EE": 9, "EM": 7, "WM": 9, "YH": 8, "NW": 11, "NE": 4, "WAL": 5, "SCO": 8, "NI": 3}

INWARD_LETTERS = "ABDEFGHJLNPQRSTUWXYZ"  # letters valid in the inward code


def make_postcode(area: str) -> str:
    return f"{area} {rng.integers(1, 10)}{rng.choice(list(INWARD_LETTERS))}{rng.choice(list(INWARD_LETTERS))}"


# StoreCode, StoreName, RegionCode, City, PostcodeArea, StoreType, SizeSqFt, OpenDate, traffic weight
STORES = [
    ("ST01", "London Oxford Street", "LDN", "London", "W1", "Flagship", 42000, "2012-03-01", 2.4),
    ("ST02", "London Stratford", "LDN", "London", "E20", "Shopping Centre", 30000, "2014-09-15", 1.8),
    ("ST03", "London Croydon", "LDN", "London", "CR0", "High Street", 18000, "2010-05-01", 1.1),
    ("ST04", "London Brent Cross", "LDN", "London", "NW4", "Shopping Centre", 26000, "2016-04-20", 1.5),
    ("ST05", "Brighton Churchill Square", "SE", "Brighton", "BN1", "Shopping Centre", 20000, "2013-06-01", 1.2),
    ("ST06", "Reading Oracle", "SE", "Reading", "RG1", "Shopping Centre", 21000, "2015-02-11", 1.2),
    ("ST07", "Bluewater Outlet", "SE", "Greenhithe", "DA9", "Outlet", 16000, "2018-10-01", 1.0),
    ("ST08", "Bristol Cabot Circus", "SW", "Bristol", "BS1", "Shopping Centre", 24000, "2011-09-01", 1.3),
    ("ST09", "Exeter Princesshay", "SW", "Exeter", "EX1", "High Street", 14000, "2017-03-15", 0.75),
    ("ST10", "Cambridge Grand Arcade", "EE", "Cambridge", "CB2", "High Street", 15000, "2014-11-01", 0.9),
    ("ST11", "Norwich Chapelfield", "EE", "Norwich", "NR2", "Shopping Centre", 16000, "2012-08-20", 0.85),
    ("ST12", "Nottingham Victoria", "EM", "Nottingham", "NG1", "Shopping Centre", 19000, "2013-04-01", 1.0),
    ("ST13", "Birmingham Bullring", "WM", "Birmingham", "B5", "Flagship", 34000, "2010-10-01", 1.9),
    ("ST14", "Coventry West Orchards", "WM", "Coventry", "CV1", "High Street", 13000, "2016-07-01", 0.7),
    ("ST15", "Leeds Trinity", "YH", "Leeds", "LS1", "Shopping Centre", 22000, "2013-03-21", 1.25),
    ("ST16", "Sheffield Meadowhall", "YH", "Sheffield", "S9", "Retail Park", 25000, "2024-07-04", 1.2),  # NEW STORE
    ("ST17", "Manchester Arndale", "NW", "Manchester", "M4", "Flagship", 36000, "2011-05-01", 2.0),
    ("ST18", "Liverpool ONE", "NW", "Liverpool", "L1", "Shopping Centre", 26000, "2012-05-30", 1.5),
    ("ST19", "Preston Fishergate", "NW", "Preston", "PR1", "High Street", 12000, "2015-08-01", 0.6),
    ("ST20", "Newcastle Eldon Square", "NE", "Newcastle upon Tyne", "NE1", "Shopping Centre", 21000, "2012-09-01", 1.1),
    ("ST21", "Cardiff St David's", "WAL", "Cardiff", "CF10", "Shopping Centre", 20000, "2014-03-01", 1.05),
    ("ST22", "Glasgow Buchanan Galleries", "SCO", "Glasgow", "G1", "Flagship", 30000, "2011-11-11", 1.6),
    ("ST23", "Edinburgh St James Quarter", "SCO", "Edinburgh", "EH1", "Shopping Centre", 23000, "2021-06-24", 1.3),
    ("ST24", "Belfast Victoria Square", "NI", "Belfast", "BT1", "Shopping Centre", 18000, "2015-03-01", 0.95),
    ("ST99", "E-commerce Hub", "ONLINE", "Milton Keynes", "MK1", "Online", 0, "2010-01-01", 0.0),
]
stores = pd.DataFrame(STORES, columns=["StoreCode", "StoreName", "RegionCode", "City", "PostcodeArea",
                                       "StoreType", "SizeSqFt", "OpenDate", "Traffic"])
stores["Postcode"] = stores["PostcodeArea"].map(make_postcode)
stores["OpenDate"] = pd.to_datetime(stores["OpenDate"])
PHYSICAL = stores[stores["StoreType"] != "Online"].reset_index(drop=True)
HUB_CODE = "ST99"

# Store-level behaviour (hidden "truth" the analysis should uncover)
STORE_EXTRA_DISCOUNT_PROB = {"ST20": 0.38}   # Newcastle: manager runs constant local promotions
STORE_RETURN_FACTOR = {"ST13": 1.35}         # Birmingham Bullring: weak returns policy enforcement

# ---------------------------------------------------------------------------
# 2. Channels
# ---------------------------------------------------------------------------
CHANNELS = ["In-Store", "Website", "Mobile App", "Click & Collect"]
CH_BASE_SHARE = np.array([0.60, 0.25, 0.08, 0.07])       # share of orders, start of 2024
CH_ANNUAL_GROWTH = np.array([0.01, 0.18, 0.45, 0.15])    # orders growth per year
CH_LINES_MEAN = np.array([0.95, 1.30, 1.20, 1.05])       # extra lines per order (Poisson mean)
CH_RETURN_FACTOR = np.array([1.0, 2.3, 2.1, 1.4])

# ---------------------------------------------------------------------------
# 3. Products
# ---------------------------------------------------------------------------
# category: (subcategories, price range, cost ratio range, base return rate, brands)
CATEGORIES = {
    "Clothing": (["Womenswear", "Menswear", "Kidswear", "Outerwear"], (10, 95), (0.40, 0.50), 0.075,
                 ["Northline", "Ashford & Co", "Urban Thread", "NorthStar Essentials"]),
    "Footwear": (["Trainers", "Boots", "Formal Shoes", "Sandals"], (22, 130), (0.45, 0.55), 0.07,
                 ["Stride Lab", "Peak Step", "Ashford & Co", "NorthStar Essentials"]),
    "Home & Kitchen": (["Cookware", "Bedding", "Home Decor", "Small Appliances"], (8, 160), (0.50, 0.60), 0.035,
                       ["Hearth & Home", "Kitchenly", "Linen Lane", "NorthStar Essentials"]),
    "Electronics": (["Headphones", "Smart Home", "Phone Accessories", "Tablets & Gadgets"], (15, 420), (0.74, 0.84), 0.04,
                    ["Voltix", "Sonara", "Pixelpoint", "NorthStar Essentials"]),
    "Beauty": (["Skincare", "Fragrance", "Makeup", "Haircare"], (5, 85), (0.33, 0.43), 0.012,
               ["Glow Theory", "Maison Belle", "Pure Botanic", "NorthStar Essentials"]),
    "Toys & Games": (["Board Games", "Kids Toys", "Puzzles", "Outdoor Toys"], (6, 75), (0.50, 0.58), 0.025,
                     ["PlayCraft", "Brainy Box", "Little Explorer"]),
    "Sports & Outdoors": (["Fitness", "Camping", "Cycling", "Activewear"], (8, 180), (0.50, 0.60), 0.04,
                          ["Peak Step", "Trailforge", "FitCore", "NorthStar Essentials"]),
    "Accessories": (["Bags", "Jewellery", "Watches", "Sunglasses"], (8, 150), (0.35, 0.48), 0.03,
                    ["Ashford & Co", "Silverleaf", "Maison Belle", "NorthStar Essentials"]),
}
CAT_NAMES = list(CATEGORIES)
CAT_PRODUCT_COUNT = {"Clothing": 260, "Footwear": 130, "Home & Kitchen": 190, "Electronics": 140,
                     "Beauty": 160, "Toys & Games": 110, "Sports & Outdoors": 120, "Accessories": 110}
CAT_CODES = {"Clothing": "CLO", "Footwear": "FTW", "Home & Kitchen": "HOM", "Electronics": "ELE",
             "Beauty": "BEA", "Toys & Games": "TOY", "Sports & Outdoors": "SPO", "Accessories": "ACC"}
CAT_DEMAND = {"Clothing": 1.30, "Footwear": 0.85, "Home & Kitchen": 0.9, "Electronics": 0.95,
              "Beauty": 1.1, "Toys & Games": 0.6, "Sports & Outdoors": 0.65, "Accessories": 0.65}

ITEM_WORDS = {
    "Womenswear": ["Wrap Dress", "Linen Shirt", "Knit Jumper", "Wide-Leg Trousers", "Midi Skirt", "Blouse"],
    "Menswear": ["Oxford Shirt", "Chino Trousers", "Crew Jumper", "Polo Shirt", "Slim Jeans", "Overshirt"],
    "Kidswear": ["Kids Hoodie", "School Polo", "Kids Joggers", "Pyjama Set", "Kids T-Shirt"],
    "Outerwear": ["Puffer Jacket", "Wool Coat", "Rain Mac", "Gilet", "Parka"],
    "Trainers": ["Running Trainer", "Court Trainer", "Canvas Trainer", "Trail Runner"],
    "Boots": ["Chelsea Boot", "Hiking Boot", "Ankle Boot", "Wellington"],
    "Formal Shoes": ["Derby Shoe", "Loafer", "Brogue", "Court Heel"],
    "Sandals": ["Slider", "Strappy Sandal", "Flip Flop", "Walking Sandal"],
    "Cookware": ["Frying Pan", "Saucepan Set", "Casserole Dish", "Knife Block"],
    "Bedding": ["Duvet Cover Set", "Pillow Pair", "Fitted Sheet", "Throw"],
    "Home Decor": ["Table Lamp", "Candle Set", "Photo Frame", "Cushion", "Mirror"],
    "Small Appliances": ["Kettle", "Toaster", "Air Fryer", "Blender", "Coffee Machine"],
    "Headphones": ["Wireless Earbuds", "Over-Ear Headphones", "Sports Earphones"],
    "Smart Home": ["Smart Plug", "Smart Bulb", "Video Doorbell", "Smart Speaker", "Indoor Camera"],
    "Phone Accessories": ["Phone Case", "Charging Cable", "Power Bank", "Wireless Charger"],
    "Tablets & Gadgets": ["Kids Tablet", "E-Reader", "Fitness Tracker", "Smartwatch", "Bluetooth Speaker"],
    "Skincare": ["Moisturiser", "Serum", "Cleanser", "SPF Cream", "Face Mask"],
    "Fragrance": ["Eau de Parfum", "Eau de Toilette", "Body Mist", "Gift Set"],
    "Makeup": ["Foundation", "Mascara", "Lipstick", "Eyeshadow Palette"],
    "Haircare": ["Shampoo", "Conditioner", "Hair Oil", "Hair Dryer"],
    "Board Games": ["Strategy Game", "Family Quiz Game", "Card Game"],
    "Kids Toys": ["Building Set", "Plush Toy", "Remote Control Car", "Doll House"],
    "Puzzles": ["1000-Piece Puzzle", "Kids Floor Puzzle", "3D Puzzle"],
    "Outdoor Toys": ["Garden Swing", "Football Goal", "Water Blaster", "Scooter"],
    "Fitness": ["Yoga Mat", "Dumbbell Set", "Resistance Bands", "Kettlebell"],
    "Camping": ["2-Person Tent", "Sleeping Bag", "Camping Chair", "Head Torch"],
    "Cycling": ["Bike Helmet", "Bike Lights Set", "Cycling Gloves", "Bike Lock"],
    "Activewear": ["Gym Leggings", "Running Top", "Training Shorts", "Sports Bra"],
    "Bags": ["Tote Bag", "Backpack", "Crossbody Bag", "Weekend Holdall"],
    "Jewellery": ["Silver Necklace", "Hoop Earrings", "Charm Bracelet", "Ring Set"],
    "Watches": ["Analogue Watch", "Chronograph Watch", "Minimalist Watch"],
    "Sunglasses": ["Aviator Sunglasses", "Round Sunglasses", "Sports Sunglasses"],
}
ADJECTIVES = ["Classic", "Essential", "Premium", "Everyday", "Signature", "Heritage", "Active", "Lite",
              "Pro", "Eco", "Deluxe", "Urban", "Coastal", "Nordic", "Studio", "Original"]
COLOURS = ["Black", "Navy", "Grey", "White", "Olive", "Sand", "Blush", "Teal", "Charcoal", "Stone"]

product_rows = []
pid = 0
for cat, (subcats, (pmin, pmax), (cmin, cmax), _ret, brands) in CATEGORIES.items():
    for i in range(CAT_PRODUCT_COUNT[cat]):
        pid += 1
        sub = subcats[i % len(subcats)]
        brand = rng.choice(brands)
        # Price: log-uniform within range, rounded to retail .99 / .49 endings
        price = float(np.exp(rng.uniform(np.log(pmin), np.log(pmax))))
        price = max(round(price) - 0.01, 2.99) if price > 10 else round(price * 2) / 2 - 0.01
        own_label = brand == "NorthStar Essentials"
        cost_ratio = rng.uniform(cmin, cmax) - (0.06 if own_label else 0.0)
        # Planted: a group of electronics "doorbuster" products with a very thin margin
        loss_leader = cat == "Electronics" and rng.random() < 0.15
        if loss_leader:
            cost_ratio = rng.uniform(0.86, 0.91)
        cost = round(price * cost_ratio, 2)
        name = f"{brand} {rng.choice(ADJECTIVES)} {rng.choice(ITEM_WORDS[sub])}"
        if cat in ("Clothing", "Footwear", "Accessories"):
            name += f" - {rng.choice(COLOURS)}"
        # 10% of products launch during the 2-year window
        launch = pd.Timestamp("2019-01-01") + pd.Timedelta(days=int(rng.integers(0, 1800)))
        if rng.random() < 0.10:
            launch = pd.Timestamp(START) + pd.Timedelta(days=int(rng.integers(30, 640)))
        popularity = rng.pareto(1.6) + 0.3      # long tail: few best-sellers, many slow movers
        product_rows.append(dict(SKU=f"NS-{CAT_CODES[cat]}-{pid:05d}", ProductName=name, Category=cat,
                                 SubCategory=sub, Brand=brand, UnitCost=cost, ListPrice=price,
                                 LaunchDate=launch, IsOwnLabel="Y" if own_label else "N",
                                 _pop=popularity, _loss_leader=loss_leader))
products = pd.DataFrame(product_rows)
P = len(products)

# ---------------------------------------------------------------------------
# 4. Seasonality (by calendar month 1..12) for categories and subcategories
# ---------------------------------------------------------------------------
CAT_SEASON = {c: np.ones(12) for c in CAT_NAMES}
CAT_SEASON["Toys & Games"] = np.array([0.5, 0.5, 0.6, 0.7, 0.7, 0.7, 0.8, 0.8, 0.8, 1.0, 2.2, 3.2])
CAT_SEASON["Electronics"] = np.array([0.9, 0.7, 0.8, 0.8, 0.8, 0.8, 0.8, 0.9, 0.9, 1.0, 1.9, 1.5])
CAT_SEASON["Beauty"] = np.array([0.8, 1.15, 0.9, 0.9, 0.95, 0.95, 0.95, 0.9, 0.9, 1.0, 1.4, 1.8])
CAT_SEASON["Sports & Outdoors"] = np.array([1.5, 1.1, 1.0, 1.1, 1.3, 1.5, 1.5, 1.3, 1.0, 0.8, 0.8, 0.8])
CAT_SEASON["Home & Kitchen"] = np.array([1.25, 0.9, 0.95, 1.0, 0.95, 0.9, 0.9, 0.95, 1.0, 1.05, 1.3, 1.3])
CAT_SEASON["Clothing"] = np.array([1.1, 0.85, 1.0, 1.05, 1.05, 1.0, 1.0, 1.05, 1.1, 1.05, 1.1, 1.2])
SUB_SEASON = {
    "Outerwear": np.array([1.6, 1.0, 0.6, 0.4, 0.3, 0.2, 0.2, 0.3, 0.8, 1.5, 1.9, 1.7]),
    "Boots": np.array([1.4, 1.0, 0.6, 0.4, 0.3, 0.3, 0.3, 0.4, 0.9, 1.5, 1.7, 1.5]),
    "Sandals": np.array([0.2, 0.2, 0.5, 1.0, 1.7, 2.3, 2.4, 1.8, 0.6, 0.3, 0.2, 0.2]),
    "Fragrance": np.array([0.6, 1.4, 0.8, 0.8, 0.9, 0.8, 0.8, 0.8, 0.8, 1.0, 1.6, 3.0]),
    "Camping": np.array([0.3, 0.4, 0.7, 1.1, 1.6, 2.0, 2.2, 1.8, 0.8, 0.4, 0.3, 0.3]),
    "Fitness": np.array([2.4, 1.4, 1.0, 0.9, 0.9, 0.8, 0.8, 0.8, 1.0, 0.9, 0.9, 0.8]),
    "Kidswear": np.array([0.8, 0.8, 0.9, 0.9, 0.9, 1.0, 1.3, 2.0, 1.6, 0.9, 0.9, 1.0]),
    "Outdoor Toys": np.array([0.3, 0.4, 0.8, 1.3, 1.7, 1.9, 1.9, 1.5, 0.7, 0.5, 0.7, 1.0]),
}
# Category mix differs by channel: electronics skew online, beauty skews in-store
CH_CAT_MULT = {
    "In-Store": {"Beauty": 1.25, "Electronics": 0.8, "Clothing": 1.05},
    "Website": {"Electronics": 1.35, "Footwear": 1.15, "Beauty": 0.75, "Clothing": 1.05},
    "Mobile App": {"Clothing": 1.25, "Footwear": 1.2, "Beauty": 0.9, "Home & Kitchen": 0.8},
    "Click & Collect": {"Electronics": 1.2, "Toys & Games": 1.3, "Home & Kitchen": 1.15},
}
# Segment price tolerance: premium customers skew to expensive items, value to cheap
SEGMENTS = ["Value", "Mainstream", "Premium"]
SEG_PRICE_ELASTICITY = {"Value": -0.45, "Mainstream": 0.0, "Premium": 0.40}

# Pre-compute product selection probabilities for each (month index 0..23, channel, segment)
prod_cat = products["Category"].to_numpy()
prod_sub = products["SubCategory"].to_numpy()
prod_price = products["ListPrice"].to_numpy()
prod_launch = products["LaunchDate"].to_numpy()
base_w = products["_pop"].to_numpy() * np.array([CAT_DEMAND[c] for c in prod_cat])
# Normalise so each category's total weight reflects demand, not number of SKUs
for c in CAT_NAMES:
    m = prod_cat == c
    base_w[m] = base_w[m] / base_w[m].sum() * CAT_DEMAND[c]

MONTHS = pd.period_range("2024-01", "2025-12", freq="M")
prob_table: dict[tuple[int, int, str], np.ndarray] = {}
for mi, per in enumerate(MONTHS):
    cal_m = per.month - 1
    season = np.array([CAT_SEASON[c][cal_m] for c in prod_cat])
    sub_season = np.array([SUB_SEASON[s][cal_m] if s in SUB_SEASON else 1.0 for s in prod_sub])
    launched = prod_launch <= np.datetime64(per.start_time)   # sellable from the first full month after launch
    for ci, ch in enumerate(CHANNELS):
        chm = np.array([CH_CAT_MULT[ch].get(c, 1.0) for c in prod_cat])
        for seg in SEGMENTS:
            w = base_w * season * sub_season * chm * (prod_price ** SEG_PRICE_ELASTICITY[seg]) * launched
            prob_table[(mi, ci, seg)] = w / w.sum()

# ---------------------------------------------------------------------------
# 5. Customers
# ---------------------------------------------------------------------------
N_CUST = 12_500
FIRST = ["Oliver", "Amelia", "George", "Isla", "Harry", "Ava", "Noah", "Mia", "Jack", "Ivy", "Leo", "Grace",
         "Arthur", "Freya", "Muhammad", "Lily", "Oscar", "Florence", "Charlie", "Emily", "Jacob", "Sophie",
         "Thomas", "Poppy", "James", "Evie", "William", "Ella", "Henry", "Isabella", "Aarav", "Priya",
         "Rohan", "Ananya", "Daniel", "Chloe", "Samuel", "Ruby", "Joshua", "Zara", "Ethan", "Hannah",
         "Lucas", "Megan", "Ryan", "Aisha", "Callum", "Niamh", "Ewan", "Eilidh", "Rhys", "Seren", "Conor", "Aoife"]
LAST = ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Patel", "Robinson",
        "Wright", "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Jackson",
        "Clarke", "Khan", "Hughes", "Edwards", "Turner", "Hill", "Moore", "Cooper", "Ward", "Morris",
        "Singh", "Ahmed", "King", "Harris", "Lewis", "Scott", "Murray", "Campbell", "Kelly", "O'Neill",
        "MacDonald", "Reid", "Price", "Morgan", "Shah", "Ali", "Begum", "Chen", "Nowak", "Kowalski"]
DOMAINS = ["gmail.com", "outlook.com", "yahoo.co.uk", "hotmail.co.uk", "icloud.com", "btinternet.com"]

reg_codes = np.array(list(REGION_POP))
reg_p = np.array(list(REGION_POP.values()), dtype=float)
reg_p /= reg_p.sum()
cust_region = rng.choice(reg_codes, size=N_CUST, p=reg_p)
cust_segment = rng.choice(SEGMENTS, size=N_CUST, p=[0.45, 0.40, 0.15])
seg_activity = {"Value": 0.85, "Mainstream": 1.0, "Premium": 1.45}
cust_activity = rng.gamma(shape=0.9, scale=1.0, size=N_CUST) * np.array([seg_activity[s] for s in cust_segment])
# Online affinity: younger and premium customers shop online more
cust_dob = np.array([pd.Timestamp("1950-01-01") + pd.Timedelta(days=int(d))
                     for d in rng.integers(0, 365 * 55, size=N_CUST)])
age_2025 = np.array([(pd.Timestamp("2025-06-30") - d).days / 365.25 for d in cust_dob])
cust_online = np.clip(rng.beta(2, 2.2, N_CUST) + (40 - age_2025) * 0.008, 0.02, 0.98)
# Active-from date: 55% existing customers before 2024, the rest acquired during the window
existing = rng.random(N_CUST) < 0.55
signup = np.where(
    existing,
    np.array([pd.Timestamp("2018-01-01") + pd.Timedelta(days=int(d)) for d in rng.integers(0, 2190, N_CUST)]),
    np.array([pd.Timestamp(START) + pd.Timedelta(days=int(d)) for d in rng.integers(0, len(DAYS) - 20, N_CUST)]),
)
signup = pd.to_datetime(signup)
# 22% of customers lapse (stop buying) at some point in the window
lapse = pd.to_datetime(np.where(rng.random(N_CUST) < 0.22,
                                np.array([pd.Timestamp(START) + pd.Timedelta(days=int(d))
                                          for d in rng.integers(60, len(DAYS), N_CUST)]),
                                pd.Timestamp("2099-01-01")))

first_names = rng.choice(FIRST, N_CUST)
last_names = rng.choice(LAST, N_CUST)
cities, postcodes = [], []
for r in cust_region:
    city, areas = POSTCODE_AREAS[r][rng.integers(0, len(POSTCODE_AREAS[r]))]
    cities.append(city)
    postcodes.append(make_postcode(rng.choice(areas)))
emails, seen = [], set()
for f, l in zip(first_names, last_names):
    e = f"{f.lower()}.{l.lower().replace(chr(39), '')}{rng.integers(1, 999)}@{rng.choice(DOMAINS)}"
    while e in seen:                       # an email address belongs to exactly one person
        e = f"{f.lower()}.{l.lower().replace(chr(39), '')}{rng.integers(1, 9999)}@{rng.choice(DOMAINS)}"
    seen.add(e)
    emails.append(e)
customers = pd.DataFrame({
    "CustomerID": [f"C{100000 + i}" for i in range(N_CUST)],
    "FirstName": first_names,
    "LastName": last_names,
    "Email": emails,
    "Gender": rng.choice(["Female", "Male", "Other/Prefer not to say"], N_CUST, p=[0.53, 0.45, 0.02]),
    "DateOfBirth": pd.to_datetime(cust_dob).date,
    "City": cities,
    "Postcode": postcodes,
    "RegionCode": cust_region,
    "Segment": cust_segment,
    "LoyaltyMember": np.where(rng.random(N_CUST) < 0.58, "Y", "N"),
    "SignupDate": signup.date,
})

# Indexes for fast weighted customer sampling, filtered by signup date
order_by_signup = np.argsort(signup.values)
signup_sorted = signup.values[order_by_signup]


def build_sampler(idx: np.ndarray, weights: np.ndarray):
    order = idx[np.argsort(signup.values[idx])]
    return order, signup.values[order], np.cumsum(weights[order])


samplers_region = {r: build_sampler(np.where(cust_region == r)[0], cust_activity * (1.15 - cust_online))
                   for r in REGION_CODES}
sampler_all_store = build_sampler(np.arange(N_CUST), cust_activity * (1.15 - cust_online))
sampler_online = build_sampler(np.arange(N_CUST), cust_activity * cust_online)


def draw_customer(sampler, when: np.datetime64) -> int:
    order, su, cw = sampler
    k = np.searchsorted(su, when, side="right")
    if k == 0:
        return -1
    for _ in range(6):
        c = order[np.searchsorted(cw[:k], rng.random() * cw[k - 1], side="right")]
        if lapse.values[c] > when:
            return int(c)
    return int(c)


# ---------------------------------------------------------------------------
# 6. Orders: daily volume by channel
# ---------------------------------------------------------------------------
MONTH_SEASON = np.array([0.98, 0.74, 0.84, 0.90, 0.92, 0.95, 1.00, 0.96, 0.88, 0.95, 1.30, 1.55])
DOW_STORE = np.array([0.82, 0.84, 0.90, 0.96, 1.10, 1.45, 0.93])   # Mon..Sun
DOW_ONLINE = np.array([1.10, 1.02, 1.00, 0.98, 0.92, 0.88, 1.12])


def black_friday(year: int) -> pd.Timestamp:
    nov30 = pd.Timestamp(year, 11, 30)
    return nov30 - pd.Timedelta(days=(nov30.weekday() - 4) % 7)


BF = {y: black_friday(y) for y in (2024, 2025)}
BASE_ORDERS_PER_DAY = 108

order_rows = []
for d in DAYS:
    years = (d - pd.Timestamp(START)).days / 365.25
    m_factor = MONTH_SEASON[d.month - 1]
    bf = BF[d.year]
    spike_store, spike_online = 1.0, 1.0
    if bf <= d <= bf + pd.Timedelta(days=3):          # Black Friday weekend + Cyber Monday
        spike_store, spike_online = 1.7, 2.6
    elif bf - pd.Timedelta(days=6) <= d < bf:         # pre-Black-Friday deals week
        spike_store, spike_online = 1.15, 1.4
    if d.month == 12 and 18 <= d.day <= 23:
        spike_store *= 1.35
    if d.month == 12 and d.day == 25:
        spike_store, spike_online = 0.0, 0.35         # stores closed Christmas Day
    if d.month == 12 and d.day == 26:
        spike_store, spike_online = 1.6, 1.8          # Boxing Day sale
    for ci, ch in enumerate(CHANNELS):
        growth = (1 + CH_ANNUAL_GROWTH[ci]) ** years
        is_store = ch in ("In-Store", "Click & Collect")
        dow = (DOW_STORE if is_store else DOW_ONLINE)[d.weekday()]
        spike = spike_store if is_store else spike_online
        if ch == "Click & Collect" and d.month == 12 and d.day >= 24:
            spike = 0.2
        lam = BASE_ORDERS_PER_DAY * CH_BASE_SHARE[ci] * growth * m_factor * dow * spike
        n = rng.poisson(lam)
        if n:
            order_rows.append((d, ci, n))

# Expand to individual orders
o_dates, o_ch = [], []
for d, ci, n in order_rows:
    o_dates.extend([d] * n)
    o_ch.extend([ci] * n)
orders = pd.DataFrame({"OrderDate": pd.to_datetime(o_dates), "ChannelIdx": o_ch})
orders = orders.sort_values(["OrderDate", "ChannelIdx"]).reset_index(drop=True)
N_ORD = len(orders)
# Add a random time-of-day so the ordering looks like a real till/web log
orders["OrderDate"] = orders["OrderDate"] + pd.to_timedelta(rng.integers(8 * 3600, 21 * 3600, N_ORD), unit="s")
orders = orders.sort_values("OrderDate").reset_index(drop=True)
orders["OrderID"] = [f"SO{1_000_000 + i}" for i in range(N_ORD)]

# Store assignment
phys_codes = PHYSICAL["StoreCode"].to_numpy()
phys_traffic = PHYSICAL["Traffic"].to_numpy()
phys_open = PHYSICAL["OpenDate"].to_numpy()
phys_region = PHYSICAL["RegionCode"].to_numpy()
store_code = np.empty(N_ORD, dtype=object)
cust_idx = np.full(N_ORD, -1)
ch_arr = orders["ChannelIdx"].to_numpy()
date_arr = orders["OrderDate"].to_numpy()

for i in range(N_ORD):
    ch = CHANNELS[ch_arr[i]]
    when = date_arr[i]
    if ch in ("In-Store", "Click & Collect"):
        open_mask = phys_open <= when
        w = phys_traffic * open_mask
        s = rng.choice(len(phys_codes), p=w / w.sum())
        store_code[i] = phys_codes[s]
        region = phys_region[s]
        guest_p = 0.31 if ch == "In-Store" else 0.0
        if rng.random() < guest_p:
            cust_idx[i] = -1
        else:
            sampler = samplers_region[region] if rng.random() < 0.85 else sampler_all_store
            cust_idx[i] = draw_customer(sampler, when)
    else:
        store_code[i] = HUB_CODE
        cust_idx[i] = draw_customer(sampler_online, when)

orders["StoreCode"] = store_code
orders["CustIdx"] = cust_idx
orders["Channel"] = [CHANNELS[c] for c in ch_arr]
orders["Segment"] = np.where(cust_idx >= 0, cust_segment[np.clip(cust_idx, 0, None)], "Mainstream")
orders["MonthIdx"] = (orders["OrderDate"].dt.year - 2024) * 12 + orders["OrderDate"].dt.month - 1

# Payment method
pay = np.empty(N_ORD, dtype=object)
is_store_ch = orders["Channel"].eq("In-Store").to_numpy()
pay[is_store_ch] = rng.choice(["Contactless", "Chip & PIN", "Cash", "Mobile Wallet"], is_store_ch.sum(),
                              p=[0.52, 0.18, 0.12, 0.18])
pay[~is_store_ch] = rng.choice(["Debit Card", "Credit Card", "PayPal", "Klarna"], (~is_store_ch).sum(),
                               p=[0.42, 0.22, 0.22, 0.14])
orders["PaymentMethod"] = pay

# ---------------------------------------------------------------------------
# 7. Order lines
# ---------------------------------------------------------------------------
n_lines = 1 + rng.poisson(CH_LINES_MEAN[ch_arr])
n_lines = np.minimum(n_lines, 7)
lines = orders.loc[orders.index.repeat(n_lines)].reset_index(drop=True)
lines["LineNo"] = lines.groupby("OrderID").cumcount() + 1
L = len(lines)

prod_idx = np.empty(L, dtype=int)
for (mi, ci, seg), grp in lines.groupby(["MonthIdx", "ChannelIdx", "Segment"]).groups.items():
    prod_idx[grp] = rng.choice(P, size=len(grp), p=prob_table[(mi, ci, seg)])
lines["ProdIdx"] = prod_idx
# Avoid the same SKU twice in one order (merge into quantity instead)
lines = lines.drop_duplicates(["OrderID", "ProdIdx"]).reset_index(drop=True)
lines["LineNo"] = lines.groupby("OrderID").cumcount() + 1
L = len(lines)
p_cat = prod_cat[lines["ProdIdx"]]
p_sub = prod_sub[lines["ProdIdx"]]

# Quantity: mostly 1; consumables more often multiples
multi_p = np.where(np.isin(p_cat, ["Beauty", "Home & Kitchen"]), 0.22, 0.09)
qty = 1 + (rng.random(L) < multi_p) * rng.integers(1, 3, L)
lines["Quantity"] = qty

# Prices: 2025 list prices +3%, costs +6% (supplier inflation not fully passed on)
is_2025 = lines["OrderDate"].dt.year.to_numpy() == 2025
list_price = prod_price[lines["ProdIdx"]] * np.where(is_2025, 1.03, 1.0)
unit_cost = products["UnitCost"].to_numpy()[lines["ProdIdx"]] * np.where(is_2025, 1.06, 1.0)
lines["UnitPrice"] = np.round(list_price, 2)
lines["UnitCost"] = np.round(unit_cost, 2)

# ---------------------------------------------------------------------------
# 8. Discounts
# ---------------------------------------------------------------------------
od = lines["OrderDate"].dt.normalize()
month = od.dt.month.to_numpy()
day = od.dt.day.to_numpy()
year = od.dt.year.to_numpy()
bf_dates = np.array([BF[y] for y in year], dtype="datetime64[ns]")
days_from_bf = (od.to_numpy() - bf_dates) / np.timedelta64(1, "D")

disc_prob = np.full(L, 0.10)                       # everyday promotions
disc_lo, disc_hi = np.full(L, 0.05), np.full(L, 0.15)

jan_sale = (month == 1) & (day <= 31)
disc_prob[jan_sale], disc_lo[jan_sale], disc_hi[jan_sale] = 0.55, 0.20, 0.45
summer = ((month == 6) & (day >= 20)) | (month == 7)
disc_prob[summer], disc_lo[summer], disc_hi[summer] = 0.40, 0.15, 0.35
bfw = (days_from_bf >= -6) & (days_from_bf <= 3)
disc_prob[bfw], disc_lo[bfw], disc_hi[bfw] = 0.62, 0.20, 0.40
boxing = (month == 12) & (day >= 26)
disc_prob[boxing], disc_lo[boxing], disc_hi[boxing] = 0.65, 0.30, 0.50

# 2025: management pushed more promotions to chase growth
disc_prob = np.where(is_2025, np.minimum(disc_prob * 1.35, 0.9), disc_prob)
# Segments: value shoppers concentrate their buying on discounted items
seg_mult = lines["Segment"].map({"Value": 1.35, "Mainstream": 1.0, "Premium": 0.65}).to_numpy()
disc_prob = np.minimum(disc_prob * seg_mult, 0.95)
# App-exclusive codes
app = lines["Channel"].eq("Mobile App").to_numpy()
disc_prob = np.where(app, np.minimum(disc_prob + 0.08, 0.95), disc_prob)
# Store behaviours
sc = lines["StoreCode"].to_numpy()
for code, extra in STORE_EXTRA_DISCOUNT_PROB.items():
    m = sc == code
    disc_prob[m] = np.minimum(disc_prob[m] + extra, 0.95)
    disc_lo[m] = np.maximum(disc_lo[m], 0.20)
    disc_hi[m] = np.maximum(disc_hi[m], 0.35)
outlet = sc == "ST07"
disc_prob[outlet], disc_lo[outlet], disc_hi[outlet] = 0.92, 0.25, 0.45
# Beauty is rarely discounted (brand agreements)
beauty = p_cat == "Beauty"
disc_prob[beauty] *= 0.5

discounted = rng.random(L) < disc_prob
disc_pct = np.where(discounted, rng.uniform(disc_lo, disc_hi), 0.0)
disc_pct = np.round(disc_pct * 20) / 20           # 5% steps like real promotions
lines["DiscountPct"] = disc_pct

gross = lines["Quantity"] * lines["UnitPrice"]
lines["DiscountAmount"] = np.round(gross * lines["DiscountPct"], 2)
lines["NetSales"] = np.round(gross - lines["DiscountAmount"], 2)
lines["CostAmount"] = np.round(lines["Quantity"] * lines["UnitCost"], 2)

# ---------------------------------------------------------------------------
# 9. Returns
# ---------------------------------------------------------------------------
cat_ret = np.array([CATEGORIES[c][3] for c in p_cat])
ch_ret = CH_RETURN_FACTOR[lines["ChannelIdx"].to_numpy()]
p_return = cat_ret * ch_ret
# Clothing/footwear online returns climb through 2025 (customers "bracket" sizes)
months_in = lines["MonthIdx"].to_numpy()
apparel_online = np.isin(p_cat, ["Clothing", "Footwear"]) & np.isin(lines["Channel"], ["Website", "Mobile App"])
p_return = np.where(apparel_online, p_return * (1 + 0.03 * np.maximum(months_in - 8, 0)), p_return)
brand = products["Brand"].to_numpy()[lines["ProdIdx"]]
# Planted: Stride Lab footwear sizing changed in 2025 -> wrong-size returns spike
stride = (brand == "Stride Lab") & is_2025
p_return = np.where(stride, p_return * 2.1, p_return)
# Planted: Voltix smart-home devices have a fault
voltix = (brand == "Voltix") & (p_sub == "Smart Home")
p_return = np.where(voltix, p_return * 3.5, p_return)
for code, f in STORE_RETURN_FACTOR.items():
    p_return = np.where(sc == code, p_return * f, p_return)
# BNPL shoppers order more speculatively
p_return = np.where(lines["PaymentMethod"].eq("Klarna"), p_return * 1.25, p_return)
p_return = np.minimum(p_return, 0.6)
is_ret = rng.random(L) < p_return

ret = lines.loc[is_ret, ["OrderID", "LineNo", "OrderDate", "Channel", "Quantity", "NetSales"]].copy()
ret["_cat"] = p_cat[is_ret]
ret["_sub"] = p_sub[is_ret]
ret["_brand"] = brand[is_ret]
online_ret = ret["Channel"].isin(["Website", "Mobile App"]).to_numpy()
lag = np.where(online_ret, rng.integers(4, 31, len(ret)), rng.integers(0, 29, len(ret)))
ret["ReturnDate"] = (ret["OrderDate"].dt.normalize() + pd.to_timedelta(lag, unit="D"))
ret = ret[ret["ReturnDate"] <= pd.Timestamp(END)]   # extract date: returns after 31 Dec 2025 not yet known
partial = (ret["Quantity"] > 1) & (rng.random(len(ret)) < 0.35)
ret["ReturnQty"] = np.where(partial, 1, ret["Quantity"])
ret["RefundAmount"] = np.round(ret["NetSales"] / ret["Quantity"] * ret["ReturnQty"], 2)


def pick_reason(row_cat, row_sub, row_brand, online, year_) -> str:
    if row_brand == "Stride Lab" and year_ == 2025 and rng.random() < 0.7:
        return "Wrong size / fit"
    if row_brand == "Voltix" and row_sub == "Smart Home" and rng.random() < 0.75:
        return "Faulty / defective"
    if row_cat in ("Clothing", "Footwear"):
        opts, p = ["Wrong size / fit", "Not as described", "Changed mind", "Damaged / defective item",
                   "Arrived late"], [0.52, 0.16, 0.20, 0.06, 0.06]
    elif row_cat in ("Electronics",) or row_sub == "Small Appliances":
        opts, p = ["Faulty / defective", "Not as described", "Changed mind", "Damaged / defective item",
                   "Arrived late"], [0.38, 0.17, 0.25, 0.13, 0.07]
    else:
        opts, p = ["Changed mind", "Not as described", "Damaged / defective item", "Faulty / defective",
                   "Arrived late"], [0.40, 0.20, 0.25, 0.07, 0.08]
    if not online:  # no delivery in-store
        p = [0 if o == "Arrived late" else q for o, q in zip(opts, p)]
        p = list(np.array(p) / sum(p))
    return rng.choice(opts, p=p)


ret["ReturnReason"] = [pick_reason(c, s, b, o, y) for c, s, b, o, y in
                       zip(ret["_cat"], ret["_sub"], ret["_brand"],
                           ret["Channel"].isin(["Website", "Mobile App"]), ret["ReturnDate"].dt.year)]
ret["ReturnMethod"] = np.where(ret["Channel"].isin(["Website", "Mobile App"]),
                               rng.choice(["Post", "In-Store"], len(ret), p=[0.72, 0.28]), "In-Store")
ret = ret.sort_values("ReturnDate").reset_index(drop=True)
ret["ReturnID"] = [f"RT{500_000 + i}" for i in range(len(ret))]

# ---------------------------------------------------------------------------
# 10. Write clean "source system" extracts (quality issues are injected next)
# ---------------------------------------------------------------------------
customers_out = customers.copy()
products_out = products.drop(columns=["_pop", "_loss_leader"]).copy()
products_out["LaunchDate"] = products_out["LaunchDate"].dt.date
stores_out = stores.drop(columns=["Traffic", "PostcodeArea"]).copy()
stores_out["OpenDate"] = stores_out["OpenDate"].dt.date
region_name = {c: n for c, n, _ in REGIONS}
stores_out["Region"] = stores_out["RegionCode"].map(region_name).fillna("Online (National)")
stores_out = stores_out[["StoreCode", "StoreName", "StoreType", "City", "Postcode", "Region", "SizeSqFt", "OpenDate"]]
customers_out["Region"] = customers_out["RegionCode"].map(region_name)
customers_out = customers_out.drop(columns=["RegionCode"])
regions_out = pd.DataFrame(REGIONS, columns=["RegionCode", "RegionName", "Nation"])

sales_out = pd.DataFrame({
    "OrderID": lines["OrderID"],
    "LineNo": lines["LineNo"],
    "OrderDateTime": lines["OrderDate"].dt.strftime("%Y-%m-%d %H:%M:%S"),
    "CustomerID": np.where(lines["CustIdx"] >= 0,
                           np.array([f"C{100000 + i}" for i in np.clip(lines["CustIdx"], 0, None)]), ""),
    "SKU": products["SKU"].to_numpy()[lines["ProdIdx"]],
    "StoreCode": lines["StoreCode"],
    "Channel": lines["Channel"],
    "Quantity": lines["Quantity"],
    "UnitPrice": lines["UnitPrice"],
    "UnitCost": lines["UnitCost"],
    "DiscountPct": lines["DiscountPct"],
    "PaymentMethod": lines["PaymentMethod"],
})
returns_out = ret[["ReturnID", "OrderID", "LineNo", "ReturnDate", "ReturnQty", "RefundAmount",
                   "ReturnReason", "ReturnMethod"]].copy()
returns_out["ReturnDate"] = returns_out["ReturnDate"].dt.strftime("%Y-%m-%d")

TRUTH = ROOT / "data" / "_truth"     # pre-corruption copy, used only to test the cleaning step
TRUTH.mkdir(exist_ok=True)
for name, df in [("customers", customers_out), ("products", products_out), ("stores", stores_out),
                 ("regions", regions_out), ("sales_transactions", sales_out), ("returns", returns_out)]:
    df.to_csv(TRUTH / f"{name}.csv", index=False)

print(f"Customers: {len(customers_out):,}")
print(f"Products:  {len(products_out):,}")
print(f"Stores:    {len(stores_out):,} (incl. e-commerce hub)")
print(f"Orders:    {sales_out['OrderID'].nunique():,}")
print(f"Lines:     {len(sales_out):,}")
print(f"Returns:   {len(returns_out):,}")
print(f"Revenue:   £{lines['NetSales'].sum():,.0f}")
