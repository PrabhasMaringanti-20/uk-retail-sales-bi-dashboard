# Notes 03 — Generating Realistic Synthetic Data (Phase 3)

**File:** `scripts/01_generate_data.py` (run: `python scripts/01_generate_data.py`)

## In one line
Since we have no real company data, we **simulated** a retailer, with deliberate business patterns so the analysis
has real things to discover.

## Simple explanation
Random numbers make boring, unrealistic data: every month the same, every store the same. Real retail has Christmas
peaks, January sales, online growth and bad suppliers. So we *designed* those behaviours into the generator, like
writing the story first and then creating the evidence.

## What the generator creates
| Table | Rows |
| --- | --- |
| Customers | 12,500 (segments Value / Mainstream / Premium; 55% existing before 2024, rest join over time; 22% stop buying) |
| Products | 1,220 across 8 categories, 32 sub-categories, real-looking UK prices per item type |
| Stores | 24 physical + 1 e-commerce hub, in 12 UK regions |
| Orders / lines | ~89,500 orders, ~186,000 lines, Jan 2024 – Dec 2025 |
| Returns | ~14,000 |

## Patterns planted on purpose (and later found by the analysis)
| Pattern | How it's made | Found in |
| --- | --- | --- |
| Seasonality | Month factors (Nov–Dec peak), Black Friday spike, stores closed 25 Dec | SQL Q13, Q20 |
| Category seasons | Toys ×3 in December, sandals in summer, fitness in January | Q13 |
| Channel shift | App +45%/yr, website +18%, store +1% | Q04, Q33 |
| Margin squeeze | 2025 prices +3%, costs +6% | Q37 |
| More discounting in 2025 | Promotion probability ×1.35 | Q37 |
| Thin Electronics margin | Cost 74–84% of price; 15% "doorbuster" products at 86–91% | Q03, Q36 |
| Over-discounting store | Newcastle: +38% chance of a 20–35% local discount | Q14 |
| Outlet | Bluewater always 25–45% off | Q14 |
| Sizing problem | Stride Lab returns ×2.1 in 2025, mostly "wrong size" | Q19 |
| Faulty product | Voltix smart home returns ×3.5, "faulty" | Q18 |
| Online returns | Website/App return factor ×2.1–2.3; apparel online creeps up through 2025 | Q16, Q39 |
| Customer value | Pareto-like activity (gamma distribution), premium buy more often | Q32, Q35 |
| Guest shoppers | 31% of in-store orders have no customer | Q23 |
| New store | Sheffield opens July 2024, which distorts YoY | Q33 (like-for-like) |
| Return lag | Returns after 31 Dec 2025 aren't in the extract | Q39 caveat |

## Key techniques (Python / pandas / numpy)
- **Random seed (`SEED = 42`):** the same data every run. Results are reproducible, which matters for any analysis.
- **Poisson distribution:** the number of orders per day (count of events around an average).
- **Log-normal popularity:** a few best-sellers, many slow movers (a long tail), like real retail.
- **Weighted random choice:** customers and products chosen with probabilities, not equally.
- **Vectorised numpy:** calculations on whole columns at once (fast) instead of row-by-row loops.

## Bugs found and fixed (good interview stories)
1. **Unrealistic prices:** a £380 smart plug. Prices were per category, so I changed them to per item type.
2. **Sales before product launch:** the SQL check failed for 356 rows; products became available at month *end*
   instead of month *start*. Fixed at source.
3. **Duplicate emails between different people:** de-duplication merged 4 real customers. Made emails unique, because
   an email belongs to one person.

> Lesson: **validation checks find bugs in your own code too**, not only in the data.

## Interview questions

**Q: Isn't synthetic data "fake"? Why should I trust your analysis?**
A: The data is simulated, and I say so upfront. The value is in the method: framing the problem, cleaning, modelling,
SQL, DAX and turning results into recommendations. Those are exactly what I'd do with real data. I also designed
realistic patterns (seasonality, channel shift, supplier issues) rather than pure randomness, and the analysis had to
*discover* them, not assume them.

**Q: How did you make it realistic?**
A: UK regions and postcode areas, realistic item-level prices, seasonality, Black Friday and Boxing Day, a new store
opening mid-period, guest shoppers, a long-tail product popularity curve, customers joining and lapsing over time.

**Q: What is a random seed and why use it?**
A: It fixes the random generator so every run gives the same data. Anyone can reproduce my numbers exactly.

## Common mistakes
- Pure random data (no story), so "insights" are noise.
- Forgetting to say the data is simulated.
- Planting patterns but not checking that they actually show up (we checked every one with SQL).
