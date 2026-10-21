"""Monte-Carlo band for the loss map (GUM Supplement 1, JCGM 101:2008).

Every registry entry with status != MEASURED is drawn from
N(value, value*uncertainty); the loss map is recomputed; the 5th/95th
percentiles of the outputs are reported.

Sampling discipline (external review 2026-10):
  - quantities bounded on (0,1] (efficiencies) are drawn then CLIPPED into
    (1e-3, 1] by a TRUNCATED normal so eta_F > 1 draws cannot happen without
    a point mass at 1.0;
  - positive quantities stay positive; negative-valued entries are drawn
    relatively (nominal*(1+N(0,u))) and keep their sign;
  - draws that make the loss map return no RTE are COUNTED and reported as
    failed_draws, not silently dropped;
  - meas.power_rel_unc is applied to the electrical energies of the result
    (E_in and E_out are additionally scaled by N(1, u_power)), because the
    registry uncertainty of device power claims is not otherwise represented.
The band covers ASSUMPTIONS + power-measurement uncertainty, not formula errors.
"""
import numpy as np
from .. import registry as R
from ..balance.d_loss_map import loss_map

_POSITIVE = ("el.", "dry.", "comp.", "stor.", "fc.", "bat.", "pv.", "meas.")
_FRACTION = ("efficiency", "faradaic", "fraction", "uncertainty_rel", "purity")

def _is_fraction(key, entry):
    unit = str(entry.get("unit", ""))
    return unit in ("-", "mol fraction", "fraction of throughput") or \
           any(k in key for k in ("efficiency", "faradaic", "vent", "purity", "uncertainty_rel"))

def _draw_value(rng, key, entry, nominal):
    """One relative draw nominal*(1 + N(0,u)).
    Fractions with a nominal value in (0,1] are drawn from a normal TRUNCATED to
    (1e-3, 1] by rejection (clipping would pile ~50% of the draws of an
    efficiency of 1.00 +- 2% onto exactly 1.0). Negative nominals (e.g. a
    temperature coefficient) keep their sign; only positive nominals are
    protected against non-positive draws.
    (Note: the check for a fraction uses the NOMINAL value; n_cells = 120 is not
    a fraction and must never be clipped to 1.)"""
    u = entry["uncertainty"]
    if _is_fraction(key, entry) and 0 < nominal <= 1.0:
        for _ in range(1000):
            v = nominal * float(rng.normal(1.0, u))
            if 1e-3 < v <= 1.0:
                return v
        return float(np.clip(nominal, 1e-3, 1.0))
    v = nominal * float(rng.normal(1.0, u))
    if nominal > 0 and v <= 0:
        v = nominal * 1e-6
    return v

def loss_map_band(df_charge, df_discharge, n=500, seed=0, ci=(5, 95), **kw):
    rng = np.random.default_rng(seed)
    keys = [k for k, v in R.REGISTRY.items() if isinstance(v["value"], (int, float))
            and not isinstance(v["value"], bool) and v["uncertainty"] > 0 and v["status"] != "MEASURED"]
    saved = {k: R.REGISTRY[k]["value"] for k in keys}
    u_power = R.get("meas.power_rel_unc")
    rtes, bars, failed = [], [], 0
    try:
        for _ in range(n):
            for k in keys:
                v = _draw_value(rng, k, R.REGISTRY[k], saved[k])
                R.REGISTRY[k]["value"] = v
            # power-measurement uncertainty on the electrical energies
            s_in = float(rng.normal(1.0, u_power)); s_out = float(rng.normal(1.0, u_power))
            out = loss_map(df_charge, df_discharge, **kw)
            rte = out["rte"]["rte"]
            if rte is None:
                failed += 1
                continue
            e_in = out["rte"]["E_in_kWh"] * s_in
            e_out = out["rte"]["E_out_kWh"] * s_out
            rtes.append((e_out / e_in) if e_in > 0 else np.nan)
            # NOTE: rte from the model itself is NOT resampled here; the power
            # scale factors s_in/s_out ARE the meas.power_rel_unc application.
            bars.append([b["kWh"] for b in out["bars"]])
    finally:
        for k, v in saved.items():
            R.REGISTRY[k]["value"] = v
    rtes = np.array([r for r in rtes if np.isfinite(r)])
    bars = np.array(bars[:len(rtes)])
    lo, hi = np.percentile(rtes, ci)
    return dict(rte_mean=float(rtes.mean()), rte_lo=float(lo), rte_hi=float(hi), n=len(rtes),
                failed_draws=failed, ci=ci,
                bar_names=[b["stage"] for b in loss_map(df_charge, df_discharge, **kw)["bars"]],
                bar_lo=np.percentile(bars, ci[0], axis=0).tolist(),
                bar_hi=np.percentile(bars, ci[1], axis=0).tolist(),
                perturbed_keys=keys)
