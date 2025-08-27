import pandas as pd
from src.triage_and_score import triage_and_score
from src.build_deck import build_deck
from src.fetch_grants import fetch_grants

def main():
    """Run the funding pipeline.

    The pipeline first tries to download the latest opportunities from
    Grants.gov. If the download fails (for example, due to missing
    network access), it falls back to the previously cached
    ``data/master.csv`` file.
    """

    try:
        df = fetch_grants(max_results=50)
    except Exception as exc:  # pragma: no cover - best effort fallback
        print(f"Warning: could not fetch data from Grants.gov ({exc})")
        df = pd.read_csv("data/master.csv")

    clean, dirty, oos = triage_and_score(df)

    clean.to_csv("outputs/CleanTable.csv", index=False)
    dirty.to_csv("outputs/Dirty.csv", index=False)
    oos.to_csv("outputs/OutOfScope.csv", index=False)
    clean.to_csv("outputs/Master_Scored.csv", index=False)

    # Build a deck showing the top 50 opportunities
    build_deck(clean, "outputs/EQORE_Deck.pptx", max_results=50)

if __name__ == "__main__":
    main()
