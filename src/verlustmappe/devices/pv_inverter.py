"""PV-side inverter (PV DC -> AC bus), position 04 in the energy-flow order.

Kept SEPARATE from the FC-side inverter (inverter.py) on purpose: different devices,
different DC voltage classes, different efficiency behaviour, and they must
stay separately analysable for the loss map.

MEASURED mode (legacy building-array telemetry exists, not F8 evidence): E_DC and E_AC both measured,
eta = E_AC / E_DC. Our 22-day window: energy-weighted 0.9719; load-dependent
~0.62 below 2 kW, 0.92 at 2-10 kW, 0.97 at 10-30 kW, 0.98 above.
PRELIM mode: Euro-efficiency assumption from the registry (inv_pv.eta_euro).
"""
import numpy as np
from .. import registry as R

class PVInverter:
    def account(self, e_dc_kWh=None, e_ac_kWh=None):
        """Measured mode when both energies given; else PRELIM estimate."""
        if e_dc_kWh and e_ac_kWh:
            eta = e_ac_kWh / e_dc_kWh
            return dict(unit="INV_PV", e_dc_kWh=e_dc_kWh, e_ac_kWh=e_ac_kWh,
                        loss_kWh=e_dc_kWh - e_ac_kWh, eta=eta, eta_is_measured=True,
                        standby_kWh=0.0,
                        note="measured DC and AC (SunSpec model 103 + Total Yield)")
        eta = R.get("inv_pv.eta_euro")
        return dict(unit="INV_PV", e_dc_kWh=e_dc_kWh, e_ac_kWh=e_dc_kWh * eta if e_dc_kWh else None,
                    loss_kWh=e_dc_kWh * (1 - eta) if e_dc_kWh else None, eta=eta,
                    eta_is_measured=False, standby_kWh=0.0,
                    note="PRELIM Euro efficiency; legacy-array telemetry would make this measured")
