"""Fuel cell system: 2 x IE-LIFT 802 on a 48 V bus with a battery.

Same alignment rule as the electrolyser: terminal power and terminal current
must live on the same samples; unmatched rows are DROPPED, gaps are NOT
bridged (see el.py and external review 2026-10).

Terminal vs stack: the IE-LIFT has an internal DC/DC converter. Telemetry
'Amperage'/'Voltage' are DC/DC OUTPUT (bus-side) values. The reverse-Faraday
route only runs on `*_stack_current_A` columns, which do not exist in the
current export. Until then, efficiency is the nameplate constant and the
returned dict says so.
"""
import math

import numpy as np
from .. import registry as R
from ..accounting.status import weakest
from ..physics.conversions import energy_kWh_from_power
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
        from .el import _sample_gaps
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
        # gap policy, fixed 2026-10; guarded by a check in test_loaders_regatron).
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


# ---------------------------------------------------------------------------
# FCM-802 Performance Optimisation Cycle (POC), layer 1 static model
# ---------------------------------------------------------------------------
#
# Owner-approved plan: decisions/2026-11-19-fc-poc-plan.md. Layer 1 is modelled
# from manufacturer data (CONTRACT §3); nothing here is validated (layer 3).
#
# Conventions (owner 2026-11-19, named in every result):
# - the manual bounds are the case values: fc.poc_case_rate_per_h events per
#   hour per module, fc.poc_case_duration_s per event, module output fully
#   suspended; the battery carries the load (manual);
# - the recovery ramp after a POC is not modelled (E_bat may be low);
# - the battery round-trip loss is attributed to the recharge:
#   E_in = E_out / eta_rt, loss = E_in - E_out.
# H2 per event is MISSING (no manufacturer statement): no number.
POC_KEYS = ("fc.poc_case_rate_per_h", "fc.poc_case_duration_s", "fc.poc_max_rate_per_h",
            "fc.poc_max_duration_s", "fc.power_limit_W", "bat.round_trip_efficiency")
POC_CONVENTIONS = (
    "manual bounds used as case values: fc.poc_case_rate_per_h, fc.poc_case_duration_s "
    "(owner convention 2026-11-19)",
    "module output fully suspended during a POC; the battery carries the load",
    "recovery ramp after a POC not modelled: battery energy may be underestimated",
    "round-trip loss attributed to the recharge: E_in = E_out / eta_rt",
    "bat.round_trip_efficiency is a maker web value marked RECHECK",
)


def _poc_number(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name}: expected a finite number")
    return float(value)


def poc_layer1(P_W_per_module, n_modules):
    """Hourly POC effect at a static FC operating point (W per module).

    Returns energies per event and per hour, the battery stock change when the
    FC cannot recharge within its factory power limit, the throughput loss,
    the status (weakest input) and the conventions. Energies in Wh.
    """
    P = _poc_number(P_W_per_module, "P_W_per_module")
    if P < 0:
        raise ValueError("P_W_per_module: must be nonnegative")
    if isinstance(n_modules, bool) or not isinstance(n_modules, int) or n_modules < 1:
        raise ValueError("n_modules: expected a positive integer")

    n = _poc_number(R.get("fc.poc_case_rate_per_h"), "fc.poc_case_rate_per_h")
    t = _poc_number(R.get("fc.poc_case_duration_s"), "fc.poc_case_duration_s")
    p_lim = _poc_number(R.get("fc.power_limit_W"), "fc.power_limit_W")
    eta = _poc_number(R.get("bat.round_trip_efficiency"), "bat.round_trip_efficiency")
    if not 0 < eta <= 1:
        raise ValueError("bat.round_trip_efficiency: outside (0, 1]")
    t_on = 3600.0 - n * t
    if t_on <= 0:
        raise ValueError("POC case: events x duration fill the whole hour")

    warnings = []
    if n > R.get("fc.poc_max_rate_per_h"):
        warnings.append("case rate above the manual bound fc.poc_max_rate_per_h")
    if t > R.get("fc.poc_max_duration_s"):
        warnings.append("case duration above the manual bound fc.poc_max_duration_s")
    if P > p_lim:
        warnings.append("operating point above the factory output power limit fc.power_limit_W")

    # per module
    e_event = P * t / 3600.0                        # battery discharge per event
    e_out = n * e_event                             # battery discharge per hour
    e_in_needed = e_out / eta                       # recharge needed per hour
    e_in_available = max(0.0, p_lim - P) * t_on / 3600.0
    e_in = min(e_in_needed, e_in_available)
    loss = e_in - e_in * eta                        # round-trip loss of what is recharged
    stock_change = e_in * eta - e_out               # 0 if fully recharged, else negative
    p_recharge_max = p_lim / (1.0 + n * t / (eta * t_on))

    statuses = [R.entry(k)["status"] for k in POC_KEYS]
    return dict(
        unit="FC_POC", layer=1, n_modules=n_modules, P_W_per_module=P,
        events_per_h_per_module=n, duration_s_per_event=t,
        battery_Wh_per_event_per_module=e_event,
        battery_peak_W_if_coincident=P * n_modules,
        battery_discharge_Wh_per_h=e_out * n_modules,
        battery_recharge_Wh_per_h=e_in * n_modules,
        battery_stock_change_Wh_per_h=stock_change * n_modules,
        battery_throughput_loss_Wh_per_h=loss * n_modules,
        fully_recharged=e_in_needed <= e_in_available,
        P_max_W_for_full_recharge=p_recharge_max,
        h2_g_per_event=None, h2_status="MISSING",
        status=weakest(statuses), inputs={k: R.entry(k)["status"] for k in POC_KEYS},
        conventions=POC_CONVENTIONS, warnings=tuple(warnings),
    )
