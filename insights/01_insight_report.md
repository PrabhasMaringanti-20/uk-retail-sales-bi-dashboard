# Insight Report — NorthStar Retail UK, FY2024 vs FY2025

> **Simulated project.** NorthStar Retail UK is fictional and all data is synthetic. Every number below is
> reproducible from `sql/04_business_questions.sql` (query numbers shown as *Qxx*) or the charts in `screenshots/`.
> No facts are claimed beyond the dataset.

## Executive summary

NorthStar grew revenue **15.7%** in 2025 (£3.96M → £4.58M), but gross profit grew only **9.4%** and gross margin fell
**2.4 points** to 41.0%. Growth is coming from digital channels, while profit is leaking through four holes:

1. **Margin squeeze:** supplier costs rose faster than prices (−1.6 pts), and discounting increased (−0.8 pts).
2. **Electronics:** revenue +14.6%, but its gross profit **fell 13%**. Discounts above about 19% sell below cost.
3. **Online returns:** online clothing and footwear returns rose from about 16% to about 27%, driven by one footwear supplier.
4. **Two stores** discount far more than their peers.

The good news: the customer base is loyal (about 93% of orders come from returning customers), the app is growing
+49%, and most leaks have a clear, low-effort fix.

## Headline KPIs (Q01, Q02)

| KPI | 2024 | 2025 | Change |
| --- | ---: | ---: | ---: |
| Revenue | £3.96M | £4.58M | +15.7% |
| Gross profit | £1.72M | £1.88M | +9.4% |
| Gross margin | 43.3% | 41.0% | −2.4 pts |
| Orders | 42,639 | 46,889 | +10.0% |
| AOV | £92.91 | £97.77 | +5.2% |
| Active known customers | 7,014 | 8,101 | +15.5% |
| Return rate (refunds ÷ revenue, by order date) | 7.0% | 8.3% | +1.2 pts |

---

## Insights

Each insight follows: **Finding → Evidence → Possible cause → Business impact → Recommendation → Expected outcome.**

### 1. Profit is growing much more slowly than revenue
- **Finding:** Margin fell from 43.3% to 41.0%.
- **Evidence:** Q37 and the margin bridge (`09_margin_bridge.png`). The discount rate rose from 5.9% to 7.1% of gross
  sales, and cost rose from 53.4% to 54.8% of gross sales. Profit fell YoY in January (−11.3%) and July (−3.9%)
  even though revenue grew (Q25).
- **Possible cause:** Supplier cost increases (about +6%) were not fully passed on to prices (about +3%), and more
  promotions were run to chase growth.
- **Business impact:** At the 2024 margin, 2025 revenue would have produced about **£109K more gross profit**
  (£4.58M × 2.4 pts).
- **Recommendation:** Run a price-cost review per category and introduce discount guardrails (see R1, R2).
- **Expected outcome:** Recover 1–1.5 points of margin in FY2026 without hurting volume.

### 2. Electronics: biggest category, weakest economics
- **Finding:** Electronics is 19.3% of revenue but only 5.9% of gross profit (Q03).
- **Evidence:** 2025 Electronics revenue +14.6% (£767K → £879K), but gross profit −13% (£114K → £99K), and margin
  14.9% → 11.3%. The break-even discount is **18.7%** (Q36); lines discounted 20%+ made a **−£24.7K** gross loss in 2025.
  All 12 weakest-margin products are Electronics (Q06).
