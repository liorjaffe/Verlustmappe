"""Tank gas temperature: the missing input of Route 2, and what to do about it.

WHY THIS MODULE EXISTS (external review 2026-10 + papers in the Storage H2
folder): Route 2 (tank pV) assumed the gas temperature = ambient. The Nexo
on-board study measured exactly this error: assuming a fixed tank temperature
biases the hydrogen mass both ways - isothermal assumption OVERestimates mass
consumed, adiabatic assumption UNDERestimates it; only a model with heat
exchange (GS_tank = 70 W/K fitted on pressure decay) matched the reference.
For our 800 L steel cylinder the same logic applies, worse: 800 L has far more
thermal inertia than a 60 L vehicle tank, so the gas stays away from ambient
for hours after a fill.

THREE-TIER TEMPERATURE MODEL (used by tank_pv.py when Tier 2/3 data exists):

Tier 1 (today, no tank temperature sensor):
    Provisional gas temperature from stor.T_assumed_C (GUESS), not measurement.
    Its rectangular-band standard uncertainty is separate from the existing
    3 K model allowance; neither is a measured tank temperature.
    Literature warning: on fast fills the gas heats by 60-90 K (de Miguel:
    Delta T_avg = 64-96 K for Type IV, 64-77 K for Type III steel); the ambient
    assumption is then WRONG BY TENS OF KELVIN on a per-mass basis ~ (deltaT/T).
    Valid ONLY for slow cycles with long rest periods (hours).

Tier 2 (generic explicit inputs only):
    No tank temperature sensor exists or is planned (owner 2026-11-20). No measured tank temperature exists.
    The helper accepts only explicitly supplied synthetic temperatures;
    its top/bottom interface describes no hardware. Literature guidance:
      - during FILLING the gas is almost perfectly uniform (forced convection
        by the jet) -> ONE sensor anywhere in the gas is representative;
      - during HOLD/EMPTY the gas stratifies vertically -> top + bottom pair
        needed, mean is the estimate;
      - the Nexo study found the BOTTOM PIPE temperature (their T3) tracked the
        mean gas temperature best; surface temps lag with wall inertia.
    Existing synthetic uncertainty terms (placement bias 1-3 K, de Miguel
    Fig. 4/6 lag behaviour) are literature assumptions, not sensor evidence.

Tier 3 (model-based, no internal sensor):
    Lumped energy balance as in the Nexo paper (their eqs 2-3):
        m_H2 cv dT/dt = -(m_H2 cp) * dT term + GS_tank * (T_amb - T)
        p V = Z m R T
    GS_tank is FITTED on pressure decay during rest periods (their method:
    fill, then let the tank rest, fit dP/dt with mdot=0). We reproduce the
    same two-equation model below; CoolProp-class EoS is replaced by our
    Z table (hydrogen/z_realgas.py), accurate to +-1% here.

The isothermal / adiabatic bracket from the Nexo study is kept as the honest
uncertainty statement for Tier 1: the truth lies between the two, and for
slow-ish cycles the heat-exchange model is the tighter bound.
"""
import numpy as np
from ..physics import constants as C
from .. import registry as R
from .z_realgas import z_h2

def tier1_temperature(T_ambient_C=None):
    """Provisional temperature: registered assumption unless explicitly supplied.

    Returns the existing 3 K model allowance, separate from the registered
    rectangular-band uncertainty of the GUESS assumption.
    """
    if T_ambient_C is None:
        T_ambient_C = R.get("stor.T_assumed_C")
    # 1 K instrument/reading; +placement/systematic term because the gas is NOT
    # guaranteed at ambient (thermal inertia of an 800 L steel tank)
    return T_ambient_C, 3.0

def assumed_temperature_standard_uncertainty_K():
    """Registry uncertainty is relative to absolute temperature, never to degC."""
    entry = R.entry("stor.T_assumed_C")
    return entry["uncertainty"] * (entry["value"] + 273.15)

def tier2_temperature(T_top_C, T_bottom_C=None, method="mean"):
    """Tier 2: measured. Mean of top/bottom if both exist (stratification),
    single value otherwise. Placement uncertainty from the papers."""
    if T_bottom_C is not None:
        T = 0.5 * (T_top_C + T_bottom_C)
    else:
        T = T_top_C
    return T, 2.0   # placement bias (boss/pipe vs gas mean), papers Fig. 4/6

