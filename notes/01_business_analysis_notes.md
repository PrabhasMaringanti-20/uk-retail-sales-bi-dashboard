# Notes 01 — Business Analysis (Phase 1)

**File built:** `business-analysis/01_business_case.md`

## In one line
Before touching data, we write down **what problem the business has, who cares, and what "success" looks like**.

## Simple explanation
Imagine a shop owner who gets 4 different reports every Monday and all show different numbers.
They don't know which one to trust. Our job is not "make a pretty chart". Our job is:
1. Understand the **problem** (numbers don't agree, profit is unclear).
2. Decide **what we will measure** (KPIs) and define each one clearly.
3. Decide **what we will NOT do** (out of scope), so the project finishes.

## Key topics

### 1. Problem statement
- One short paragraph saying what is wrong and why it matters.
- Ours: revenue is growing, but leadership can't see where profit is lost (margins, discounts, returns, weak stores).
- **Why it matters:** every later step (SQL, dashboard) must answer this problem. If a chart doesn't help, remove it.

### 2. SMART objectives
- **S**pecific, **M**easurable, **A**chievable, **R**elevant, **T**ime-bound.
- Bad: "Improve reporting". Good: "All dashboard KPIs reconcile to the database within 0.1%".

### 3. Scope / Out of scope
- Scope = what we deliver. Out of scope = what we deliberately skip, **with a reason**.
- We skipped inventory, marketing spend and overheads. So we measure **gross profit**, not net profit.
- **Interview tip:** saying what you left out (and why) shows maturity.

### 4. Stakeholders and the stakeholder map
- Stakeholder = anyone affected by or interested in the project.
- **Influence vs Interest grid** (Mendelow's matrix):
  - High influence + high interest → *manage closely* (CEO, CFO)
  - High influence + low interest → *keep satisfied* (IT)
  - Low influence + high interest → *keep informed* (customer service)
  - Low/low → *monitor*
- Different stakeholders need different pages: the CEO wants the summary, store managers want their store.

### 5. KPI definitions
- The most important part of Phase 1. **Same word must mean the same number everywhere.**
- Revenue = Gross Sales − Discount. Gross Profit = Revenue − Cost. Margin % = Profit ÷ Revenue.
- AOV (Average Order Value) = Revenue ÷ number of orders (not ÷ number of lines!).
- Return rate here uses **value** (refund £ ÷ revenue £). You could also use units or orders. Pick one and write it down.

### 6. Assumptions and constraints
- Assumption = something we accept as true without proof (e.g. prices exclude VAT).
- Constraint = a limit we must work within (e.g. no new tools, CSV-only data).
- Writing them down protects you: if an assumption is wrong, everyone knows which numbers change.

## Why this phase matters for a job
Data Analyst / BI / Business Analyst roles in the UK all ask: *"How do you gather requirements?"*
This phase is your answer.

## Interview questions and model answers

**Q: What business problem did your project solve?**
A: NorthStar (a fictional UK retailer I simulated) had four disconnected reports that disagreed. Revenue was growing, but leadership couldn't see where profit was lost. I built one source of truth: a cleaned database, a star-schema model and a Power BI dashboard, plus prioritised recommendations on discounts, returns and weak stores.

**Q: How did you decide which KPIs to show?**
A: I started from stakeholder questions, not from the data. The CFO cares about margin and discount cost, Operations about store league tables, Customer Service about return reasons. I defined each KPI in writing (for example, AOV = revenue ÷ distinct orders) so SQL and Power BI give the same number.

**Q: What was out of scope and why?**
A: Inventory, marketing spend and overheads, because there was no reliable data for them. So I report gross profit, not net profit, and say so clearly.

**Q: Who were the stakeholders and how would you manage them?**
A: Use the influence/interest grid. Manage the CEO and CFO closely, keep IT satisfied, keep Customer Service and store managers informed.

**Q (follow-up trap): Is this real company data?**
A: No. It's a simulated project with synthetic data I generated with realistic patterns. I always say that upfront. Be honest; interviewers respect it.

## Common mistakes to avoid
- Starting with the dashboard before knowing the question.
- Defining revenue differently in SQL and Power BI.
- Claiming fake business impact ("I saved £2M"). Never do this.
