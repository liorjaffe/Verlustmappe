# P08 - Pre-M1 definition gates (DECISIONS D20-D30, AGENTS alignment)

**Status:** Complete (pending review); all entries approved by the owner on 2026-10-28
**Reference:** ROADMAP.md M0/M1 entry condition; HANDOFF order (D5, gates before M1);
DECISIONS D2, D5, D7, D8, D15.
**Patch base:** `main` after PR #6 (`e15704b`).

## Goal
The definitions the new core needs before M1 (cycle closure, RTE terms, control-energy netting,
ledger scope, integration rule, validity gates, status vocabulary, registry scope, truth order,
AC8 scope) are recorded as DECISIONS entries D20-D30, each approved by the owner individually.
AGENTS.md is aligned in the same commit. Text only: no code, registry or test change.

## Write-Scope
`DECISIONS.md` (append D20-D30; note on D5), `AGENTS.md` ("Status vocabulary" and "Legacy
freeze" sections only), `HANDOFF.md`, this file. Protected paths: approval is the owner's
per-entry release in this task.

## Do not touch
`src/`, `tests/`, `registry.py`, `SPEC.md` (translation of D20-D26 is P09), `ci_guard.py`,
`pyproject.toml`, `SOURCES.md`.

## Open follow-up
SPEC follow-up mandatory in P09 before M1 code (D20, D21, D22 change SPEC wording).

## Explicitly outside P08
SPEC text (P09); the register column "u not assessed" and the enforcement test (P09/M1);
params adapter behavior (P11); status of `fc.poc_max_duration_s` (audit item in HANDOFF).

## Acceptance
`run_all` ALL PASS, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check`;
one text commit; every entry carries its owner-approved status.
