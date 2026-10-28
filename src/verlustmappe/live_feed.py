"""Live layer: rolling-window pipeline between telemetry stream and plotter.
No hardware dependency: feeds on any generator of DataFrames (mock included)."""
import json
import numpy as np
import pandas as pd
from .devices import ElectrolyzerUnit
from .devices import FuelCellSystem
from .balance.a_modes import partition_modes

class LivePipeline:
    """Call .push(df_window) periodically; get back a plain dict for the plotter.

    Works on ANY device frame whose columns match the pipeline vocabulary
    (docs/03_data_dictionary.md): EL (power_W + el_stack_current_A), FC
    (fc_power_W + fc1/fc2_*), PV (ac_power_W / dc_power_W), Solis inverter
    (ac_out_W + bus_voltage_V). The loaders (loaders/) produce exactly these
    columns; live wiring per device:

      EL        : Enapter cloud telemetry (~1 Hz) or local Modbus TCP;
                  stack_amperage -> el_stack_current_A enables Route 1 live
      Regatron  : bridge fast log (20 Hz) via loaders/regatron.load_fastlog
      Solis (Inverter 2, FC side): cloud/datalogger export via loaders/solis.load_solis
      Solis (Inverter 1, F8 PV side): LIVE via loaders/solis_live.poll_solis_live /
                  history via f8_range_dfs + f8_day_balance (E_AC from the eToday counter)
      legacy PV: SunSpec export via loaders/grafana (PV_MAP)
    """

    def __init__(self, dt_s=1.0, window_s=600):
        self.dt_s = dt_s
        self.window_s = window_s
        self.el = ElectrolyzerUnit()
        self.fcs = FuelCellSystem()

    def push(self, df):
        out = {"ts": str(df.index[-1]) if len(df) else None,
               "n_points": int(len(df))}
        poc = _detect_poc(df, "fc_power_W")
        power_col = "power_W" if "power_W" in df.columns else ("fc_power_W" if "fc_power_W" in df.columns else None)
        if power_col is not None:
            dfm = partition_modes(df, power_col=power_col, events=poc)
            counts = dfm["mode"].value_counts().to_dict()
            out["modes"] = counts
            if "el_current_A" in df.columns or "el_stack_current_A" in df.columns:
                acc = self.el.account(df)
                span_s = float((df.index[-1] - df.index[0]) / np.timedelta64(1, "s")) if len(df) > 1 else 0.0
                covered_s = span_s * (acc.get("data_coverage") or 0.0)
                out["el"] = {"power_kW": df["power_W"].mean()/1000,
                             "h2_NLh": (acc["h2"]["NL"] / (covered_s/3600.0)) if covered_s > 0 else None,
                             "eta_LHV": acc["efficiency_LHV"],
                             "route": acc["h2"]["route"]}
            if "fc_power_W" in df.columns:
                dfm = partition_modes(df, power_col="fc_power_W", events=poc)
                acc = self.fcs.account(dfm)
                out["fc"] = {"power_kW": df["fc_power_W"].mean()/1000,
                             "eta_LHV": acc["efficiency_LHV"],
                             "h2_route": acc["h2"]["route"], "h2_g": acc["h2"]["kg"]*1000}
        return out

    def push_json(self, df):
        return json.dumps(self.push(df), default=str)

def _detect_poc(df, col="fc_power_W", thresh=0.5):
    """POC = sustained drop below thresh*median for >=3 consecutive samples."""
    if col not in df.columns or len(df) < 5:
        return []
    v = df[col].values
    med = np.median(v)
    low = v < thresh * med
    events, start = [], None
    for i, flag in enumerate(low):
        if flag and start is None: start = i
        if not flag and start is not None:
            if i - start >= 3: events.append((start, i))
            start = None
    if start is not None and len(v) - start >= 3: events.append((start, len(v)))
    return events

def mock_stream(duration_s=3600, dt_s=1.0, poc_at=(1200, 1212), seed=0):
    """Synthetic telemetry stream (any dt): steady FC load with a POC dip."""
    rng = np.random.default_rng(seed)
    n = max(int(round(duration_s/dt_s)), 2)
    dt_s = duration_s / n
    t = pd.timedelta_range(0, periods=n, freq=f"{dt_s}s")
    p = np.full(n, 2400.0) * (1 + 0.02*rng.standard_normal(n))
    i1 = np.full(n, 19.39) * (1 + 0.02*rng.standard_normal(n))
    i2 = np.full(n, 19.39) * (1 + 0.02*rng.standard_normal(n))

    p[poc_at[0]:poc_at[1]] *= 0.2          # FC output collapses during POC
    df = pd.DataFrame({"fc_power_W": p, "fc1_stack_current_A": i1,
                       "fc2_stack_current_A": i2,
                       "load_current_A": p/48},
                      index=t)
    return df

def iter_windows(df, window_s, dt_s):
    n = int(window_s/dt_s)
    if n <= 0: return
    for start in range(0, len(df) - n + 1, n):
        yield df.iloc[start:start+n]
