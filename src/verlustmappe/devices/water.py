"""Water-system energy and water account for electrolyser supply.

The water chain is included in the plant energy balance because the RO unit
consumes electrical energy. Water demand is taken from a measured value or
caller input when available; otherwise it is derived from actual H2 production.
That H2-based estimate is the stoichiometric minimum. Purges and bleeds may add
water demand and are not modelled. If neither a water value nor H2 production
is provided, the model uses the configured nominal electrolyser water rate as
a fallback and marks that basis in the result.

The RO production duty is derived from water demand and configured permeate
capacity, which is specified at 15 C. Modelled RO energy combines production
and standby energy; measured RO energy replaces the modelled total. The RO,
like the WTM and the dryers, is powered only while the EL are switched on
(owner, 2026-11-19): RO standby = standby power x EL on-time (el_on_h); without
the on-time the standby and the modelled RO total stay open. Feed and
concentrate volumes are derived from the configured water conversion factor.

Filter-train pump energy is reported separately. When pump power is available,
the current model applies it over the full calculation window; actual pump
operating time is not measured or represented separately.

Water path (owner, 2026-11-19): RO permeate -> Enapter WTM 2.1 water tank ->
all EL 2.1. The tank decouples RO operation from EL demand:

- Permeate = EL demand + change of the tank level over the window. Without a
  level change the window is treated as steady state (permeate = demand).
- The tank volume does NOT change total RO energy: RO run time is
  permeate / capacity however it is batched. Per-start RO overhead (e.g. a
  flush) is unsourced and not modelled.
- Refill cycles (count, interval, RO run time per refill) need the refill
  start/stop levels, which are BACKLOG; they stay None until set.
- WTM energy is a separate line. The WTM is powered only while the EL are
  switched on (production and start-up phases), like the dryers (owner,
  2026-11-19). Standby = standby power x EL on-time; without the on-time it
  stays open. Pump energy = operative power x pump duty x EL on-time; the duty
  is BACKLOG. Until then only an envelope is reported (lower bound: minimum
  pump time at maximum outlet flow at operative power; upper bound: operative
  power over the EL on-time, or over the window if the on-time is unknown).
  The envelope is not a value and never enters a total.
- Fixed chain checks compare sourced limits: PASS / FAIL / OPEN.

This module supplies the water side of Route 4; hydrogen inferred from water
is calculated in hydrogen/route4_water.py.
"""
import math
from numbers import Real

from .. import registry as R


def _require_finite_nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


def _optional(key):
    """Registry value or None when the key is absent, has no value or is BACKLOG."""
    entry = R.REGISTRY.get(key)
    if entry is None or entry["value"] is None or entry["status"] == "BACKLOG":
        return None
    _require_finite_nonnegative(key, entry["value"])
    return entry["value"]


def _check(ok, detail):
    return dict(status="PASS" if ok else "FAIL", detail=detail)


def _chain_checks(perm_Lh):
    """Fixed checks RO -> WTM -> EL from sourced limits (PASS / FAIL / OPEN)."""
    checks = {}
    n_el = _optional("water.n_el_supplied")
    el_Lh = R.get("el.water_consumption_mLh") / 1000.0
    if n_el is None:
        checks["ro_capacity_vs_design_demand"] = dict(status="OPEN", detail="number of EL unknown")
    else:
        demand = n_el * el_Lh
        checks["ro_capacity_vs_design_demand"] = _check(
            perm_Lh >= demand,
            f"RO {perm_Lh:g} L/h vs {n_el:g} EL x {el_Lh:g} L/h = {demand:g} L/h")
    q_in = _optional("water.tank_min_inlet_flow_Lmin")
    checks["ro_permeate_vs_tank_inlet_flow"] = (
        dict(status="OPEN", detail="WTM inlet flow requirement unknown") if q_in is None else
        _check(perm_Lh / 60.0 > q_in,
               f"RO {perm_Lh / 60.0:g} L/min vs WTM requirement > {q_in:g} L/min"))
    max_el = _optional("water.tank_max_el")
    checks["el_count_vs_tank_rating"] = (
        dict(status="OPEN", detail="EL count or WTM rating unknown")
        if n_el is None or max_el is None else
        _check(n_el <= max_el, f"{n_el:g} EL vs WTM rating up to {max_el:g}"))
    p_out = _optional("water.tank_outlet_p_barg")
    p_lo = _optional("water.el_inlet_p_min_barg")
    p_hi = _optional("water.el_inlet_p_max_barg")
    checks["tank_outlet_vs_el_inlet_pressure"] = (
        dict(status="OPEN", detail="WTM outlet or EL inlet pressure unknown")
        if None in (p_out, p_lo, p_hi) else
        _check(p_lo <= p_out <= p_hi,
               f"WTM {p_out:g} barg vs EL H2O IN {p_lo:g}-{p_hi:g} barg"))
    checks["ro_permeate_pressure_vs_tank_inlet"] = dict(
        status="OPEN", detail="RO permeate outlet pressure is not documented "
                              "(1.5-4.0 bar is the RO intake pressure)")
    return checks


