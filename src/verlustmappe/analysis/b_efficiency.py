"""Efficiency vs temperature, direction-aware (external review 2026-10).

  FUEL CELL:  eta = E_electrical,out / E_H2,in     -> P / chem
  ELECTROLYSER: eta = E_H2,out / E_electrical,in   -> chem / P

The first draft always computed P/chem, which returns 1/eta for an
electrolyser (1.60 instead of 0.624). The caller must pass device='el' or
'fc'; the default raises rather than guessing.
WARNING: uses the device-reported H2 flow (Route 3), correlated with the
electrical data; treat results as a trend, not an independent measurement.
"""
import numpy as np
import pandas as pd
from ..constants import RHO_H2_KG_PER_NL, LHV_H2_WH_PER_NL, HHV_H2_WH_PER_NL

H2_G_PER_NL = RHO_H2_KG_PER_NL * 1000.0

def nl_to_g(nl):
    return nl * H2_G_PER_NL

def efficiency_vs_temperature(df, power_col, h2_flow_col, temp_col, basis="LHV", device="fc"):
    if device not in ("el", "fc"):
        raise ValueError("device must be 'el' or 'fc'")
    kwh_per_nl = (LHV_H2_WH_PER_NL if basis == "LHV" else HHV_H2_WH_PER_NL) / 1000.0
    d = df[[power_col, h2_flow_col, temp_col]].dropna()
    d = d[d[h2_flow_col] > 1]
    chem_kW = d[h2_flow_col] * kwh_per_nl          # NL/h * kWh/NL = kW
    p_kW = d[power_col] / 1000.0
    eta = (chem_kW / p_kW) if device == "el" else (p_kW / chem_kW)
    out = pd.DataFrame({"eta": eta.values, "T": d[temp_col].values}, index=d.index)
    bins = pd.cut(out["T"], bins=6)
    return out.groupby(bins, observed=True).agg(T_mean=("T", "mean"), eta_mean=("eta", "mean"),
                                                eta_std=("eta", "std"), n=("eta", "size")).reset_index()
