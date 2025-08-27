"""Helpers for pulling opportunity data directly from Grants.gov.

This module provides a small wrapper around the public Grants.gov search
API so the pipeline can download fresh opportunities without relying on a
locally maintained ``master.csv`` file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd
import requests

# Grants.gov "search2" endpoint used by the curl commands in the project
DEFAULT_URL = "https://api.grants.gov/v1/api/search2"


@dataclass
class GrantHit:
    """Simple structure representing a single grant opportunity."""

    title: str | None
    agency: str | None
    id: str | None
    open_date: str | None
    close_date: str | None
    status: str | None

    def to_row(self) -> dict:
        """Convert the hit into a row compatible with downstream CSV usage."""

        link = (
            f"https://www.grants.gov/web/grants/view-opportunity.html?oppId={self.id}"
            if self.id
            else None
        )
        return {
            "Grant Name": self.title,
            "Sponsor": self.agency,
            "Link": link,
            "Open Date": self.open_date,
            "Deadline": self.close_date,
            "Status": self.status,
        }


def fetch_grants(keyword: str, max_results: int = 50) -> pd.DataFrame:
    """Fetch opportunity data from Grants.gov.

    Parameters
    ----------
    keyword:
        Keyword to search in the Grants.gov catalogue.
    max_results:
        Maximum number of records to return. Grants.gov caps this at 500.

    Returns
    -------
    DataFrame
        A table with one row per opportunity. Only a subset of useful fields
        is returned; consumers can enrich the data further if needed.
    """

    payload = {
        "keyword": keyword,
        "oppStatuses": "posted|forecasted",
        "startRecordNum": 1,
        "maximumRecords": max_results,
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = requests.post(DEFAULT_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    hits: List[GrantHit] = [
        GrantHit(
            title=hit.get("title"),
            agency=hit.get("agency"),
            id=hit.get("id"),
            open_date=hit.get("openDate"),
            close_date=hit.get("closeDate"),
            status=hit.get("oppStatus"),
        )
        for hit in data.get("oppHits", [])
    ]

    rows = [h.to_row() for h in hits]
    return pd.DataFrame(rows)


def main() -> None:  # pragma: no cover - convenience CLI
    """CLI entry-point for quick manual fetching."""

    import argparse

    parser = argparse.ArgumentParser(description="Fetch opportunities from Grants.gov")
    parser.add_argument("keyword", help="search keyword, e.g. 'energy efficiency'")
    parser.add_argument("--max", type=int, default=50, help="maximum records to pull")
    parser.add_argument(
        "--outfile",
        default="data/grants_raw.csv",
        help="where to write the downloaded CSV",
    )
    args = parser.parse_args()

    df = fetch_grants(args.keyword, args.max)
    df.to_csv(args.outfile, index=False)
    print(f"Wrote {len(df)} rows to {args.outfile}")


if __name__ == "__main__":  # pragma: no cover - script mode
    main()

