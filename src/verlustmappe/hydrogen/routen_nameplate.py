"""Route N: hydrogen from electrical energy via the datasheet specific consumption.

  electrolyser:  V_H2 [Nm3] = E_el [kWh] / 4.8 [kWh/Nm3]   (Enapter, beginning of life)
  fuel cell:     m_H2 [kg]  = E_el [kWh] * 0.070 [kg/kWh]   (IE-LIFT '<70 g/kWh')

WARNING, read twice: this route makes the device efficiency a CONSTANT by
construction (EL 62.4% LHV, FC 42.9% LHV) regardless of the data. It cannot
show part-load behaviour, ageing, or temperature effects. It is a nameplate
BOUND, useful only to sanity-check the other routes and as a last-resort
fallback that must be labelled as such in every figure.
"""
from ..conversions import NL_to_kg, kg_to_mol, kg_to_NL, kg_to_kWh_LHV
from .. import registry as R

def h2_from_energy_nameplate(E_kWh, device):
    if device == "el":
        NL = E_kWh / R.get("el.spec_energy_kWh_per_Nm3") * 1000.0
        kg = NL_to_kg(NL); u = R.entry("el.spec_energy_kWh_per_Nm3")["uncertainty"]
        bound = "produced H2 assuming beginning-of-life spec energy (upper bound on H2)"
    elif device == "fc":
        kg = E_kWh * R.get("fc.h2_consumption_g_per_kWh") / 1000.0
        u = R.entry("fc.h2_consumption_g_per_kWh")["uncertainty"]
        bound = "consumed H2 at the nameplate MAXIMUM (upper bound on consumption)"
    else:
        raise ValueError(device)
    return dict(route="nameplate_" + device, mol=kg_to_mol(kg), kg=kg, NL=kg_to_NL(kg),
                kWh_LHV=kg_to_kWh_LHV(kg), uncertainty_rel=u, independent_of=["tank_pv", "water"],
                blind_to=["everything: efficiency is constant by construction"], note=bound)
