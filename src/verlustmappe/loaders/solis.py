"""Loader for Solis S5-EO1P5K-48 telemetry (FC-side inverter).

The device exposes CAN + BMS comm (built-in) and optional Wi-Fi/RS485 via a
Solis datalogger. Until the channel is connected, this loader accepts the two
formats the pipeline will realistically receive and normalises them to the
column vocabulary (docs/03_data_dictionary.md):

  Format A "Solis Cloud export" (typical columns, comma or semicolon separated):
      Timestamp, AC output power (W) or "Load power", Battery voltage (V),
      Battery current (A, + = discharge into bus), AC voltage (V)
  Format B "generic CSV": one value column with a known raw name.

Pipeline vocabulary produced:
  ac_out_W          inverter AC output to the island load (MEASURED)
  bus_voltage_V     battery-side bus voltage (40-60 V range)
  batt_current_A    + = battery discharging into the bus (inverter drawing)
  e_ac_cum_Wh       cumulative AC energy counter, if the export has one

The FC-side inverter boundary in the loss map needs e_ac_measured; with this
loader the inverter flips to eta_is_measured = True automatically once a file
is fed through devices/inverter.FCInverter.account().
"""
import numpy as np
import pandas as pd

# raw-name -> pipeline name, case-insensitive substring matching
SOLIS_MAP = [
    (("ac output power", "load power", "output power", "ac power"), "ac_out_W"),
    (("battery voltage", "bus voltage", "battery volt"), "bus_voltage_V"),
    (("battery current", "bms current"), "batt_current_A"),
    (("ac voltage", "output voltage"), "ac_V"),
    (("ac energy", "total energy", "load energy", "ac yield"), "e_ac_cum_Wh"),
]

def _match(colname_lower):
    for needles, target in SOLIS_MAP:
        if any(n in colname_lower for n in needles):
            return target
    return None

def load_solis(path, time_col_candidates=("timestamp", "time", "date", "datetime")):
    """Solis export CSV -> UTC-indexed DataFrame in pipeline vocabulary."""
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    # time column
    tcol = next((c for c in df.columns
                 if any(t in c.lower() for t in time_col_candidates)), None)
    if tcol is None:
        raise ValueError(f"{path}: no time column found (tried {time_col_candidates})")
    idx = pd.to_datetime(df[tcol], errors="coerce", utc=True)
    out = pd.DataFrame(index=idx)
    mapped = {}
    for c in df.columns:
        if c == tcol: continue
        target = _match(c.lower())
        if target:
            mapped[target] = pd.to_numeric(df[c], errors="coerce").to_numpy()
    if not mapped:
        raise ValueError(f"{path}: no known Solis columns found; headers were {list(df.columns)}")
    for k, v in mapped.items():
        out[k] = v
    return out.sort_index()

def inverter_eta_measured(df):
    """Energy-weighted measured efficiency over the loaded window:
    eta = sum(AC out) / sum(battery-side DC in). Needs batt_current_A and
    bus_voltage_V to reconstruct the DC side (no direct DC power column in
    Solis exports): E_in = sum(V * I dt) with I>0 = discharge."""
    if not {"ac_out_W", "bus_voltage_V", "batt_current_A"}.issubset(df.columns):
        raise ValueError("need ac_out_W, bus_voltage_V, batt_current_A")
    d = df[["ac_out_W", "bus_voltage_V", "batt_current_A"]].dropna()
    d = d[d["batt_current_A"] > 0]           # only discharge periods
    t = (d.index.values.astype("datetime64[ns]").astype(np.int64)) / 1e9
    dt = np.gradient(t) if len(t) > 1 else np.array([1.0])
    e_in = float(np.sum(d["bus_voltage_V"].values * d["batt_current_A"].values * dt) / 3.6e6)
    e_out = float(np.sum(d["ac_out_W"].values * dt) / 3.6e6)
    return dict(e_dc_in_kWh=e_in, e_ac_kWh=e_out,
                eta=e_out / e_in if e_in > 0 else None,
                n_samples=int(len(d)))
