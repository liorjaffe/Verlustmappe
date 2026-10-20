"""Compare hydrogen routes.

Two DIFFERENT quantities live here and must not be conflated (external review
2026-10):

1. Route agreement (closure): when routes measure the SAME quantity (e.g. two
   production estimates), their spread is an uncertainty.
2. Route DIFFERENCE (gas loss): Faraday measures gas PRODUCED at the stack,
   the tank route measures gas DELIVERED to storage. Their difference is not
   an uncertainty - it is an ESTIMATE OF SYSTEM GAS LOSS (purge, vent, leak).
   The first draft reported it as uncertainty; that conflated loss with error.

This module therefore returns:
  mean/uncertainty from the routes that measure the same quantity;
  gas_loss_estimate when a production route AND the tank route are both
  present: production minus (net into tank), with the tank route's uncertainty
  as the loss estimate's uncertainty floor.
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
    used = [r for r in routes if base(r) not in exclude and np.isfinite(r["kg"])]
    if not used:
        return dict(mean_kg=None, note="no independent routes available")
    vals = np.array([r["kg"] for r in used])
    sig = np.array([max(r["uncertainty_rel"], 1e-3) * abs(r["kg"]) for r in used])
    w = 1.0 / sig**2
    mean = float(np.sum(w * vals) / np.sum(w))
    u_mean = float(1.0 / np.sqrt(np.sum(w)) / abs(mean)) if mean else None
    devs = {r["route"]: float((r["kg"] - mean) / mean) for r in routes if mean}
    spread = float((vals.max() - vals.min()) / abs(mean)) if mean else None  # used routes only
    # Handbook card G promises "reported uncertainty = max(statistical, spread)".
    # The first draft RETURNED both separately but never combined them, so every
    # downstream consumer silently used the (smaller) statistical value and the
    # promise was broken (fixed 2026-10; guarded by test_02).
    u_reported = u_mean
    if spread is not None and np.isfinite(spread) and mean:
        u_reported = float(max(u_mean if u_mean is not None else 0.0, spread))
    out = dict(mean_kg=mean, weighted_uncertainty_rel=u_mean,
               uncertainty_rel=u_reported,
               max_spread_independent=spread, n_independent=len(used),
               note=("agreement analysis over same-quantity routes only; "
                     "uncertainty_rel = max(statistical, spread) per handbook card G"))
    # gas-loss estimate: a production-side route vs the tank route
    tank = next((r for r in routes if r["route"] == "tank_pv"), None)
    prod = next((r for r in routes if base(r) in ("faraday_el", "water")), None)
    if tank is not None and prod is not None and prod["kg"] > 0:
        loss_kg = prod["kg"] - tank["kg"]
        u_loss = float(np.sqrt((prod["uncertainty_rel"] * prod["kg"])**2 +
                               (tank["uncertainty_rel"] * tank["kg"])**2))
        out["gas_loss_estimate"] = dict(kg=loss_kg,
                                        fraction_of_production=loss_kg / prod["kg"],
                                        uncertainty_kg=u_loss,
                                        note="PRODUCTION - DELIVERED = system gas loss (purge+vent+leak); "
                                             "a physical loss estimate, NOT an uncertainty")
    return out
