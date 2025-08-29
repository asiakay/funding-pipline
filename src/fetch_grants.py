"""Helpers for pulling opportunity data directly from Grants.gov.

This module provides a small wrapper around the public Grants.gov search
API so the pipeline can download fresh opportunities without relying on a
locally maintained ``master.csv`` file.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import logging
import re
from pathlib import Path

import pandas as pd
import requests

# Grants.gov "search2" endpoint used by the curl commands in the project
DEFAULT_URL = "https://api.grants.gov/v1/api/search2"
# Preferred human-facing detail page for a single opportunity
DETAIL_URL = "https://www.grants.gov/search-results-detail"

logger = logging.getLogger(__name__)


@dataclass
class GrantHit:
    """Simple structure representing a single grant opportunity."""

    title: str | None
    agency: str | None
    id: str | None
    number: str | None
    open_date: str | None
    close_date: str | None
    status: str | None

    def to_row(self) -> dict:
        """Convert the hit into a row compatible with downstream CSV usage."""

        link = f"{DETAIL_URL}/{self.id}" if self.id else None
        name = self.title
        if self.title and self.number:
            name = f"{self.title} ({self.number})"
        return {
            "Grant Name": name,
            "Sponsor": self.agency,
            "Link": link,
            "Open Date": self.open_date,
            "Deadline": self.close_date,
            "Status": self.status,
        }


def fetch_grants(
    keyword: str,
    max_results: int = 100,
    *,
    status: str | None = None,
    agency: str | None = None,
    cfda: str | None = None,
    eligibility: str | None = None,
    instrument: str | None = None,
    category: str | None = None,
    sort: str | None = None,
) -> pd.DataFrame:
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

    def _norm(value: str | None) -> str | None:
        """Normalize comma/space separated values into pipe-delimited string."""
        if not value:
            return None
        parts = [p.strip() for p in re.split(r"[\s,|]+", value) if p.strip()]
        return "|".join(parts) if parts else None

    payload = {
        "keyword": keyword,
        # default to posted|forecasted if not provided
        "oppStatuses": _norm(status) or "posted|forecasted",
        "startRecordNum": 1,
        # Grants.gov expects 'rows' not 'maximumRecords'
        "rows": max_results,
    }
    # Optional filters
    if agency := _norm(agency):
        payload["agencies"] = agency
    if cfda := _norm(cfda):
        payload["cfda"] = cfda
    if eligibility := _norm(eligibility):
        payload["eligibilities"] = eligibility
    if instrument := _norm(instrument):
        payload["fundingInstruments"] = instrument
    if category := _norm(category):
        payload["fundingCategories"] = category
    if sort := (sort.strip() if sort else None):
        payload["sortBy"] = sort
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    logger.debug("POST %s payload=%s", DEFAULT_URL, payload)
    response = requests.post(DEFAULT_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    data = response.json()
    logger.debug("Status %s; parsed JSON keys: %s", response.status_code, list(data.keys()))
    
    # Results may be nested under top-level 'data'
    container = data
    if "oppHits" not in container and isinstance(data.get("data"), dict):
        logger.debug("Using nested 'data' container for oppHits")
        container = data["data"]
    hits: List[GrantHit] = [
        GrantHit(
            title=hit.get("title"),
            agency=hit.get("agency"),
            id=hit.get("id"),
            number=hit.get("number"),
            open_date=hit.get("openDate"),
            close_date=hit.get("closeDate"),
            status=hit.get("oppStatus"),
        )
        for hit in container.get("oppHits", [])
    ]

    rows = [h.to_row() for h in hits]
    logger.debug("Constructed %d rows for DataFrame", len(rows))
    return pd.DataFrame(rows)


def to_summary_table(df: pd.DataFrame, *, enrich: bool = False) -> pd.DataFrame:
    """Transform base results into the requested summary structure.

    Columns:
    - Grant name, Sponsor org, Link, Award max, RFP, Innovation/execution,
      Latest preparation start date, App deadline, Partners notes,
      Match req %, Timeline summary, App process, App package, Extra notes

    If ``enrich`` is True, attempts to fetch Award Ceiling from Grants.gov detail page.
    """

    # Prepare base frame with required columns
    base = pd.DataFrame(
        {
            "Grant name": df.get("Grant Name"),
            "Sponsor org": df.get("Sponsor"),
            "Link": df.get("Link"),
            "Award max": "",
            "RFP": df.get("Link"),  # default to Grants.gov page
            "Innovation/execution": "",
            "Latest preparation start date": "",
            "App deadline": df.get("Deadline"),
            "Partners notes": "",
            "Match req %": "",
            "Timeline summary": df.apply(
                lambda r: f"Open {r['Open Date']} → Close {r['Deadline']}" if pd.notna(r.get("Open Date")) and pd.notna(r.get("Deadline")) else "",
                axis=1,
            ) if not df.empty else pd.Series(dtype=str),
            "App process": "",
            "App package": "",
            "Extra notes": df.apply(
                lambda r: f"Status: {r['Status']}" if pd.notna(r.get("Status")) else "",
                axis=1,
            ) if not df.empty else pd.Series(dtype=str),
        }
    )

    if enrich and not base.empty:
        # Best-effort extraction of Award Ceiling from the detail page HTML
        import re as _re
        import requests as _req

        def _fetch_award_max(url: str | None) -> str:
            if not url:
                return ""
            try:
                resp = _req.get(url, timeout=20)
                resp.raise_for_status()
                html = resp.text
                # Crude pattern: find "Award Ceiling" label then capture following currency/number
                m = _re.search(r"Award Ceiling\s*</[^>]+>\s*<[^>]*>([^<]+)", html, _re.IGNORECASE)
                if not m:
                    m = _re.search(r"Award Ceiling[^\d$]*([$\d,\.]+)", html, _re.IGNORECASE)
                val = m.group(1).strip() if m else ""
                return val
            except Exception as e:  # pragma: no cover - network/fragile parsing
                logger.debug("award_max fetch failed for %s: %s", url, e)
                return ""

        base["Award max"] = base["Link"].map(_fetch_award_max)

    return base


def main() -> None:  # pragma: no cover - convenience CLI
    """CLI entry-point for quick manual fetching."""

    import argparse

    parser = argparse.ArgumentParser(description="Fetch opportunities from Grants.gov")
    parser.add_argument("keyword", help="search keyword, e.g. 'energy efficiency'")
    parser.add_argument("--max", type=int, default=50, help="maximum records to pull")
    parser.add_argument("--status", help="statuses, e.g. posted,forecasted,closed,archived")
    parser.add_argument("--agency", help="agency or sub-agency codes, comma or pipe separated")
    parser.add_argument("--cfda", help="CFDA codes, comma separated")
    parser.add_argument("--eligibility", help="eligibility codes, comma separated")
    parser.add_argument("--instrument", help="funding instrument codes (G,CA,O,PC)")
    parser.add_argument("--category", help="funding category codes (e.g., EN,ST,...)\n")
    parser.add_argument("--sort", help="sort key if supported by API")
    parser.add_argument(
        "--outfile",
        default=None,
        help="output CSV path; defaults to data/grants_raw_{keyword}.csv",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable verbose debug logging",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="write curated summary columns instead of raw fields",
    )
    parser.add_argument(
        "--enrich",
        action="store_true",
        help="when used with --summary, best-effort fetch Award max from detail page",
    )
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
        logger.debug("Debug logging enabled")

    # Determine output path; auto-name by keyword when not provided
    if args.outfile is None:
        slug = re.sub(r"[^a-z0-9]+", "-", args.keyword.lower()).strip("-")
        outfile = f"data/grants_{'summary_' if args.summary else 'raw_'}{slug}.csv"
    else:
        outfile = args.outfile
    outpath = Path(outfile)
    outpath.parent.mkdir(parents=True, exist_ok=True)

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
    # Transform to summary if requested
    if args.summary:
        df = to_summary_table(df, enrich=args.enrich)
    # Choose delimiter by extension: use tab for .tsv/.tab to make URLs click-friendly in editors
    ext = outpath.suffix.lower()
    sep = "\t" if ext in {".tsv", ".tab"} else ","
    if args.debug:
        logger.debug("Writing file with sep=%r based on extension %s", sep, ext)
    df.to_csv(outpath, index=False, sep=sep)
    print(f"Wrote {len(df)} rows to {outpath}")



if __name__ == "__main__":  # pragma: no cover - script mode
    main()
