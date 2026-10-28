# P13 hand reference: integration (D24)

Status: DRAFT for owner approval (protected path, approval per file). Committed BEFORE the code
that must reproduce it exists (hand README rule 2). Computed by `p13_hand_calc.py` (stdlib only,
no import of `verlustmappe`, no legacy output).

## Definition (from D24 and the P13 owner decisions, not from code)
- Samples with a non-finite TIMESTAMP are dropped and counted. The remaining timestamps define
  the span (first to last, including edge samples whose VALUE is non-finite).
- Time over these samples must be non-decreasing. dt < 0: INVALID "non-monotonic time".
- Samples with a non-finite VALUE are then dropped and counted (`n_dropped` counts both kinds).
  dt = 0 with different values: INVALID "duplicate timestamp with conflicting values".
  dt = 0 with equal values: allowed, contributes zero. "Equal" means exact equality: a tolerance
  would be an invented number (rule 8) and may only be introduced by a DECISIONS entry. The
  strictness is deliberate: two boundary samples of merged exports that differ in the last
  decimal make the window INVALID; do not "repair" it silently.
- Gap limit = max(3 x nominal_dt_s, 30 s). A segment with dt > limit is a gap (strict). Gaps are
  excluded, never bridged. Other segments contribute the trapezoid (y0 + y1) / 2 x dt.
- `covered_fraction` = sum of the times of the non-gap segments / span, with span = last minus
  first finite timestamp of the INPUT (time based, not a sample count; NaN-valued samples count
  for the span, not for the value). Over the valid samples only, a series with NaN edges would
  show full coverage: the plausible-number trap. Optional explicit window limits for the ledger
  call are a P14 matter and are not part of P13.
- Fewer than two finite samples remain (single sample, all values non-finite): INVALID
  "no valid samples". Samples exist but no segment with positive time below the gap limit (all
  intervals are gaps, or only duplicate timestamps): INVALID "no covered segment". `value` is
  None in both cases, never 0. The reason text lands in ledger and report, so it must say what
  is true.
- Result shape: every branch returns the same keys (`valid`, `reason`, `value`,
  `covered_fraction`, `n_gaps`, `n_dropped`); fields that cannot be computed are None (e.g.
  `n_gaps` for non-monotonic time), never missing.
- Known limitation: in the non-monotonic branch `n_dropped` counts only the dropped non-finite
  timestamps (the branch exits before the value drop). The branch is INVALID anyway; documented,
  not fixed.
- A non-finite TIMESTAMP is a different problem from a non-finite value; it is handled alike
  (sample dropped, counted in `n_dropped`) and does not widen the span.
- Within the gap limit the trapezoid bridges dropped samples linearly (D24 continuity). Those
  bridged values are reconstructed, not measured; `n_dropped` is the only trace. A
  `covered_fraction` of 1.0 is therefore NOT a statement of completeness (case D).
- Constants D24: factor 3, `max_gap_s` = 30 s (pinned in the test).
- Unit: y-unit x s (power in W gives J; kWh = J / 3.6e6 by the caller).

