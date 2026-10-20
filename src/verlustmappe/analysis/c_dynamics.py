"""Phase 4/5 extensions: ramp rates, settle/overshoot beyond baseline,
start/stop cycle energy."""
import numpy as np
import pandas as pd

def ramp_rates(df, cols=("fc_power_W", "fc1_current_A", "fc1_voltage_V")):
    """Median positive/negative slew rate per channel [unit/s]."""
    out = {}
    t = df.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    for c in cols:
        if c not in df.columns: continue
        v = df[c].interpolate(limit_direction="both").values
        d = np.diff(v) / np.diff(t)
        out[c] = dict(ramp_up_per_s=float(np.nanmedian(d[d > 0])) if (d > 0).any() else None,
                      ramp_down_per_s=float(np.nanmedian(d[d < 0])) if (d < 0).any() else None,
                      max_up=float(np.nanmax(d)) if len(d) else None,
                      max_down=float(np.nanmin(d)) if len(d) else None)
    return out

def start_stop_cycles(df, power_col="fc_power_W", threshold_frac=0.1, rated_w=2500.0):
    """Phase 5: detect cycles above threshold; per cycle duration, peak,
    startup energy (integral from start to peak) and shutdown energy."""
    p = df[power_col].interpolate(limit_direction="both").values
    t = df.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    thr = threshold_frac * rated_w
    on = p > thr
    cycles, start = [], None
    for k, flag in enumerate(on):
        if flag and start is None: start = k
        if not flag and start is not None:
            cycles.append((start, k)); start = None
    if start is not None: cycles.append((start, len(on)))
    rows = []
    for a, b in cycles:
        if b - a < 5: continue
        e_cycle = np.trapezoid(p[a:b], t[a:b]) / 3600.0          # Wh
        peak = int(np.argmax(p[a:b])) + a
        e_up = np.trapezoid(p[a:peak + 1], t[a:peak + 1]) / 3600.0   # inclusive of peak sample
        e_down = np.trapezoid(p[peak:b], t[peak:b]) / 3600.0        # from peak (exclusive) to end
        rows.append(dict(t_start=df.index[a], t_end=df.index[b - 1],
                         duration_s=round(t[b - 1] - t[a], 1),
                         peak_W=round(float(p[a:b].max()), 1),
                         energy_cycle_Wh=round(e_cycle, 3),
                         energy_startup_Wh=round(e_up, 3),
                         energy_shutdown_Wh=round(e_down, 3)))
    return pd.DataFrame(rows)
