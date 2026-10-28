# P11 - port of constants and fill work, minimal params adapter (M1 start)

**Status:** Code written (commit 1); tests need owner approval (commit 2, own commit, rule 4)
**Reference:** ROADMAP M1 ("port of the core pieces into `src/verlustmappe/models/`"), AGENTS
Legacy freeze (new-core import rule, one adapter exception), D2, D26, D28, SPEC AC1.
**Patch base:** `main` after PR #10.

## Goal
Start the new core with the pieces that need no open source: constants, the fill-integral
work (definition B of `tests/reference/hand/isothermal_work.md`), and a minimal adapter.

## Write-Scope
Commit 1: `src/verlustmappe/models/` (new: `__init__.py`, `constants.py`, `temperature_model.py`,
`params.py`), `HANDOFF.md`, this file.
Commit 2: `tests/test_36_port_core_physics.py` (new file, protected path).
Draft: session folder `files/draft_tests/test_36_port_core_physics.py`, 11 tests pass.

## Do not touch
Legacy modules, `registry.py`, `tests/` other than the new file, `.github/CODEOWNERS`,
`tools/ci_guard.py` (planned follow-up P14: import-rule guard for the new core).

## Deliberately NOT in P11
- `z_realgas` (no independent source yet, docs/94 C25; needs the Z-source clarification).
- Definition A (`isothermal_work_kWh`): no active consumer.
- Other `temperature_model` functions (tiers, GS fit, hot-end bracket): depend on Z.
- Full adapter (u class passing, per-run parameter sets): P12.

## Owner decisions (2026-10-28)
1. The `max(p_start, ps)` start and the 0.0 for a non-rising vessel or one below suction are
   properties of the fill integral (empty integration range, no compression work below ps), not
   clamps in the sense of AGENTS rule 8 (pattern C5: silent clamping to `mol_window`). Condition:
   the zero stays recognizable. `isothermal_fill_work_kWh` therefore returns the frozen
   `FillWork(work_kWh, exactly_zero, reason)`, so the P12 ledger can tell "physically zero" from
   "not computed".
2. `barg_to_abs_bar` is physics, not adapter: it lives in `models/constants.py` (1.01325 bar,
   as the legacy booster). `params.py` stays the only module that reads `registry.py`.
3. The u class is not imported (reporting is legacy); `get_param` passes the status; the computed
   class and weakest-wins propagation are P12.
4. D28: with the adapter in place, test_36 carries the general guard (every registry entry with
   status REJECTED or SUPERSEDED is blocked, every other entry is readable); test_34 stays.

## Notes
- The import guard in test_36 overlaps with the planned ci_guard check for the new-core import
  rule (P14). Deliberate double protection: do not drop either as duplicate work.
- Import mechanics: there is no installed package and no conftest. Each test inserts `src/` into
  `sys.path` itself (as test_33/test_34 do); pyproject only sets `testpaths`. New-core tests must do
  the same until packaging is decided (owner).

## Acceptance
`run_all`, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check` green after
each commit; ported constants equal legacy exactly, fill work equals P10 hand values (rel 1e-6)
and legacy (rel 1e-12); the adapter blocks REJECTED and does not write back.
