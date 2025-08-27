# EQORE Funding Pipeline

## How to Run
```bash
pip install -r requirements.txt
python -m src.pipeline [--deck] [--pdf]
```

The script reads `data/master.csv`, scores each opportunity, and
splits the results into Clean, Dirty, and Out‑of‑Scope tables under the
`outputs/` folder. Use `--deck` to build a PowerPoint deck and
`--pdf` for a simple one‑pager PDF of the top opportunities.

## Outputs
- `outputs/CleanTable.csv`
- `outputs/DirtyTable.csv`
- `outputs/OutOfScope.csv`
- `outputs/Master_Scored.csv`
- `outputs/Tables.xlsx`
- `outputs/EQORE_Deck.pptx` (with `--deck`)
- `outputs/OnePager.pdf` (with `--pdf`)
