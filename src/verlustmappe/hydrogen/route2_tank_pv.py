"""Route 2: hydrogen from storage tank pressure change, now with the
three-tier gas-temperature model (external review + papers 2026-10).

    delta n = V/R * [ p2/(Z(p2,T2) T2) - p1/(Z(p1,T1) T1) ]

The temperature is the weak input, not the pressure: since the DCT 541
transmitter replaced manual gauge readings, pressure uncertainty is
+-0.5% FSO (IEC 61298-2), i.e. +-1.25 bar on a 250-bar range. The gas
temperature inside an 800 L steel tank is NOT ambient for hours after a fill
(de Miguel IJHE 2015: +64-96 K on fast fills; Nexo study: isothermal/adiabatic
bracket, heat-exchange model is the tightest).

Tiers (see tank_thermal.py and handbook card C):
  tier 1: T = ambient, +-3 K placement/systematic, +-15 K fast-fill bias
          -> the isothermal/adiabatic bracket quantifies the latter
  tier 2: measured (top+bottom mean, or bottom-pipe), +-2 K placement
  tier 3: model T from the GS_tank fit (pressure-decay calibration)
"""
import numpy as np
from ..conversions import mol_from_pVT, mol_to_kg, mol_to_NL, kg_to_kWh_LHV
from .. import constants as C
from .. import registry as R
from .z_realgas import z_h2, Z_TABLE_UNCERTAINTY_REL
from .temperature_model import isothermal_adiabatic_bracket, tier1_temperature, tier2_temperature

def h2_from_tank_pressure(p_start_barg, p_end_barg, T_start_C=None, T_end_C=None,
                          tier=1, T_top_C=None, T_bottom_C=None, return_bracket=False):
    """tier 1: T from ambient assumption (registry-free, +-3 K + fast-fill bias)
    tier 2: T from measured sensors (pass T_top_C / T_bottom_C)
    """
    V = R.get("stor.volume_L") / 1000.0
    p1, p2 = p_start_barg + C.P_ATM_BAR, p_end_barg + C.P_ATM_BAR
    if tier == 2 and (T_top_C is not None or T_bottom_C is not None):
        T_start, u_T_start = tier2_temperature(T_top_C if T_top_C is not None else T_bottom_C,
                                               T_bottom_C)
        T_end, u_T_end = T_start, u_T_start
    else:
        T_start, u_T_start = tier1_temperature()
        T_end, u_T_end = T_start, u_T_start
    T_start_C = T_start if T_start_C is None else T_start_C
    T_end_C = T_end if T_end_C is None else T_end_C
    n1 = mol_from_pVT(p1, V, T_start_C + 273.15, z_h2(p1, T_start_C))
    n2 = mol_from_pVT(p2, V, T_end_C + 273.15, z_h2(p2, T_end_C))
    dmol = n2 - n1
    kg = mol_to_kg(dmol)
    # DCT 541 uncertainty: the absolute error per READING is fso_bar (0.5% of the
    # 250-bar full scale = 1.25 bar). It is NOT multiplied by the relative FSO
    # again (the first draft computed 0.5% x 1.25 bar = 0.006 bar, a unit error
    # that understated the pressure term by ~200x; fix validated against
    # delta-mass propagation in test_07).
    fso_abs = R.get("meas.p_sensor_fso_bar")
    amp = max(p1, p2) / max(abs(p2 - p1), 1e-9)
    u_T_frac = u_T_start / max(T_start_C + 273.15, 1.0)
    # Propagation (GUM, independent contributions):
    #  - pressure: the sensor error is ABSOLUTE (FSO-based, +-1.25 bar per
    #    reading, independent) -> sigma(dp) = fso_abs*sqrt(2), relative to the
    #    swing only: fso_abs*sqrt(2)/dp. NO extra p/dp factor: the first draft
    #    (and the first fix) multiplied by amp as well, double-amplifying the
    #    absolute term; amp applies only to RELATIVE errors (Z, T, V), whose
    #    effect on a DIFFERENCE grows with p/dp.
    #  - Z, T, V: relative errors, amplified by amp = p/dp.
    u = float(np.sqrt((fso_abs * np.sqrt(2) / max(p2 - p1, 1e-9))**2 +
                      (R.entry("stor.volume_L")["uncertainty"] * amp)**2 +
                      (Z_TABLE_UNCERTAINTY_REL * amp)**2 +
                      (u_T_frac * amp)**2))
    out = dict(route="tank_pv", mol=dmol, kg=kg, NL=mol_to_NL(dmol), kWh_LHV=kg_to_kWh_LHV(kg),
               uncertainty_rel=u, temperature_tier=tier,
               T_used_C=(T_start_C, T_end_C),
               independent_of=["faraday", "telemetry", "water", "nameplate"],
               blind_to=["nothing upstream; only sees net change in the tank"],
               note=("pressure uncertainty from DCT 541 (0.5%% FSO), amplification %.1f; "
                     "temperature tier %d" % (amp, tier)))
    if return_bracket and tier == 1:
        out["fast_fill_bracket"] = isothermal_adiabatic_bracket(
            p1, p2, R.get("stor.volume_L"), T_ambient_C=T_start_C, delta_T_K=15.0)
    return out
