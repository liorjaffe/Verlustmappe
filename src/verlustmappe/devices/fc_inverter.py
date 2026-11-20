"""FC-side inverter: Solis S5-EO1P5K-48 off-grid, 48 V -> 230 V AC.

POSITION in the energy path: after the fuel cell system (fc_50_system.py),
converting the 48-52 V FC/battery bus to the 230 V island AC. This is the
LAST conversion before the load.

DEVICE (from the "Inverter 2" folder: datasheet, instruction manual, and a
nameplate photo with S/N 2051010224220020 - the unit is physically on site):
  - rated output 5 kVA / 5 kW (+-1%), 230 V +-1%, pure sine, 25 A max
  - battery voltage range 40-60 V: covers the FCM factory 52 V target bus voltage
  - surge capacity 10 kVA, transfer time 10 ms typical
  - communication CAN/BMS; parallel-capable variant exists (-P)

EFFICIENCY (CONTRACT §6, D3b): the datasheet 96.6% and the manual 93-95% are
PV->AC peak values and not evidence for the battery->AC discharge path, which
is unpublished. `inv_fc.eta` is the owner working value 0.94, status GUESS,
with the provisional envelope keys inv_fc.eta_envelope_lower/upper
(decisions/2026-11-18-fc-inverter-discharge-working-value.md).

MEASURED ENERGIES (owner 2026-11-19, same rule as the PV inverter): AC/DC of
the supplied window is reported as that window's eta; DC - AC is a diagnostic,
never a booked loss (CONTRACT §6). The booked loss is always modelled,
DC x (1 - inv_fc.eta). DC = 0 with AC != 0 is flagged `dc0_ac_nonzero`.

STANDBY: not published -> GUESS 20 W (inv_fc.standby_W), not used here.

POC RELEVANCE: the 10 ms transfer time is orders of magnitude below the
FCM-802 POC duration (~12 s), so this inverter does not mask POC events.
"""
import math
from numbers import Real

from .. import registry as R


def _validate(name, value, *, nonnegative=False):
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise ValueError(f"{name} must be finite")
    if nonnegative and value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


class FCInverter:
    def account(self, e_dc_in_kWh=None, e_ac_measured_kWh=None):
        """Modelled conversion loss from inv_fc.eta; measured energies give the window
        eta and a DC - AC diagnostic, never a booked loss."""
        _validate("e_dc_in_kWh", e_dc_in_kWh, nonnegative=True)
        _validate("e_ac_measured_kWh", e_ac_measured_kWh)
        dc, ac = e_dc_in_kWh, e_ac_measured_kWh
        measured = dc is not None and ac is not None
        anomaly = measured and dc == 0 and ac != 0
        eta_model = R.get("inv_fc.eta")
        eta_entry_status = R.entry("inv_fc.eta")["status"]
        model_valid = dc is not None and not anomaly
        model_ac = dc * eta_model if model_valid else None
        loss = dc * (1 - eta_model) if model_valid else None
        if measured:
            eta = ac / dc if dc > 0 else None
        else:
            eta = eta_model if dc is not None else None
        return dict(
            unit="INV_FC", device="Solis S5-EO1P5K-48",
            e_dc_in_kWh=dc, e_ac_kWh=ac if ac is not None else model_ac,
            loss_kWh=loss, loss_is_modelled=loss is not None,
            loss_status=eta_entry_status if loss is not None else "MISSING",
            eta=eta, eta_is_measured=measured and eta is not None,
            eta_status=("MISSING" if eta is None else
                        "WINDOW: status of the supplied energies" if measured else eta_entry_status),
            eta_model=eta_model, eta_model_status=eta_entry_status,
            model_ac_kWh=model_ac,
            dc_minus_ac_diagnostic_kWh=dc - ac if measured and not anomaly else None,
            model_minus_measured_ac_diagnostic_kWh=(
                model_ac - ac if measured and model_ac is not None else None),
            undefined_case="dc0_ac_nonzero" if anomaly else None,
            note=("loss modelled from inv_fc.eta (owner working value 0.94, GUESS, D3b; "
                  "PV-AC datasheet/manual values are not evidence for the discharge path). "
                  "DC - AC is a diagnostic, never a booked loss. A window eta from measured "
                  "energies is MEASURED only with an independent cross-check (D3b)."))
