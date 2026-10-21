"""Preliminary PV channel: energy generation and losses from irradiance to AC.

STATUS: "vorerst" (preliminary). No real PV modules, inverter, cables or
distances have been chosen. Every number comes from the registry as PRELIM
(typical-market value anchored on published 2025/26 datasheet ranges) or
BACKLOG. When real hardware exists: replace registry entries, flip statuses
to DATASHEET/MEASURED, and the SAME functions produce the final numbers.

Chain (per IEC 61724 performance-ratio family and standard PV loss decomposition,
e.g. PVsyst/SAM loss trees):
    irradiation (POA) -> soiling/mismatch/shading -> DC at cell temperature
    -> DC cable -> inverter (Euro efficiency) -> AC cable -> AC to the bus

  E_DC,STC = H_POA * A_array * eta_module          (STC potential)
  E_DC     = E_DC,STC * (1 - soiling)(1 - mismatch)(1 - shading)
             * [1 + gamma_Pmax * (T_cell - 25)]     (temp derating, gamma<0)
             * (1 + bifacial_gain)                   (optional)
  E_AC     = E_DC * (1 - dc_cable) * eta_euro * (1 - ac_cable)
  capture ratio (performance ratio family): E_DC / (H_POA * A * eta_module)

Two modes of operation:
  mode 'measured' (SMA telemetry exists): E_DC and E_AC come from the inverter
  directly (as already done in devices/pv_measured.py); this channel only ADDS the
  site-loss bars that the inverter cannot see (soiling, mismatch, shading,
  temperature), each flagged GUESS/PRELIM.
  mode 'preliminary' (no hardware, no telemetry): everything computed from
  irradiation + registry PRELIM values, whole result labelled PRELIM.
"""
import numpy as np
from .. import registry as R

# Plant profiles override the registry module values per call. The default
# "reference_184kWp" holds the former PRELIM values (the paper-comparison anchor,
# bit-for-bit unchanged); "F8_12.74kWp" is the real BYD array (DATASHEET values).
# F8 numbers are derived in tests/test_10_pv_f8.py, not typed independently:
# 28 x 455 W = 12740 W; 2.094 x 1.038 x 28 = 60.86 m2.
PLANT_PROFILES = {
    "reference_184kWp": dict(
        name="UFSC reference array (184 kWp, PRELIM module values)",
        eta_module=0.220, gamma_pmax=-0.0029, noct_C=43.0, bifacial_gain=0.05,
        p_dc_stc_W=None, A_array_m2=None, module_status="PRELIM", warning=None),
    "F8_12.74kWp": dict(
        name="F8 Fachada Leste (BYD 28 x 455 Wp)",
        eta_module=0.209, gamma_pmax=-0.0038, noct_C=45.0, bifacial_gain=0.0,
        p_dc_stc_W=12740.0, A_array_m2=60.86, module_status="DATASHEET",
        orientation="east vertical facade - POA placeholder NOT valid for optimal tilt",
        warning="POA placeholder not valid for east-vertical facade"),
}
DEFAULT_PROFILE = "reference_184kWp"

def cell_temperature(T_ambient_C, G_W_m2, noct_C=None):
    """Sandia/NOCT-style cell temperature: T_cell = T_amb + (NOCT-20)/800 * G."""
    noct = noct_C if noct_C is not None else R.get("pv.noct_C")
    return T_ambient_C + (noct - 20.0) / 800.0 * G_W_m2

