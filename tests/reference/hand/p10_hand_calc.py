"""Independent hand calculation for P10 (constants, isothermal work). Stdlib only.

Imports nothing from `verlustmappe` and reads no legacy output (hand README rules 1 and 3).
Run: python3 tests/reference/hand/p10_hand_calc.py
"""
import math

# CODATA 2018 exact SI definitions
K_B = 1.380649e-23        # J/K
N_A = 6.02214076e23       # 1/mol
E_CH = 1.602176634e-19    # C
R = K_B * N_A             # J/(mol K)
F = E_CH * N_A            # C/mol

P_N_PA = 101325.0         # 1 atm
T_N_K = 273.15
M_H2 = 2.016e-3           # kg/mol (project input, see constants.md)
LHV_MJ_PER_KG = 119.96    # IEA / NIST (project input)
P_ATM_BAR = 1.01325


def fill_w_over_RT(p1, p2):
    """Fill of a vessel p1 -> p2 with suction ps = p1: work per mol delivered, in units of RT."""
    return p2 / (p2 - p1) * math.log(p2 / p1) - 1.0


def fill_w_over_RT_numeric(p1, p2, n=200000):
    """Same quantity by midpoint integration: (1/(p2-p1)) * int_{p1}^{p2} ln(p/p1) dp."""
    h = (p2 - p1) / n
    s = sum(math.log((p1 + (i + 0.5) * h) / p1) for i in range(n)) * h
    return s / (p2 - p1)


def main():
    print("R =", R, "J/(mol K);  F =", F, "C/mol")
    v_mol_nl = R * T_N_K / P_N_PA * 1000.0
    print("V_mol(NL) =", v_mol_nl, "L/mol")
    rho = M_H2 / v_mol_nl
    print("rho_H2,NL =", rho, "kg/NL")
    lhv_kwh_kg = LHV_MJ_PER_KG / 3.6
    print("LHV =", lhv_kwh_kg, "kWh/kg;", "Wh/NL =", lhv_kwh_kg * rho * 1000.0)

    print("\n(A) closed system, ideal gas: W = n R T ln(p2/p1)")
    print(" 1 mol, 1 -> 10 bar, 293.15 K:", R * 293.15 * math.log(10.0), "J")

    print("\n(B) fill integral, ps = p1: w/RT = p2/(p2-p1) ln(p2/p1) - 1")
    for p1, p2 in [(1.0, 2.0), (40.0, 200.0), (10.0, 200.0),
                   (35 + P_ATM_BAR, 140 + P_ATM_BAR), (35 + P_ATM_BAR, 300 + P_ATM_BAR)]:
        f = fill_w_over_RT(p1, p2)
        g = fill_w_over_RT_numeric(p1, p2)
        a = math.log(p2 / p1)
        w_j_mol = f * R * 293.15
        kwh_nm3 = w_j_mol * (1000.0 / v_mol_nl) / 3.6e6
        print(f" p1={p1:.5f} p2={p2:.5f} abs: B/RT={f:.6f} (numeric {g:.6f}) A/RT={a:.6f}"
              f" | B at 293.15 K: {w_j_mol:.1f} J/mol = {kwh_nm3:.5f} kWh per Nm3")

    n_bovo = 33.22 * 1000.0 / v_mol_nl
    w = fill_w_over_RT(40.0, 200.0) * R * 293.15 * n_bovo / 3.6e6
    print("\nBovo point: 33.22 Nm3 =", n_bovo, "mol; B 40->200 bar abs, 293.15 K:", w, "kWh")


if __name__ == "__main__":
    main()
