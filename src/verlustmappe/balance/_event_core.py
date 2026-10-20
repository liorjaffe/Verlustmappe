"""
FC data analysis: event/POC detection + steady-state statistics
Channel-agnostic (V, I, P), numpy + pandas only.

Usage:
    df = pd.read_csv("data.csv", parse_dates=["time"], index_col="time")
    res = analyse_window(df, ["voltage", "current", "power"], t0, t1)
    print(res["events"])     # event table
    print(res["steady"])     # usable steady segments with means
"""

import numpy as np
import pandas as pd

CFG = {
    "win": "60s",          # window for rolling median/MAD (time-based)
    "mad_thresh": 4.0,     # robust z-score threshold for an event
    "min_event": "2s",     # deviations shorter than this are ignored
    "min_gap": "10s",      # events closer than this are merged
    "settle_tol_pct": 1.0, # "settled again" = within +-% of plateau
    "settle_hold": "30s",  # ... and must hold for this long
    "plateau_win": "60s",  # window before the event used for the plateau
    "min_steady": "60s",   # shorter steady segments are not usable
}


# ---------- Core: robust deviation scores ----------

def deviation_score(x: pd.Series, win: str) -> pd.Series:
    """Robust z-score: |x - rolling median| / rolling MAD. 0 = normal operation."""
    med = x.rolling(win, center=True, min_periods=1).median()
    mad = (x - med).abs().rolling(win, center=True, min_periods=1).median() * 1.4826
    mad = mad.replace(0, np.nan).bfill().ffill().fillna(1e-9)
    return (x - med).abs() / mad


def runs_from_mask(mask: pd.Series, min_len: pd.Timedelta) -> list:
    """Contiguous True blocks as (start, end) list, filtered by min_len."""
    out, start = [], None
    for ts, flag in mask.items():
        if flag and start is None:
            start = ts
        elif not flag and start is not None:
            if ts - start >= min_len:
                out.append((start, ts))
            start = None
    if start is not None and mask.index[-1] - start >= min_len:
        out.append((start, mask.index[-1]))
    return out


def merge_runs(runs: list, min_gap: pd.Timedelta) -> list:
    merged = []
    for s, e in runs:
        if merged and s - merged[-1][1] <= min_gap:
            merged[-1] = (merged[-1][0], e)
        else:
            merged.append((s, e))
    return merged


# ---------- Events + recovery time per channel ----------

def _last_window(series: pd.Series, window_td: pd.Timedelta) -> pd.Series:
    """Equivalent of the now-removed Series.last(window): the tail slice of
    `series` covering the given time span, ending at its last timestamp."""
    if series.empty:
        return series
    end = series.index[-1]
    return series.loc[end - window_td:end]


def detect_events(x: pd.Series, cfg=CFG) -> pd.DataFrame:
    """Finds events (POC/purge/outliers) in one channel plus recovery times."""
    score = deviation_score(x, cfg["win"])
    mask = score > cfg["mad_thresh"]
    events = merge_runs(runs_from_mask(mask, pd.Timedelta(cfg["min_event"])),
                        pd.Timedelta(cfg["min_gap"]))
    rows = []
    for s, e in events:
        plateau = _last_window(x.loc[:s], pd.Timedelta(cfg["plateau_win"])).median()
        if pd.isna(plateau):
            plateau = x.median()
        tol = cfg["settle_tol_pct"] / 100.0 * abs(plateau)
        hold = pd.Timedelta(cfg["settle_hold"])
        settled_at = None
        count, prev = pd.Timedelta(0), None
        for ts, val in x.loc[e:].items():
            within = abs(val - plateau) <= tol
            if within and prev is not None and (ts - prev) <= hold:
                count += ts - prev
            elif within:
                count = pd.Timedelta(0)
            else:
                count = pd.Timedelta(0)
            prev = ts
            if count >= hold:
                settled_at = ts - hold
                break
        seg = x.loc[s:e]
        rows.append({
            "channel": x.name, "start": s, "end": e,
            "depth": seg.min() - plateau,        # dip (negative)
            "overshoot": seg.max() - plateau,    # overshoot (positive)
            "plateau": plateau,
            "recovery_s": None if settled_at is None
                          else (settled_at - e).total_seconds(),
        })
    return pd.DataFrame(rows)