class WaterSystem:
    def account(self, duration_h, water_consumed_L=None, measured_kWh=None,
                measured_water_L=None, h2_produced_NL=None,
                tank_level_change_L=None, measured_tank_kWh=None, el_on_h=None):
        """RO energy, separate pump energy and water account over a window.

        duration_h           window length [h] (wall-clock, incl. idle time)
        water_consumed_L     EL water demand over the window (caller override)
        h2_produced_NL       actual H2 production over the window [NL]; default
                             water demand = h2_produced_NL x L/NL (part-load aware)
        measured_kWh         plug-meter energy of the RO unit over the window
                             (replaces the model; model values still reported)
        measured_water_L     water meter / BWT app reading; currently treated
                             as permeate volume (replaces the datasheet estimate)
        tank_level_change_L  WTM level at window end minus start [L] (telemetry);
                             permeate = EL demand + change. None = steady state.
                             Not combinable with measured_water_L (already permeate).
        measured_tank_kWh    metered WTM energy over the window (replaces the
                             WTM model; model lines still reported)
        el_on_h              hours the EL are switched on in the window, incl.
                             start-up phases; the WTM is powered only then
                             (None = unknown: RO and WTM standby stay open)
        """
        _require_finite_nonnegative("duration_h", duration_h)
        if duration_h == 0:
            raise ValueError("duration_h must be > 0")
        for name, value in (
                ("water_consumed_L", water_consumed_L),
                ("measured_kWh", measured_kWh),
                ("measured_water_L", measured_water_L),
                ("h2_produced_NL", h2_produced_NL),
                ("measured_tank_kWh", measured_tank_kWh),
                ("el_on_h", el_on_h)):
            if value is not None:
                _require_finite_nonnegative(name, value)
        if el_on_h is not None and el_on_h > duration_h:
            raise ValueError("el_on_h must not exceed duration_h")
        if tank_level_change_L is not None:
            if (isinstance(tank_level_change_L, bool) or not isinstance(tank_level_change_L, Real)
                    or not math.isfinite(tank_level_change_L)):
                raise ValueError("tank_level_change_L must be a finite number")
            if measured_water_L is not None:
                raise ValueError("tank_level_change_L cannot be combined with measured_water_L, "
                                 "which is already a permeate volume")

        perm_Lh = R.get("water.ro_perm_Lh")
        p_op_W = R.get("water.ro_power_op_W")
        p_stb_W = R.get("water.ro_power_standby_W")
        wcf = R.get("water.wcf")
        _require_finite_nonnegative("water.ro_perm_Lh", perm_Lh)
        if perm_Lh == 0:
            raise ValueError("water.ro_perm_Lh must be > 0")
        _require_finite_nonnegative("water.ro_power_op_W", p_op_W)
        _require_finite_nonnegative("water.ro_power_standby_W", p_stb_W)
        if (isinstance(wcf, bool) or not isinstance(wcf, Real) or not math.isfinite(wcf)
                or not 0 < wcf <= 1):
            raise ValueError("water.wcf must be finite and in (0, 1]")

        h2_known = h2_produced_NL is not None
        water_basis = None
        fallback_warning = None
        if measured_water_L is not None:
            water_L = measured_water_L
            water_status = "MEASURED"
        elif water_consumed_L is not None:
            water_L = water_consumed_L
            water_status = "DERIVED (caller)"
        elif h2_known:
            water_L = h2_produced_NL * R.get("water.spec_water_L_per_NL")
            water_status = "DATASHEET (scaled by H2 production)"
            water_basis = "H2-production-scaled"
        else:
            fallback_rate_Lh = R.get("el.water_consumption_mLh") / 1000.0
            water_L = fallback_rate_Lh * duration_h
            water_status = "DATASHEET (EL 2.1 x duration)"
            water_basis = "nominal-rate x duration"
            fallback_warning = ("water demand FALLBACK: no H2 production given, using nominal "
                                f"{fallback_rate_Lh:g} L/h x duration (ignores part load)")

        # permeate: the RO refills the WTM; over a window it delivers the EL demand
        # plus the change of the tank level (measured_water_L already is permeate)
        if tank_level_change_L is None:
            permeate_L = water_L
            permeate_basis = ("MEASURED permeate" if measured_water_L is not None
                              else "steady state: no tank level change given")
        else:
            permeate_L = water_L + tank_level_change_L
            permeate_basis = "EL demand + tank level change"
            if permeate_L < 0:
                raise ValueError("EL demand + tank_level_change_L must not be negative")

        # duty: the RO must produce permeate_L at perm_Lh capacity; batching via the
        # tank does not change this total
        t_prod_h = permeate_L / perm_Lh
        duty = t_prod_h / duration_h
        e_prod = t_prod_h * p_op_W / 1000.0
        e_ro_stb = None if el_on_h is None else el_on_h * p_stb_W / 1000.0
        e_model = None if e_ro_stb is None else e_prod + e_ro_stb
        e_kWh = measured_kWh if measured_kWh is not None else e_model

        feed_L = permeate_L / wcf
        conc_L = feed_L - permeate_L

        pump_entry = R.REGISTRY.get("water.filter_train_power_W")
        p_filter_W = pump_entry["value"] if pump_entry is not None else None
        pump_status = pump_entry["status"] if pump_entry is not None else "BACKLOG"
        if p_filter_W is not None and (
                isinstance(p_filter_W, bool) or not isinstance(p_filter_W, Real)
                or not math.isfinite(p_filter_W) or p_filter_W < 0):
            raise ValueError("water.filter_train_power_W must be a finite non-negative number or missing")
        if p_filter_W is None or pump_status == "BACKLOG":
            e_filter = None
            pump_status = "BACKLOG"
        else:
            e_filter = p_filter_W / 1000.0 * duration_h

        tank = self._tank(duration_h, water_L, permeate_L, perm_Lh, measured_tank_kWh, el_on_h)
        checks = _chain_checks(perm_Lh)

        energy_is_measured = measured_kWh is not None
        warnings = []
        if fallback_warning:
            warnings.append(fallback_warning)
        if not energy_is_measured:
            warnings.append("RO-unit energy is modelled using configured production and standby "
                            f"power ({p_op_W:g} W and {p_stb_W:g} W); meter the RO unit for a "
                            "MEASURED bar")
        if el_on_h is None and not energy_is_measured:
            warnings.append("RO standby OPEN: EL on-time (el_on_h) not given; the RO is "
                            "powered only while the EL are on, so the modelled RO total stays open")
        elif el_on_h is not None and t_prod_h > el_on_h:
            warnings.append("RO production time exceeds the EL on-time; the RO runs only "
                            "while the EL are on")
        if pump_status == "BACKLOG":
            warnings.append("filter-train pump energy OPEN (BACKLOG): missing value; "
                            "dependent sums stay open per CONTRACT sec. 7")
        elif pump_status == "GUESS":
            warnings.append("filter-train pump power is a GUESS, not a measured value")
        warnings.extend(tank.pop("warnings"))
        for name, check in checks.items():
            if check["status"] == "FAIL":
                warnings.append(f"water chain check FAILED: {name}: {check['detail']}")

        return dict(unit="WATER", duration_h=duration_h,
                    water_consumed_L=water_L, water_status=water_status, water_basis=water_basis,
                    permeate_L=permeate_L, permeate_basis=permeate_basis,
                    feed_L=feed_L, concentrate_L=conc_L,
                    ro_production_h=t_prod_h, duty=duty,
                    energy_kWh=e_kWh, energy_is_measured=energy_is_measured,
                    energy_kWh_model=e_model,
                    energy_kWh_production=e_prod,
                    energy_kWh_standby=e_ro_stb,
                    filter_train_energy_kWh=e_filter,
                    filter_train_status=pump_status,
                    uncertainty_rel=R.entry("water.ro_power_op_W")["uncertainty"]
                        if not energy_is_measured else 0.02,
                    **tank,
                    chain_checks=checks,
                    warnings=warnings if warnings else None)

    @staticmethod
    def _tank(duration_h, water_L, permeate_L, perm_Lh, measured_tank_kWh, el_on_h):
        """WTM 2.1 energy line, pump envelope and refill cycles."""
        warnings = []
        p_stb = _optional("water.tank_power_standby_W")
        p_op = _optional("water.tank_power_op_W")
        q_max = _optional("water.tank_max_outlet_flow_Lmin")
        volume = _optional("water.tank_volume_L")
        start = _optional("water.tank_refill_start_L")
        stop = _optional("water.tank_refill_stop_L")
        duty = _optional("water.tank_pump_duty")
        if duty is not None and duty > 1:
            raise ValueError("water.tank_pump_duty must be in [0, 1]")

        e_stb = None if (p_stb is None or el_on_h is None) else p_stb * el_on_h / 1000.0
        if el_on_h is None:
            warnings.append("WTM standby OPEN: EL on-time (el_on_h) not given; the WTM is "
                            "powered only while the EL are on")
        e_pump = (None if (duty is None or p_op is None or el_on_h is None)
                  else p_op * duty * el_on_h / 1000.0)
        if e_pump is None:
            warnings.append("WTM pump energy OPEN (BACKLOG): pump running time unknown; "
                            "only an envelope is reported, dependent sums stay open "
                            "per CONTRACT sec. 7")

        t_pump_min_h = None if not q_max else water_L / (q_max * 60.0)
        bounds = None
        if p_op is not None and t_pump_min_h is not None:
            t_avail_h = duration_h if el_on_h is None else el_on_h
            if t_pump_min_h > t_avail_h:
                warnings.append("WTM: EL demand exceeds the maximum outlet flow over the "
                                "available on-time")
            bounds = dict(
                lower_kWh=p_op * min(t_pump_min_h, t_avail_h) / 1000.0,
                upper_kWh=p_op * t_avail_h / 1000.0,
                label=("ENVELOPE, not a value. Lower: minimum pump time (water delivered / "
                       "max outlet flow) at operative power; assumes the pump draws the "
                       "operative power whenever it runs. Upper: operative power over the "
                       + ("EL on-time." if el_on_h is not None
                          else "whole window (EL on-time unknown).")))

        e_model = None if (e_stb is None or e_pump is None) else e_stb + e_pump
        tank_measured = measured_tank_kWh is not None
        e_tank = measured_tank_kWh if tank_measured else e_model

        refill_L = n_refills = interval_h = ro_h_per_refill = None
        if start is None or stop is None:
            warnings.append("WTM refill levels OPEN (BACKLOG): refill count and interval "
                            "not computed")
        else:
            if not start < stop or (volume is not None and stop > volume):
                raise ValueError("WTM refill levels must satisfy 0 <= start < stop <= tank volume")
            refill_L = stop - start
            n_refills = permeate_L / refill_L
            ro_h_per_refill = refill_L / perm_Lh
            demand_Lh = water_L / duration_h
            interval_h = refill_L / demand_Lh if demand_Lh > 0 else None

        return dict(tank_energy_kWh=e_tank, tank_energy_is_measured=tank_measured,
                    tank_energy_kWh_model=e_model,
                    tank_energy_kWh_standby=e_stb,
                    tank_standby_basis=("EL on-time (WTM powered only while the EL are on)"
                                        if el_on_h is not None else "OPEN: EL on-time unknown"),
                    tank_pump_energy_kWh=e_pump,
                    tank_pump_status="BACKLOG" if e_pump is None else "MODELLED",
                    tank_pump_min_h=t_pump_min_h,
                    tank_pump_energy_envelope=bounds,
                    tank_refill_L=refill_L, tank_refills=n_refills,
                    tank_refill_interval_h=interval_h,
                    tank_ro_h_per_refill=ro_h_per_refill,
                    warnings=warnings)
