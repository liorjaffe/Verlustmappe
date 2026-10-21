"""The loss map: run one charge/discharge cycle through every device.

New in this version (external review 2026-10):
  - h2_closure check: hydrogen PRODUCED (charge side) vs hydrogen CONSUMED
    (discharge side) vs net change in storage. The demo cycle does not
    consume what it produced; the map now says so explicitly instead of
    silently mixing an open cycle into a closed-cycle RTE.
  - rte_closed: RTE where the discharge energy is limited by the hydrogen
    that actually came out of storage. Two numbers, clearly labelled:
      rte_open   = E_out / E_in (as measured; valid if H2 in == H2 out)
      rte_closed = (E_stored * eta_FC) / E_in  (fair closed-cycle comparison)
  - compressor: accepts the actual suction/discharge pressure trajectory;
    if the storage fill path is a ramp 20->200 bar, the average pressure
    ratio (not the top pressure) is the honest reference.
"""
import numpy as np
from ..devices import ElectrolyzerUnit, Dryer, AirDrivenBooster, FuelCellSystem, Tank, FCInverter, PVInverter
from ..hydrogen import h2_from_tank_pressure, compare_routes
from .. import registry as R
from .. import constants as C
from ..conversions import kg_to_kWh_LHV
from .e_rte import storage_chain_rte, island_rte

def _plausibility_warnings(rte_open, rte_closed, closure, h2_in_kWh, tank_kWh,
                           loss_sigma=2.0, tank_excess_factor=1.25):
    """Flags for physically implausible results (never silently pass them on)."""
    w = []
    if rte_open is not None and rte_open > 1:
        w.append("rte_open = %.2f > 1: more energy out than in" % rte_open)
    if rte_closed is not None and rte_closed > 1:
        w.append("rte_closed = %.2f > 1: more energy out than in" % rte_closed)
    gl = closure.get("gas_loss_estimate")
    if gl and gl["kg"] < -loss_sigma * gl["uncertainty_kg"]:
        w.append("gas loss estimate is negative beyond its uncertainty (%.1f%% of production): "
                 "the tank holds more hydrogen than was produced; check the tank window"
                 % (100 * gl["fraction_of_production"]))
    if h2_in_kWh and tank_kWh is not None and tank_kWh > tank_excess_factor * h2_in_kWh:
        w.append("tank window holds %.0f%% of the produced hydrogen" % (100 * tank_kWh / h2_in_kWh))
    return w