## Cases (values by hand, asserted in `p13_hand_calc.py`)
| Case | Input | Expected |
|---|---|---|
| Limits | nominal 60 / 1 / 20 s | limit 180 / 30 / 60 s |
| A constant | t = 0..300 step 60, y = 1000 | 300 000, coverage 1, 0 gaps |
| B ramp | t = 0..3600 step 60 (61 samples), y = 3000 t / 3600 | trapezoid 5.4e6 J = 1.5 kWh (analytic 0.5 x 3000 x 3600); forward rectangles 5.31e6 J = 1.475 kWh; deviation 0.09e6 / 5.31e6 = 1.695 % of the rectangle value (1.667 % of the trapezoid value) |
| C gap | t = 0, 60, 120, 600, 660, 720, y = 1000, nominal 60 | 240 000, coverage 240 / 720 = 1/3, 1 gap |
| D NaN boundary | t = 0..300 step 60, y nan at 120 and 180 | samples 0, 60, 240, 300: the dt = 180 equals the limit, no gap; 60 000 + 270 000 + 120 000 = 450 000, coverage 1, dropped 2 |
| D2 NaN gap | y nan at 120, 180, 240 | dt 60 to 300 = 240 > 180 is a gap: 60 000, coverage 60 / 300 = 0.2, 1 gap, dropped 3 |
| E nominal 1 s | t = 0, 30, 61, y = 100 | limit 30: dt = 30 passes (3 000), dt = 31 is a gap; coverage 30 / 61 |
| E2 nominal 20 s | t = 0, 60, 121, y = 100 | limit 60 (3 x 20 > 30): dt = 60 passes (6 000), dt = 61 is a gap |
| F two samples | t = 0, 60, y = 0, 600 | 18 000, coverage 1 |
| F single sample | one sample | INVALID "no valid samples" |
| G equal duplicate | t = 0, 60, 60, 120, y = 1000 | 120 000, coverage 1 |
| G2 conflicting duplicate | same t, y = 1000, 1000, 2000, 2000 | INVALID "duplicate timestamp with conflicting values" |
| J NaN at edges | t = 0..300 step 60, y = nan, 1000 x4, nan | 3 segments x 60 s x 1000 W = 180 000, coverage 180 / 300 = 0.6 (a span over valid samples only would give 1.0), dropped 2 |
| J1 NaN first value | t = 0, 60, 120, y = nan, 1000, 1000 | 60 000, coverage 60 / 120 = 0.5 (over the remaining samples it would be 1.0), dropped 1 |
| M result shape | five invalid branches | same six keys each time |
| J2 NaN timestamp | t = 0, 60, nan, 120, y = 1000 | 120 000, coverage 1, dropped 1 |
| K only duplicates | t = 0, 0, 0, y = 5 | INVALID "no covered segment" (no segment with positive time) |
| H non-monotonic | t = 0, 60, 30 | INVALID "non-monotonic time" |
| I zero coverage | t = 0, 1000, 2000, nominal 60 | INVALID "no covered segment" (3 valid samples, 2 gaps), never 0 |
| I2 all non-finite | y = nan, nan, nan | INVALID "no valid samples", dropped 3 |

## Sign predicate `check_nonnegative(value, name)` (D31; three-way, owner decision 2026-10-28)
- Finite and >= 0.0: returns True. Exact comparison, no tolerance (a tolerance would be an
  invented limit, rule 8); -0.0 counts as 0.0.
- Finite and < 0.0: returns False. This is the D25 data verdict "a physical quantity is negative",
  so the caller books INVALID with a reason; the predicate must not raise, otherwise the ledger
  cannot record the verdict.
- NaN, +inf, -inf, or a non-number (including bool): raises ValueError (caller error: a broken
  calculation path, not a data condition).
Asserted in case L of `p13_hand_calc.py`. Applies to computed/modelled quantities only, never
to raw channel values (D31 wording).

## Reading of D24's ramp number (rule 3)
D24 quotes "1.475 vs 1.5 kWh, about 1.7 % at 60 s sampling" without stating the ramp. The ramp in
case B (0 to 3000 W linearly over one hour) is MY reconstruction; it reproduces both kWh numbers
(1.475 kWh forward rectangles, 1.5 kWh trapezoid). The percentage depends on the denominator:
0.025 / 1.475 = 1.695 % (relative to the rectangle value, the one asserted here) and
0.025 / 1.5 = 1.667 % (relative to the trapezoid value); both read "about 1.7 %" as in D24. The
numbers are recomputed here, not copied. UNVERIFIED: that this is the ramp the D24 text had in mind.

## Provenance
All inputs are synthetic and chosen by hand; no external source is used and none is needed.
The rule itself is DECIDED in D24 (factor 3, 30 s), D31 (signs) and the P13 owner decisions of
2026-10-28.

## UNVERIFIED
- The ramp of D24 (see above).
- Explicit window limits for `covered_fraction` (P14); the default span is the input span.
