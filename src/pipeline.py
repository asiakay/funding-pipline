import argparse
import pandas as pd
from src.triage_and_score import triage_and_score
from src.build_deck import build_deck
from src.build_pdf import build_pdf



def main(argv=None):
    """Run the funding pipeline on ``data/master.csv``.

    The script scores all opportunities, splits them into Clean, Dirty,
    and Out-of-Scope buckets, and writes the results to the ``outputs``
    directory. Optional flags control generation of a PowerPoint deck and
    a one-pager PDF summarizing the top opportunities.
    """

    parser = argparse.ArgumentParser(description="EQORE funding pipeline")
    parser.add_argument("--deck", action="store_true", help="generate PowerPoint deck")
    parser.add_argument("--pdf", action="store_true", help="generate one-pager PDF")


    required = {"Relevance", "EQORE Fit", "Ease of Use"}
    if required.issubset(df.columns):
        clean, dirty, oos = triage_and_score(df)
    else:
        # Without scoring columns, simply dump the raw data and exit early.
        df.to_csv("outputs/GrantsRaw.csv", index=False)
        print("Missing scoring columns; wrote outputs/GrantsRaw.csv")
        return

    clean.to_csv("outputs/CleanTable.csv", index=False)
    dirty.to_csv("outputs/DirtyTable.csv", index=False)
    oos.to_csv("outputs/OutOfScope.csv", index=False)
    clean.to_csv("outputs/Master_Scored.csv", index=False)

    # Excel workbook with all tables
    with pd.ExcelWriter("outputs/Tables.xlsx", engine="openpyxl") as xls:
        clean.to_excel(xls, "Clean", index=False)
        dirty.to_excel(xls, "Dirty", index=False)
        oos.to_excel(xls, "OutOfScope", index=False)

    if args.deck:
        try:  # pragma: no cover - building deck is optional
            build_deck(clean, "outputs/EQORE_Deck.pptx", max_results=50)
        except Exception as exc:
            print(f"Warning: could not build deck ({exc})")

    if args.pdf:
        try:  # pragma: no cover - building PDF is optional
            build_pdf(clean, "outputs/OnePager.pdf", max_results=5)
        except Exception as exc:
            print(f"Warning: could not build PDF ({exc})")


if __name__ == "__main__":
    main()
