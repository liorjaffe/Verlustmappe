"""Phase 11: summary + relative difference columns between two datasets."""
import pandas as pd

def summary_table(summaries):
    """summaries: list of dicts (one per dataset). Missing -> dash."""
    df = pd.DataFrame(summaries)
    return df.fillna("-")

def relative_diff(df, a, b, higher_better=()):
    """Add %-difference columns dataset_b relative to dataset_a."""
    out = df.copy()
    for col in df.columns:
        if col in ("dataset",) or not pd.api.types.is_numeric_dtype(df[col]):
            continue
        va, vb = df.loc[df["dataset"] == a, col].iloc[0], df.loc[df["dataset"] == b, col].iloc[0]
        if pd.api.types.is_number(va) and pd.api.types.is_number(vb) and va:
            out[f"d_{col}_pct"] = round((vb - va) / abs(va) * 100, 2)
    return out
