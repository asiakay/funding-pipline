import pandas as pd

def triage_and_score(df):
    # For demo, just return the df as clean and empty others
    clean = df.copy()
    dirty = pd.DataFrame()
    oos = pd.DataFrame()
    return clean, dirty, oos
