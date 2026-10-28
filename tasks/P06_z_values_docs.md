# P06 - Z-value documentation aligned with the code and test_02

**Status:** Complete (pending review)
**Reference:** ROADMAP.md M0 (documentation hygiene); HANDOFF order (Z-value check);
DECISIONS D2 (docs are outside the frozen code).
**Patch base:** `main` after PR #4 (`8ea1e13`).

## Goal
docs/01, docs/04 and the README FAQ quote the Z values that `src/verlustmappe/hydrogen/z_realgas.py`
and `tests/test_02_hydrogen_routes.py` actually use (1.125 at 200 bar/20 C, 1.227 at 350 bar/20 C),
with the CoolProp 8.0.0 cross-check as a named verification tool, not a dependency.

## Write-Scope
`docs/01_methods_handbook.md` (the "Verified by" line of the real-gas section),
`docs/04_validation_log.md` (test_02 table row, history marker), `README.md` (FAQ answer
"Is 200 bar hydrogen an ideal gas?" only, outside the generated block), `HANDOFF.md`, this file.

## Do not touch
Code, tests, registry, `docs/94` (no new C entry: the 15 C / 20 C wording is a precision
issue in the evidence text, not a defect), `pyproject.toml` and the CI package list (CoolProp
stays out), anything between the README GENERATED markers.

## Work items
1. docs/01: quote the `test_02` assertions exactly (values, temperatures, tolerances) and the
   CoolProp cross-check Z(200,20)=1.1247, Z(350,20)=1.2240 (table deviation 0.25 %, within +-1 %),
   Z(350,15)=1.2273, rho(200 bar, 20 C)=14.7 kg/m3.
2. docs/04: same values in the test_02 row; the "NIST table (1.132)" history line gets the marker
   "superseded; current table 1.125".
3. README FAQ: Z = 1.125, about 12.5 %, +-1 % (0-300 bar, 0-50 C).

## Acceptance
`run_all` ALL PASS, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check`;
`grep -rn "1\.132\|1\.234" docs README.md` leaves only the marked history line.
Values were recomputed with CoolProp 8.0.0 on 2026-10-28 (not taken from a review text).

## Notes (no action)
- The `test_02` comment "CoolProp/Leachman check point (at 20 C)" for 350 bar is imprecise: CoolProp
  gives 1.2273 at 15 C and 1.2240 at 20 C; the test compares the table to 1.227 (tolerance 0.002).
  Tests are protected and unchanged.
