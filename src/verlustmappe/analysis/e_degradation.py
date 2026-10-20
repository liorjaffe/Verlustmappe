"""Phase 8: multi-session degradation + lifetime projection."""
import numpy as np
import pandas as pd

def degradation_sessions(sessions, i_target, hours):
    """sessions: dict name -> iv DataFrame (I, V). hours: dict name -> op hours.
    Returns V@i_target per session + regression (mV/h, %/h)."""
    rows = []
    for name, df in sessions.items():
        if df.empty: continue
        i, v = df.iloc[:, 0].values, df.iloc[:, 1].values
        rows.append(dict(session=name, hours=hours.get(name, np.nan),
                         V_at_I=round(float(np.interp(i_target, i, v)), 4)))
    d = pd.DataFrame(rows).sort_values("hours")
    if len(d) >= 2:
        c = np.polyfit(d["hours"], d["V_at_I"] * 1000, 1)   # mV per h
        d["mV_per_h"] = round(float(c[0]), 4)
        d["pct_per_h"] = round(float(c[0] / (d["V_at_I"].iloc[0] * 1000) * 100), 6)
    d["pct_vs_first"] = ((d["V_at_I"] / d["V_at_I"].iloc[0]) - 1) * 100
    return d

def lifetime_to_x_pct(deg_df, x_pct=10.0):
    """Hours until V_at_I has fallen x_pct below beginning of life (linear model)."""
    if "mV_per_h" not in deg_df.columns or deg_df["mV_per_h"].dropna().empty:
        return None
    rate = deg_df["mV_per_h"].iloc[-1]
    v0 = deg_df["V_at_I"].iloc[0] * 1000
    if rate >= 0: return None
    return round((x_pct / 100.0 * v0) / abs(rate), 1)