def gs_fit_from_pressure_decay(t_s, p_abs_bar, T_amb_C=20.0, V_L=None, Z_at=None,
                               steel_mass_kg=None, c_steel_kJ_per_kgK=0.47, return_detail=False):
    """Tier 3 calibration: fit GS_tank from pressure decay at rest (mdot = 0).
    Model: m cv dT/dt = GS (T_amb - T)  with  p V = Z m R T.
    The pressure decay follows p(t) = p_eq + (p0 - p_eq) exp(-t/tau) with
    tau = m cv / GS. Three-parameter fit (p0, p_eq, tau) by least squares on
    the ORIGINAL series - the naive linearisation with p_eq = last value fails
    whenever the exponential has not converged (found by test on synthetic data).
    steel_mass_kg: thermal mass of the steel (c ~ 0.46-0.48 kJ/kgK) that
    exchanges heat with the gas. It adds to the heat capacity, so the combined
    GS = (m_gas cv + m_steel c_steel) / tau is larger than the gas-only value.
    Returns (GS_tank_W_per_K, tau_s, fit_quality_r2); GS is the combined value
    when steel_mass_kg is given, otherwise gas-only. return_detail=True returns
    a dict with gas-only and combined GS.
    No registry steel mass is loaded: stor.steel_mass_kg is bundle TARA including
    the frame, NOT thermally effective mass. Passing that value requires an
    explicit upper-bound assumption; effective thermal mass remains open.
    Method: Nexo paper - same idea, they fitted GS = 70 W/K on a vehicle tank
    from resting-period pressure data.
    """
    p = np.asarray(p_abs_bar, float); t = np.asarray(t_s, float)
    if len(p) < 5: return None, None, None
    t0 = t - t[0]
    p0, p_eq0 = float(p[0]), float(p[-1])
    try:
        from scipy.optimize import curve_fit
        def model(tt, p_eq, amp, tau):
            return p_eq + amp * np.exp(-tt / np.maximum(tau, 1.0))
        popt, _ = curve_fit(model, t0, p, p0=[p_eq0, p0 - p_eq0, max(t0[-1] / 5.0, 60.0)],
                            maxfev=20000)
        p_eq, amp, tau = popt
        model_fit = model(t0, *popt)
    except Exception:
        # fallback: linearised fit with the last value as equilibrium
        y = np.log(np.maximum(p - p_eq0, 1e-9))
        A = np.vstack([t0, np.ones(len(t0))]).T
        k, _ = np.linalg.lstsq(A, y, rcond=None)[0]
        if k >= 0: return None, None, None
        tau, p_eq, amp = -1.0 / k, p_eq0, float(np.exp(y[0]))
        model_fit = p_eq + amp * np.exp(-t0 / tau)
    if not np.isfinite(tau) or tau <= 0:
        return None, None, None
    V_m3 = (V_L or R.get("stor.volume_L")) / 1000.0
    p_mean = float(np.mean(p))
    Z = z_h2(p_mean, T_amb_C) if Z_at is None else Z_at
    m = p_mean * 1e5 * V_m3 / (Z * C.R_J_PER_MOL_K * (T_amb_C + 273.15)) * C.M_H2_KG_PER_MOL
    cv = 10.2e3      # H2 cv ~ 10.2 kJ/(kg K) near ambient (CoolProp/standard tables)
    GS_gas = m * cv / tau
    GS = GS_gas
    GS_combined = None
    if steel_mass_kg:
        GS_combined = (m * cv + steel_mass_kg * c_steel_kJ_per_kgK * 1e3) / tau
        GS = GS_combined
    ss_res = float(np.sum((p - model_fit)**2)); ss_tot = float(np.sum((p - p.mean())**2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    if return_detail:
        return dict(GS=GS, tau_s=tau, r2=r2, GS_gas_only=GS_gas, GS_combined=GS_combined)
    return GS, tau, r2

def temperature_corrected_mass(p_abs_bar, V_L, T_gas_C):
    """Route 2 core, single point: mass from p, V, T with the real-gas Z."""
    Z = z_h2(p_abs_bar, T_gas_C)
    mol = (p_abs_bar * C.PA_PER_BAR) * (V_L / 1000.0) / (Z * C.R_J_PER_MOL_K * (T_gas_C + 273.15))
    return mol * C.M_H2_KG_PER_MOL

def isothermal_work_mol_integral(mol, p1_abs_bar, p2_abs_bar, T_K, p_suction_abs_bar=None):
    """Correct minimum (reversible, isothermal) work for FILLING a vessel.

    Physics: the compressor takes dm = V dp / (R T) per pressure increment from
    the SUCTION pressure p_s and compresses it to the current vessel pressure p,
    costing dW = dm R T ln(p/p_s). With the vessel rising from p1 to p2:

        W_ideal = (V/(R T)) * R T * [ G(p2) - G(p1) ] / (p2 - p1) * mol_added
                = mol * R T * [ G(p2) - G(p1) ] / (p2 - p1)
        with G(p) = p * ln(p/p_s) - p          (integral of ln(p/p_s) dp)

    where mol is the ADDED amount (compressor throughput) and V is recovered
    from mol = V (p2 - p1)/(R T). The old single-shot form n R T ln(p2/p1) is
    only correct when ALL mol are compressed at once to the final pressure; the
    first draft's arithmetic-mean shortcut (ln at (p_s + p_top)/2) overstated a
    20->200 bar fill by ~21% and understated 100->200 bar by ~16%. Fixed and
    verified against this closed form and against Monte-Carlo dm integration
    (test_hydrogen_routes; legacy test_03 in archive-2026-11).

    p_suction defaults to p1 (tank already at compressor inlet pressure). Pass
    the real suction (e.g. EL output 35 bar) when the tank starts above it.
    """
    import numpy as np
    from ..physics import constants as C
    p1, p2 = float(p1_abs_bar), float(p2_abs_bar)
    ps = float(p_suction_abs_bar) if p_suction_abs_bar is not None else p1
    if not (np.isfinite(p1) and np.isfinite(p2) and np.isfinite(ps)):
        raise ValueError("pressures must be finite")
    if p2 <= p1:
        return 0.0   # no fill, no compression work
    if ps <= 0:
        raise ValueError("suction pressure must be positive")
    if p2 <= ps:
        return 0.0   # tank stays below suction: no compression needed

    def G(p):
        return p * np.log(p / ps) - p

    p_work_start = max(p1, ps)
    w_per_mol = C.R_J_PER_MOL_K * T_K * (G(p2) - G(p_work_start)) / (p2 - p1)

    return float(mol * w_per_mol / C.J_PER_KWH)


def hot_end_fill_bracket(p1_abs_bar, p2_abs_bar, V_L, T_ambient_C=None, delta_T_K=15.0):
    """Tier-1 honesty bracket for a fast fill: the gas starts at ambient and is
    hot (ambient + delta_T) only at the END of the fill. The mass change
    assumed at ambient throughout (m_cold) is compared with the real one
    (start ambient, end hot). relative_spread = bias of the ambient assumption
    relative to the hot-end scenario (not a measured mass change).
    Missing base temperature uses stor.T_assumed_C."""
    temperature_is_assumed = T_ambient_C is None
    if temperature_is_assumed:
        T_ambient_C = R.get("stor.T_assumed_C")
    m_cold = (temperature_corrected_mass(p2_abs_bar, V_L, T_ambient_C)
              - temperature_corrected_mass(p1_abs_bar, V_L, T_ambient_C))
    m_hot_end = (temperature_corrected_mass(p2_abs_bar, V_L, T_ambient_C + delta_T_K)
                 - temperature_corrected_mass(p1_abs_bar, V_L, T_ambient_C))
    return dict(mass_cold_assumption_kg=m_cold, mass_hot_end_kg=m_hot_end,
                T_base_C=T_ambient_C, temperature_is_assumed=temperature_is_assumed,
                relative_spread=(m_cold - m_hot_end) / m_hot_end if m_hot_end else None,
                note=("bias of the ambient-T assumption for a fast fill (start ambient, "
                      "hot only at the end); delta_T_K should reflect the fill rate (papers: "
                      "64-96 K for fast fills, ~0 for slow ones)"))


# --- Fill work with unit-carrying names and domain checks (formerly models/temperature_model.py).
# Same physics as isothermal_work_mol_integral above; test_physics_and_params compares both.
# Ideal isothermal work of filling a vessel (fill integral, definition B in
# tests/reference/hand/isothermal_work.md).
#
# Filling from p1 to p2 delivers only (p2 - p1) V / (R T) mol, each compressed from the suction
# pressure ps to the current vessel pressure p:
#     W = n R T [G(p2) - G(p_start)] / (p2 - p1),   G(p) = p ln(p/ps) - p
# Ported from `hydrogen/temperature_model.isothermal_work_mol_integral`; behavior is identical,
# only names carry units. The closed-system form n R T ln(p2/p1) (definition A) is not ported:
# it has no active consumer in the legacy chain.

import math
from dataclasses import dataclass

@dataclass(frozen=True)
class FillWork:
    """Result of the fill integral. `exactly_zero` marks a physically exact zero (the integral
    is empty), so the ledger can tell it from "not computed"; `reason` names the case."""
    work_kWh: float
    exactly_zero: bool = False
    reason: str = ""


def isothermal_fill_work_kWh(amount_mol, p_start_abs_bar, p_end_abs_bar, T_K, p_suction_abs_bar=None):
    """Minimum isothermal work to add `amount_mol` while the vessel rises from p_start to
    p_end (absolute pressures). The suction pressure defaults to p_start.

    Two cases are an exact zero of the integral, not a clamp (flagged in the result): the vessel
    does not rise (p_end <= p_start) or stays below the suction pressure (p_end <= ps).
    A vessel starting below ps is compressed only from ps upward: gas flows in without
    compression work until the vessel reaches ps, so the integration starts at max(p_start, ps).
    """
    p1, p2 = float(p_start_abs_bar), float(p_end_abs_bar)
    ps = float(p_suction_abs_bar) if p_suction_abs_bar is not None else p1
    if not (math.isfinite(p1) and math.isfinite(p2) and math.isfinite(ps)):
        raise ValueError("pressures must be finite")
    if p2 <= p1:
        return FillWork(0.0, True, "vessel does not rise")
    if ps <= 0:
        raise ValueError("suction pressure must be positive")
    if p2 <= ps:
        return FillWork(0.0, True, "vessel stays below suction pressure")

    def G(p):
        return p * math.log(p / ps) - p

    p_work_start_abs_bar = max(p1, ps)
    work_J_per_mol = C.R_J_PER_MOL_K * T_K * (G(p2) - G(p_work_start_abs_bar)) / (p2 - p1)
    return FillWork(float(amount_mol * work_J_per_mol / C.J_PER_KWH))
