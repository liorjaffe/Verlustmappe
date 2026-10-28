# P09 - SPEC translation of D20-D26 (and the SPEC-visible parts of D23-D25, D29, D30)

**Status:** Executed (owner approved paragraphs and D31, 2026-10-28)
**Reference:** ROADMAP.md M0/M1 entry condition; HANDOFF "SPEC follow-up mandatory in P09
before M1 code"; DECISIONS D7 (SPEC changes only via DECISIONS), D20-D26, D29, D30.
**Patch base:** `main` after PR #7 (`49d8bc1`).

## Goal
`SPEC.md` states the decided definitions (closure, RTE terms, control-energy netting, ledger
scope, integration rule, validity gates, status vocabulary) so that M1 tests can be derived
from it. No new requirement beyond D20-D30.

## Write-Scope
`SPEC.md` (sections: Sources of truth, System boundary, Layers/ledger, new sections for RTE
netting and data validity, Functional criteria AC1/AC7/AC8, Status vocabulary), `DECISIONS.md`
(append D31 only, the sign rule of D25), `HANDOFF.md`, this file. SPEC and DECISIONS are
protected paths: approval is the owner's per-paragraph / per-entry release in this task.

## Do not touch
`src/`, `tests/`, `registry.py`, existing DECISIONS entries, `AGENTS.md`, `tools/`, README.

## Outside P09 (own task P09b, code)
The register column "u not assessed" (`reporting/make_register.py`, docs/02) and the
enforcement test for the D26 classification: code and tests, therefore not text-only.
Order: P09 -> P09b -> P10. The SPEC paragraphs for D26 stay in P09 and do not wait for P09b.

## Acceptance
`run_all` ALL PASS, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check`;
every SPEC statement traceable to a D-number; no SPEC text contradicts D20-D30.
