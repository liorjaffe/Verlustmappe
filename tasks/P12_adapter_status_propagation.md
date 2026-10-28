# P12 - status ranking, u class and weakest-wins in the new core (DRAFT)

**Status:** Code written (commit 1); test_37 awaits owner approval (commit 2, own commit, rule 4). Draft: session folder `files/draft_tests/test_37_status_propagation.py`, 9 tests pass.
**Reference:** ROADMAP M1 ("evidence status per bar"), D26 (b)/(c), D28 (adapter propagates
status, weakest-wins), SPEC AC1/AC7, AGENTS Legacy freeze.
**Patch base:** `main` after PR #12.

## Goal
Give the new core the evidence status and u class of a parameter and the weakest-wins
combination, so a later ledger bar can state its weakest input and whether it includes
UNCERTAINTY_NOT_ASSESSED. Bookkeeping only: no ledger, no physics, no `ParamSet` (rule 0:
it gets a consumer only with P14).

## M1 decomposition (replaces the ROADMAP shorthand "P12 ledger and gates")
- **P12:** status ranking, `u_class`, `weakest` (this task).
- **P13:** integration function (D24) with hand references in `tests/reference/hand/`
  (constant, ramp, gap, non-monotonic) and the validity gates (D25/D31) as pure predicates
  only (raw values in, validity verdict out). Anything that needs a run or a result object
  (INVALID of a bar or run) belongs to P14, so P13 gets neither an empty wrapper layer nor a
  second implementation of the gates.
- **P14:** ledger items (D23) and balances, `ParamSet` (first consumer), `test_20_static_map.py`
  (AC1) grows here. Items needing only electrical data, Faraday and fill work first; every
  real-gas item (tank, compression with Z) waits for the Z-source clarification (C25, then
  `z_realgas` port, tank-pVT reference). Compression-air items (D14 stage 2) are booked as
  BACKLOG and not computed until the Kaeser measurement exists (E3); no plausible number.
- **P15:** netting and RTE (D20-D22, D31). D22 is DECIDED (control energy drawn on the DC
  bus before the inverter); its open measurement-point confirmation is carried as a
  documented assumption in the result, not as a blocker.
- **P16:** fault injection (AC5, `test_24`), explicit production route.
- Hand references (Faraday, integration, nameplate, tank-pVT) are written in the task that
  introduces the function; each such task lists `tests/reference/hand/` in its Write-Scope
  (protected path, approval per file). AC tests stay test_20-26 per the SPEC allocation;
  unit tests continue with test_37 and up; P13 does not take test_20.

## Write-Scope (P12)
Commit 1: `src/verlustmappe/models/status.py` (new), `src/verlustmappe/models/params.py`
(`Param` gets `u_class`), `HANDOFF.md`, this file.
Commit 2: `tests/test_37_status_propagation.py` (new file, protected path, own commit, rule 4).

## Do not touch
Legacy modules (incl. `reporting/make_register.py`), `registry.py`, existing tests,
`tools/ci_guard.py`, `SPEC.md`, `DECISIONS.md`.

## Design
1. **Ranking** (D26 evidence_status, strongest first): MEASURED > CALIBRATED > DATASHEET >
   DATASHEET_SECONDARY > DERIVED > PRELIM/ENVELOPE > GUESS > BACKLOG. Weakest-wins applies
   within evidence_status only.
2. **`u_class(key, entry)`**: the D26(b) rule: exact for OWNER_DECISION and the two
   TOLERANCE_BAND keys, assessed for u > 0, otherwise NOT ASSESSED. The new core must not
   import `reporting/`, so the rule exists twice until M6; parity is pinned by a test against
   `make_register.u_class` (tests may import legacy).
3. **`weakest(statuses)`**: returns the weakest evidence status of a list.
4. `get_param` stays the only registry reader; blocked statuses as before (D28).

## Owner decisions (2026-10-28)
1. OWNER_DECISION is skipped by `weakest` (D26: weakest-wins within evidence_status only; it is
   a registry source status). If no evidence status remains (empty list or only OWNER_DECISION),
   `weakest` raises ValueError referencing D26: no default; a purely owner-based result is
   classified by a DECISIONS entry, not by code. In the u class it stays `exact` (D26(b)(i)).
2. The u-class rule is copied into `models/status.py`, parity with `make_register.u_class` is
   pinned in test_37. Consolidation to one implementation is a candidate for the M6 teardown.
3. Unknown status strings raise ValueError (value named, pointer to DECISIONS) in `weakest` and
   `u_class`. REJECTED/SUPERSEDED reaching `weakest` is a program error (the adapter blocks
   them) and raises the same way. `u_class` is total over the registry incl. REJECTED/SUPERSEDED
   (D26(c) classifies all numeric entries; the register column does too), so it is one truth
   for register and core. Correction by the owner: the block belongs to `weakest`/adapter.

## Notes
- The registry spells the sixth evidence level "PRELIM"; D26 writes "PRELIM/ENVELOPE". The code
  ranks "PRELIM" and accepts "PRELIM/ENVELOPE" as an alias (no registry change). A bare
  "ENVELOPE" is not accepted and raises ValueError; if it ever appears, a DECISIONS entry
  decides, not the code.
- `Param.u_class` is computed in `get_param`; blocked entries still raise before.

## Tests (draft, expected values from the D26 text, not from the model)
Ranking order pinned; weakest of mixed lists (DATASHEET + GUESS gives GUESS, with BACKLOG gives
BACKLOG); u class on the four exact entries and one u > 0 entry (both directions, as test_35);
parity with the register column over all entries (46 / 4 / 59 of 109); unknown status raises;
empty list raises; the registry is unchanged afterwards.

## Acceptance
`run_all`, `pytest -q`, `BASE_REF=origin/main ci_guard`, `make_readme_demo --check` green after
the last edit; final report in the rule 9 format.
