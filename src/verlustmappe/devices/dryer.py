"""Dryers DRY 2.1 (35 bar): two units, TSA/PSA with two alternating cartridges each.

Coupling (owner, 2026-11-19): the dryers run only while the EL are switched on
(production and start-up phases) and dry the produced H2.

Electrical energy
  Value: dryer.spec_energy_kWh_Nm3 x H2 throughput (owner decision 2026-11-19,
  production-coupled). Envelope (not a value): lower = standby power x units x
  EL on-time, upper = rated power x units x EL on-time (window if the on-time is
  unknown). The 200 W rating and 0.045 kWh/Nm3 (112.5 W at 2.5 Nm3/h) are not
  reconciled by the manufacturer; a meter reading replaces the model.

H2 losses (purge)
  No sourced loss fraction exists. The value stays open (BACKLOG) unless a
  measured purge volume is given. Envelope: 0 to regeneration purge maximum x
  units x EL on-time + shutdown purge maximum x dryer shutdown events. The
  shutdown part stays open without an event count.

Capacity checks: average H2 flow over the EL on-time vs units x rated drying
rate; per unit: EL 1-5 feed one dryer, EL 6-9 the other (owner, 2026-11-20), so
5 EL x nominal EL rate vs the rated drying rate of one dryer.
"""
import math
from numbers import Real

from .. import registry as R
from ..physics.conversions import NL_to_kg, kg_to_kWh_LHV


