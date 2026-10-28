# P02b - Evidence attribution in docs/01-04, README legacy note, generator text (D19)

**Status:** Open
**Reference:** ROADMAP.md M0; docs/94 C13; DECISIONS D4, D11, D17, D19.
**Patch base:** `main` after PR #3 (`ff63504`). This file replaces the earlier P02b text;
items already done by P04/P05 were removed (docs/02 SMA wording, C13 file list in docs/94).
**Out of scope (own task after P02b):** docs/94 C14-C29 (text provided by the owner).

## Goal
No document attributes a measurement of the removed legacy building array (~184 kWp,
22 days) to the F8 storage chain; superseded compression numbers are marked as superseded;
the generator text carries the API-verified station id. Text only; every number, status
and uncertainty stays byte-identical.

## Write-Scope
- `docs/01_methods_handbook.md`, `docs/03_data_dictionary.md`, `docs/04_validation_log.md`
  (attribution/marker wording only)
- `README.md` (legacy note above the BEGIN marker; FAQ line "weakest number" only after
  the owner decision below)
- `src/verlustmappe/reporting/make_register.py` (weakest-numbers items 4 and 4b only, D19)
  and `docs/02_uncertainty_register.md` (regenerated, no hand edit)
- `HANDOFF.md`, `docs/94_known_defects_legacy.md` (only C13 status "docs fixed in P02b")
- this file

## Do not touch
Values/statuses in docs/01-04, anything between the README GENERATED markers, `tests/`,
`tools/`, `SOURCES.md`, `SPEC.md`, `AGENTS.md`, `ROADMAP.md`, `DECISIONS.md` (D19 exists),
registry, other `src/` files, docs/94 C14-C29.

## Work items
1. docs/01:
   - line ~119 "until the SMA discharge inverter is metered" -> Solis F8 discharge inverter
     channel (F8 wording).
   - lines ~208-209 and ~233: the 0.9719 value and the `test_08b` comparison come from the
     removed legacy building array, not F8 evidence (D4).
   - line ~100: after "GUESS 0.014 +-30 %" add "(superseded, see status note)"; the status
     note below it stays.
   - line ~261 already attributes the legacy array correctly; leave.
2. docs/03 line 37: heading relabelled "legacy building array mapping (kept for reference,
   outside the F8 boundary)"; table untouched.
3. docs/04:
   - lines ~115-120: "against our own SMA telemetry" -> legacy building array; the
     statement supports only the generic string-inverter assumption, not the F8 inverter.
   - line ~89 (0.10 -> 0.04 history) and ~159 (registry 0.014): marker "superseded by D11;
     comp.* REJECTED"; no value changed, no status changed.
4. README: remove the C13 mention in the legacy note (keep C3). FAQ "weakest number" answer
   (line ~293-296, outside the generated block) replaced by the owner-approved text:
   "Today: the compression energy. Its registered estimate is REJECTED (D11: wrong device
   basis, Maximator DLE 30-2); it is replaced by the air-chain model (D13/D14) and the
   planned Kaeser metering. The demo RTE below is a frozen legacy result that still uses
   that rejected value. The full ranking is in docs/02 ("five weakest numbers"); the tank
   volume is a DATASHEET value (hydrostatic check open, not a placeholder)."
   Check it against the regenerated docs/02 list before committing; the list wins.
   Labelling the demo summary line as open-cycle is NOT done here: it sits in the generated
   block (README numbers are generated, rule 7); needs its own approved change.
5. `make_register.py`: item 4 text as in D19; item 4b station id `1298491919449567877`
   (verified against `loaders/solis_live.py`, `tests/test_10_pv_f8.py`, docs/03); regenerate
   docs/02, review the diff (only these two lines may change).
6. docs/94: C13 gets "docs/01-04 attribution fixed in P02b".
7. HANDOFF: P02b done with commit hash; next: Z-value check, C14-C29 task, gates.

## Failure modes to avoid
Drifting into value changes; touching generated README block; hand-editing docs/02; deleting
information docs/06 needs; reformatting formula sections.

## Acceptance
- `.venv/bin/python tests/run_all.py` ALL PASS; `pytest -q` passes;
  `BASE_REF=origin/main .venv/bin/python tools/ci_guard.py` ok;
  `.venv/bin/python tools/make_readme_demo.py --check` ok.
- `git diff` of docs/01, 03, 04: no digit sequence changes except the intended wording.
- `grep -rn "568000" docs src` returns nothing.
- Every remaining SMA mention in docs/01-04 is attributed to the removed legacy array.
- Residual-SMA list in the report (AGENTS rule 9 format, UNVERIFIED listed).
