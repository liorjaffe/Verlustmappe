"""Route 1: hydrogen from stack current (Faraday's law).

    ELECTROLYSER (production):  n_H2 = eta_F * N_cells * (integral I dt) / (2F)
    FUEL CELL (consumption):    n_H2 = N_cells * (integral I dt) / (2F * eta_F)

The direction matters (external review 2026-10): a lower Faradaic efficiency
means MORE hydrogen must flow per unit of charge in a fuel cell (some current
is lost to crossover/parasitic reactions), so the efficiency enters the
denominator on the consumption side and the numerator on the production side.
The first draft multiplied in both directions, which biased FC consumption low.

Inputs that are assumptions: n_cells, eta_F (registry, GUESS). The route is
blind to shunt currents, crossover, leaks and purge losses regardless of
direction: on the electrolyser side it overestimates delivered gas, on the
fuel-cell side it underestimates consumed gas.
"""
import numpy as np
from ..conversions import mol_from_charge, mol_to_kg, mol_to_NL, kg_to_kWh_LHV
from .. import registry as R

def h2_from_stack_current(I_stack_paths, dt_s, n_cells, faradaic_eff, device="el"):
    """I_stack_paths: list of 1-D arrays, one per parallel stack. dt_s: sample
    intervals [s] (array or scalar). device: 'el' (production) or 'fc'
    (consumption) - selects the direction of the efficiency correction and the
    registry entries used for the uncertainty."""
    if device not in ("el", "fc"):
        raise ValueError(device)
    paths = I_stack_paths if isinstance(I_stack_paths, (list, tuple)) else [I_stack_paths]
    mol_faraday = sum(mol_from_charge(np.asarray(p, float),
                                      np.broadcast_to(dt_s, np.shape(p)), n_cells)
                      for p in paths)
    if device == "el":
        mol = mol_faraday * faradaic_eff
    else:
        mol = mol_faraday / max(faradaic_eff, 1e-3)
    kg = mol_to_kg(mol)
    u_n = R.entry(f"{device}.n_cells")["uncertainty"]
    u_f = R.entry(f"{device}.faradaic_efficiency")["uncertainty"]
    u_p = R.get("meas.power_rel_unc")
    u = float(np.sqrt(u_n**2 + u_f**2 + u_p**2))
    return dict(route=f"faraday_{device}", mol=mol, kg=kg, NL=mol_to_NL(mol),
                kWh_LHV=kg_to_kWh_LHV(kg), uncertainty_rel=u,
                independent_of=["tank_pv", "water"],
                blind_to=["shunt current", "crossover", "leaks",
                          "purge/vent losses", "device-internal losses downstream of the stack"],
                note=("production: eta_F multiplies (Faradaic losses reduce delivered H2)"
                      if device == "el" else
                      "consumption: eta_F divides (Faradaic losses increase consumed H2)"))