# ---------- Steady segments ----------

def steady_segments(x: pd.Series, events: pd.DataFrame, cfg=CFG) -> pd.DataFrame:
    """Event-free periods longer than min_steady, with summary stats."""
    if len(events):
        covered = pd.IntervalIndex.from_tuples(
            [(r.start, r.end) for r in events.itertuples()])
    else:
        covered = pd.IntervalIndex([])
    idx = x.dropna().index
    cuts, cur = [], None
    for ts in idx:
        inside = any(iv.left <= ts <= iv.right for iv in covered)
        if inside:
            if cur is not None:
                cuts.append((cur, ts))
                cur = None
        elif cur is None:
            cur = ts
    if cur is not None:
        cuts.append((cur, idx[-1]))
    rows = []
    for s, e in cuts:
        if e - s < pd.Timedelta(cfg["min_steady"]):
            continue
        seg = x.loc[s:e]
        rows.append({"channel": x.name, "start": s, "end": e,
                     "mean": seg.mean(), "std": seg.std(),
                     "duration_s": (e - s).total_seconds()})
    return pd.DataFrame(rows)


# ---------- Main API ----------

def analyse_window(df: pd.DataFrame, cols: list, t0=None, t1=None, cfg=CFG):
    """Analyze a time window across multiple channels."""
    sub = df.loc[t0:t1, cols] if t0 or t1 else df[cols]
    all_events, all_steady = [], []
    for col in cols:
        x = sub[col].dropna()
        ev = detect_events(x, cfg)
        st = steady_segments(x, ev, cfg)
        if not ev.empty:
            all_events.append(ev)
        if not st.empty:
            all_steady.append(st)
    events = pd.concat(all_events, ignore_index=True) if all_events else pd.DataFrame()
    steady = pd.concat(all_steady, ignore_index=True) if all_steady else pd.DataFrame()
    return {"events": events, "steady": steady}


def plot_analysis(df, cols, t0=None, t1=None, cfg=CFG):
    """Raw data + event highlighting + steady segments in one plot."""
    import matplotlib.pyplot as plt
    res = analyse_window(df, cols, t0, t1, cfg)
    fig, axes = plt.subplots(len(cols), 1, figsize=(12, 3 * len(cols)),
                             sharex=True, squeeze=False)
    for ax, col in zip(axes[:, 0], cols):
        sub = df.loc[t0:t1, col] if t0 or t1 else df[col]
        ax.plot(sub.index, sub.values, lw=0.8, label=col)
        for r in res["events"][res["events"]["channel"] == col].itertuples():
            ax.axvspan(r.start, r.end, color="red", alpha=0.2)
        for r in res["steady"][res["steady"]["channel"] == col].itertuples():
            ax.axvspan(r.start, r.end, color="green", alpha=0.08)
        ax.legend(loc="upper right")
    return fig, res


# ---------- Demo with synthetic data ----------

if __name__ == "__main__":
    rng = np.random.default_rng(0)
    idx = pd.date_range("2026-01-01", periods=3600, freq="1s")
    base = 47.0 + rng.normal(0, 0.05, 3600)
    base[600:660] += np.linspace(0, -1.5, 60)   # POC dip
    base[660:720] += np.linspace(-1.5, 0.3, 60) # recovery with overshoot
    df = pd.DataFrame({"voltage": base,
                       "current": 40 + rng.normal(0, 0.1, 3600)},
                      index=idx)
    res = analyse_window(df, ["voltage", "current"])
    print(res["events"], "\n")
    print(res["steady"])
