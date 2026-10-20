"""Tank thermal module: GS fit, temperature tiers, bracket, DCT 541 uncertainty."""
import _path
import numpy as np
from verlustmappe.hydrogen.temperature_model import (gs_fit_from_pressure_decay,
    isothermal_adiabatic_bracket, tier1_temperature, tier2_temperature,
    temperature_corrected_mass)
from verlustmappe.hydrogen import h2_from_tank_pressure

def main():
    # GS fit on synthetic decay: tau=1800 s -> r2 ~ 1
    t = np.arange(0, 3600.0, 60.0)
    p = 120.0 + 100.0 * np.exp(-t / 1800.0)
    GS, tau, r2 = gs_fit_from_pressure_decay(t, p)
    assert tau is not None and abs(tau - 1800.0) / 1800.0 < 0.02, tau
    assert r2 is not None and r2 > 0.99, r2
    # Nexo anchor: their vehicle tank gave 70 W/K; our 800 L steel must give MORE
    # (scale ~ surface): check GS > 50 W/K as a physicality bound
    assert GS > 50.0, GS
    # tiers
    t1, u1 = tier1_temperature(); assert u1 == 3.0
    t2, u2 = tier2_temperature(35.0, 30.0); assert t2 == 32.5 and u2 == 2.0
    # bracket: hot fill stores LESS mass -> spread positive, ~4% for 15 K
    b = isothermal_adiabatic_bracket(21.0, 200.0, 800.0, delta_T_K=15.0)
    assert 0.02 < b["relative_spread"] < 0.08, b["relative_spread"]
    # temperature sensitivity: mass ~ 1/(Z(T) T) - the 1/T law holds only at
    # fixed Z; with the 1/T Z-correction the ratio shifts slightly (correct)
    from verlustmappe.hydrogen.z_realgas import z_h2
    m20 = temperature_corrected_mass(200.0, 800.0, 20.0)
    m30 = temperature_corrected_mass(200.0, 800.0, 30.0)
    z20, z30 = z_h2(200.0, 20.0), z_h2(200.0, 30.0)   # same p as the module call
    expected = (z30 * 303.15) / (z20 * 293.15)
    assert abs(m20 / m30 - expected) < 1e-9, (m20 / m30, expected)
    # Route 2 with the DCT 541 uncertainty: a 100-bar swing must be a few percent
    r = h2_from_tank_pressure(50.0, 150.0)
    assert 0.01 < r["uncertainty_rel"] < 0.06, r["uncertainty_rel"]
    # tier 2 shifts the mass (32.5 C mean vs 20 C ambient): fewer kg
    r2t = h2_from_tank_pressure(50.0, 150.0, tier=2, T_top_C=35.0, T_bottom_C=30.0)
    assert r2t["kg"] < r["kg"], (r["kg"], r2t["kg"])
    assert 0.01 < r2t["uncertainty_rel"] < 0.06
    print("PASS 07 tank thermal: GS fit (tau %.0f s, r2 %.3f), tiers, bracket %.1f%%, DCT 541 Route 2 u %.1f%%"
          % (tau, r2, b["relative_spread"] * 100, r["uncertainty_rel"] * 100))

if __name__ == "__main__": main()
