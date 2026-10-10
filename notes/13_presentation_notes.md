# Notes 13 — Executive Presentation & Storytelling (Phase 13)

**File:** `presentation/NorthStar_Executive_Presentation.pptx` (10 slides, built by `scripts/06_build_presentation.py`)

## In one line
Executives want the answer first, then the evidence, then what to do. Ten slides, about 8 minutes.

## Storytelling rules used
1. **Headline = the message**, not the topic. Not "Sales by channel" but "Growth is digital; stores are flat like-for-like".
2. **One idea per slide**, one or two charts maximum.
3. **Pyramid principle:** answer first (slide 1 gives the tension: revenue up, profit not), then supporting evidence.
4. **Numbers with context:** "+15.7% vs 2024", not "£4.58M".
5. **End with actions, owners and timing** (30/60/90 days).

## Slide-by-slide script (what to say)
| # | Slide | Say this (≈ 45 seconds each) |
| --- | --- | --- |
| 1 | Problem | "Revenue grew 15.7%, but gross profit only 9.4%. Leadership had four reports that disagreed, so nobody could say why." |
| 2 | Objectives | "Six objectives: one source of truth, where profit is lost, discount cost, returns, customers, actions." |
| 3 | Data | "185,000 order lines, two years, cleaned into a star schema in PostgreSQL and Power BI." |
| 4 | Data quality | "The data was messy: 14 channel spellings, duplicates, impossible dates. 40 documented rules took validity from 92% to 100%." |
| 5 | Sales | "Growth is digital: app +49%. Like-for-like stores only +5%." |
| 6 | Profitability | "Margin fell 2.4 points: 1.6 from costs not passed on, 0.8 from discounting. Electronics loses money above a ~19% discount." |
| 7 | Customers | "A loyal core: 14% of customers give half the revenue. But 1,450 formerly loyal customers have gone quiet." |
| 8 | Returns | "Online apparel returns rose from 16% to 27%, mostly one supplier with a sizing problem." |
| 9 | Insights | "Five things to remember." (read the five headlines) |
| 10 | Recommendations | "Start with quick wins: discount guardrails, supplier action, win-back. About £120–140K gross profit a year, illustrative." |

## Handling questions
- **"Is this real?"** "No, it's a simulated company with synthetic data. The methods are what I'd use on real data."
- **"How sure are you?"** Point to the assumptions and suggest a test (pilot discount caps in one region).
- **"What would you do next?"** Inventory data, a forecast, an A/B test of discount caps, automated monthly refresh.

## Common mistakes
- Reading the slide word for word.
- Too many numbers on one slide.
- Ending without a clear ask ("approve the discount guardrails pilot").
