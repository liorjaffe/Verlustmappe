"""Gate predicates (DECISIONS D25, D31). Pure functions: raw values in, verdict out. No run or
result objects (P14).

check_nonnegative(value, name) is the D31 sign rule. It applies to COMPUTED and MODELLED
quantities of the storage-chain ledger, never to raw channel values with a sign convention.
The caller declares which quantity is on the D31 list; the predicate only checks. Three-way:
  finite and >= 0.0   -> True
  finite and <  0.0   -> False  (the D25 data verdict; the caller books INVALID with a reason.
                                 It must not raise, otherwise the ledger cannot record it.)
  NaN, +-inf, a non-number or a bool -> ValueError (caller error: a broken calculation path)
Exact comparison, no tolerance (a tolerance would be an invented limit, AGENTS rule 8).
"""
import math


def check_nonnegative(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: expected a finite number, got {type(value).__name__} {value!r}")
    if not math.isfinite(value):
        raise ValueError(f"{name}: non-finite value {value!r} (caller error, not a data verdict)")
    return value >= 0.0


def time_is_monotonic(t_s):
    """True when the finite timestamps never decrease (equal neighbours allowed). Non-finite
    timestamps are skipped, as in `integration.integrate_trapezoid`."""
    prev = None
    for t in t_s:
        if not math.isfinite(t):
            continue
        if prev is not None and t < prev:
            return False
        prev = t
    return True
