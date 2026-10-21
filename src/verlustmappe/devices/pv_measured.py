"""PV array + SMA inverter. Both DC and AC are MEASURED (SunSpec model 103),
so the inverter loss is a measured bar, not an assumption.
   eta_inv = E_AC / E_DC ;  loss = E_DC - E_AC
Capture ratio (optional, needs plane-of-array irradiation and STC power):
   CR = E_DC / (H_POA * P_STC)   (IEC 61724 performance-ratio family)
With pv.p_dc_stc_W = 12740 W (F8 array, 28 x 455 Wp) the capture-ratio branch is
ACTIVE for the F8 channel as soon as plane-of-array irradiation exists. For the
legacy SMA telemetry (~184 kWp) 12740 W is NOT the right P_STC: keep the two plants
separate.
Review fix 1: `account(p_stc_W=...)` overrides the registry P_STC per plant; without it
the result carries `p_stc_source` naming the registry default, never silently.
"""
from .. import registry as R

class PVSystem:
    def account(self, e_dc_kWh, e_ac_kWh, H_poa_kWh_m2=None, p_stc_W=None):
        res = dict(unit="PV", e_dc_kWh=e_dc_kWh, e_ac_kWh=e_ac_kWh,
                   inverter_loss_kWh=e_dc_kWh - e_ac_kWh,
                   inverter_eff=e_ac_kWh / e_dc_kWh if e_dc_kWh > 0 else None, energy_is_measured=True)
        pstc = p_stc_W if p_stc_W is not None else R.get("pv.p_dc_stc_W")
        if H_poa_kWh_m2 is not None and pstc:
            # review fix 1: the registry P_STC belongs to the F8 array only
            res["p_stc_source"] = ("explicit p_stc_W argument" if p_stc_W is not None else
                                   "registry default (%.0f W, F8 array) - override p_stc_W for other plants" % pstc)
            ref = H_poa_kWh_m2 * pstc / 1000.0
            res.update(capture_ratio=e_dc_kWh / ref, pv_capture_loss_kWh=ref - e_dc_kWh)
        return res
