"""Phase 6: voltage recovery after purge events (anode pressure -> V)."""
import numpy as np
import pandas as pd

def recovery_after_purges(df, purge_times, v_col="fc1_voltage_V", window_s=60.0, tol_pct=1.0):
    """For each purge timestamp: voltage drop depth and time to return within
    tol% of the pre-purge mean (plateau window = 30 s before purge)."""
    if v_col not in df.columns or not purge_times: return pd.DataFrame()
    t = df.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    v = df[v_col].interpolate(limit_direction="both").values
    rows = []
    for pt in purge_times:
        ts = pd.Timestamp(pt).value / 1e9
        pre = (t >= ts - 30) & (t <= ts)
        plateau = float(np.nanmean(v[pre])) if pre.any() else np.nan
        post = (t > ts) & (t <= ts + window_s)
        if not post.any() or np.isnan(plateau): continue
        seg = v[post]
        rec = None
        tol = tol_pct / 100.0 * abs(plateau)
        hold_n = 5
        for k in range(len(seg) - hold_n + 1):
            if np.all(np.abs(seg[k:k + hold_n] - plateau) <= tol):
                rec = float(t[post][k] - ts); break
        rows.append(dict(purge_at=pt, V_plateau=round(plateau, 3),
                         V_min_after=round(float(np.nanmin(seg)), 3),
                         dip_V=round(float(plateau - np.nanmin(seg)), 3),
                         recovery_s=rec))
    return pd.DataFrame(rows)