def loss_map(df_charge, df_discharge, tank_p_start_barg=None, tank_p_end_barg=None,
             p_in_barg=None, p_out_barg=None, eta_inverter=None, E_pv_ac_kWh=None,
             air_compressor_kWh=None, dryer_kWh=None, bundle_isolated=None, **kw_e):
    """kw_e accepts optional PV-channel inputs: E_pv_dc_kWh, E_pv_ac_kWh,
    pv_status, pv_inverter_measured (from devices.pv_prelim_channel.pv_account)."""
    eta_inverter = R.get("inv_fc.eta") if eta_inverter is None else eta_inverter
    el = ElectrolyzerUnit().account(df_charge)
    hours = max((df_charge.index[-1] - df_charge.index[0]).total_seconds() / 3600.0, 1e-9)
    dry = Dryer().account(hours, el["h2"]["NL"], measured_kWh=dryer_kWh)
    NL_to_tank = el["h2"]["NL"] - dry["gas_loss_NL"]

    # compressor: suction = EL output pressure; the ideal work integrates over
    # the actual tank fill window when the caller provides one (the first draft
    # evaluated ln() at the arithmetic mean of suction and end pressure, which
    # is not the correct average of the per-mole work; fixed 2026-10).
    if p_in_barg is None:
        p_in_barg = R.get("el.output_pressure_barg")
    if p_out_barg is None:
        p_out_barg = tank_p_end_barg if tank_p_end_barg is not None else R.get("stor.p_work_barg")
    comp = AirDrivenBooster().account(NL_to_tank, p_in_barg, p_out_barg,
                                      air_compressor_kWh=air_compressor_kWh,
                                      p_tank_start_barg=tank_p_start_barg,
                                      p_tank_end_barg=tank_p_end_barg)
    fc = FuelCellSystem().account(df_discharge)

    routes = []
    if el["h2"]["route"] != "none":
        prod = dict(el["h2"]); prod["route"] = el["h2"]["route"]
        routes.append(prod)
        routes.append(dict(route="nameplate_el", kg=el["h2"]["kg"] * (1 - R.get("dry.vent_fraction")),
                           uncertainty_rel=R.entry("el.spec_energy_kWh_per_Nm3")["uncertainty"] + R.entry("dry.vent_fraction")["uncertainty"]))
        routes[-1]["route"] = "nameplate_el_minus_vent"
    tank_kWh = None
    if tank_p_start_barg is not None and tank_p_end_barg is not None:
        tk = h2_from_tank_pressure(tank_p_start_barg, tank_p_end_barg, bundle_isolated=bundle_isolated)
        routes.append(tk)
        tank_kWh = tk["kWh_LHV"]
    closure = compare_routes(routes)

    rte = storage_chain_rte(el["energy_in_kWh"], dry["energy_kWh"], comp["energy_kWh"],
                            fc["energy_out_kWh"], fc["control_energy_kWh_envelope"], eta_inverter,
                            E_standby_kWh=el.get("standby_kWh", 0.0) + kw_e.get("E_standby_kWh_extra", 0.0))
    # closure check: H2 balance across the cycle
    h2_in = el["h2"]["kWh_LHV"] if el["h2"]["route"] != "none" else None
    h2_out_fuel = fc["h2"]["kWh_LHV"]
    h2_stored = tank_kWh
    balance = dict(h2_in_kWh=h2_in, h2_consumed_kWh=h2_out_fuel, h2_stored_kWh=h2_stored)
    cycle_closed = (h2_in is not None and h2_stored is not None and
                    abs(h2_in - h2_stored) / h2_in < 0.05)
    consumed_matches = (h2_in is not None and abs(h2_in - h2_out_fuel) / h2_in < 0.05)
    balance.update(cycle_closed=cycle_closed, consumed_matches_production=consumed_matches,
                   note=("OPEN cycle: discharge consumed %.0f%% of produced hydrogen. "
                         "rte_open overstates a closed cycle; use rte_closed for fair comparison."
                         % (100 * h2_out_fuel / h2_in)) if (h2_in and not consumed_matches) else
                        ("cycle closes on the hydrogen balance" if consumed_matches else
                         "no hydrogen closure possible with the given inputs"))
    # fair closed-cycle RTE: energy from the H2 that actually left storage,
    # converted at the FC efficiency observed on the discharge side
    rte_closed = None
    if h2_stored and el["h2"]["kWh_LHV"] > 0 and fc["efficiency_LHV"]:
        e_out_fair = h2_stored * fc["efficiency_LHV"] * eta_inverter
        e_in_fair = el["energy_in_kWh"] + dry["energy_kWh"] + comp["energy_kWh"]
        rte_closed = e_out_fair / e_in_fair if e_in_fair > 0 else None
    balance["rte_closed"] = rte_closed
    balance["rte_open"] = rte["rte"]

    # bars in ENERGY-FLOW ORDER, from the PV array to the island load:
    #   PV capture -> PV inverter -> [AC bus] -> EL conversion -> dryer
    #   (electrical + gas) -> compression -> [tank] -> FC conversion
    #   -> FC control -> AC inverter -> AC out
    # E_pv_ac_kWh is a NAMED parameter of this function (used for island RTE),
    # so kw_e.get("E_pv_ac_kWh") was always None and the PV bars were dead code
    # in the first draft. Use the named parameter directly (fixed 2026-10).
    e_pv_dc = kw_e.get("E_pv_dc_kWh"); e_pv_ac_pv = E_pv_ac_kWh
    # the vent is a loss of THIS window only if hydrogen actually went missing
    # between production and tank; otherwise the envelope value is not booked
    vent_kWh, vent_status = dry["gas_loss_kWh_LHV"], "GUESS"
    gl = closure.get("gas_loss_estimate")
    if gl is not None:
        missing_kWh = max(kg_to_kWh_LHV(gl["kg"]), 0.0)
        vent_kWh = min(vent_kWh, missing_kWh)
        vent_status = "GUESS" if vent_kWh > 0 else "NOT OBSERVED"
    bars = []
    if e_pv_dc is not None and e_pv_ac_pv is not None:
        # PV capture bar: everything between the STC potential and the measured
        # DC energy (soiling + mismatch + shading + temperature + cables NOT in
        # the inverter path). The first draft subtracted E_AC from E_DC here,
        # which duplicated the inverter loss under a wrong label; and the next
        # bar applied (1 - eta_euro) to the AC energy instead of the DC energy.
        # Both fixed 2026-10; guarded by test_03.
        e_stc = kw_e.get("E_pv_stc_kWh")
        if e_stc is not None and e_stc > e_pv_dc:
            bars.append(dict(stage="PV capture (soiling/mismatch/shading/temp)",
                             kWh=e_stc - e_pv_dc, status=kw_e.get("pv_status", "PRELIM")))
        bars.append(dict(stage="PV inverter (DC->AC)",
                         kWh=e_pv_dc - e_pv_ac_pv,
                         status="MEASURED" if kw_e.get("pv_inverter_measured") else "PRELIM"))
    bars += [
        dict(stage="EL conversion (AC->H2)", kWh=el["energy_in_kWh"] - el["h2"]["kWh_LHV"],
             status="MEASURED" if el["efficiency_is_measured"] else "NAMEPLATE"),
        dict(stage="Dryer electrical", kWh=dry["energy_kWh"],
             status="MEASURED" if dry["energy_is_measured"] else "ENVELOPE"),
        dict(stage="Dryer vent (H2)", kWh=vent_kWh, status=vent_status),
        dict(stage="Compression (air-driven)", kWh=comp["energy_kWh"],
             status="MEASURED" if comp["energy_is_measured"] else "GUESS"),
        dict(stage="FC conversion (H2->DC)", kWh=fc["h2"]["kWh_LHV"] - fc["energy_out_kWh"],
             status="MEASURED" if fc["efficiency_is_measured"] else "NAMEPLATE"),
        dict(stage="FC control (aux)", kWh=fc["control_energy_kWh_envelope"], status="ENVELOPE"),
        dict(stage="FC inverter (48V DC->AC out)", kWh=(fc["energy_out_kWh"] - fc["control_energy_kWh_envelope"]) * (1 - eta_inverter),
             status="MEASURED" if kw_e.get("inv_fc_eta_is_measured") else "PRELIM"),
    ]
    # open cycle: hydrogen consumed != hydrogen delivered to the tank. The
    # difference is stored (or drawn) hydrogen, not an efficiency loss, and gets
    # its own bar so that E_in == sum(bars) + E_out holds for the storage chain.
    chain_sum = sum(b["kWh"] for b in bars if not b["stage"].startswith("PV"))
    residual = rte["E_in_kWh"] - chain_sum - rte["E_out_kWh"]
    bars.append(dict(stage="H2 storage change (open cycle: +stored / -drawn)", kWh=residual,
                     status="DERIVED"))
    warnings = _plausibility_warnings(rte["rte"], rte_closed, closure, h2_in, tank_kWh)
    out = dict(devices=dict(EL=el, DRY=dry, CSU=comp, FC=fc), h2_closure=closure,
               h2_balance=balance, rte=rte, bars=bars,
               plausible=not warnings, warnings=warnings)
    if E_pv_ac_kWh is not None:
        out["island"] = island_rte(E_pv_ac_kWh, rte)
    return out
