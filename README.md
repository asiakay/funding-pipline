# EQORE Funding Pipeline

## How to Run
```bash
pip install -r requirements.txt
python src/pipeline.py
```

The pipeline will attempt to download the latest funding opportunities from
the Grants.gov `search2` API (``https://www.grants.gov/api/common/search2``).
If the download fails (e.g., no network access), it will fall back to the
previously cached `data/master.csv` file.

## Outputs
- outputs/CleanTable.csv
- outputs/Dirty.csv
- outputs/OutOfScope.csv
- outputs/Master_Scored.csv
- outputs/EQORE_Deck.pptx (top 50 opportunities)
# funding-pipline