- **Possible cause:** Thin supplier margins plus blanket promotional discounts that ignore category margin.
- **Business impact:** The fastest-selling Electronics lines (e.g. over-ear headphones, kids' tablet) sell volume at
  close to zero profit.
- **Recommendation:** Cap Electronics promotions at 15%; renegotiate with suppliers or delist products under 10% margin.
- **Expected outcome:** About +£28K gross profit a year from the cap alone (illustrative, see R1).

### 3. Deep discounts don't pay
- **Finding:** Margin falls to 18.4% at 30–35% discount and **5.6% at 40%+** (Q09).
- **Evidence:** In 2025, lines discounted 30%+ produced £406K revenue but only £56K gross profit, after giving away
  £225K of discount. Black Friday week runs at 30.1% margin and the January sale at 31.3%, vs 44.7% in regular
  trading (Q20).
- **Possible cause:** The same discount depth is applied to every category, regardless of each category's
  break-even point.
- **Business impact:** Sale periods drive volume but not profit.
- **Recommendation:** Set category-specific maximum discounts (Electronics 15%, Home/Sports/Toys 30%,
  Clothing/Footwear 40%, Beauty/Accessories 50%).
- **Expected outcome:** Higher sale-period margin; measure with an A/B test in the January 2026 sale.

### 4. Online returns are rising and eat online profit
- **Finding:** Online return rates are 12.2–12.5% vs 4.5% in store (2025, Q16).
- **Evidence:** After refunds, website margin drops from 40.1% to **28.3%** vs 39.3% in store (Q38). Online
  clothing & footwear return rate rose from about 16% (2024) to 27–28% (H2 2025) (Q39, `06_online_apparel_return_trend.png`).
- **Possible cause:** Customers ordering several sizes ("bracketing"), plus one supplier's sizing problem (Insight 5).
- **Business impact:** Online apparel refunds nearly doubled: £83K → £160K.
- **Recommendation:** Add size guidance and fit notes on product pages, and flag customers who habitually return
  most of what they order.
- **Expected outcome:** Every 3 points off the online apparel return rate saves about £20K a year in refunds.

### 5. One footwear supplier explains most of the return spike
- **Finding:** Stride Lab's return rate jumped from **10.2% to 28.2%** (Q19); other brands rose by less than 4 points.
- **Evidence:** 83% of Stride Lab's 2025 returns give "wrong size / fit" as the reason; all 5 products with a unit
  return rate above 25% in Q18 are Stride Lab or Voltix.
- **Possible cause:** A sizing or last change at the supplier in 2025.
- **Business impact:** 2025 Stride Lab refunds were £61K vs £22K expected at the 2024 rate.
- **Recommendation:** Raise it with the supplier immediately, add a "runs small" note, and claim credit for defective stock.
- **Expected outcome:** Up to about £39K a year in refunds avoided if the rate returns to 2024 levels.

### 6. A faulty smart-home range
- **Finding:** Voltix smart-home devices have a ~22% return rate vs 6.1% for other smart-home brands.
- **Evidence:** Q18 (doorbell 30%, camera 29%, smart bulb 25.5% of units returned). In Electronics, 53% of returns
  give "faulty / defective" as the reason (Q17).
- **Possible cause:** Product quality.
- **Business impact:** About £14K a year in refunds, plus customer dissatisfaction.
- **Recommendation:** Quality claim to the supplier, and pause the range until it is fixed.
- **Expected outcome:** Refunds fall to about the category norm (about £10K a year saved) and fewer complaints.

### 7. Two stores sit far below the pack
- **Finding:** Bluewater Outlet runs at a 24.7% margin and Newcastle Eldon Square at 37.0%. Every other store is at 43–45% (Q14).
- **Evidence:** Newcastle's average discount is 15.3%, three times the store average (about 5%), even though it is a
  full-price store. The North East region's low margin (38.6%) is entirely this one store (Q08).
- **Possible cause:** Local promotions run without central approval. The outlet's low margin is by design.
- **Business impact:** Newcastle gave up about £6K gross profit in 2025 vs the peer discount rate.
- **Recommendation:** Require central sign-off for local discounts and review Newcastle's promotion calendar.
  Assess whether the outlet is still worth its role.
- **Expected outcome:** Newcastle margin moves toward the peer level of about 43%.

### 8. Growth is digital; stores are flat like-for-like
- **Finding:** Like-for-like stores grew 5.3%; the online hub grew 29% (Q33).
- **Evidence:** Mobile App +49%, Website +22%, Click & Collect +24%, In-Store +4% (Q04).
- **Possible cause:** Customers shifting to app shopping.
- **Business impact:** Headline growth (+15.7%) overstates store health; online growth carries higher return costs.
- **Recommendation:** Keep investing in the app but track **margin after returns** per channel as the KPI, not
  revenue alone. Always report LFL.
- **Expected outcome:** Channel decisions are based on profit, not sales.

### 9. A loyal core, with a valuable group drifting away
- **Finding:** 14% of customers generate 50% of known-customer revenue, and 38% generate 80% (Q32).
- **Evidence:** RFM (Q35): Champions are 23% of customers and 55% of revenue. **1,450 "At risk" customers** (formerly
  loyal, average 7.7 orders) account for 14.6% of revenue but haven't bought for about 8 months on average.
- **Possible cause:** Normal churn; nothing currently prompts them to come back.
- **Business impact:** Losing them means losing a large share of repeat revenue.
- **Recommendation:** Targeted win-back campaign, and a loyalty offer for Champions.
- **Expected outcome:** Reactivating 15% of 850 high-frequency lapsed customers is worth about £16K gross profit (R7).

### 10. A third of store sales are anonymous
- **Finding:** 32–34% of in-store revenue (£686K in 2025) has no customer attached (Q23).
- **Evidence:** It is consistent across every store, so it is a process gap rather than a local issue.
- **Possible cause:** Loyalty card not scanned / no incentive to identify at the till.
- **Business impact:** These shoppers cannot be marketed to, analysed or retained.
- **Recommendation:** Offer e-receipts and a points prompt at the till; set a target of 75% identified sales.
- **Expected outcome:** Better customer data. The benefit is mostly enabling (it improves insight 9), not direct cash.

---

## Data caveats (said upfront, as in a real engagement)
- **Gross profit only:** no overheads, staff, marketing or delivery costs.
- **Refunded goods are assumed not resold**, which is conservative. If some are resold, the cost of returns is lower.
- **Return lag:** December 2025 orders have not had time to be returned, so recent return rates are understated.
- **Data window:** the data starts in January 2024, so "new customers" in Q1 2024 includes existing customers.
- **Synthetic data:** patterns were designed to be realistic, but they are not observations of a real business.
