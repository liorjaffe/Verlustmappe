"""Four independent-ish ways to estimate the hydrogen mass in a time window,
numbered like the handbook cards: Route 1 (Faraday), Route 2 (tank pV),
Route 3 (telemetry), Route 4 (water), Route N (nameplate bound).

No hydrogen flow meter exists in this plant. Hydrogen mass is never "measured";
it is ESTIMATED by several routes and the routes are compared (z_closure.py).
Route disagreement IS the reported hydrogen uncertainty; production-minus-
delivered is a physical gas-loss estimate.

Support modules (z_ prefix, alphabetical after the routes):
  z_realgas.py         compressibility factor Z (NIST/Leachman table)
  temperature_model.py three-tier tank gas temperature (ambient / sensors /
                       GS-fit model, from the Nexo + de Miguel papers)
  z_closure.py         route agreement + gas-loss estimate
"""
from .route1_faraday import h2_from_stack_current
from .route2_tank_pv import h2_from_tank_pressure
from .route3_telemetry import h2_from_telemetry
from .route4_water import h2_from_water
from .routen_nameplate import h2_from_energy_nameplate
from .z_closure import compare_routes
from .z_realgas import z_h2
from .temperature_model import gs_fit_from_pressure_decay
