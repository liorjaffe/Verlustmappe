"""Fuel cell system: 2 x IE-LIFT 802 on a 48 V bus with a battery.

Same alignment rule as the electrolyser: terminal power and terminal current
must live on the same samples; unmatched rows are DROPPED, gaps are NOT
bridged (see electrolyzer.py and external review 2026-10).

Terminal vs stack: the IE-LIFT has an internal DC/DC converter. Telemetry
'Amperage'/'Voltage' are DC/DC OUTPUT (bus-side) values. The reverse-Faraday
route only runs on `*_stack_current_A` columns, which do not exist in the
current export. Until then, efficiency is the nameplate constant and the
returned dict says so.
"""
import numpy as np
from .. import registry as R
from ..conversions import energy_kWh_from_power
from ..hydrogen import h2_from_stack_current, h2_from_energy_nameplate
from ._common import t_seconds

class FuelCellSystem:
    def __init__(self, n_modules=2):
        self.n = n_modules

    def account(self, df, max_gap_s=30.0):
        t = t_seconds(df.index)
        P = df["fc_power_W"].values.astype(float)
        stack_cols = [c for c in df.columns if c.endswith("_stack_current_A")]
        term_cols = [c for c in df.columns if c.endswith("_current_A")
                     and "stack" not in c and c != "load_current_A"]
        keep = np.isfinite(P)
        if stack_cols:
            for c in stack_cols: keep &= np.isfinite(df[c].values.astype(float))
        elif term_cols:
            for c in term_cols: keep &= np.isfinite(df[c].values.astype(float))
        P, t, df = P[keep], t[keep], df[keep]
        from .electrolyzer import _sample_gaps
        dt, coverage = _sample_gaps(t, max_gap_s)
        e_out = float(np.sum(np.where(np.isfinite(P), P, 0.0) * dt) / 3.6e6)
        if stack_cols:
            h2 = h2_from_stack_current([df[c].fillna(0).values for c in stack_cols], dt,
                                       R.get("fc.n_cells"), R.get("fc.faradaic_efficiency"), device="fc")
            h2["route"] = "faraday_fc"; eff_is_measured = True
        else:
            h2 = h2_from_energy_nameplate(e_out, "fc"); eff_is_measured = False
        eta = e_out / h2["kWh_LHV"] if h2["kWh_LHV"] > 0 else None
        # control energy over OBSERVED time only: the first draft used
        # len(df) * mean(dt), which bridges data gaps and invents auxiliary
        # consumption during unobserved periods (violates the project's own
        # gap policy, fixed 2026-10; guarded by test_05b-style check in test_06).
        observed_s = float(np.sum(dt[~np.isnan(dt)])) if len(dt) else 0.0
        e_ctrl = R.get("fc.control_input_W_max") / 1000.0 * observed_s / 3600.0
        # control energy scales with the number of modules actually present in the frame
        n_modules = len(stack_cols) if stack_cols else len(term_cols)
        e_ctrl = e_ctrl * max(1, n_modules)
        I_bat = None
        if "load_current_A" in df.columns and term_cols:
            I_bat = df["load_current_A"].fillna(0).values - sum(df[c].fillna(0).values for c in term_cols)
        return dict(unit="FCU", energy_out_kWh=e_out, h2=h2, efficiency_LHV=eta,
                    efficiency_is_measured=eff_is_measured,
                    control_energy_kWh_envelope=e_ctrl, battery_current_residual_A=I_bat,
                    warning=None if eff_is_measured else
                    "FC efficiency is the nameplate constant (terminal current is not stack current)")
