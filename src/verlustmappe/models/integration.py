"""One integration function for the whole core (DECISIONS D24).

Trapezoid within valid segments; a gap is dt > max(GAP_FACTOR x nominal_dt_s, MAX_GAP_S). Gaps
are excluded, never bridged and never filled. The covered fraction is time based over the span of
the input (first to last finite timestamp), so NaN-valued edge samples count for the span, not
for the value. Within the gap limit the trapezoid bridges dropped samples linearly: those values
are reconstructed, `n_dropped` is the only trace, and covered_fraction = 1.0 is no statement of
completeness.

Data conditions return an `Integral` with valid = False, a reason and value = None (never a
plausible number, never 0). An empty input is a caller error and raises ValueError.
Reference and branch order: tests/reference/hand/integration.md, p13_hand_calc.py.

Unit: y-unit x s (power in W gives J; the caller converts to kWh).
"""
import math
from dataclasses import dataclass
from typing import Optional

GAP_FACTOR = 3.0   # D24: multiplier on the nominal sampling interval
MAX_GAP_S = 30.0   # D24: legacy-continuity value (not newly derived)


@dataclass(frozen=True)
class Integral:
    """Same keys in every branch; fields that cannot be computed are None."""
    valid: bool
    reason: str
    value: Optional[float] = None
    covered_fraction: Optional[float] = None
    n_gaps: Optional[int] = None
    n_dropped: Optional[int] = None


def gap_limit_s(nominal_dt_s):
    return max(GAP_FACTOR * nominal_dt_s, MAX_GAP_S)


def integrate_trapezoid(t_s, y, nominal_dt_s):
    """Integral of y over t_s per D24. `nominal_dt_s` has no default: the caller names the
    source's nominal sampling interval (docs/03)."""
    t_s = list(t_s)
    y = list(y)
    if not t_s or len(t_s) != len(y):
        raise ValueError("t_s and y must be non-empty and of equal length")
    if not (math.isfinite(nominal_dt_s) and nominal_dt_s > 0.0):
        raise ValueError(f"nominal_dt_s must be finite and > 0, got {nominal_dt_s!r}")

    stamped = [(a, b) for a, b in zip(t_s, y) if math.isfinite(a)]
    n_bad_time = len(t_s) - len(stamped)
    for (t0, _), (t1, _) in zip(stamped, stamped[1:]):
        if t1 < t0:
            return Integral(False, "non-monotonic time", n_dropped=n_bad_time)

    pts = [(a, b) for a, b in stamped if math.isfinite(b)]
    n_dropped = len(t_s) - len(pts)
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        if t1 == t0 and y1 != y0:
            return Integral(False, "duplicate timestamp with conflicting values",
                            n_dropped=n_dropped)
    if len(pts) < 2:
        return Integral(False, "no valid samples", n_dropped=n_dropped)

    limit = gap_limit_s(nominal_dt_s)
    value = covered = 0.0
    n_gaps = 0
    for (t0, y0), (t1, y1) in zip(pts, pts[1:]):
        dt = t1 - t0
        if dt > limit:
            n_gaps += 1
            continue
        value += 0.5 * (y0 + y1) * dt
        covered += dt
    if covered <= 0.0:
        return Integral(False, "no covered segment", n_gaps=n_gaps, n_dropped=n_dropped)
    span = stamped[-1][0] - stamped[0][0]
    return Integral(True, "", value, covered / span, n_gaps, n_dropped)