def pv_account(H_poa_kWh_m2=None, A_array_m2=None, E_dc_measured_kWh=None, E_ac_measured_kWh=None,
               T_ambient_C=25.0, G_typical_W_m2=800.0, months=1.0, mode=None, profile=None):
    """Returns the loss map bars for the PV channel plus the AC energy delivered
    to the bus. See module docstring for the two modes. `profile` selects a
    PLANT_PROFILES entry for the module values (default: reference_184kWp)."""
    prof = PLANT_PROFILES[profile or DEFAULT_PROFILE]
    if A_array_m2 is None:
        A_array_m2 = prof["A_array_m2"]
    status_mode = mode or ("measured" if (E_dc_measured_kWh and E_ac_measured_kWh) else "preliminary")
    if status_mode == "preliminary" and (H_poa_kWh_m2 is None or A_array_m2 is None):
        return dict(unit="PV", mode="preliminary", bars=[], error=
                    "preliminary mode needs irradiation (H_poa) and array area; "
                    "neither exists yet - install sensors or enter the design")
    eta_stc = prof["eta_module"]
    if status_mode == "preliminary":
        e_stc = H_poa_kWh_m2 * A_array_m2 * eta_stc
    else:
        # measured DC is the anchor; STC potential still useful for the capture bar
        e_stc = H_poa_kWh_m2 * A_array_m2 * eta_stc if (H_poa_kWh_m2 and A_array_m2) else None
    # site losses (GUESS/PRELIM family)
    soiling = R.get("pv.soiling_rel"); mismatch = R.get("pv.mismatch_rel"); shading = R.get("pv.shading_rel")
    # cell temperature derating
    T_cell = cell_temperature(T_ambient_C, G_typical_W_m2, noct_C=prof["noct_C"])
    gamma = prof["gamma_pmax"]
    bif = prof["bifacial_gain"]
    temp_factor = 1.0 + gamma * (T_cell - 25.0)
    if status_mode == "preliminary":
        e_dc = e_stc * (1-soiling) * (1-mismatch) * (1-shading) * temp_factor * (1 + bif)
    else:
        e_dc = E_dc_measured_kWh
    # cables + inverter
    e_after_dc_cable = e_dc * (1 - R.get("cable.dc_loss_rel"))
    e_ac_conv = e_after_dc_cable * R.get("inv_pv.eta_euro")
    e_ac = e_ac_conv * (1 - R.get("cable.ac_loss_rel"))
    if status_mode == "measured" and E_ac_measured_kWh is not None:
        e_ac = E_ac_measured_kWh   # the inverter sees its own AC; bars below stay preliminary

    # measured DC and AC are both taken AT the inverter terminals: the inverter
    # bar is then the measured difference and no cable loss exists in between
    at_terminals = (status_mode == "measured" and E_dc_measured_kWh is not None
                    and E_ac_measured_kWh is not None)
    bars = []
    if e_stc:
        # sequential site losses so that the bars sum exactly to E_stc - E_dc
        e1 = e_stc * (1 - soiling); e2 = e1 * (1 - mismatch); e3 = e2 * (1 - shading)
        e4 = e3 * temp_factor
        temp_bar = dict(stage="Cell temperature", kWh=e3 - e4, status="PRELIM")
        if prof["module_status"] == "DATASHEET":
            temp_bar.update(status="DERIVED", note="DERIVED (DATASHEET coeffs, PRELIM irradiance)")
        bars += [
            dict(stage="Soiling", kWh=e_stc - e1, status="PRELIM"),
            dict(stage="Mismatch", kWh=e1 - e2, status="PRELIM"),
            dict(stage="Shading", kWh=e2 - e3, status="PRELIM"),
            temp_bar,
            dict(stage="Bifacial gain", kWh=-e4 * bif, status="PRELIM"),
        ]
    if at_terminals:
        bars.append(dict(stage="Inverter conversion", kWh=E_dc_measured_kWh - E_ac_measured_kWh, status="MEASURED"))
    else:
        bars += [
            dict(stage="DC cable", kWh=e_dc * R.get("cable.dc_loss_rel"), status="PRELIM"),
            dict(stage="Inverter conversion", kWh=e_after_dc_cable * (1 - R.get("inv_pv.eta_euro")), status="PRELIM"),
            dict(stage="AC cable", kWh=e_ac_conv * R.get("cable.ac_loss_rel"), status="PRELIM"),
        ]
    out = dict(unit="PV", mode=status_mode, e_dc_kWh=e_dc, e_ac_kWh=e_ac, e_stc_kWh=e_stc,
               T_cell_C=T_cell, bars=bars,
               eta_dc_to_ac=(e_ac / e_dc) if e_dc > 0 else None,
               capture_ratio=(e_dc / e_stc) if (e_stc and e_stc > 0) else None,
               profile=profile or DEFAULT_PROFILE,
               warning="PRELIMINARY PV channel: all site losses are typical-market guesses; "
                       "replace registry PRELIM entries when hardware and layout exist")
    if prof["warning"]:
        out["warning"] += "; " + prof["warning"]
    return out
