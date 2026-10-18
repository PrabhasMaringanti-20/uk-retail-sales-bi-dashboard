# scripts/

| File | What it does | Explain in interviews? |
| --- | --- | --- |
| `01_generate_data.py` | Creates 2 years of realistic pretend sales (with planted business patterns) | One sentence |
| `02_inject_quality_issues.py` | Breaks the data in 37 counted ways, to test the cleaning | One sentence |
| `03_clean_data.py` | Cleans the data with 40 logged rules and builds the star schema | **Yes**: the rules and why |
| `run_pipeline.sh` | Runs 01 → 02 → 03 → loads PostgreSQL → zips the data (Mac/Linux) | No |
| `helpers/` | Tools that only **build output files**: charts, Excel workbook, slides, Power BI project | No, just know what each makes |

Run order on Windows (from the project folder):
```
python scripts\01_generate_data.py
python scripts\02_inject_quality_issues.py
python scripts\03_clean_data.py
python scripts\helpers\build_charts.py
python scripts\helpers\build_excel.py
python scripts\helpers\build_presentation.py
python scripts\helpers\build_powerbi_project.py
```
See `../CODE_GUIDE.md` for how to read each file.
