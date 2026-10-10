#!/usr/bin/env bash
# Rebuild everything from scratch: generate -> break -> clean -> load PostgreSQL -> package.
# Usage (from the project root):  bash scripts/run_pipeline.sh
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/01_generate_data.py
python scripts/02_inject_quality_issues.py
python scripts/03_clean_data.py > /dev/null
echo "Clean star schema written to data/clean/"

if command -v psql >/dev/null && psql -d northstar -c "select 1" >/dev/null 2>&1; then
  psql -d northstar -q -f sql/01_create_schema.sql
  psql -d northstar -f sql/02_load_data.sql
  psql -d northstar -f sql/03_data_quality_checks.sql
else
  echo "PostgreSQL database 'northstar' not found - skipping load (run: createdb northstar)"
fi

# Zipped copies so the repo stays small but the data is one download away
rm -f data/raw_data.zip data/clean_data.zip
python - <<'PY'
import zipfile, pathlib
for name in ("raw", "clean"):
    src = pathlib.Path("data") / name
    with zipfile.ZipFile(f"data/{name}_data.zip", "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(src.glob("*.csv")):
            z.write(f, f"{name}/{f.name}")
    print(f"data/{name}_data.zip", round(pathlib.Path(f"data/{name}_data.zip").stat().st_size / 1e6, 1), "MB")
PY
