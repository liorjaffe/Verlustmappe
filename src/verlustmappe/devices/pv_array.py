"""PV measured-energy accounting; PV generation modelling is deferred."""

from .. import registry as R
from .pv_inverter import PVInverter, _validate_pv_measurements


def _generation_model():
    """Reserved for future PV generation modelling; no model or plant values are set."""
    raise NotImplementedError("PV generation modelling is deferred and not implemented")

def pv_account(H_poa_kWh_m2=None, A_array_m2=None, E_dc_measured_kWh=None, E_ac_measured_kWh=None,
               T_ambient_C=None, G_typical_W_m2=None, months=None, mode=None, profile=None,
               *, enable_generation_model=False):
    """Account for measured terminal energies; generation inputs are deferred.

    The historical F8 profile identifier selects the approved inverter model;
    no profile selects no inverter model. It is not a generation profile.
    """
    _validate_pv_measurements(E_dc_measured_kWh, E_ac_measured_kWh)
    if not isinstance(enable_generation_model, bool):
        raise ValueError("enable_generation_model must be a bool")
    if mode not in (None, "measured", "preliminary"):
        raise ValueError("mode must be 'measured' or 'preliminary'")
    if profile not in (None, "F8_12.74kWp"):
        raise ValueError(f"Unknown PV measured-energy profile: {profile!r}")
    status_mode = mode or ("measured" if (E_dc_measured_kWh is not None or
                                           E_ac_measured_kWh is not None) else "preliminary")
    if status_mode == "preliminary" or enable_generation_model:
        _generation_model()
    e_dc = E_dc_measured_kWh
    at_terminals = (status_mode == "measured" and E_dc_measured_kWh is not None
                    and E_ac_measured_kWh is not None)
    partial_measurement = status_mode == "measured" and not at_terminals
    e_ac = E_ac_measured_kWh

    bars = []
    inverter_diagnostics = None
    if at_terminals:
        if profile == "F8_12.74kWp":
            inverter_diagnostics = PVInverter().account(E_dc_measured_kWh, E_ac_measured_kWh)
            bars.append(dict(stage="Inverter conversion", kWh=inverter_diagnostics["loss_kWh"],
                             status=inverter_diagnostics["loss_status"],
                             note="INTERIM F8 EU efficiency model; uncertainty not assessed"))
        else:
            bars.append(dict(stage="Inverter conversion", kWh=None, status="MISSING",
                             note="No approved inverter model for this profile"))
    elif partial_measurement:
        bars += [
            dict(stage=stage, kWh=None, status="MISSING",
                 note="Incomplete measured DC/AC pair")
            for stage in ("Inverter conversion", "AC cable")
        ]
    out = dict(unit="PV", mode=status_mode, e_dc_kWh=e_dc, e_ac_kWh=e_ac, e_stc_kWh=None,
               T_cell_C=None, bars=bars,
               eta_dc_to_ac=(e_ac / e_dc) if e_ac is not None and e_dc is not None and e_dc > 0 else None,
               capture_ratio=None,
               missing_parameters=[],
               pv_start_boundary="inverter_dc_input",
               dc_cable_status="OUTSIDE_BOUNDARY",
               profile=profile,
               warning="PV generation modelling is deferred; no generation-model outputs calculated; "
                       "PV DC cable is upstream and outside this provisional boundary, not assumed lossless")
    if H_poa_kWh_m2 is not None:
        out["warning"] += "; supplied irradiation was not used"
    if partial_measurement:
        out["warning"] += "; incomplete measured DC/AC pair; dependent results are MISSING"
    if at_terminals:
        out["inverter_diagnostics"] = inverter_diagnostics
        out["eta_dc_to_ac_status"] = (
            "DIAGNOSTIC" if out["eta_dc_to_ac"] is not None else "MISSING")
        out["dc_minus_ac_diagnostic_kWh"] = (
            E_dc_measured_kWh - E_ac_measured_kWh
            if E_dc_measured_kWh != 0 or E_ac_measured_kWh == 0 else None)
        out["undefined_case"] = (
            "dc0_ac_nonzero" if E_dc_measured_kWh == 0 and E_ac_measured_kWh != 0 else None)
    return out


# --- Measured mode (formerly devices/pv_measured.py) ------------------------------
# PV array + inverter (legacy building array, not F8 evidence). Both DC and AC are MEASURED (SunSpec model 103),
# so their ratio and difference are diagnostics, not independently measured losses.
# Capture ratio (optional, needs plane-of-array irradiation and STC power):
#    CR = E_DC / (H_POA * P_STC)   (IEC 61724 performance-ratio family)
# With pv.p_dc_stc_W = 12740 W (F8 array, 28 x 455 Wp) the capture-ratio branch is
# ACTIVE for the F8 channel as soon as plane-of-array irradiation exists. For the
# legacy building-array telemetry (~184 kWp) 12740 W is NOT the right P_STC: keep the two plants
# separate.
# Review fix 1: `account(p_stc_W=...)` overrides the registry P_STC per plant; without it
# the result carries `p_stc_source` naming the registry default, never silently.

class PVSystem:
    def account(self, e_dc_kWh, e_ac_kWh, H_poa_kWh_m2=None, p_stc_W=None):
        _validate_pv_measurements(e_dc_kWh, e_ac_kWh)
        anomaly = e_dc_kWh == 0 and e_ac_kWh != 0
        res = dict(unit="PV", e_dc_kWh=e_dc_kWh, e_ac_kWh=e_ac_kWh,
                   inverter_loss_kWh=None, inverter_loss_status="MISSING",
                   dc_minus_ac_diagnostic_kWh=None if anomaly else e_dc_kWh - e_ac_kWh,
                   undefined_case="dc0_ac_nonzero" if anomaly else None,
                   inverter_eff=e_ac_kWh / e_dc_kWh if e_dc_kWh > 0 else None,
                   inverter_eff_status="DIAGNOSTIC" if e_dc_kWh > 0 else "MISSING",
                   energy_is_measured=True,
                   inverter_loss_note="No inverter model specified for this plant; DC-AC is diagnostic only")
        pstc = p_stc_W if p_stc_W is not None else R.get("pv.p_dc_stc_W")
        if H_poa_kWh_m2 is not None and pstc:
            # review fix 1: the registry P_STC belongs to the F8 array only
            res["p_stc_source"] = ("explicit p_stc_W argument" if p_stc_W is not None else
                                   "registry default (%.0f W, F8 array) - override p_stc_W for other plants" % pstc)
            ref = H_poa_kWh_m2 * pstc / 1000.0
            res["capture_ratio"] = e_dc_kWh / ref
        return res