def _nonneg(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


class Dryer:
    def account(self, duration_h, throughput_NL, measured_kWh=None, el_on_h=None,
                n_shutdowns=None, measured_gas_loss_NL=None):
        """Electrical energy and H2 purge of both dryers over a window.

        duration_h            window length [h]
        throughput_NL         H2 dried in the window = H2 production [NL]
        measured_kWh          metered energy of both dryers (replaces the model)
        el_on_h               hours the EL (and thus the dryers) are switched on,
                              incl. start-up phases; None = unknown
        n_shutdowns           dryer shutdown events in the window, summed over units
        measured_gas_loss_NL  measured purge H2 of both dryers (telemetry)
        """
        _nonneg("duration_h", duration_h)
        if duration_h == 0:
            raise ValueError("duration_h must be > 0")
        for name, value in (("throughput_NL", throughput_NL), ("measured_kWh", measured_kWh),
                            ("el_on_h", el_on_h), ("n_shutdowns", n_shutdowns),
                            ("measured_gas_loss_NL", measured_gas_loss_NL)):
            if value is not None:
                _nonneg(name, value)
        if el_on_h is not None and el_on_h > duration_h:
            raise ValueError("el_on_h must not exceed duration_h")

        n = R.get("dryer.n_units")
        p_op = R.get("dryer.power_operative_W")
        p_stb = R.get("dryer.power_standby_W")
        spec = R.get("dryer.spec_energy_kWh_Nm3")
        rate = R.get("dryer.rate_Nm3h")
        purge_h = R.get("dryer.regen_purge_max_NLh")
        purge_sd = R.get("dryer.shutdown_purge_max_NL")
        for key, value in (("dryer.n_units", n), ("dryer.power_operative_W", p_op),
                           ("dryer.power_standby_W", p_stb), ("dryer.spec_energy_kWh_Nm3", spec),
                           ("dryer.rate_Nm3h", rate), ("dryer.regen_purge_max_NLh", purge_h),
                           ("dryer.shutdown_purge_max_NL", purge_sd)):
            _nonneg(key, value)

        warnings = []
        t_on = duration_h if el_on_h is None else el_on_h
        on_label = "EL on-time" if el_on_h is not None else "whole window (EL on-time unknown)"

        # electrical
        e_model = spec * throughput_NL / 1000.0
        e_env = dict(lower_kWh=None if el_on_h is None else p_stb * n * el_on_h / 1000.0,
                     upper_kWh=p_op * n * t_on / 1000.0,
                     label=("ENVELOPE, not a value. Lower: standby power x units x EL "
                            "on-time (open if unknown). Upper: rated power x units x "
                            + on_label + "."))
        if e_env["lower_kWh"] is not None and e_model < e_env["lower_kWh"]:
            warnings.append("dryer: production-coupled energy is below the standby floor "
                            "(EL on without matching production, e.g. start-up); not clipped")
        if e_model > e_env["upper_kWh"]:
            warnings.append("dryer: production-coupled energy exceeds the rated-power bound")
        energy_is_measured = measured_kWh is not None
        e = measured_kWh if energy_is_measured else e_model
        if not energy_is_measured:
            warnings.append("dryer electrical energy is modelled from 0.045 kWh/Nm3 (DATASHEET); "
                            "200 W rating not reconciled; meter the dryers for a MEASURED bar")

        # H2 purge
        regen_max = purge_h * n * t_on
        sd_max = None if n_shutdowns is None else purge_sd * n_shutdowns
        gas_env = dict(lower_NL=0.0,
                       upper_regen_NL=regen_max,
                       upper_shutdown_NL=sd_max,
                       upper_NL=None if sd_max is None else regen_max + sd_max,
                       label=("ENVELOPE, not a value. Regeneration: max purge rate x units x "
                              + on_label + "; shutdown: max purge per event x events "
                              "(open without an event count)."))
        if measured_gas_loss_NL is not None:
            gas_NL, gas_status = measured_gas_loss_NL, "MEASURED"
        else:
            gas_NL, gas_status = None, "BACKLOG"
            warnings.append("dryer H2 purge loss OPEN (BACKLOG): no sourced loss fraction; "
                            "only an envelope is reported, dependent sums stay open per "
                            "CONTRACT sec. 7")
        if n_shutdowns is None:
            warnings.append("dryer shutdown purge bound OPEN: shutdown event count not given")

        # capacity
        if t_on > 0:
            flow = throughput_NL / 1000.0 / t_on
            cap = dict(status="PASS" if flow <= n * rate else "FAIL",
                       detail=f"average {flow:g} Nm3/h over {on_label} vs {n:g} x {rate:g} Nm3/h")
        else:
            cap = dict(status="OPEN", detail="no on-time")
        if cap["status"] == "FAIL":
            warnings.append(f"dryer capacity check FAILED: {cap['detail']}")
        max_el = R.REGISTRY.get("dryer.max_el_per_unit", {}).get("value")
        el_rate = R.get("el.production_rate_NLh")
        if max_el is None:
            unit_cap = dict(status="OPEN", detail="EL-to-dryer assignment unknown")
        else:
            _nonneg("dryer.max_el_per_unit", max_el)
            unit_flow = max_el * el_rate / 1000.0
            margin = rate - unit_flow
            unit_cap = dict(status="PASS" if unit_flow <= rate else "FAIL",
                            detail=(f"{max_el:g} EL x {el_rate:g} NL/h = {unit_flow:g} Nm3/h vs "
                                    f"{rate:g} Nm3/h per dryer (margin {margin:g} Nm3/h"
                                    + ("; at the rating limit" if margin == 0 else "") + ")"))
        if unit_cap["status"] == "FAIL":
            warnings.append(f"dryer per-unit capacity check FAILED: {unit_cap['detail']}")
        elif unit_cap["status"] == "PASS" and margin == 0:
            warnings.append("dryer: the 5-EL group loads one dryer exactly at its rated "
                            "drying rate at nominal EL output (no margin)")
        checks = dict(total_capacity=cap, per_unit_capacity=unit_cap)

        return dict(unit="DRY", n_units=n,
                    energy_kWh=e, energy_is_measured=energy_is_measured,
                    energy_kWh_model=e_model, energy_envelope=e_env,
                    gas_loss_NL=gas_NL, gas_loss_status=gas_status,
                    gas_loss_kWh_LHV=None if gas_NL is None else kg_to_kWh_LHV(NL_to_kg(gas_NL)),
                    gas_loss_envelope=gas_env,
                    checks=checks, warnings=warnings)
