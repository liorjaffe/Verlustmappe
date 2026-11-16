"""F8 PV-side inverter (PV DC -> AC bus), identified by model and serial numbers.

Kept SEPARATE from the FC-side inverter on purpose: different devices,
different DC voltage classes, different efficiency behaviour, and they must
stay separately analysable for the loss map.

MEASURED mode (legacy building-array telemetry exists, not F8 evidence): E_DC and E_AC both measured,
eta = E_AC / E_DC. Our 22-day window: energy-weighted 0.9719; load-dependent
~0.62 below 2 kW, 0.92 at 2-10 kW, 0.97 at 10-30 kW, 0.98 above.
Model mode: DATASHEET EU-efficiency anchor used as an interim constant (DERIVED),
not an F8 part-load curve. Exact standby consumption remains missing.
"""
import math
from numbers import Real

from .. import registry as R


def _validate_measured_energy(name, value, *, nonnegative=False):
    if value is None:
        return
    valid = not isinstance(value, bool) and isinstance(value, Real) and math.isfinite(value)
    if not valid or (nonnegative and value < 0):
        requirement = "finite and nonnegative" if nonnegative else "finite"
        raise ValueError(f"{name} must be {requirement}")


def _validate_pv_measurements(e_dc_kWh, e_ac_kWh):
    _validate_measured_energy("e_dc_kWh", e_dc_kWh, nonnegative=True)
    _validate_measured_energy("e_ac_kWh", e_ac_kWh)

class PVInverter:
    def account(self, e_dc_kWh=None, e_ac_kWh=None):
        """Return measured readings and separate interim-model and diagnostic values."""
        _validate_pv_measurements(e_dc_kWh, e_ac_kWh)
        measured = e_dc_kWh is not None and e_ac_kWh is not None
        anomaly = measured and e_dc_kWh == 0 and e_ac_kWh != 0
        eta_model = R.get("inv_pv.eta_euro")
        model_valid = e_dc_kWh is not None and not anomaly
        model_ac = e_dc_kWh * eta_model if model_valid else None
        loss = e_dc_kWh * (1 - eta_model) if model_valid else None
        eta = (e_ac_kWh / e_dc_kWh if measured and e_dc_kWh > 0 else
               eta_model if not measured and e_dc_kWh is not None and e_dc_kWh > 0 else None)
        return dict(
            unit="INV_PV", e_dc_kWh=e_dc_kWh,
            e_ac_kWh=e_ac_kWh if e_ac_kWh is not None else model_ac,
            loss_kWh=loss, loss_status="INTERIM DERIVED" if loss is not None else "MISSING",
            loss_is_modelled=loss is not None, eta=eta,
            eta_is_measured=False,
            eta_based_on_measured_energies=measured and eta is not None,
            eta_status=("MISSING" if eta is None else
                        "DIAGNOSTIC" if measured else R.entry("inv_pv.eta_euro")["status"]),
            eta_anchor_status=R.entry("inv_pv.eta_euro")["status"],
            eta_model_status="DERIVED", uncertainty_rel=None, standby_kWh=None,
            model_ac_kWh=model_ac,
            dc_minus_ac_diagnostic_kWh=(e_dc_kWh - e_ac_kWh if measured and not anomaly else None),
            model_minus_measured_ac_diagnostic_kWh=(
                model_ac - e_ac_kWh if measured and model_ac is not None else None),
            undefined_case="dc0_ac_nonzero" if anomaly else None,
            note="INTERIM constant EU efficiency, DATASHEET anchor; curve BACKLOG, "
                 "efficiency uncertainty not assessed, no part-load coverage. "
                 "Low-load efficiency may be overestimated and losses underestimated; "
                 "not verified for F8. DC/AC differences are diagnostics, not losses; "
                 "their causes and the AC measurement boundary remain open. "
                 "Standby energy missing (<1 W per unit is a bound, not a point value).")
