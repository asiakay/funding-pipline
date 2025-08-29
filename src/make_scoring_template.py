"""Create a scoring template from a fetched Grants.gov CSV/TSV.

Reads an input file (raw or summary from fetch_grants), ensures the pipeline's
required columns exist, adds scoring columns (blank), and writes the result.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import pandas as pd


PREFERRED_ORDER = [
    "Grant Name",
    "Sponsor",
    "Link",
    "Open Date",
    "Deadline",
    "Status",
    "Relevance",
    "EQORE Fit",
    "Ease of Use",
    "Match %",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common alternative headers to what the pipeline expects."""
    rename_map: Dict[str, str] = {}

    # Summary-mode to raw column header mappings
    if "Grant name" in df.columns and "Grant Name" not in df.columns:
        rename_map["Grant name"] = "Grant Name"
    if "Sponsor org" in df.columns and "Sponsor" not in df.columns:
        rename_map["Sponsor org"] = "Sponsor"
    if "App deadline" in df.columns and "Deadline" not in df.columns:
        rename_map["App deadline"] = "Deadline"

    # Occasionally alternative casing/spaces slip in
    if "OpenDate" in df.columns and "Open Date" not in df.columns:
        rename_map["OpenDate"] = "Open Date"
    if "Close Date" in df.columns and "Deadline" not in df.columns:
        rename_map["Close Date"] = "Deadline"

    if rename_map:
        df = df.rename(columns=rename_map)
    return df


def make_scoring_template(inp: Path) -> pd.DataFrame:
    """Load input and return a frame with scoring columns added (blank)."""
    sep = "\t" if inp.suffix.lower() in {".tsv", ".tab"} else ","
    df = pd.read_csv(inp, sep=sep)

    df = normalize_columns(df)

    # Ensure required fields exist even if empty, so users can fill them in
    for col in ["Grant Name", "Sponsor", "Link", "Deadline"]:
        if col not in df.columns:
            df[col] = ""

    # Add scoring columns if missing
    for col in ["Relevance", "EQORE Fit", "Ease of Use", "Match %"]:
        if col not in df.columns:
            df[col] = ""

    # Reorder columns: preferred order first, then the rest
    front = [c for c in PREFERRED_ORDER if c in df.columns]
    rest = [c for c in df.columns if c not in front]
    df = df[front + rest]
    return df


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Create a funding scoring template from fetched data")
    parser.add_argument("input", help="path to fetched CSV/TSV from fetch_grants")
    parser.add_argument(
        "--outfile",
        help="output path (defaults to data/master.csv or based on input name)",
        default=None,
    )
    args = parser.parse_args(argv)

    inp = Path(args.input)
    if args.outfile is None:
        # Default to data/master.csv, or master_{stem}.csv if multiple
        stem = inp.stem
        default = Path("data") / ("master.csv" if stem.startswith("grants_raw") else f"master_{stem}.csv")
        out = default
    else:
        out = Path(args.outfile)

    out.parent.mkdir(parents=True, exist_ok=True)

    df = make_scoring_template(inp)

    # Choose delimiter based on extension
    ext = out.suffix.lower()
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    df.to_csv(out, index=False, sep=sep)
    print(f"Wrote scoring template with {len(df)} rows to {out}")


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()

