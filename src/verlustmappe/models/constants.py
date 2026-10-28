"""Physical constants of the new core. FACTS, not assumptions.

Ported from `verlustmappe/constants.py` (frozen legacy copy until the teardown in M6); a
regression test compares both. A mismatch is a defect, never a reason to edit the legacy file.
Hand derivation: tests/reference/hand/constants.md.
"""

# Molar mass of H2 [kg/mol]: 2 x 1.008 (IUPAC 2021 standard atomic weight).
M_H2_KG_PER_MOL = 2.016e-3

# Faraday constant [C/mol]. CODATA 2018 exact: 96485.33212 C/mol.
F_C_PER_MOL = 96485.332

# Universal gas constant [J/(mol K)]. CODATA 2018 exact: 8.314462618 J/(mol K).
R_J_PER_MOL_K = 8.314462618

# Molar volume of an ideal gas at the NORMAL basis (0 degC, 1.01325 bar abs, dry, DIN 1343) [NL/mol].
V_MOL_NL_PER_MOL = 22.414

RHO_H2_KG_PER_NL = M_H2_KG_PER_MOL / V_MOL_NL_PER_MOL

# Heating values of hydrogen [kWh/kg]; efficiencies are LHV-based unless labelled otherwise.
LHV_H2_KWH_PER_KG = 33.322
HHV_H2_KWH_PER_KG = 39.411
LHV_H2_WH_PER_NL = LHV_H2_KWH_PER_KG * RHO_H2_KG_PER_NL * 1000.0
HHV_H2_WH_PER_NL = HHV_H2_KWH_PER_KG * RHO_H2_KG_PER_NL * 1000.0

J_PER_KWH = 3.6e6
J_PER_WH = 3600.0
PA_PER_BAR = 1.0e5
P_ATM_BAR = 1.01325


def barg_to_abs_bar(pressure_barg):
    """Gauge to absolute pressure with the normal atmosphere (project convention)."""
    return pressure_barg + P_ATM_BAR
