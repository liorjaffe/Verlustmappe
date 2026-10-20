"""Robust event detection. Wraps the validated median/MAD detector in
_event_core.py (originally the user's fc_event_analysis.py).

Why median/MAD instead of mean/std: the events we look for (POC dips, purges)
ARE the outliers; mean/std would be inflated by them and hide them. The MAD
scaled by 1.4826 estimates sigma for Gaussian data (Rousseeuw & Croux, JASA
1993). Threshold 4 sigma-equivalents; events shorter than 2 s ignored; events
closer than 10 s merged; recovery = back within 1% of the pre-event plateau
and holding for 30 s (settle-and-hold, avoids counting a single crossing).
Outputs are CANDIDATES; confirm them visually before naming them POC/purge.
"""
import numpy as np
import pandas as pd
from . import _event_core as core

CFG = dict(core.CFG)

def detect_events(df, channels, cfg=None):
    res = core.analyse_window(df, channels, cfg=cfg or CFG)
    return res["events"], res["steady"]

def purge_candidates(df, pressure_col="anode_pressure_mbar", min_drop_mbar=150.0, min_gap_s=10.0):
    """Purge = a fast drop of anode pressure between consecutive samples.

    Uses a first-difference threshold, NOT the MAD detector: a purge lasts one
    or two 5-s samples, which is below the MAD detector's resolution (60 s
    window tuned for 1-s data). The threshold is physical: the IE-LIFT anode
    purge visibly drops pressure by several hundred mbar. Returns timestamps and
    drop sizes; validate them against a purge-state channel when available."""
    if pressure_col not in df.columns: return pd.DataFrame()
    ap = df[pressure_col].dropna()
    d = ap.diff()
    t = ap.index.values.astype("datetime64[ns]").astype("int64") / 1e9
    rows, last = [], -1e18
    for i in np.where(d.values < -min_drop_mbar)[0]:
        if t[i] - last >= min_gap_s:
            rows.append(dict(start=ap.index[i], drop_mbar=float(-d.iloc[i]), p_before=float(ap.iloc[i - 1])))
            last = t[i]
    return pd.DataFrame(rows)
