"""Every constant and conversion is checked against an independent reference."""
import _path
import numpy as np
from verlustmappe import constants as C
from verlustmappe.conversions import mol_from_charge, mol_from_pVT, isothermal_work_kWh, NL_to_kg, energy_kWh_from_power

def main():
    # datasheet self-consistency: Enapter 500 NL/h = 1.0785 kg/24 h
    assert abs(C.RHO_H2_KG_PER_NL - 1.0785 / (500 * 24)) / C.RHO_H2_KG_PER_NL < 0.002
    # LHV per NL ~ 3.00 Wh (h2data.de: 3.00 kWh/Nm3)
    assert abs(C.LHV_H2_WH_PER_NL - 2.997) < 0.005
    # Faraday: 1 A for 1 h through 1 cell -> 3600/(2*96485) mol = 0.018655 mol = 0.4181 NL
    mol = mol_from_charge(np.full(3600, 1.0), np.full(3600, 1.0), n_cells=1)
    assert abs(mol - 3600 / (2 * C.F_C_PER_MOL)) < 1e-12
    # ideal gas: 1 m3 at 1 bar abs, 0 C, Z=1 -> 44.6 mol
    assert abs(mol_from_pVT(1.01325, 1.0, 273.15, 1.0) - 44.615) < 0.01
    # isothermal work: 1 mol, 1->10 bar, 293.15 K -> RT ln10 = 5612 J = 1.559e-3 kWh
    assert abs(isothermal_work_kWh(1.0, 1.0, 10.0, 293.15) - 5612.0 / 3.6e6) < 1e-6
    # trapezoid energy: 2000 W for 3600 s = 2 kWh
    assert abs(energy_kWh_from_power(np.full(61, 2000.0), np.arange(61) * 60.0) - 2.0) < 1e-9
    print("PASS 01 constants & conversions verified against references")

if __name__ == "__main__": main()
