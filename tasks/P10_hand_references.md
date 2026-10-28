# P10 - independent hand references for the ported physics (M1 entry)

**Status:** Files written, per-file owner review pending (separate commit per file)
**Reference:** ROADMAP M1 ("port of the core pieces"), SPEC Traceability (AC1 reference source
`tests/reference/hand/`), `tests/reference/hand/README.md` rules 1-4, AGENTS rule 4 and D2
(ported physics exists twice until M6).
**Patch base:** `main` after PR #9 (`8b11636`).

## Goal
Commit independent reference values BEFORE the P11 port exists (hand README rule 2), so the
ported `constants`, `z_realgas`, `temperature_model` can be tested against values that neither
the legacy nor the new code produced.

## Write-Scope
`tests/reference/hand/` (new files only: `constants.md`, `isothermal_work.md`, `p10_hand_calc.py`, protected path, owner approval per file),
`HANDOFF.md`, this file. No `src/`, no registry, no existing test.

## Scope decision (owner, 2026-10-28): items 1 and 2 now; Z later
Z (items 3/4) waits for the source clarification: first read what the existing table in
`z_realgas.py` actually rests on (docs/94 C25), then either a cited tabulation or a
recomputation from the published Leachman 2009 coefficients; check whether NIST WebBook offers
Z tables at 20 C at all. CoolProp stays a check tool. When Z comes, add one point BETWEEN
nodes (interpolation) and one above 350 bar (range guard, C25). Separate commits per file.

## Reference files now
1. `constants.md`: V_mol(NL) = R*273.15/101325, rho_H2,NL, LHV 119.96 MJ/kg -> kWh/kg, Wh/NL,
   J/kWh, Pa/bar. Normal-volume basis stated explicitly: 0 C, 1.01325 bar (the sys.volume_basis
   decision of the workbook). The key exists ONLY in the workbook (Master sheet, status "Project
   decision", layer "-"); it is text, not a number, so it is no registry candidate (D15). The
   reference cites the hash-pinned workbook row. Cites the provenance already in `constants.py`.
2. `isothermal_work.md`: TWO definitions exist in the code, each is checked on its own:
   (A) `conversions.isothermal_work_kWh`: closed system, ideal gas, W = n R T ln(p2/p1).
   (B) `temperature_model.isothermal_work_mol_integral`: fill integral against suction ps,
   per mol w/RT = [p2 ln(p2/p1) - (p2 - p1)] / (p2 - p1) for ps = p1,
   i.e. p2/(p2-p1) * ln(p2/p1) - 1. Hand values from a script that does not import verlustmappe.
   Hand check: at 2:1 (A) = 0.6931 RT, (B) = 2 ln 2 - 1 = 0.3863 RT.

## Findings from reading the code (documented, not fixed; frozen legacy)
- `devices/booster.py` `account()`: without a tank window it calls the fill integral (B) with
  ps = p_in; the docstring still says the single-shot form is kept. Text/behavior mismatch,
  candidate for docs/94.
- `conversions.isothermal_work_kWh` (A) has no active consumer: `devices/booster.py` imports
  it but never calls it; only `test_01` uses it. Candidate for docs/94 together with the
  docstring mismatch above (own docs/94 task in the pattern of P07, not P10).
- `test_02` pins (B) (Bovo anchor 33.22 Nm3, 40->200 bar, ps = 40: ~1.02 kWh).

## Acceptance
`run_all`, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check` green;
no value traced to code output; every number has derivation or page/table; README rules 1-4 met.
