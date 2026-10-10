# Final Quality Check (from the project brief)

An honest self-assessment, the weak areas, and what was done or still needs doing about each.

| Area | Score /10 | Why | Improvement |
| --- | :-: | --- | --- |
| Business realism | 8 | UK regions, real-world patterns (Black Friday, new store, guest shoppers, supplier issues), item-level prices | Data is still synthetic; say so every time |
| SQL | 9 | 40 questions from basics to cohorts/RFM, constraints, 13 automated checks, every result interpreted | Add `EXPLAIN ANALYZE` examples |
| Power BI | 6 → 8 once built | Full build guide, theme, measures, mockups, **but no .pbix yet** | **Build the .pbix and replace mockups with real screenshots (top priority)** |
| Data modelling | 9 | Grain, surrogate keys, unknown member, role-playing date, no ambiguous paths, GDPR minimisation | SCD Type 2 example as a stretch |
| Business insight | 9 | 10 insights in the Finding → Outcome format, margin decomposition, quantified with assumptions | Validate one recommendation with an A/B design write-up |
| BA relevance | 8 | Problem statement, stakeholders, SMART objectives, KPI definitions, prioritisation | Add a short requirements/user-story list per page |
| Portfolio quality | 8 | Clear README, reproducible pipeline, documented decisions, deck | Real dashboard screenshots + a 2-minute video walkthrough |
| Interview value | 9 | Notes for each phase, 50-question bank with follow-ups, STAR stories from real bugs | Practise out loud with someone |
| UK job relevance | 9 | UK retail, UK financial year, bank holidays, GDPR, £, the SQL + Power BI + Excel stack UK adverts ask for | — |
| AI-dependency risk | 6 | Much of the code was AI-assisted | **Re-type the key SQL and DAX yourself, build the .pbix by hand, and be able to explain every line**. Interviewers will test this |

## Action list for the candidate (in order)
1. Build the Power BI report following `powerbi/01_build_guide.md`; reconcile totals; take real screenshots.
2. Re-write 10 SQL queries and 10 DAX measures from memory.
3. Practise `notes/15_project_explained_simply.md` until you can say it naturally.
4. Do the practice tasks at the end of each notes file.
5. Put the project in its own GitHub repository with the real screenshots, then add the CV bullets and LinkedIn post.
