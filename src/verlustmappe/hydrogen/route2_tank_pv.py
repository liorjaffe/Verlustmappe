"""Paused independent tank route and retained synthetic pVT model.

Route 2 is unavailable: DCT 541 is not installed, no tank temperature sensor exists
or is planned (owner 2026-11-20), and independent
tank-state data are missing. Scenario pressures/temperatures are not evidence.

model_tank_pressure_change retains synthetic physics/test calculations:
    delta n = V/R * [ p2/(Z(p2,T2) T2) - p1/(Z(p1,T1) T1) ]
Its legacy sensor-accuracy budget is hypothetical, never a validation input.

Tiers (see tank_thermal.py and handbook card C):
  tier 1: provisional registered temperature assumption (GUESS), no measured T;
          rectangular-band standard uncertainty plus separate existing 3 K allowance;
          +-15 K fast-fill scenario
          -> the isothermal/adiabatic bracket quantifies the latter
  tier 2: explicitly supplied synthetic/future temperature inputs, +-2 K placement
          (existing assumption, not sensor evidence). No tank temperature
          sensor exists or is planned (owner 2026-11-20).
  tier 3: model T from the GS_tank fit (pressure-decay calibration)
"""
import numpy as np
from ..physics.conversions import mol_from_pVT, mol_to_kg, mol_to_NL, kg_to_kWh_LHV
from ..physics import constants as C
from .. import registry as R
from .z_realgas import z_h2, Z_TABLE_UNCERTAINTY_REL
from .temperature_model import hot_end_fill_bracket, tier1_temperature, tier2_temperature
from .temperature_model import assumed_temperature_standard_uncertainty_K
from ..accounting.status import weakest

ROUTE2_UNAVAILABLE_REASON = (
    "Route 2 paused: independent tank pressure and suitable temperature data are missing; "
    "DCT 541 is not installed and no tank temperature sensor exists (owner 2026-11-20). "
    "Reactivation requires approved independent "
    "state data, connected volume/isolation, matching time boundaries and gas-flow accounting.")

def h2_from_tank_pressure(p_start_barg, p_end_barg, T_start_C=None, T_end_C=None,
                          tier=1, T_top_C=None, T_bottom_C=None, return_bracket=False,
                          bundle_isolated=None, *, analyze_temperature_uncertainty=False):
    """Independent countercheck is paused even if scenario inputs are supplied.

    No model quantity or sensor uncertainty substitutes for missing independent data.
    The signature is retained for callers; use model_tank_pressure_change explicitly
    for synthetic calculations, not independent route comparison.
    """
    return dict(route="tank_pv", availability="UNAVAILABLE", reason=ROUTE2_UNAVAILABLE_REASON,
                mol=None, kg=None, NL=None, kWh_LHV=None, uncertainty_rel=None,
                uncertainty_incomplete=True, independent_of=[], origin=None)


