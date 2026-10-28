"""Ideal isothermal work of filling a vessel (fill integral, definition B in
tests/reference/hand/isothermal_work.md).

Filling from p1 to p2 delivers only (p2 - p1) V / (R T) mol, each compressed from the suction
pressure ps to the current vessel pressure p:
    W = n R T [G(p2) - G(p_start)] / (p2 - p1),   G(p) = p ln(p/ps) - p
Ported from `hydrogen/temperature_model.isothermal_work_mol_integral`; behavior is identical,
only names carry units. The closed-system form n R T ln(p2/p1) (definition A) is not ported:
it has no active consumer in the legacy chain.
"""
import math
from dataclasses import dataclass

from . import constants as C


@dataclass(frozen=True)
class FillWork:
    """Result of the fill integral. `exactly_zero` marks a physically exact zero (the integral
    is empty), so the ledger can tell it from "not computed"; `reason` names the case."""
    work_kWh: float
    exactly_zero: bool = False
    reason: str = ""


def isothermal_fill_work_kWh(amount_mol, p_start_abs_bar, p_end_abs_bar, T_K, p_suction_abs_bar=None):
    """Minimum isothermal work to add `amount_mol` while the vessel rises from p_start to
    p_end (absolute pressures). The suction pressure defaults to p_start.

    Two cases are an exact zero of the integral, not a clamp (flagged in the result): the vessel
    does not rise (p_end <= p_start) or stays below the suction pressure (p_end <= ps).
    A vessel starting below ps is compressed only from ps upward: gas flows in without
    compression work until the vessel reaches ps, so the integration starts at max(p_start, ps).
    """
    p1, p2 = float(p_start_abs_bar), float(p_end_abs_bar)
    ps = float(p_suction_abs_bar) if p_suction_abs_bar is not None else p1
    if not (math.isfinite(p1) and math.isfinite(p2) and math.isfinite(ps)):
        raise ValueError("pressures must be finite")
    if p2 <= p1:
        return FillWork(0.0, True, "vessel does not rise")
    if ps <= 0:
        raise ValueError("suction pressure must be positive")
    if p2 <= ps:
        return FillWork(0.0, True, "vessel stays below suction pressure")

    def G(p):
        return p * math.log(p / ps) - p

    p_work_start_abs_bar = max(p1, ps)
    work_J_per_mol = C.R_J_PER_MOL_K * T_K * (G(p2) - G(p_work_start_abs_bar)) / (p2 - p1)
    return FillWork(float(amount_mol * work_J_per_mol / C.J_PER_KWH))
