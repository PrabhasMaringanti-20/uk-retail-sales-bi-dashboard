# Notes 11 — Business Insights & Decision Support (Phases 11 and 12)

**Files:** `insights/01_insight_report.md`, `insights/02_recommendations.md`, `screenshots/11_impact_effort_matrix.png`

## In one line
Charts aren't the goal. The goal is **decisions**: what's happening, why, how much it costs, and what to do.

## The insight formula (use it for every finding)
**Finding → Evidence → Possible cause → Business impact → Recommendation → Expected outcome**

Example (Insight 5):
- **Finding:** One footwear brand's return rate jumped.
- **Evidence:** Stride Lab 10.2% → 28.2% (SQL Q19); 83% of its 2025 returns say "wrong size / fit".
- **Possible cause:** A sizing change at the supplier in 2025.
- **Impact:** £61K refunds in 2025 vs £22K expected at the old rate.
- **Recommendation:** Supplier meeting, a "runs small" note on product pages, a credit claim.
- **Expected outcome:** Up to ~£39K a year of refunds avoided.

Notice "**possible** cause". The data shows *what*; the cause is a hypothesis to confirm with the business.
Saying this in an interview shows maturity.

## The 10 insights in one line each
1. Profit +9.4% vs revenue +15.7%; margin −2.4 pts (cost −1.6, discount −0.8).
2. Electronics: 19% of revenue, 6% of profit; 2025 profit −13% despite +14.6% revenue.
3. Deep discounts (30%+) give little profit: 18% margin at 30–35%, 6% at 40%+.
4. Online returns 2.5–3× store returns and rising; website margin after refunds 28% vs 39% in store.
5. Stride Lab sizing problem (10% → 28% returns).
6. Voltix smart-home fault (22% returns vs 6% for other brands).
7. Newcastle discounts like an outlet (15% vs ~5%); the outlet's low margin is by design.
8. Growth is digital (app +49%); like-for-like stores only +5.3%.
9. 14% of customers = 50% of revenue; 1,450 "at risk" customers hold 14.6% of revenue.
10. A third of in-store revenue is anonymous (guests).

## Decision support tools
### Impact vs Effort matrix
```
 High impact │ QUICK WINS        │ MAJOR PROJECTS
             │ R1 R3 R7          │ R2 R4 R8 R9
 ────────────┼───────────────────┼──────────────
 Low impact  │ FILL-INS          │ DEPRIORITISE
             │ R5 R6             │ R10
               Low effort          High effort
```
Do quick wins first: they build trust and fund the bigger projects.

### Prioritisation criteria
- **Impact:** profit effect.
- **Effort:** time/cost/complexity.
- **Urgency:** is it getting worse? (Stride Lab returns are rising → high.)
- **Risk:** could it backfire? (Discount caps might reduce volume → test first.)

### Benefit estimates: always show the assumptions
Example R1: "Electronics lines at 20%+ discount made −£24.7K gross profit in 2025. If capped at 15% and we lose 30% of
those units, gross profit becomes +£3.2K, so the benefit is ≈ £28K."
**Assumptions are written down, so anyone can challenge or change them.** Never present an estimate as a fact.

Total of costed actions ≈ £120–140K gross profit a year (≈ 6–7% of 2025 gross profit). Illustrative, based on simulated data.

## Interview questions

**Q: What was your most important insight?**
A: That profit grew much more slowly than revenue: +9.4% vs +15.7%. I broke the 2.4-point margin fall into two parts:
about 1.6 points from supplier costs rising faster than prices, and 0.8 from more discounting. That moved the
conversation from "sell more" to "protect margin", especially in Electronics, where discounts over about 19% sell below cost.

**Q: How did you prioritise recommendations?**
A: I scored each on impact, effort, urgency and risk, then plotted impact vs effort. Discount guardrails and the
Stride Lab supplier fix are quick wins: high impact, low effort, worsening problems.

**Q: How confident are you in the £ benefits?**
A: They're illustrative estimates with stated assumptions, such as 30% volume loss when discounts are capped. In a
real business, I'd validate with an A/B test, for example capping discounts in some regions only and comparing.

**Q: Correlation vs causation?**
A: The data shows that Newcastle has high discounts and low margin. That discounting *causes* the low margin is a
strong hypothesis (the store sells the same products as its peers), but I'd confirm with the store manager before acting.

## Common mistakes
- Describing charts ("sales went up in December") instead of insights.
- Recommendations without numbers, or numbers without assumptions.
- Claiming real financial impact from a portfolio project.
