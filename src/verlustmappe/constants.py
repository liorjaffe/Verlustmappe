"""Physical constants used throughout. These are FACTS, not assumptions.

Every value carries its source so a reviewer can check it. Device parameters
(which ARE assumptions or datasheet claims) live in registry.py, not here.
"""

# Molar mass of H2 [kg/mol]. H standard atomic weight 1.008 (IUPAC 2021);
# the older IUPAC value 1.00794 was doubled here; identical to 4 significant
# digits either way (2.016e-3).
M_H2_KG_PER_MOL = 2.016e-3

# Faraday constant [C/mol]. CODATA 2018 exact: 96485.33212 C/mol.
F_C_PER_MOL = 96485.332

# Universal gas constant [J/(mol K)]. CODATA 2018 exact: 8.314462618 J/(mol K).
R_J_PER_MOL_K = 8.314462618

# Molar volume of an ideal gas at NORMAL conditions (0 C, 101325 Pa) [NL/mol].
# V = RT/p = 8.314462618*273.15/101325 = 22.414 L/mol.
# "NL" (normal litre) throughout this project means 0 C and 1 atm, the European
# convention. Enapter's datasheet is self-consistent with this: 500 NL/h =
# 1.0785 kg/24 h  ->  8.99e-5 kg/NL  ->  matches M_H2 / V_MOL below.
V_MOL_NL_PER_MOL = 22.414

# Derived: H2 density at normal conditions [kg/NL] = 2.016e-3 / 22.414 = 8.994e-5
RHO_H2_KG_PER_NL = M_H2_KG_PER_MOL / V_MOL_NL_PER_MOL

# Heating values of hydrogen [kWh/kg].
# LHV (lower / net calorific value): 119.96 MJ/kg = 33.322 kWh/kg  (IEA, NIST)
# HHV (higher / gross):              141.88 MJ/kg = 39.411 kWh/kg
# All efficiencies in this project are LHV-based unless labelled otherwise
# (IEA convention for electrolysers and fuel cells).
LHV_H2_KWH_PER_KG = 33.322
HHV_H2_KWH_PER_KG = 39.411

# Derived: energy per normal litre [Wh/NL]: 33.322 * 89.94e-6 * 1000 = 2.997
LHV_H2_WH_PER_NL = LHV_H2_KWH_PER_KG * RHO_H2_KG_PER_NL * 1000.0
HHV_H2_WH_PER_NL = HHV_H2_KWH_PER_KG * RHO_H2_KG_PER_NL * 1000.0

# Conversions
J_PER_KWH = 3.6e6
J_PER_WH = 3600.0
PA_PER_BAR = 1.0e5
P_ATM_BAR = 1.01325
