"""PV array + SMA inverter. Both DC and AC are MEASURED (SunSpec model 103),
so the inverter loss is a measured bar, not an assumption.
   eta_inv = E_AC / E_DC ;  loss = E_DC - E_AC
Capture ratio (optional, needs plane-of-array irradiation and STC power):
   CR = E_DC / (H_POA * P_STC)   (IEC 61724 performance-ratio family)
"""
from .. import registry as R

class PVSystem:
    def account(self, e_dc_kWh, e_ac_kWh, H_poa_kWh_m2=None):
        res = dict(unit="PV", e_dc_kWh=e_dc_kWh, e_ac_kWh=e_ac_kWh,
                   inverter_loss_kWh=e_dc_kWh - e_ac_kWh,
                   inverter_eff=e_ac_kWh / e_dc_kWh if e_dc_kWh > 0 else None, energy_is_measured=True)
        pstc = R.get("pv.p_dc_stc_W")
        if H_poa_kWh_m2 is not None and pstc:
            ref = H_poa_kWh_m2 * pstc / 1000.0
            res.update(capture_ratio=e_dc_kWh / ref, pv_capture_loss_kWh=ref - e_dc_kWh)
        return res
