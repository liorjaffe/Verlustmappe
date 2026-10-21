"""Water treatment system feeding the EL 2.1 (BWT bestaqua 14ROC COFFEE RO unit
+ upstream Popular Filtros cartridge train: resin -> activated carbon -> 1/5 um).

Why this is in the energy balance: the water chain is a REAL electrical
consumer. The RO unit draws 200 W in operation and <3 W standby, and the
standby is continuous (the unit stays powered). The cartridge train itself is
purely hydraulic (0 W), but a pump in the water path is NOT excluded (control
panel observed on site, power unmeasured) and is carried as an open item.

Physics:
  - Water demand comes from the electrolyser, NOT from the water system: the
    EL 2.1 refills automatically via its H2O IN solenoid valve. The demand is
    the stoichiometric MINIMUM scaled by the ACTUAL hydrogen production
    (0.4 L/h at 500 NL/h nominal = 0.0008 L/NL; route4_water.py: 9.0 g water
    per g H2), so it follows part load. Purges/bleeds add on top; refills are
    periodic, so the proportionality is the honest first-order model until a
    water meter exists (BWT app inlet/outlet counters can replace it). The old
    datasheet x duration value is only a loud fallback when no H2 is given.
  - The RO does not run continuously: duty = t_production / duration with
    t_production = water_demand / permeate_capacity (120 L/h at 15 C).
  - Raw feed = permeate / WCF (factory ~50%); the difference is the
    concentrate stream to drain. It costs no energy but DOUBLES the raw-water
    draw and is a water-scope number for the plant balance.
  - Energy model (until metered): E = t_production * P_op + t_on * P_standby
    with t_on = duration (standby is continuous). A plug meter on the RO unit
    replaces the whole model; the BWT app also shows inlet/outlet litre
    counters that can be read as measured water volumes.

Stoichiometric consistency: water_L * (M_H2 / M_H2O) is the H2 mass the water
route implies; h2_from_water() in hydrogen/route4_water.py does exactly this.
This module supplies the water side of Route 4.
"""
from .. import registry as R

class WaterSystem:
    def account(self, duration_h, water_consumed_L=None, measured_kWh=None,
                measured_water_L=None, ro_standby_always_on=True, h2_produced_NL=None):
        """Energy and water account of the water system over a window.

        duration_h           window length [h] (wall-clock, incl. idle time)
        water_consumed_L     EL water demand over the window (caller override)
        h2_produced_NL       actual H2 production over the window [NL]; default
                             water demand = h2_produced_NL x L/NL (part-load aware)
        measured_kWh         plug-meter energy of the RO unit over the window
                             (replaces the model; model values still reported)
        measured_water_L     water meter / BWT app inlet-or-outlet counter over
                             the window (replaces the datasheet estimate)
        ro_standby_always_on standby counts over the WHOLE window when True
                             (as built); set False if the RO is switched off
                             with the electrolyser
        """
        if duration_h <= 0:
            raise ValueError("duration_h must be > 0")
        perm_Lh = R.get("water.ro_perm_Lh")
        p_op_W = R.get("water.ro_power_op_W")
        p_stb_W = R.get("water.ro_power_standby_W")
        wcf = R.get("water.wcf")

        h2_known = h2_produced_NL is not None and h2_produced_NL == h2_produced_NL
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
            water_L = R.get("el.water_consumption_mLh") / 1000.0 * duration_h
            water_status = "DATASHEET (EL 2.1 x duration)"
            water_basis = "nominal-rate x duration"
            fallback_warning = ("water demand FALLBACK: no H2 production given, using nominal "
                                "0.4 L/h x duration (ignores part load)")

        # duty: the RO must produce water_L at perm_Lh capacity
        t_prod_h = water_L / perm_Lh
        duty = t_prod_h / duration_h
        t_on_h = duration_h if ro_standby_always_on else t_prod_h
        e_model = t_prod_h * p_op_W / 1000.0 + t_on_h * p_stb_W / 1000.0
        e_kWh = measured_kWh if measured_kWh is not None else e_model

        feed_L = water_L / wcf
        conc_L = feed_L - water_L

        # upstream cartridge train: 0 W until a pump is proven in the water path
        p_filter_W = R.get("water.filter_train_power_W")
        e_filter = p_filter_W / 1000.0 * duration_h

        energy_is_measured = measured_kWh is not None
        warnings = []
        if fallback_warning:
            warnings.append(fallback_warning)
        if not energy_is_measured:
            warnings.append("water-system energy is modelled (duty x 200 W + "
                            "continuous <3 W standby); meter the RO unit for a MEASURED bar")
        if R.entry("water.filter_train_power_W")["status"] == "GUESS":
            warnings.append("filter-train pump power is an open item (control panel "
                            "observed, no nameplate); 0 W booked until verified")

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
                    uncertainty_rel=R.entry("water.ro_power_op_W")["uncertainty"]
                        if not energy_is_measured else 0.02,
                    warnings=warnings if warnings else None)
