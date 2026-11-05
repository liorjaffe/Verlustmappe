"""FC-side inverter: Solis S5-EO1P5K-48 off-grid, 48 V -> 230 V AC.

POSITION in the energy path: after the fuel cell system (fc_50_system.py),
converting the 48-52 V FC/battery bus to the 230 V island AC. This is the
LAST conversion before the load.

DEVICE (from the "Inverter 2" folder: datasheet, instruction manual, and a
nameplate photo with S/N 2051010224220020 - the unit is physically on site):
  - rated output 5 kVA / 5 kW (+-1%), 230 V +-1%, pure sine, 25 A max
  - battery voltage range 40-60 V: covers the FCM-802-regulated 52 V bus
  - surge capacity 10 kVA, transfer time 10 ms typical
  - communication CAN/BMS; parallel-capable variant exists (-P)

EFFICIENCY - registered carefully because the two documents disagree:
  - datasheet: peak efficiency (PV-AC path) 96.6%
  - instruction manual series table: peak efficiency (PV-AC) 93-95%
  Both refer to the PV->AC path (MPPT boost + inverter). The BATTERY->AC
  discharge path - the one we need for the fuel-cell loss map - is not
  explicitly published. Working value: 0.94 (midpoint of the manual range),
  status DERIVED. PV string inverters reach 98% because of high DC string
  voltage; this device steps up from 40-60 V, so conduction losses are higher.
  MEASURE on the installed unit to replace it.

STANDBY: not published -> GUESS 20 W +-50%.

POC RELEVANCE: the 10 ms transfer time is orders of magnitude below the
FCM-802 POC duration (~12 s), so this inverter does not mask POC events.
"""
import numpy as np
from .. import registry as R

class FCInverter:
    def account(self, e_dc_in_kWh=None, e_ac_measured_kWh=None):
        """Measured mode when the AC output is metered (e_ac_measured given);
        otherwise DERIVED 0.94 discharge-path estimate from the registry."""
        if e_dc_in_kWh and e_ac_measured_kWh:
            eta = e_ac_measured_kWh / e_dc_in_kWh
            return dict(unit="INV_FC", device="Solis S5-EO1P5K-48",
                        e_dc_in_kWh=e_dc_in_kWh, e_ac_kWh=e_ac_measured_kWh,
                        loss_kWh=e_dc_in_kWh - e_ac_measured_kWh, eta=eta,
                        eta_is_measured=True)
        eta = R.get("inv_fc.eta")
        e_ac = e_dc_in_kWh * eta if e_dc_in_kWh else None
        return dict(unit="INV_FC", device="Solis S5-EO1P5K-48",
                    e_dc_in_kWh=e_dc_in_kWh, e_ac_kWh=e_ac,
                    loss_kWh=e_dc_in_kWh * (1 - eta) if e_dc_in_kWh else None, eta=eta,
                    eta_is_measured=False,
                    note=("eta = 0.94 = midpoint of the manual range 93-95%; "
                          "datasheet 96.6% refers to the PV-AC path, not battery->AC; "
                          "MEASURE on the installed unit"))
