"""Compare hydrogen routes.

Two DIFFERENT quantities live here and must not be conflated (external review
2026-10):

1. Route agreement: only complete routes measuring the SAME quantity may
   contribute to an agreement estimate.
2. Production minus delivered is a diagnostic residual, not an established
   physical loss. Its possible causes remain open.

This module therefore returns:
  mean/uncertainty only when at least two complete routes measure the same
  quantity; a diagnostic production-minus-delivered residual when both routes
  are present, without treating it as a loss.
"""
import numpy as np

def compare_routes(routes, exclude=("telemetry", "nameplate_el", "nameplate_fc",
                                    "faraday_el_minus_vent", "nameplate_el_minus_vent")):
    """Agreement analysis over routes that measure the same quantity.
    The exclusion list now also catches renamed variants (e.g.
    'nameplate_el_minus_vent') so a relabelled constant-efficiency route can
    no longer sneak into the independent vote (external review 2026-10)."""
    def base(r):
        return r["route"].replace("_minus_vent", "").replace("_minus_losses", "")
    # Production and delivered routes are separate groups; never combine them.
    PRODUCTION, DELIVERED = ("faraday_el", "water"), ("tank_pv",)
    cand = [r for r in routes if base(r) not in exclude and np.isfinite(r["kg"])]

    def has_complete_uncertainty(route):
        uncertainty_rel = route.get("uncertainty_rel")
        return (not route.get("uncertainty_incomplete", False)
                and isinstance(uncertainty_rel, (int, float, np.number))
                and not isinstance(uncertainty_rel, (bool, np.bool_))
                and bool(np.isfinite(uncertainty_rel)))

    complete = [r for r in cand if has_complete_uncertainty(r)]
    production_routes = [r for r in complete if base(r) in PRODUCTION]
    delivered_routes = [r for r in complete if base(r) in DELIVERED]
    production_present = any(base(r) in PRODUCTION for r in cand)
    if production_present and len(production_routes) >= 2:
        used = production_routes
    elif not production_present and len(delivered_routes) >= 2:
        used = delivered_routes
    else:
        used = []

    if used:
        vals = np.array([r["kg"] for r in used])
        sig = np.array([max(r["uncertainty_rel"], 1e-3) * abs(r["kg"]) for r in used])
        w = 1.0 / sig**2
        mean = float(np.sum(w * vals) / np.sum(w))
        u_mean = float(1.0 / np.sqrt(np.sum(w)) / abs(mean)) if mean else None
        spread = float((vals.max() - vals.min()) / abs(mean)) if mean else None
        u_reported = u_mean
        if spread is not None and np.isfinite(spread) and mean:
            u_reported = float(max(u_mean if u_mean is not None else 0.0, spread))
        out = dict(mean_kg=mean, weighted_uncertainty_rel=u_mean,
                   uncertainty_rel=u_reported,
                   max_spread_independent=spread, n_independent=len(used),
                   note=("agreement analysis over at least two complete routes "
                         "measuring the SAME quantity group"))
    else:
        out = dict(mean_kg=None, weighted_uncertainty_rel=None,
                   uncertainty_rel=None, max_spread_independent=None,
                   n_independent=0,
                   note="no quantity group has at least two complete routes with uncertainty")

    # Production minus delivered is diagnostic only; it is not a booked loss.
    tank = next((r for r in routes if r["route"] == "tank_pv"), None)
    prod = next((r for r in routes if base(r) == "faraday_el"), None)
    if prod is None:
        prod = next((r for r in routes if base(r) == "water"), None)
    if tank is not None and prod is not None and prod["kg"] > 0:
        residual_kg = prod["kg"] - tank["kg"]
        uncertainty_incomplete = not (
            has_complete_uncertainty(prod) and has_complete_uncertainty(tank))
        uncertainty_kg = None
        if not uncertainty_incomplete:
            uncertainty_kg = float(np.sqrt(
                (prod["uncertainty_rel"] * prod["kg"])**2 +
                (tank["uncertainty_rel"] * tank["kg"])**2))
        out["production_minus_delivered_residual"] = dict(
            kg=residual_kg,
            fraction_of_production=residual_kg / prod["kg"],
            uncertainty_kg=uncertainty_kg,
            uncertainty_incomplete=uncertainty_incomplete,
            note=("diagnostic residual only; cause NOT established "
                  "(purge/vent/leakage are candidates, not findings); "
                  "never booked as a loss"))
    return out
