"""Route 3: device-reported hydrogen flow (Enapter 'h2_flow', NL/h).

Enapter computes this internally from electrical quantities (the device has no
flow meter). It is therefore CORRELATED with Route 1 and must not be counted as
an independent confirmation. Use it for the time SHAPE of production and as a
sanity check, not as a second vote in the closure.
Reference: Enapter handbook, EL 2.1 'Data collected by Enapter Cloud'.
"""
import numpy as np
from ..conversions import NL_to_kg, NL_to_mol, kg_to_kWh_LHV
from ..conversions import energy_kWh_from_power  # for signature symmetry only

def h2_from_telemetry(flow_NLh, t_s):
    """Integrate a NL/h flow series over time [s] -> NL."""
    f = np.asarray(flow_NLh, float); t = np.asarray(t_s, float)
    ok = np.isfinite(f) & np.isfinite(t)
    NL = float(np.trapezoid(f[ok], t[ok]) / 3600.0) if ok.sum() >= 2 else 0.0
    kg = NL_to_kg(NL)
    return dict(route="telemetry", mol=NL_to_mol(NL), kg=kg, NL=NL, kWh_LHV=kg_to_kWh_LHV(kg),
                uncertainty_rel=0.10, independent_of=["tank_pv", "water"],
                blind_to=["same as faraday; correlated with it"])
