# Portfolio Case Study, CV Bullets & LinkedIn Post (Phase 15)

> Everything below is truthful: it describes a **simulated** project and claims no real company, employer or financial result.

## Portfolio case study (for a personal website or GitHub)

### UK Retail Sales & BI Dashboard: why profit lagged revenue at a simulated UK retailer
**Role:** solo, end to end (business analysis → data engineering → SQL → Power BI → recommendations)
**Tools:** PostgreSQL, SQL, Python (pandas), Excel, Power Query, Power BI, DAX, Git/GitHub
**Data:** synthetic, 185,858 order lines, 89,528 orders, 12,500 customers, 1,220 products, 24 stores + online, Jan 2024 – Dec 2025

**The problem.** NorthStar Retail UK (fictional) received four disconnected reports that disagreed. Revenue was growing,
but leadership could not see where profit was being lost.

**What I did**
1. Wrote the business case: problem statement, stakeholder map, SMART objectives and agreed KPI definitions.
2. Generated realistic data with designed patterns (seasonality, channel shift, cost inflation, supplier issues), then
   injected 37 types of data-quality problems.
3. Cleaned it with 40 documented rules (fix / flag / quarantine). Sales validity went from 91.7% to 100%, with 0.05% of
   rows quarantined and the result proven against an answer key.
4. Modelled a star schema (2 facts, 6 dimensions) in PostgreSQL with PK/FK/CHECK constraints and 13 automated quality checks.
5. Answered 40 business questions in SQL: window functions, cohorts, RFM, break-even discount, margin decomposition.
6. Designed a 5-page Power BI report with 50 DAX measures (time intelligence, USERELATIONSHIP, RANKX).
7. Wrote 10 insights and 10 prioritised recommendations with an impact/effort matrix and an executive deck.

**What I found**
- Revenue +15.7% but gross profit only +9.4%; margin −2.4 pts (−1.6 cost inflation, −0.8 discounting).
- Electronics: 19% of revenue, 6% of profit; it sells below cost at discounts above ~19%.
- Online apparel returns rose from ~16% to ~27%, mostly one footwear brand with a sizing problem.
- 14% of customers generate 50% of revenue; 1,450 formerly loyal customers are at risk.

**Recommendations:** category discount guardrails, supplier action on sizing and faulty products, a win-back campaign
and like-for-like reporting. Illustrative benefit ≈ £120–140K gross profit a year under stated assumptions.

**What I learned:** defining grain and KPIs first prevents most errors; constraints and automated checks caught bugs in
my own code; and a recommendation is only credible when its assumptions are written down.

---

## CV bullets (pick 2–3; all truthful)

**Projects: UK Retail Sales & BI Dashboard (simulated data) | SQL, PostgreSQL, Power BI, DAX, Excel, Python**
- Built an end-to-end retail analytics solution on 185K synthetic transactions: cleaned the data with 40 documented
  validation rules (validity 92% → 100%), modelled a star schema in PostgreSQL, and delivered a 5-page Power BI dashboard
  with 50 DAX measures.
- Wrote 40 SQL analyses (window functions, CTEs, cohort retention, RFM segmentation) that traced a 2.4-point margin decline
  to discounting and cost inflation, and identified that Electronics sold below cost at discounts above 19%.
- Translated findings into 10 prioritised recommendations using an impact/effort matrix and stated benefit assumptions,
  presented in a 10-slide executive deck.

*(Under "Projects", not "Experience". Never write "increased profit by…": the project is simulated.)*

---

## LinkedIn post (draft)

> 📊 **New portfolio project: why was a retailer's profit growing slower than its sales?**
>
> I built an end-to-end BI project for a *simulated* UK retailer (synthetic data, fictional company) to practise the full
> analyst workflow, not just a dashboard.
>
> What I did:
> 🔹 Framed the business problem and agreed KPI definitions first
> 🔹 Cleaned 186K messy records with 40 documented rules (duplicates, 14 spellings of 4 channels, impossible dates…)
> 🔹 Modelled a star schema in PostgreSQL and wrote 40 SQL analyses, from GROUP BY to cohort retention and RFM
> 🔹 Built a Power BI report with DAX time intelligence
> 🔹 Turned it into prioritised recommendations with an impact/effort matrix
>
> The headline: revenue +15.7%, gross profit only +9.4%. Electronics was 19% of sales but 6% of profit, and lost money
> on every sale discounted more than ~19%.
>
> Biggest lesson: automated data checks caught bugs in *my own* code, not just in the data.
>
> Repo, SQL and dashboard screenshots: [link]
> Feedback from analysts and hiring managers very welcome!
>
> #DataAnalytics #PowerBI #SQL #BusinessIntelligence #DataAnalyst #PortfolioProject
