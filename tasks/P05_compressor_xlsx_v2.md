# P05 - Mark the DLE 30-2 compressor assumptions as REJECTED, add workbook v2 primary data

**Status:** Implemented on branch `feat/p05-compressor-xlsx-v2`, awaiting owner review
**Reference:** ROADMAP M1 (AC1, layer-1 parameters); DECISIONS D11–D15 (2026-10-27).
**Patch base:** `166a634` (re-verify with `git rev-parse main`).
**Precondition:** D11–D15 committed (owner-approved) before any other edit.
**Workbook SHA-256:** `0aa9f8ed0618d9bfd61123055674418969e0d7479d63b962afb18944cfd942ae`

## Goal
1. Status `REJECTED` for the six `comp.*` keys (values unchanged, legacy reproducible).
2. Register ONLY workbook rows with an allowed status (D15 list): Kaeser nameplate/datasheet,
   stage geometry, ratio, stroke counts, pressure limits, `sys.n_rotex`,
   `sys.p_h2_out_project_barg`, `kaeser.p_package_dealer_kw`. Each value needs a SOURCES
   entry (page/table, short verbatim quote, transferability). No Path A/B, no curve,
   no calculated values.
3. Hash-pinned workbook tests in pytest style (`test_30`–`test_34`), plus D9 (a)–(d).

## Expected result
No RTE number and no changed legacy output. The new core has no air parameter (BACKLOG
until manufacturer answer or L3 readout, D13).

## Write-Scope
- `src/verlustmappe/registry.py` (status of comp.*, new primary entries)
- `src/verlustmappe/reporting/make_register.py` (ORDER, "weakest number" text; D11 exception)
- `docs/02_uncertainty_register.md` (regenerated), `docs/01`, `docs/04`, `docs/93`,
  `docs/94` (notes only), (README note dropped: the demo block is generated, see HANDOFF)
- `SOURCES.md`, `DECISIONS.md`, `HANDOFF.md`
- `tests/`: new `test_30_workbook_integrity.py`, `test_31_hand_calcs.py`,
  `test_32_physics_bounds.py`, `test_33_registry_vs_workbook.py`,
  `test_34_comp_rejected_guard.py`, `xlsx_reader.py`, workbook fixture
- D9 owner commit: `pyproject.toml`, `.github/workflows/ci.yml`, `tests/run_all.py`
  (limited to test_01–12), `AGENTS.md` Commands
- P04: the D1-text part lapses (D11 supersedes D1); the ci_guard part stays (registry
  false alarm) and is NOT done here.

## Do not touch
`SPEC.md`, `ROADMAP.md`, `tools/ci_guard.py`, `devices/booster.py`, `balance/*`, other
frozen legacy, data CSVs, `stor.p_work_barg` (legacy 200 barg, used by d_loss_map).

## Work items and expected red tests
1. Baseline: `python3 tests/run_all.py`, `BASE_REF=origin/main python3 tools/ci_guard.py`.
   Result: green.
2. Site readout (owner, no code): SC2 load hours + kWh counter, stroke counters, EL
   production, same period. Send the Maximator question incl. continuous vs intermittent.
3. DECISIONS D11–D15, then SOURCES entries. Red: none.
4. Registry + `make_register.py` + regenerated docs/02, one commit. Dry run first:
   `make_register.py` runs, `run_all` ALL PASS, README check passes (needs numpy, ask).
   Red: none expected; any red is a defect.
5. Docs notes (REJECTED/superseded marker in the same line or up to 2 lines above an old
   value; DECISIONS, docs/93, docs/94 are history, exempt from the scan).
6. Tests commit (own commit, rule 4): suites + D9. `test_33` maps registry keys to
   workbook rows (`_barg` names); `test_34` asserts comp.* = REJECTED and no `comp.` read
   under `models/`, `sim/`, `scenarios/`, `calibration/` (weak text guard, adapter missing).
   Red after: none; ends with pytest -q and run_all both green.
7. Gates, HANDOFF.md, report (rule 9), push, `gh pr create`; owner merges.

## Known limits
Hand calculations come from one author; pins are drift detectors; no model-behaviour
tests yet; the text guard is not an adapter; any workbook edit changes its hash.