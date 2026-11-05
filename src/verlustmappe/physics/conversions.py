"""Unit conversions and the four textbook formulas used everywhere.

Each function states its formula and where it comes from. Nothing here is an
assumption; all inputs that are assumptions arrive via registry.py.
"""
import numpy as np
from . import constants as C

# ------------------------------------------------------------------ mass/volume
def mol_to_kg(mol):  return mol * C.M_H2_KG_PER_MOL
def kg_to_mol(kg):   return kg / C.M_H2_KG_PER_MOL
def mol_to_NL(mol):  return mol * C.V_MOL_NL_PER_MOL
def NL_to_mol(NL):   return NL / C.V_MOL_NL_PER_MOL
def NL_to_kg(NL):    return NL * C.RHO_H2_KG_PER_NL
def kg_to_NL(kg):    return kg / C.RHO_H2_KG_PER_NL

# ------------------------------------------------------------------ energy
def kg_to_kWh_LHV(kg): return kg * C.LHV_H2_KWH_PER_KG
def kg_to_kWh_HHV(kg): return kg * C.HHV_H2_KWH_PER_KG

def energy_kWh_from_power(power_W, t_s):
    """E = integral P dt, trapezoidal rule. Returns kWh.
    power_W and t_s are arrays; NaN in power is skipped segment-wise."""
    p = np.asarray(power_W, float); t = np.asarray(t_s, float)
    ok = np.isfinite(p) & np.isfinite(t)
    if ok.sum() < 2: return 0.0
    return float(np.trapezoid(p[ok], t[ok]) / C.J_PER_KWH)

# ------------------------------------------------------------------ Faraday
def mol_from_charge(I_A, dt_s, n_cells, z=2):
    """Faraday's law of electrolysis (Faraday 1834; any electrochemistry
    textbook, e.g. Bard & Faulkner, Electrochemical Methods, ch. 1):
        n = Q / (z F),   Q = integral I dt
    For a stack of n_cells cells in SERIES the same current flows through every
    cell and each cell converts Q/(zF) mol, so n_total = n_cells * Q / (z F).
    z = 2 electrons per H2 molecule."""
    I = np.asarray(I_A, float); dt = np.asarray(dt_s, float)
    Q = float(np.nansum(I * dt))
    return n_cells * Q / (z * C.F_C_PER_MOL)

# ------------------------------------------------------------------ gas law
def mol_from_pVT(p_abs_bar, V_m3, T_K, Z):
    """Real-gas equation of state  p V = Z n R T  ->  n = p V / (Z R T).
    Z is the compressibility factor (see hydrogen/z_realgas.py)."""
    return (p_abs_bar * C.PA_PER_BAR) * V_m3 / (Z * C.R_J_PER_MOL_K * T_K)

def isothermal_work_kWh(mol, p1_bar, p2_bar, T_K):
    """Minimum (reversible, isothermal) work to compress an ideal gas:
        W = n R T ln(p2 / p1)
    (any thermodynamics textbook, e.g. Cengel & Boles, ch. 7). Real compressors
    need 3-20x this; the ratio W_ideal / W_electrical is the compressor's
    overall efficiency."""
    return float(mol * C.R_J_PER_MOL_K * T_K * np.log(p2_bar / p1_bar) / C.J_PER_KWH)
