# P02b - Evidence attribution in docs/01-04 and C13/C14 corrections

**Status:** Open
**Reference:** ROADMAP.md, M0; docs/94_known_defects_legacy.md, C13 and the
new C14.
**Preconditions:** D2 (text-only changes in docs are outside the frozen code),
D4 (first calibrated device; the Solis F8 channel is the F8 evidence path),
SPEC system boundary (the removed SMA array is never F8 evidence).

## Goal

No document may attribute a measurement of the removed legacy SMA array
(~184 kWp) to the F8 storage chain or its Solis inverters, and C13/C14 must
describe the actual state accurately.

## Write-Scope

- `docs/01_methods_handbook.md` (attribution wording only; no formulas)
- `docs/02_uncertainty_register.md` (source wording only; no values, no
  statuses, no uncertainty columns)
- `docs/03_data_dictionary.md` (PV section header and wording only)
- `docs/04_validation_log.md` (attribution wording only)
- `docs/94_known_defects_legacy.md` (C13 file-list correction, C14 append,
  AC8 table row for C14)
- `README.md` (only the legacy note paragraph above the BEGIN marker)
- `HANDOFF.md`, `tasks/P02b_docs_evidence_attribution.md`

## Do not touch

- Any number, status or uncertainty value in docs/01-04.
- Anything between the README GENERATED DEMO TABLE markers.
- `src/`, `tests/`, `tools/`, `SOURCES.md`.
- SPEC.md, AGENTS.md, DECISIONS.md, ROADMAP.md.

## Work items

1. `docs/01_methods_handbook.md`:
   - Line 207 area: "measured on our own SMA telemetry at 0.9719" must state
     that the 0.9719 cross-check comes from the removed legacy building array
     (~184 kWp, 22 days, Sept 2026) and is NOT evidence for the F8 Solis
     inverter; the F8 cross-check path is the Solis data (`f8_day_balance`,
     `loaders/solis_live.py`).
   - Line 232: same attribution for the `test_08b` comparison.
   - Line 118: replace "until the SMA discharge inverter is metered" with the
     F8 wording (until the Solis F8 discharge inverter channel is metered).
2. `docs/02_uncertainty_register.md`:
   - Line 18 (`meas.power_rel_unc`): the source note "Enapter/SMA telemetry"
     must say Enapter telemetry (legacy building array); it is not F8
     evidence.
   - Line 33 (`inv_pv.eta_euro`): already correct (it says the 0.9719 belongs
     to the ALT building array); no value changes, leave as is.
3. `docs/03_data_dictionary.md` line 37: heading "PV (SMA Sunny Tripower
   CORE2 via SunSpec/Enapter blueprint)" must be relabeled as the legacy
   building array mapping, kept for reference, explicitly outside the F8
   boundary.
4. `docs/04_validation_log.md` lines 115/120: statements that Euro-eta 0.98 is
   "consistent with the measured hardware" must be attributed correctly: the
   measured hardware behind the cross-check is the legacy array, so the
   statement may only support the generic string-inverter assumption, not the
   F8 inverter. Reword accordingly without changing any validation status.
5. `docs/94_known_defects_legacy.md`:
   - C13 file list correction: remove `loaders/grafana.py` (no hit), add
     `loaders/solis_live.py`, `devices/__init__.py`, `devices/pv_prelim_channel.py`;
     add "docs/01-04 evidence-attribution statements (fixed in P02b)".
   - Append defect C14 after C13, same format:
     "- **C14 - No range/sign guard on model inputs.** [read] Device models
     accept out-of-range or wrongly signed inputs without a guard; a
     `plausible` check either does not exist or does not constrain anything.
     Impact: silent nonsense results possible in the legacy chain. Fix: the
     new core validates input ranges and signs at the model boundary (M1/M2
     tests); legacy is not modified. AC8 treatment: none."
   - Add the AC8 table row for C14: "| C14 range/sign guard | none: new-core
     concern; legacy unmodified |".
6. `README.md` legacy note above the BEGIN marker: remove the C13 mention
   (C13 is wording in documents, not a defect of the demo table or plots);
   keep the C3 mention.
7. HANDOFF.md: P02b done with commit hash; sequence note: P03 next, then P04
   (which keeps only src/ SMA text, ci_guard, SOURCES).

## Working rules for this task

- Before editing, list failure modes (e.g. drifting into value changes in
  docs/02, deleting information that docs/06 needs, breaking the demo check,
  rewording formula sections in docs/01).
- Attribution wording only; every number stays byte-identical.

## Acceptance

- `python3 tests/run_all.py` ALL PASS; `python3 tools/ci_guard.py` ok;
  `python3 tools/make_readme_demo.py --check` passes.
- `grep -n 'SMA telemetry' docs/01_methods_handbook.md` returns no line that
  attributes the cross-check to F8 or to the storage chain.
- `grep -c 'C14' docs/94_known_defects_legacy.md` >= 2.
- `grep -c 'C13' README.md` returns 0.
- Every remaining SMA mention in docs/01-04 is explicitly attributed to the
  removed legacy array or is a cross-check statement with the legacy-array
  attribution.

## Completion evidence

Commit hash, command outputs, and the residual-SMA list, reported in the
AGENTS.md format with UNVERIFIED items listed.

git add tasks/P02b_docs_evidence_attribution.md
git commit -m "tasks: P02b evidence attribution in docs/01-04, C13 file-list correction, C14 guard defect"
git push

