# P13 - integration function (D24) and gate predicates (D25/D31) (DRAFT)

**Status:** Hand references merged (PR #17). Code written (this PR, commit 1); test_38 awaits owner approval (commit 2, own commit, rule 4). Draft: session folder `files/draft_tests/test_38_integration_gates.py`, 19 tests pass.
**Reference:** ROADMAP M1, D24, D25, D31, SPEC "Data integration and validity", AGENTS rules 1, 4, 8.
**Patch base:** `main` after PR #15.

## Goal
One integration function for the new core (trapezoid within valid segments, gaps segment the
series, covered fraction reported) and the sign/time gates as pure predicates. No ledger, no
run or result objects (P14).

## Findings from reading the repo (they shape the cut)
1. **D24 and D25(a) point to docs/03 for data that is not there.** `docs/03` has no nominal
   sampling interval per source, no multiplier table and no mandatory-channel list (grep: none).
   The legacy gap rule uses the MEDIAN dt of the data (`devices/electrolyzer._sample_gaps`), not a
   nominal interval. Rule 8: the core must not invent them. Consequence: the integrator takes
   `nominal_dt_s` as a required argument without a default, and the mandatory-channel predicate
   is NOT part of P13.
2. **The REQUIRED-BACKLOG gate has no data basis.** `registry.py` has no REQUIRED flag, so "a
   REQUIRED parameter is BACKLOG" cannot be evaluated yet. Not in P13; belongs to the AC1
   mechanism in P14 together with a decision where REQUIRED is recorded.
3. **The Route-2 gate has no consumer in the new core** (D8/D31(c): the new core does not use
   Route 2). Building it now violates rule 0. Not in P13; it stays a legacy-path rule.
4. **The NAMEPLATE fallback needs a result object**: P14/P15.
5. **Legacy integrates with forward rectangles** (`sum(P * dt_forward)`), `conversions.energy_kWh_from_power`
   uses the trapezoid without gap handling. D24 replaces both for the new core; the AC8 note in D24
   (1.475 vs 1.5 kWh on a ramp) is a number from the decision text: the hand reference recomputes
   it, it is not reused (rule 3).

## Proposed scope
**In:** `src/verlustmappe/models/integration.py` (new) and `src/verlustmappe/models/validity.py`
(new, pure predicates):
- `integrate_trapezoid(t_s, y, nominal_dt_s, max_gap_s)` returning a frozen
  `Integral(value, covered_fraction, n_gaps, valid, reason)`; `value` is `None` when `valid` is
  False (INVALID, never a plausible number).
  Gap: dt > max(3 x nominal_dt_s, max_gap_s) (D24). `max_gap_s` and the factor 3 are D24 values
  (the factor is written into the code with the D24 reference, no registry entry; the owner
  may adjust it via DECISIONS).
- Predicates: `time_is_monotonic(t_s)`; `check_nonnegative(value, name)` (see decision 2).

**Out (named):** mandatory channels, REQUIRED-BACKLOG, Route-2 (its predicate arrives with a
re-admission by DECISIONS entry, D31(c); it is not forgotten), NAMEPLATE fallback, any
run/result object, Faraday integration (own task with its hand reference).

## Write-Scope (proposal, one commit each)
1. This file + `HANDOFF.md`.
2. `tests/reference/hand/integration.md` and `tests/reference/hand/p13_hand_calc.py` (protected
   path, approval per file): constant series, ramp, gap, non-monotonic, NaN stretch, short series;
   stdlib only, expected values by hand, the D24 1.475 vs 1.5 case recomputed.
3. `src/verlustmappe/models/integration.py`, `validity.py`.
4. `tests/test_38_integration_gates.py` (new, protected path). Not test_20 (reserved for AC1).

## Do not touch
Legacy modules (including `conversions.py`, `devices/electrolyzer.py`), `registry.py`, `SPEC.md`,
`DECISIONS.md`, `docs/03` (a separate docs task, see question 1), existing tests.

## Owner decisions (2026-10-28)
1. **Constants.** `nominal_dt_s` is a required argument without a default (the caller names the
   source). The factor 3 and `max_gap_s = 30 s` are DECIDED in D24, so they are module constants
   in `models/integration.py` with a "D24" provenance comment and pinned in the test.
   **Docs task (separate, docs/03):** the NOMINAL cadence per source (instrument or telemetry
   specification, with the source named), not the observed median. The observed median may only
   appear as an explicitly marked fallback ("observed, not nominal") when no specification is
   found; otherwise a nominal quantity silently becomes a sample statistic.
2. **Predicates:** `time_is_monotonic` and `check_nonnegative(value, name)`. The D31 list says
   which quantities are non-negative; the caller declares it, the predicate only checks. Module
   header: applies to computed/modelled quantities, never to raw channel values (D31 wording).
3. **Non-finite samples** are dropped before the gap check (the span between the surrounding
   valid samples still measures the gap). `covered_fraction` is time-based: sum of valid segment
   times divided by t_end - t_start, not a sample count. The number of dropped samples is
   reported. A window without a single valid segment returns `valid = False`, reason
   "no valid samples", `value = None`; never 0 (a zero for a missing window is the plausible
   number the project must not output).
4. **Timestamps:** dt < 0 is INVALID; dt = 0 is allowed only when the values are equal (weight
   zero); dt = 0 with different values is INVALID, reason "duplicate timestamp with conflicting
   values". Both cases go into the hand reference.
5. **Result vs exception:** data conditions (non-monotonic time, no valid samples, conflicting
   duplicates) return the result object with `valid = False`, `reason`, `value = None`. An empty
   input sequence is a caller error and raises ValueError (same split as P12: program error
   raises, data condition reports).

## Hand reference content (`integration.md`, `p13_hand_calc.py`)
Constant series; ramp (the D24 1.475 vs 1.5 kWh case recomputed, not copied: rule 3); gap
(segmented, covered fraction time-based); NaN stretch; short series; dt = 0 equal values and
conflicting values; zero coverage; the two constants (factor 3, 30 s) as pinned values.

## Acceptance
`run_all`, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check` green after
the last edit; final report in the rule 9 format.

## Implementation notes
- `models/integration.py` mirrors the branch order of `p13_hand_calc.py` (monotonicity over finite
  timestamps before the value drop); stdlib only. Result `Integral` is a frozen dataclass with the
  same six keys in every branch.
- Addition not in the owner decisions: `nominal_dt_s` that is not finite or not > 0 raises
  ValueError (caller error; a zero or NaN nominal interval would silently make the gap limit the
  30 s constant). Reported for review.
- `models/validity.py`: `check_nonnegative` three-way contract (False for negative, ValueError for
  non-finite or non-number, bool excluded) and `time_is_monotonic` (agrees with the integrator).
- test_38 asserts the error messages, includes a seeded parity run (300 series) against the
  independent reference procedure, and mutation checks (strict gap boundary, factor 3) fail it.
