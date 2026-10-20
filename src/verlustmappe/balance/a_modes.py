"""Operating-mode labels per sample. Needed because the headline numbers
(efficiency, RTE) must be reported PER MODE: a steady-state number hides what
start-ups, standby and events cost.

  standby : P <= p_standby_W
  startup : first `startup_s` seconds after an off->on transition
  event   : inside a supplied (start,end) index list (POC/purge)
  steady  : everything else while on
"""
import numpy as np

def partition_modes(df, power_col, p_standby_W=None, startup_s=None, events=None):
    from .. import registry as R
    if p_standby_W is None: p_standby_W = 3 * R.get("el.power_standby_W")
    if startup_s is None: startup_s = R.get("el.startup_duration_s")
    df = df.copy()
    p = df[power_col].values.astype(float)
    on = p > p_standby_W
    mode = np.where(on, "steady", "standby").astype(object)
    t = df.index.values.astype("datetime64[ns]").astype(np.int64) / 1e9 if hasattr(df.index, "tz") or df.index.dtype.kind == "M" \
        else df.index.values.astype("timedelta64[ns]").astype(np.int64) / 1e9
    trans = np.zeros(len(p), bool); trans[1:] = on[1:] & ~on[:-1]
    for i in np.where(trans)[0]:
        j = np.searchsorted(t, t[i] + startup_s)
        mode[i:j] = np.where(on[i:j], "startup", mode[i:j])
    for (a, b) in (events or []):
        mode[a:b] = "event"
    df["mode"] = mode
    return df

def energy_by_mode(df, power_col, mode_col="mode"):
    """kWh per mode (rectangular sum with local dt; fine for uniform sampling)."""
    t = np.arange(len(df)) if len(df) < 2 else None
    idx = df.index
    try: ts = idx.values.astype("datetime64[ns]").astype(np.int64) / 1e9
    except Exception: ts = idx.values.astype("timedelta64[ns]").astype(np.int64) / 1e9
    dt = np.gradient(ts) if len(ts) > 1 else np.array([1.0])
    e = df[power_col].values * dt / 3.6e6
    return {m: float(np.nansum(e[df[mode_col].values == m])) for m in np.unique(df[mode_col].values)}
