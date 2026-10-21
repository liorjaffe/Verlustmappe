"""Hydrogen routes on a constructed truth: they must agree when fed consistent data."""
import _path
import numpy as np
from verlustmappe import registry as R
from verlustmappe.hydrogen import (h2_from_stack_current, h2_from_tank_pressure, h2_from_telemetry,
                                   h2_from_water, h2_from_energy_nameplate, compare_routes)
from verlustmappe.hydrogen.z_realgas import z_h2
from verlustmappe.devices import Tank

def main():
    # Z table checkpoints (NIST/Leachman EOS)
    assert abs(z_h2(350.0, 20.0) - 1.227) < 0.002   # CoolProp/Leachman check point (at 20 C)
    assert abs(z_h2(200.0, 20.0) - 1.125) < 0.002   # CoolProp/Leachman check point
    assert abs(z_h2(1.013, 20.0) - 1.0) < 0.002
    # density check: 200 bar 20 C -> ~14.7 kg/m3 (Leachman EOS)
    t = Tank(); R.REGISTRY["stor.volume_L"]["value"] = 1000.0
    rho = t.stored(200 - 1.01325)["kg"]
    assert 14.6 < rho < 14.8, rho
    # Route 1 EL: 10 A x 6 h x 120 cells x 0.98 -> mol (eta_F multiplies)
    I = np.full(360, 10.0); dt = np.full(360, 60.0)
    r1 = h2_from_stack_current([I], dt, 120, 0.98, device="el")
    expected = 0.98 * 120 * 10 * 6 * 3600 / (2 * 96485.332)
    assert abs(r1["mol"] - expected) < 1e-9
    # Route 1 FC: eta_F DIVIDES (consumption rises with losses) - reviewer 2026-10
    r1fc = h2_from_stack_current([I], dt, 120, 0.98, device="fc")
    expected_fc = 120 * 10 * 6 * 3600 / (2 * 96485.332) / 0.98
    assert abs(r1fc["mol"] - expected_fc) < 1e-9, (r1fc["mol"], expected_fc)
    # Route 2: construct the pressure rise that stores exactly r1 mass in a 1000 L tank
    R.REGISTRY["stor.volume_L"]["value"] = 1000.0
    p1 = 50.0
    # find p2 by bisection using the same physics the tank uses
    lo, hi = p1, 300.0
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        m = h2_from_tank_pressure(p1, mid, bundle_isolated=True)["kg"]
        lo, hi = (mid, hi) if m < r1["kg"] else (lo, mid)
    r2 = h2_from_tank_pressure(p1, 0.5 * (lo + hi), bundle_isolated=True)
    assert abs(r2["kg"] - r1["kg"]) / r1["kg"] < 1e-6
    # Route 4: water 9x mass
    r4 = h2_from_water(r1["kg"] * 18.015 / 2.016)
    assert abs(r4["kg"] - r1["kg"]) / r1["kg"] < 1e-9
    # closure over independent routes -> spread ~0
    c = compare_routes([r1, r2, r4])
    # production routes (faraday, water) agree; the tank route is the delivered
    # quantity and only enters the gas-loss estimate, not the spread
    assert c["n_independent"] == 2 and c["max_spread_independent"] < 1e-5
    assert abs(c["gas_loss_estimate"]["fraction_of_production"]) < 1e-5
    # nameplate route is a constant-efficiency bound
    rn = h2_from_energy_nameplate(14.4, "el")
    assert abs(rn["kWh_LHV"] / 14.4 - 0.624) < 0.01
    # fill-integral compressor work vs brute-force summation (fix 2026-10):
    # dW = dm RT ln(p/p_s) integrated over the tank fill 20->200 bar
    from verlustmappe.hydrogen.temperature_model import isothermal_work_mol_integral
    Rg, T = 8.314462618, 293.15
    m_test = 1000.0   # mol
    w_code = isothermal_work_mol_integral(m_test, 20.0, 200.0, T)
    ps = 20.0
    w_brute = sum((m_test/(200.0-20.0)) * Rg * T * np.log(pp/ps) * (200.0-20.0)/1000.0
                  for pp in np.linspace(20.0, 200.0, 200001)) / 1000.0 / 1000.0
    # (per-mol work integrated linearly in p, total mol m_test)
    w_brute = m_test * Rg * T * float(np.trapezoid([np.log(pp/ps) for pp in np.linspace(20, 200, 200001)],
                                                   np.linspace(20, 200, 200001))) / (200.0-20.0) / 3.6e6
    assert abs(w_code - w_brute) / w_brute < 1e-4, (w_code, w_brute)
    # Bovo anchor: 33.22 Nm3, 40->200 bar, suction 40 -> ideal ~1.02 kWh
    w_bovo = isothermal_work_mol_integral(33.22/22.414*1000, 40.0, 200.0, T)
    assert 0.9 < w_bovo < 1.15, w_bovo
    # closure now reports max(statistical, spread) as uncertainty_rel (card G)
    r_hi = h2_from_stack_current([np.full(360, 10.0)], np.full(360, 60.0), 120, 0.98, device="el")
    r_shift = dict(r_hi); r_shift["route"] = "water"; r_shift["kg"] = r_hi["kg"] * 1.20
    c2 = compare_routes([r_hi, r_shift])
    assert abs(c2["uncertainty_rel"] - c2["max_spread_independent"]) < 1e-9
    assert c2["uncertainty_rel"] >= c2["weighted_uncertainty_rel"]
    print("PASS 02 hydrogen routes: Z table, Faraday, tank-pV, water, closure(+max), "
          "nameplate bound, fill-integral work, Bovo anchor")

if __name__ == "__main__": main()
