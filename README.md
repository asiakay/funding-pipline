# EQORE Funding Pipeline
Overview
- Purpose: Fetch funding opportunities, prepare a scoring master, triage and score, and export clean/dirty/out-of-scope tables (plus an Excel workbook and optional deck/PDF).
- Sources: Grants.gov Search API with useful filters and a curated summary export.

Key Scripts
- `src/fetch_grants.py`: Fetches opportunities; supports filters and summary output.
- `src/make_scoring_template.py`: Creates a scoring-ready master from a fetched CSV/TSV.
- `src/triage_and_score.py`: Splits, filters, and scores opportunities.
- `src/pipeline.py`: Orchestrates the scoring pipeline and writes outputs.
- `src/prepare_master.py`: One-command wrapper that fetches and prepares the scoring master.
- Optional builders: `src/build_deck.py`, `src/build_pdf.py` (if present).

Install
- Python: 3.10+ recommended
- Setup:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`

Quick Start
- One-command prep: `python -m src.prepare_master "energy"`
  - Produces `data/master.csv` ready for scoring (and keeps the raw fetch).
- Edit `data/master.csv`: Fill `Relevance`, `EQORE Fit`, `Ease of Use`, `Match %`.
- Run pipeline: `python -m src.pipeline`

Typical Workflow
- Narrowed fetch (with filters): `python src/fetch_grants.py "energy" --agency DOE-ARPAE --status posted --max 100`
- Use summary mode (curated columns): `python src/fetch_grants.py "energy" --summary --outfile data/grants_summary_energy.tsv`
- Create scoring master: `python src/make_scoring_template.py data/grants_summary_energy.tsv --outfile data/master_energy.csv`
- Score + export: `python -m src.pipeline --input data/master_energy.csv --deck --pdf`

CLI Reference
- `src/prepare_master.py`
  - `keyword`: free-text search term
  - `--max`: page size (maps to API `rows`)
  - Filters passthrough: `--status`, `--agency`, `--cfda`, `--eligibility`, `--instrument`, `--category`, `--sort`
  - `--master-out`: output path for scoring master (default `data/master.csv`)
  - `--raw-out`: where to write fetched raw file (auto-named if omitted)
  - `--summary`: fetch curated columns instead of raw
  - `--debug`: verbose logs
- `src/fetch_grants.py`
  - `keyword` (positional): free-text search term
  - `--max`: page size (maps to API `rows`)
  - `--status`: posted|forecasted|closed|archived (comma/space/pipe accepted)
  - `--agency`: agency/sub-agency codes (e.g., `DOE-ARPAE,NSF`)
  - `--cfda`, `--eligibility`, `--instrument`, `--category`, `--sort`
  - `--outfile`: default auto-names `data/grants_raw_{keyword}.csv`
  - `--summary`: write curated columns; `--enrich` tries Award Ceiling from detail page
  - `--debug`: verbose logs
- `src/make_scoring_template.py`
  - `input`: CSV/TSV from fetch
  - `--outfile`: default `data/master.csv` (or `data/master_{stem}.csv`)
- `src/pipeline.py`
  - `--input`: path to master (default `data/master.csv`)
  - `--deck`, `--pdf`: optional exports

Data Flow
- Fetch → `data/grants_raw_{keyword}.csv` (or `.tsv`)
  - Link format: `https://www.grants.gov/search-results-detail/{oppId}`
  - TSV avoids “clicking grabs comma” issues in plain text viewers
- Make scoring master → `data/master.csv` (or custom name)
  - Ensures columns: `Grant Name`, `Sponsor`, `Link`, `Deadline`, `Relevance`, `EQORE Fit`, `Ease of Use`, `Match %`
- Pipeline → outputs
  - `outputs/CleanTable.csv`, `outputs/DirtyTable.csv`, `outputs/OutOfScope.csv`
  - `outputs/Master_Scored.csv`
  - `outputs/Tables.xlsx` (sheets: Clean, Dirty, OutOfScope)
  - Optional: `outputs/EQORE_Deck.pptx`, `outputs/OnePager.pdf`

Scoring Logic
- Expected columns: `Relevance`, `EQORE Fit`, `Ease of Use` (0–5 scale), optional `Match %`
- Weighted score: `Relevance × EQORE Fit × (Ease of Use / 5)`
- Fatal filters (to Dirty):
  - Deadline passed
  - Match % ≥ 33
  - Missing `Grant Name`/`Sponsor`/`Link`
- Out-of-scope: `Relevance == 0`
- Clean: Not fatal and relevance > 0; ranked with `Rank`

File References
- `src/fetch_grants.py:57`: API fetch + filters
- `src/fetch_grants.py:40`: Row mapping and link format
- `src/make_scoring_template.py:1`: Scoring master generation
- `src/triage_and_score.py:19`: Scoring and triage
- `src/pipeline.py:9`: Orchestration and outputs
- `src/prepare_master.py:1`: One-command fetch → template

Tips
- Use `.tsv` outputs when you want clickable URLs in text editors.
- For Grants.gov API quirks: response data may be nested under `data.oppHits` (handled).
- Pandas Excel: Sheets are written via `openpyxl`; sheet names are explicit.

Troubleshooting
- No input file: Create `data/master.csv` with `src/make_scoring_template.py` or `src/prepare_master.py`.
- Wrote 0 rows: Ensure `--status`/filters aren’t too restrictive; verify API returned `data.oppHits`.
- Deadlines not parsed: Use ISO `YYYY-MM-DD`.
- URL clicks include comma: Prefer `.tsv` or open CSV in Excel/Sheets.
## How to Run
```bash
pip install -r requirements.txt
```

- `outputs/DirtyTable.csv`
- `outputs/OutOfScope.csv`
- `outputs/Master_Scored.csv`
- `outputs/Tables.xlsx`
- `outputs/EQORE_Deck.pptx` (with `--deck`)
- `outputs/OnePager.pdf` (with `--pdf`)
