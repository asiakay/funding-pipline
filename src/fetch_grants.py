"""Utilities for downloading opportunity data from Grants.gov's ``search2`` API."""

from __future__ import annotations

import pandas as pd
import requests

# The Grants.gov "search2" endpoint returns public opportunity data.
DEFAULT_URL = "https://www.grants.gov/api/common/search2"


def fetch_grants(max_results: int = 50, outfile: str = "data/master.csv") -> pd.DataFrame:
    """Fetch funding opportunities from the Grants.gov ``search2`` API.

    Parameters
    ----------
    max_results:
        Maximum number of opportunity records to request from the API.
    outfile:
        CSV file path where the results will be written.

    Returns
    -------
    DataFrame
        The downloaded opportunity data.
    """

    params = {
        "oppStatuses": "posted",
        "startRecordNum": 1,
        "oppNumRecords": max_results,
        "sortBy": "openDate",
        "sortOrder": "desc",
    }
    headers = {"Accept": "application/json"}

    response = requests.get(DEFAULT_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    # Different Grants.gov APIs expose the opportunity list under different keys;
    # try several options to stay compatible with future changes.
    opportunities = []
    for key in ("opportunities", "oppHits", "results", "hits", "grants"):
        if key in data and data[key]:
            opportunities = data[key]
            break

    df = pd.DataFrame(opportunities)
    df.to_csv(outfile, index=False)
    return df
