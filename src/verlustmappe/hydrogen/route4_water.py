"""Route 4: hydrogen from water consumed.

    2 H2O -> 2 H2 + O2      1 mol H2O (18.015 g)  ->  1 mol H2 (2.016 g)

So every 9.0 g of water consumed yields 1.0 g of hydrogen (mass ratio 8.94).
Measured by weighing/metering the feed water over a window. Cheap and fully
independent of electrochemistry and of the tank. Caveats: water also leaves as
vapour in the H2 stream (removed in the dryer) and in the O2 vent, which makes
this route an UPPER bound on H2 produced.
"""
from ..conversions import kg_to_mol, kg_to_NL, kg_to_kWh_LHV

M_H2O_KG_PER_MOL = 18.015e-3
M_H2_KG_PER_MOL = 2.016e-3

def h2_from_water(water_kg, uncertainty_rel=0.05):
    kg = water_kg * M_H2_KG_PER_MOL / M_H2O_KG_PER_MOL
    return dict(route="water", mol=kg_to_mol(kg), kg=kg, NL=kg_to_NL(kg), kWh_LHV=kg_to_kWh_LHV(kg),
                uncertainty_rel=uncertainty_rel, independent_of=["faraday", "tank_pv", "telemetry"],
                blind_to=["water lost as vapour: makes this an upper bound"])
