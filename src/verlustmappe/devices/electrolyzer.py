"""Electrolyser unit (EL 2.1 incl. its AC/DC power supply).

Alignment rule (external review 2026-10): power and stack current must live on
the SAME samples. Real telemetry is a wide Grafana frame where power and
current sit on interleaved timestamps; fillna(0) on one and interpolation on
the other silently halves the efficiency. account() therefore REQUIRES an
aligned frame: rows where either quantity is missing are DROPPED, never
filled. If nothing overlaps, a loud warning is returned instead of a number.

Energy integration: no gap bridging. An interval longer than max_gap_s is a
GAP: it contributes at most max_gap_s seconds at the mean observed power, and
data_coverage reports the observed fraction of the wall-clock window.
"""
import numpy as np
from .. import registry as R
from ..hydrogen import h2_from_stack_current, h2_from_energy_nameplate
from ._common import t_seconds

def _sample_gaps(t, max_gap_s):
    """Per-sample integration weights with a unified gap policy (external
    review 2026-10): a GAP is an interval longer than max(3 x median interval,
    max_gap_s). Gaps are EXCLUDED from integrals (dt = 0), never bridged and
    never filled with a guessed power level - a guess would invent production.
    Returns (dt_for_integration, coverage)."""
    if len(t) < 2:
        return np.array([0.0]), 0.0
    dt = np.diff(t)                     # dt[i] = t[i+1]-t[i], weight of sample i
    med = float(np.median(dt[dt > 0])) if (dt > 0).any() else 1.0
    gap_lim = max(3 * med, max_gap_s)
    is_gap = dt > gap_lim
    w = np.where(is_gap, 0.0, dt)
    w = np.append(w, 0.0)               # last sample has no forward interval
    span = max(t[-1] - t[0], 1e-9)
    coverage = float(w.sum() / span)
    return w, coverage

def _aligned_energy(P, t, max_gap_s):
    w, coverage = _sample_gaps(t, max_gap_s)
    e = float(np.sum(np.where(np.isfinite(P), P, 0.0) * w) / 3.6e6)
    return e, coverage

class ElectrolyzerUnit:
    def account(self, df, max_gap_s=30.0):
        t = t_seconds(df.index)
        P = df["power_W"].values.astype(float)
        has_I = "el_stack_current_A" in df.columns
        I = df["el_stack_current_A"].values.astype(float) if has_I else None
        keep = np.isfinite(P) & (np.isfinite(I) if has_I else True)
        P, t = P[keep], t[keep]
        df = df[keep]
        if has_I: I = I[keep]
        if has_I and len(t) < 2:
            h2 = dict(route="none", kg=np.nan, NL=np.nan, kWh_LHV=0.0, mol=0.0,
                      uncertainty_rel=1.0, note="unusable: no samples with power AND stack current")
            return dict(unit="ELU", energy_in_kWh=0.0, h2=h2, efficiency_LHV=None,
                        efficiency_is_measured=False, data_coverage=0.0, standby_kWh=0.0,
                        warning="no samples where power AND stack current are both finite: "
                                "timestamp alignment is broken, export is unusable")
        e_in, coverage = _aligned_energy(P, t, max_gap_s)
        if has_I:
            w, _ = _sample_gaps(t, max_gap_s)
            h2 = h2_from_stack_current([I], w, R.get("el.n_cells"),
                                       R.get("el.faradaic_efficiency"), device="el")
            eff_is_measured = True
        else:
            h2 = h2_from_energy_nameplate(e_in, "el")
            eff_is_measured = False
        eta = h2["kWh_LHV"] / e_in if e_in > 0 else None
        stby = np.where(P <= 3 * R.get("el.power_standby_W"), P, 0.0)
        e_stby = float(np.sum(stby * _sample_gaps(t, max_gap_s)[0]) / 3.6e6)
        return dict(unit="ELU", energy_in_kWh=e_in, h2=h2, efficiency_LHV=eta,
                    efficiency_is_measured=eff_is_measured, data_coverage=coverage,
                    standby_kWh=e_stby,
                    warning=None if eff_is_measured else
                    "EL efficiency is the nameplate constant (no stack current in data)")
