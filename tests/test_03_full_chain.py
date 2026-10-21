"""Whole loss map on a synthetic cycle with physically consistent truth."""
import _path
import numpy as np, pandas as pd
from verlustmappe import registry as R
from verlustmappe.balance.d_loss_map import loss_map
from verlustmappe.uncertainty import loss_map_band

def main():
    R.REGISTRY["stor.volume_L"]["value"] = 1000.0
    n = 361
    idx = pd.date_range("2026-01-01", periods=n, freq="60s")
    dfc = pd.DataFrame({"power_W": np.full(n, 2400.0), "el_stack_current_A": np.full(n, 10.0)}, index=idx)
    n2 = 121
    idx2 = pd.date_range("2026-01-02", periods=n2, freq="60s")
    dfd = pd.DataFrame({"fc_power_W": np.full(n2, 2500.0),
                        "fc1_stack_current_A": np.full(n2, 19.39), "fc2_stack_current_A": np.full(n2, 19.39)}, index=idx2)
    # tank end pressure consistent with produced H2 minus vent (bisection on the same physics)
    from verlustmappe.hydrogen import h2_from_tank_pressure
    el0 = loss_map(dfc, dfd, eta_inverter=0.96)["devices"]["EL"]
    target_kg = el0["h2"]["kg"]   # tank must hold what the stack PRODUCED; vent is a loss estimate, not a storage correction
    lo, hi = 50.0, 300.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if h2_from_tank_pressure(50.0, mid)["kg"] < target_kg else (lo, mid)
    p_end = 0.5 * (lo + hi)
    out = loss_map(dfc, dfd, tank_p_start_barg=50.0, tank_p_end_barg=p_end, eta_inverter=0.96)
    assert out["h2_closure"]["max_spread_independent"] < 0.001, out["h2_closure"]
    # the demo discharges MORE hydrogen than it produces (open cycle by design:
    # 2.5 kW x 2 h draws 132% of the 6 h charge production). The old line
    # "assert ... and ... or True" was a tautology and hid this; assert it
    # EXPLICITLY now: tank closes on production, consumption exceeds it.
    assert out["h2_balance"]["cycle_closed"] is True
    assert out["h2_balance"]["consumed_matches_production"] is False
    assert out["h2_balance"]["rte_closed"] is not None
    assert 0.15 < out["h2_balance"]["rte_closed"] < 0.35, out["h2_balance"]["rte_closed"]
    # compression: with the fill-window integral, ideal work must be BELOW the
    # single-shot nRT ln(p_end/p_start) (fill integrals are cheaper than the
    # single-shot work at the top pressure for the same mass)
    # PV bars: if PV energies are given, capture bar must be E_stc - E_dc and
    # inverter bar E_dc - E_ac (the first draft swapped/duplicated these)
    pv_out = loss_map(dfc, dfd, eta_inverter=0.96,
                      tank_p_start_barg=50.0, tank_p_end_barg=p_end,
                      E_pv_dc_kWh=90.0, E_pv_ac_kWh=87.0,
                      E_pv_stc_kWh=100.0, pv_status="PRELIM")
    pv_bars = {b["stage"]: b["kWh"] for b in pv_out["bars"]}
    assert abs(pv_bars["PV capture (soiling/mismatch/shading/temp)"] - 10.0) < 1e-6, pv_bars
    assert abs(pv_bars["PV inverter (DC->AC)"] - 3.0) < 1e-6, pv_bars
    # tank holds 100% of production -> no gas left the system -> no vent loss booked
    vent = [b for b in out["bars"] if "vent" in b["stage"]]
    assert vent and abs(vent[0]["kWh"]) < 1e-9, vent
    el, fc = out["devices"]["EL"], out["devices"]["FC"]
    assert abs(el["energy_in_kWh"] - 14.4) < 1e-6
    assert el["efficiency_is_measured"] and fc["efficiency_is_measured"]
    assert 0.55 < el["efficiency_LHV"] < 0.70, el["efficiency_LHV"]
    assert 0.35 < fc["efficiency_LHV"] < 0.50, fc["efficiency_LHV"]
    rte = out["rte"]["rte"]
    assert 0.20 < rte < 0.35, rte
    assert out["h2_closure"]["n_independent"] == 2
    band = loss_map_band(dfc, dfd, n=150, tank_p_start_barg=50.0, tank_p_end_barg=p_end, eta_inverter=0.96)
    assert band["rte_lo"] <= band["rte_mean"] <= band["rte_hi"]
    assert band["rte_lo"] <= rte <= band["rte_hi"] or abs(band["rte_mean"] - rte) < 0.02, \
        "MC band must bracket the point estimate (reviewer 2026-10)"
    assert band["failed_draws"] == 0, band["failed_draws"]
    print("PASS 03 full chain: EL eta %.1f%%, FC eta %.1f%%, RTE %.1f%% [MC %.1f-%.1f], H2 spread %.1f%%"
          % (el["efficiency_LHV"]*100, fc["efficiency_LHV"]*100, rte*100, band["rte_lo"]*100, band["rte_hi"]*100,
             out["h2_closure"]["max_spread_independent"]*100))
    for b in out["bars"]:
        print("      %-18s %7.3f kWh  [%s]" % (b["stage"], b["kWh"], b["status"]))

if __name__ == "__main__": main()