def model_tank_pressure_change(p_start_barg, p_end_barg, T_start_C=None, T_end_C=None,
                              tier=1, T_top_C=None, T_bottom_C=None, return_bracket=False,
                              bundle_isolated=None, *, analyze_temperature_uncertainty=False):
    """tier 1: T from registered provisional assumption unless explicitly supplied.
    tier 2: explicitly supplied synthetic/future inputs (T_top_C / T_bottom_C).
    The interface does not imply installed top/bottom sensors.
    The +/-10 K band is analyzed only on explicit request. The main calculation
    models the stated temperatures; existing route uncertainty terms are retained.
    """
    if bundle_isolated is None:
        raise ValueError("bundle_isolated is required: stor.volume_L = 800 L holds only while the "
                         "instrumented 16 x 50 L bundle is valved off from the second bundle. Pass True "
                         "in that case; if the bundles are connected, set stor.volume_L to the connected "
                         "volume and pass False.")
    if tier == 3:
        raise NotImplementedError("tier 3 (GS_tank model) is not wired in yet")
    if tier == 2 and T_top_C is None and T_bottom_C is None:
        raise ValueError("tier=2 requires explicit T_top_C or T_bottom_C; "
                         "no tank temperature sensor exists; no ambient fallback is allowed")

    V = R.get("stor.volume_L") / 1000.0
    p1, p2 = p_start_barg + C.P_ATM_BAR, p_end_barg + C.P_ATM_BAR
    temperature_is_assumed = tier != 2 and (T_start_C is None or T_end_C is None)
    both_temperatures_assumed = tier != 2 and T_start_C is None and T_end_C is None
    mixed_temperature_sources = temperature_is_assumed and not both_temperatures_assumed
    if tier == 2:
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
    # 400-bar full scale = 2.0 bar). It is NOT multiplied by the relative FSO
    # again (the first draft computed 0.5% x 1.25 bar = 0.006 bar, a unit error
    # that understated the pressure term by ~200x; fix validated against
    # delta-mass propagation in test_hydrogen_tank_thermal).
    fso_abs = R.get("meas.p_sensor_fso_bar")
    amp = max(p1, p2) / max(abs(p2 - p1), 1e-9)
    u_T_frac = u_T_start / max(T_start_C + 273.15, 1.0)
    analyze_assumption = analyze_temperature_uncertainty and temperature_is_assumed
    u_assumed_temperature_K = assumed_temperature_standard_uncertainty_K() if analyze_assumption else None
    # Owner-approved fixed-Z approximation: a common offset on two assumed
    # states contributes u_T/T, not independent per-reading sqrt(2) terms.
    u_assumed_temperature_rel = (
        u_assumed_temperature_K / (T_start_C + 273.15) if analyze_assumption and both_temperatures_assumed
        else None if not analyze_temperature_uncertainty or mixed_temperature_sources else 0.0)
    # Propagation (GUM, independent contributions):
    #  - pressure: the sensor error is ABSOLUTE (FSO-based, +-2.0 bar per
    #    reading, independent) -> sigma(dp) = fso_abs*sqrt(2), relative to the
    #    swing only: fso_abs*sqrt(2)/dp. NO extra p/dp factor: the first draft
    #    (and the first fix) multiplied by amp as well, double-amplifying the
    #    absolute term; amp applies only to RELATIVE errors (Z, T, V), whose
    #    effect on a DIFFERENCE grows with p/dp.
    #  - V and the common temperature offset (placement/systematic, same sign at
    #    both readings) are COMMON factors: they scale n1 and n2 alike, so they
    #    enter the mass difference 1:1 (no p/dp amplification).
    #  - Z: the table error depends on pressure, so it is not common to both
    #    readings; treated as independent per reading -> amplified by amp = p/dp.
    u = float(np.sqrt((fso_abs * np.sqrt(2) / max(abs(p2 - p1), 1e-9))**2 +
                      R.entry("stor.volume_L")["uncertainty"]**2 +
                      (Z_TABLE_UNCERTAINTY_REL * amp)**2 +
                      u_T_frac**2 +
                      (u_assumed_temperature_rel**2
                       if analyze_assumption and both_temperatures_assumed else 0.0)))
    out = dict(route="tank_pv_model", validation_eligible=False,
               mol=dmol, kg=kg, NL=mol_to_NL(dmol), kWh_LHV=kg_to_kWh_LHV(kg),
               uncertainty_rel=u, temperature_tier=tier,
               T_used_C=(T_start_C, T_end_C),
               temperature_is_assumed=temperature_is_assumed,
               temperature_status="GUESS" if temperature_is_assumed else None,
               evidence_status=weakest(("DATASHEET", R.entry("stor.T_assumed_C")["status"]))
               if temperature_is_assumed else None,
               origin="computed",
               temperature_uncertainty_analysis_requested=analyze_temperature_uncertainty,
               temperature_standard_uncertainty_K=u_assumed_temperature_K,
               temperature_assumption_uncertainty_rel=u_assumed_temperature_rel,
               temperature_model_allowance_K=u_T_start,
               temperature_model_allowance_rel=u_T_frac,
               temperature_correlation_assumption="fully common offset; owner model choice"
               if analyze_assumption and both_temperatures_assumed else "not assessed for mixed sources"
               if analyze_assumption and mixed_temperature_sources else "band analysis not performed"
               if not analyze_temperature_uncertainty else "no registered temperature assumption used",
               temperature_source=R.entry("stor.T_assumed_C")["source"]
               if temperature_is_assumed else "explicitly supplied; not automatically measured",
               uncertainty_incomplete=analyze_assumption and mixed_temperature_sources,
               uncertainty_note=("mixed explicit/assumed temperatures: correlation and difference "
                                 "propagation require reassessment; total shown is partial")
               if analyze_assumption and mixed_temperature_sources else
               ("GUESS rectangular band propagated as common-offset fixed-Z first-order u_T/T; "
                "3 K allowance separate; model uncertainty only, volume confirmation and measurement "
                "validation remain open")
               if analyze_assumption and both_temperatures_assumed else
               "defined model temperatures; no +/-10 K band analysis performed; "
               "existing route uncertainty terms are not measurement validation"
               if not analyze_temperature_uncertainty else
               "existing temperature allowance is not sensor validation",
               independent_of=[],
               blind_to=["nothing upstream; only sees net change in the tank"],
               note=("synthetic model only, NOT an independent Route 2 countercheck; "
                     "hypothetical planned DCT 541 accuracy (0.5%% FSO), amplification %.1f; "
                     "temperature tier %d" % (amp, tier)))
    if return_bracket and tier == 1:
        out["fast_fill_bracket"] = hot_end_fill_bracket(
            p1, p2, R.get("stor.volume_L"), T_ambient_C=T_start_C, delta_T_K=15.0)
    return out
