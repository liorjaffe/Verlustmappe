"""Compressibility factor Z of hydrogen.

Why it matters: at 200 bar hydrogen holds ~12% LESS mass than the ideal gas
law predicts. Ignoring Z biases Route 2 by that amount.

Source: equation of state of Leachman, Jacobsen, Penoncello & Lemmon,
J. Phys. Chem. Ref. Data 38, 721 (2009) - the same EOS CoolProp/NIST REFPROP
implement. Table values were cross-checked against CoolProp at 20 C and are
rounded to be consistent with it (the first draft of this table ran up to
+0.9% high; corrected 2026-10). Check points (CoolProp): Z(350 bar, 15 C) =
1.227, Z(200 bar, 20 C) = 1.125, density(200 bar, 20 C) = 14.7 kg/m3.
Independent sanity band from NIST density tables: 1.125-1.139.

Temperature correction: (Z - 1) scales approximately with 1/T in the ambient
range (second-virial behaviour), so Z(p,T) = 1 + (Z(p,20C) - 1) * 293.15 / T.
This correction is approximate; at 0 C it adds ~+0.5% error on top of the
table error. Stated uncertainty: +-1% for 0-300 bar, 0-50 C (was +-0.5%,
too tight - external review 2026-10).
"""
import numpy as np

_P_BAR = np.array([1, 25, 50, 75, 100, 125, 150, 175, 200, 225, 250, 275, 300, 350])
_Z_20C = np.array([1.0000, 1.014, 1.029, 1.044, 1.059, 1.074, 1.089, 1.107,
                   1.125, 1.142, 1.158, 1.175, 1.192, 1.227])

def z_h2(p_abs_bar, T_C=20.0):
    """Compressibility factor of H2 at absolute pressure p [bar] and T [C]."""
    z20 = float(np.interp(p_abs_bar, _P_BAR, _Z_20C))
    return 1.0 + (z20 - 1.0) * 293.15 / (T_C + 273.15)

Z_TABLE_UNCERTAINTY_REL = 0.010
