"""Utilities for downloading opportunity data from Grants.gov."""

from __future__ import annotations

import pandas as pd
import requests

DEFAULT_URL = "https://www.grants.gov/grantsws/rest/opportunities/search"


def fetch_grants(max_results: int = 50, outfile: str = "data/master.csv") -> pd.DataFrame:
    """Fetch funding opportunities from Grants.gov and save them to ``outfile``.

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
        "startRecordNum": 1,
        "oppNumRecords": max_results,
        "sortBy": "openDate",
        "sortOrder": "desc",
    }
    headers = {"Accept": "application/json"}

    response = requests.get(DEFAULT_URL, params=params, headers=headers, timeout=30)
    response.raise_for_status()

    data = response.json()
    # The API returns a list of opportunities under the ``oppHits`` key.
    opportunities = data.get("oppHits", [])
    df = pd.DataFrame(opportunities)
    df.to_csv(outfile, index=False)
    return df
