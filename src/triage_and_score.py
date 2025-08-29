import pandas as pd
from datetime import datetime
from typing import Tuple


def _parse_match(value: object) -> float:
    """Convert a match percentage string to a float."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip().replace('%', '').replace(',', '')
    if not text or text.lower().startswith('var'):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def triage_and_score(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Split a master opportunity table into Clean/Dirty/Out-of-Scope sets."""
    df = df.copy()

    # Normalize numeric scoring columns
    for col in ["Relevance", "EQORE Fit", "Ease of Use"]:
        df[col] = pd.to_numeric(df.get(col), errors="coerce").fillna(0)

    # Weighted score
    df["Weighted Score"] = df["Relevance"] * df["EQORE Fit"] * (df["Ease of Use"] / 5)

    # Parse deadlines and match %
    df["Deadline"] = pd.to_datetime(df.get("Deadline"), errors="coerce")
    today = pd.Timestamp.today().normalize()
    if "Match %" in df.columns:
        df["MatchNumeric"] = df["Match %"].apply(_parse_match)
    else:
        df["MatchNumeric"] = None

    # Fatal flaw filters
    fatal = pd.Series(False, index=df.index)
    fatal |= df["Deadline"].notna() & (df["Deadline"] < today)           # deadline passed
    fatal |= df["MatchNumeric"].notna() & (df["MatchNumeric"] >= 33)     # high match
    for col in ["Grant Name", "Sponsor", "Link"]:                        # missing critical fields
        if col in df.columns:
            fatal |= df[col].isna()
    df["fatal"] = fatal

    # Categorization
    relevance_zero = df["Relevance"] == 0
    out_of_scope = df[relevance_zero].copy().reset_index(drop=True)

    clean = (
        df[(~relevance_zero) & (~df["fatal"])]
        .sort_values("Weighted Score", ascending=False)
        .copy()
        .reset_index(drop=True)
    )
    clean["Rank"] = range(1, len(clean) + 1)
    # Put Rank first if present
    cols = ["Rank"] + [c for c in clean.columns if c != "Rank"]
    clean = clean[cols]

    dirty = df[(~relevance_zero) & df["fatal"]].copy().reset_index(drop=True)

    # Drop helper columns
    for frame in (clean, dirty, out_of_scope):
        for col in ["fatal", "MatchNumeric"]:
            if col in frame.columns:
                del frame[col]

    return clean, dirty, out_of_scope
