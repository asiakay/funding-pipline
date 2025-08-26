import pandas as pd
from src.triage_and_score import triage_and_score
from src.build_deck import build_deck

def main():
    df = pd.read_csv("data/master.csv")
    clean, dirty, oos = triage_and_score(df)

    clean.to_csv("outputs/CleanTable.csv", index=False)
    dirty.to_csv("outputs/Dirty.csv", index=False)
    oos.to_csv("outputs/OutOfScope.csv", index=False)
    clean.to_csv("outputs/Master_Scored.csv", index=False)

    build_deck(clean, "outputs/EQORE_Deck.pptx")

if __name__ == "__main__":
    main()
