"""Characteristic curves from steady segments.

IMPORTANT: with the current IE-LIFT telemetry the V and I are TERMINAL values
behind an internal DC/DC converter. The resulting V-I curve is the converter
output characteristic on a battery bus, NOT the stack polarisation curve. Name
it accordingly in any figure ("terminal V-I characteristic").


Builds IV/IP curves from steady segments (NOT swept: per roadmap decision),
key characteristic values (Kennwert-Tabelle), slopes, and density axes.
"""
import numpy as np
import pandas as pd

def iv_from_segments(segments, v_col="V_mean", i_col="I_mean", p_col="P_mean"):
    """segments: list of dicts from balance.segments.steady_segments.
    Returns DataFrame: I, V, P, dV/dI, dP/dI sorted by current."""
    df = pd.DataFrame(segments)
    need = [c for c in (i_col, v_col) if c in df.columns]
    if not need or len(df) < 3: return pd.DataFrame()
    out = df[[c for c in (i_col, v_col, p_col) if c in df.columns]].dropna().sort_values(i_col)
    out = out.drop_duplicates(subset=i_col, keep="first").reset_index(drop=True)
    # slope only when the current span is wide enough to be meaningful
    span_ok = (out[i_col].max() - out[i_col].min()) > 0.2 * out[i_col].max()
    out["dVdI_V_per_A"] = np.gradient(out[v_col], out[i_col]) if span_ok else np.nan
    out["slope_note"] = "" if span_ok else "current span too narrow for dV/dI"
    if p_col in out:
        out["dPdI_V"] = np.gradient(out[p_col], out[i_col])
    return out

def key_values(iv_df, i_ref_a=None, v_ref_v=None, area_cm2=None, stack_weight_kg=None,
               rated_power_w=None, rated_current_a=None):
    """Kennwert-Tabelle: OCV, V@I_ref, I@V_ref, MPP, densities."""
    if iv_df.empty: return {}
    i, v = iv_df["I_mean" if "I_mean" in iv_df else iv_df.columns[0]].values, \
           iv_df["V_mean" if "V_mean" in iv_df else iv_df.columns[1]].values
    kv = {}
    # OCV: the lowest-current DATA POINT, never an extrapolation to I=0
    # (np.interp clamps and would silently fabricate an intercept).
    kv["OCV_V"] = float(v[np.argmin(i)])
    kv["OCV_note"] = "lowest-current data point, not extrapolated"
    if i_ref_a is not None:
        kv["V_at_Iref_V"] = float(np.interp(i_ref_a, i, v))
    if v_ref_v is not None:
        # highest I where V >= V_ref (first crossing on the descending curve)
        below = np.where(v < v_ref_v)[0]
        kv["I_at_Vref_A"] = float(i[below[0] - 1]) if len(below) and below[0] > 0 else None
    p = i * v
    mpp = int(np.argmax(p))
    kv["Pmax_W"] = float(p[mpp]); kv["I_at_MPP_A"] = float(i[mpp]); kv["V_at_MPP_V"] = float(v[mpp])
    kv["Pmax_note"] = ("highest MEASURED point; the true MPP may lie outside the measured "
                       "current range (reviewer 2026-10)")
    if area_cm2:
        kv["j_at_MPP_A_per_cm2"] = float(i[mpp] / area_cm2)
        kv["p_max_W_per_cm2"] = float(p[mpp] / area_cm2)
    if stack_weight_kg:
        kv["specific_power_W_per_kg"] = float(p.max() / stack_weight_kg)
    if rated_power_w: kv["rated_power_W"] = rated_power_w
    if rated_current_a: kv["rated_current_A"] = rated_current_a
    return kv

def compare_at_operating_point(iv_dfs, i_targets):
    """iv_dfs: dict name -> iv DataFrame. Returns V at each target current."""
    rows = []
    for name, df in iv_dfs.items():
        if df.empty: continue
        i, v = df.iloc[:, 0].values, df.iloc[:, 1].values
        row = {"dataset": name}
        for it in i_targets:
            row[f"V_at_{it}A"] = round(float(np.interp(it, i, v)), 4)
        rows.append(row)
    return pd.DataFrame(rows)

def deviation_from_reference(iv_df, ref_df, sigma_frac=0.02):
    """Phase 10: flag operating points deviating from a saved reference IV."""
    if iv_df.empty or ref_df.empty: return pd.DataFrame()
    ri, rv = ref_df.iloc[:, 0].values, ref_df.iloc[:, 1].values
    out = iv_df.copy()
    out["V_ref"] = np.interp(out.iloc[:, 0], ri, rv)
    out["dV_V"] = out.iloc[:, 1] - out["V_ref"]
    out["deviation_flag"] = out["dV_V"].abs() > sigma_frac * out["V_ref"]
    return out
