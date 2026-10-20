"""Storage tank: mass in the tank from p, V, T and Z (real gas)."""
from .. import registry as R
from .. import constants as C
from ..conversions import mol_from_pVT, mol_to_kg, mol_to_NL, kg_to_kWh_LHV
from ..hydrogen.z_realgas import z_h2

class Tank:
    def stored(self, p_barg, T_C=20.0):
        p = p_barg + C.P_ATM_BAR
        mol = mol_from_pVT(p, R.get("stor.volume_L") / 1000.0, T_C + 273.15, z_h2(p, T_C))
        kg = mol_to_kg(mol)
        return dict(p_barg=p_barg, Z=z_h2(p, T_C), mol=mol, kg=kg, NL=mol_to_NL(mol),
                    kWh_LHV=kg_to_kWh_LHV(kg))
