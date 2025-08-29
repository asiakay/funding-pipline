"""One-command wrapper: fetch → scoring master.

Usage:
    python -m src.prepare_master "energy" [--status posted] [--agency NSF] [--max 100]

Writes a raw fetch (auto-named) and a scoring master (default data/master.csv).
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import re

import pandas as pd

from src.fetch_grants import fetch_grants, to_summary_table  # type: ignore
from src.make_scoring_template import make_scoring_template  # type: ignore


logger = logging.getLogger(__name__)


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Fetch from Grants.gov and prepare a scoring master")
    p.add_argument("keyword", help="search keyword, e.g. 'energy efficiency'")
    p.add_argument("--max", type=int, default=50, help="maximum records to pull")

    # Filters passthrough (normalized inside fetch_grants)
    p.add_argument("--status", help="statuses, e.g. posted,forecasted,closed,archived")
    p.add_argument("--agency", help="agency or sub-agency codes, comma or pipe separated")
    p.add_argument("--cfda", help="CFDA codes, comma separated")
    p.add_argument("--eligibility", help="eligibility codes, comma separated")
    p.add_argument("--instrument", help="funding instrument codes (G,CA,O,PC)")
    p.add_argument("--category", help="funding category codes (e.g., EN,ST,...)")
    p.add_argument("--sort", help="sort key if supported by API")

    # Output controls
    p.add_argument("--master-out", default="data/master.csv", help="path for scoring master")
    p.add_argument("--raw-out", default=None, help="path for raw fetch; auto-named if omitted")
    p.add_argument("--summary", action="store_true", help="fetch curated summary columns instead of raw")
    p.add_argument("--debug", action="store_true", help="enable verbose logging")
    args = p.parse_args(argv)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        logger.debug("Debug logging enabled")

    slug = _slug(args.keyword)
    raw_out = args.raw_out
    if raw_out is None:
        raw_out = f"data/grants_{'summary_' if args.summary else 'raw_'}{slug}.csv"
    raw_path = Path(raw_out)
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    # Fetch
    df = fetch_grants(
        args.keyword,
        args.max,
        status=args.status,
        agency=args.agency,
        cfda=args.cfda,
        eligibility=args.eligibility,
        instrument=args.instrument,
        category=args.category,
        sort=args.sort,
    )
    if args.summary:
        df = to_summary_table(df, enrich=False)

    # Write raw (CSV or TSV based on extension)
    ext = raw_path.suffix.lower()
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    df.to_csv(raw_path, index=False, sep=sep)
    print(f"Wrote raw fetch with {len(df)} rows to {raw_path}")

    # Make scoring master
    master_path = Path(args.master_out)
    master_path.parent.mkdir(parents=True, exist_ok=True)
    templ = make_scoring_template(raw_path)
    # Respect output extension for delimiter
    mext = master_path.suffix.lower()
    msep = "\t" if mext in {".tsv", ".tab"} else ","
    templ.to_csv(master_path, index=False, sep=msep)
    print(f"Wrote scoring master with {len(templ)} rows to {master_path}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()

