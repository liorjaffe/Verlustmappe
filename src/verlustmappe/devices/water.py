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
and standby energy; measured RO energy replaces the modelled total. Feed and
concentrate volumes are derived from the configured water conversion factor.

Filter-train pump energy is reported separately. When pump power is available,
the current model applies it over the full calculation window; actual pump
operating time is not measured or represented separately.

This module supplies the water side of Route 4; hydrogen inferred from water
is calculated in hydrogen/route4_water.py.
"""
import math
from numbers import Real

from .. import registry as R


def _require_finite_nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a finite non-negative number")


class WaterSystem:
    def account(self, duration_h, water_consumed_L=None, measured_kWh=None,
                measured_water_L=None, ro_standby_always_on=True, h2_produced_NL=None):
        """RO energy, separate pump energy and water account over a window.

        duration_h           window length [h] (wall-clock, incl. idle time)
        water_consumed_L     EL water demand over the window (caller override)
        h2_produced_NL       actual H2 production over the window [NL]; default
                             water demand = h2_produced_NL x L/NL (part-load aware)
        measured_kWh         plug-meter energy of the RO unit over the window
                             (replaces the model; model values still reported)
        measured_water_L     water meter / BWT app reading; currently treated
                             as permeate volume (replaces the datasheet estimate)
        ro_standby_always_on when True, standby counts over the whole window;
                             when False, it counts over production time only
        """
        _require_finite_nonnegative("duration_h", duration_h)
        if duration_h == 0:
            raise ValueError("duration_h must be > 0")
        for name, value in (
                ("water_consumed_L", water_consumed_L),
                ("measured_kWh", measured_kWh),
                ("measured_water_L", measured_water_L),
                ("h2_produced_NL", h2_produced_NL)):
            if value is not None:
                _require_finite_nonnegative(name, value)

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

        # duty: the RO must produce water_L at perm_Lh capacity
        t_prod_h = water_L / perm_Lh
        duty = t_prod_h / duration_h
        t_on_h = duration_h if ro_standby_always_on else t_prod_h
        e_model = t_prod_h * p_op_W / 1000.0 + t_on_h * p_stb_W / 1000.0
        e_kWh = measured_kWh if measured_kWh is not None else e_model

        feed_L = water_L / wcf
        conc_L = feed_L - water_L

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

        energy_is_measured = measured_kWh is not None
        warnings = []
        if fallback_warning:
            warnings.append(fallback_warning)
        if not energy_is_measured:
            warnings.append("RO-unit energy is modelled using configured production and standby "
                            f"power ({p_op_W:g} W and {p_stb_W:g} W); meter the RO unit for a "
                            "MEASURED bar")
        if pump_status == "BACKLOG":
            warnings.append("filter-train pump energy OPEN (BACKLOG): missing value; "
                            "dependent sums stay open per CONTRACT sec. 7")
        elif pump_status == "GUESS":
            warnings.append("filter-train pump power is a GUESS, not a measured value")

        return dict(unit="WATER", duration_h=duration_h,
                    water_consumed_L=water_L, water_status=water_status, water_basis=water_basis,
                    permeate_L=water_L,
                    feed_L=feed_L, concentrate_L=conc_L,
                    ro_production_h=t_prod_h, duty=duty,
                    energy_kWh=e_kWh, energy_is_measured=energy_is_measured,
                    energy_kWh_model=e_model,
                    energy_kWh_production=t_prod_h * p_op_W / 1000.0,
                    energy_kWh_standby=t_on_h * p_stb_W / 1000.0,
                    filter_train_energy_kWh=e_filter,
                    filter_train_status=pump_status,
                    uncertainty_rel=R.entry("water.ro_power_op_W")["uncertainty"]
                        if not energy_is_measured else 0.02,
                    warnings=warnings if warnings else None)
