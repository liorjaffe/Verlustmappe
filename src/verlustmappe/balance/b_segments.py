"""Steady-state windows: contiguous samples above a power floor with a low
coefficient of variation. Their means become the points of the characteristic
curves (V-I, efficiency vs load). Segments are stricter than 'not an event'."""
import numpy as np, pandas as pd

def steady_segments(df, col, p_min=None, min_dur_s=120, max_cv=0.15, extra_cols=()):
    p = df[col].values.astype(float)
    try: t = df.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    except Exception: t = df.index.values.astype("timedelta64[ns]").astype(np.int64) / 1e9
    floor = p_min if p_min is not None else 0.4 * np.nanmax(p)
    on = p > floor
    out, start = [], None
    for k, f in enumerate(np.append(on, False)):
        if f and start is None: start = k
        if not f and start is not None:
            a, b = start, k; start = None
            if t[b - 1] - t[a] < min_dur_s: continue
            v = p[a:b]; v = v[np.isfinite(v)]
            if len(v) < 10 or np.nanstd(v) / np.nanmean(v) > max_cv: continue
            row = dict(t_start=df.index[a], t_end=df.index[b - 1], dur_min=round((t[b - 1] - t[a]) / 60, 1),
                       P_mean=float(np.nanmean(v)), P_std=float(np.nanstd(v)), n=int(len(v)))
            for c in extra_cols:
                if c in df.columns: row[c + "_mean"] = float(np.nanmean(df[c].values[a:b]))
            out.append(row)
    return pd.DataFrame(out)
