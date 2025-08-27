

from __future__ import annotations

import pandas as pd
import requests


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

    df = pd.DataFrame(opportunities)
    df.to_csv(outfile, index=False)
    return df
