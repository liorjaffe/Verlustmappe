# P09b - register column "u class" (D26 classification)

**Status:** Commit 1 (code + docs) executed; commit 2 (enforcement test) needs owner approval
**Reference:** DECISIONS D26(b)/(c), SPEC "Status vocabulary" (uncertainty classification), AC7;
HANDOFF order P09 -> P09b -> P10.
**Patch base:** `main` after PR #8 (`f756f3a`).

## Goal
Make the D26 classification visible and checkable: a computed `u class` per registry entry
(`assessed` / `exact` / `NOT ASSESSED`), shown in `docs/02_uncertainty_register.md`. No new
status, no new registry field, no registry value change.

## Write-Scope
Commit 1: `src/verlustmappe/reporting/make_register.py` (function `u_class`, new column and
summary line; text/reporting only, no physics), `docs/02_uncertainty_register.md` (regenerated),
`HANDOFF.md`, this file.
Commit 2 (own commit, rule 4; tests/ is protected): `tests/test_35_u_class.py`, new file.

## Do not touch
`registry.py`, `SPEC.md`, `DECISIONS.md`, `AGENTS.md`, `tools/`, other tests, physics code.

## Classification rule as implemented
EXACT with u = 0.0 = status OWNER_DECISION, or one of the two TOLERANCE_BAND keys of D26(b)(iii)
(a closed list, extended only via DECISIONS). DERIVED with u = 0.0 is NOT ASSESSED by default
(D26: DERIVED alone does not establish exactness); a single DERIVED entry becomes exact only
through a DECISIONS entry that extends the D26 enumeration. D26(b)(ii) "pure arithmetic" is not
machine-checkable, so it has no automatic path. Today this affects `fc.poc_max_duration_s`
(open audit item). Result on 2026-10-28: 109 entries, 46 assessed, 4 exact (2 OWNER_DECISION,
2 TOLERANCE_BAND), 59 NOT ASSESSED (63 with u = 0.0 minus 4). REJECTED entries with u = 0.0
are NOT ASSESSED too (D26 counts them); D28 regulates their use, the column describes the entry.

## Acceptance
`run_all` ALL PASS, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check`;
docs/02 reproducible from `make_register.py`; counts above match.
