# Verlustmappe agent rules (binding)

This file applies to every AI agent working in this repository (Copilot, Codex, Claude Code).
Keep it short. Rules that a tool can enforce are enforced in CI where a check exists; what CI
does and does not enforce today is listed under Commands. Domain pitfalls and physics caveats
live in `docs/` and the SPEC; this file only points to them.

## Commands
- Run all tests: `python3 tests/run_all.py` (must end with `ALL PASS`)
- Run one test: `python3 tests/test_XX_<name>.py`
- Before finishing any task, run: `python3 tools/ci_guard.py` and
  `python3 tools/make_readme_demo.py --check`
  - Locally set `BASE_REF=origin/main`, otherwise ci_guard silently skips all diff-based
    guards (registry-to-SOURCES, test-file protection).
- `pytest -q` is mandatory; pytest-style tests start at test_30 (test_20-26 are reserved
  by the SPEC). `tests/run_all.py` runs only the legacy scripts test_01 to test_12 (D9).
- Known CI limits, stated honestly:
  - ci_guard does NOT detect weakened tolerances or removed assertions.
  - The legacy freeze is NOT machine-checked today: no guard rejects a change to a frozen
    file. Planned: a ci_guard check that compares frozen files against tag `legacy-1.0`.
  - The new-core import rule is NOT machine-checked today. Planned: a ci_guard check that
    allows exactly one legacy import, the adapter `src/verlustmappe/models/params.py`.
  - ci_guard fails whenever `registry.py` changes without a `tests/` change in the same
    diff, also for text-only edits, because it compares the file path, not the entries.
    Never add an unrelated test change to silence it. The planned fix is an owner-approved
    change to `tools/ci_guard.py` that compares parsed entries (value, uncertainty, status)
    instead of file text (see D1).
  - Rule 4 applies regardless; green CI means reproducible, not correct.

## Source of truth (one place per fact)
- What the system must do and when it is accepted: `SPEC.md`
- How work is done here: this file (`AGENTS.md`)
- Parameters, uncertainty, status: `src/verlustmappe/registry.py`
- External sources for every number: `SOURCES.md`
- Plant and design decisions: `DECISIONS.md`
- Current state: `HANDOFF.md`; acceptance evidence per criterion: `docs/04_validation_log.md`
- Milestones: `ROADMAP.md`; your assignment: `tasks/Pxx_*.md` (read it first; do only that)
- Known legacy defects: `docs/94_known_defects_legacy.md` (read before touching legacy code)
- Why each rule exists: `RULES_LOG.md` (merge candidate into this file; do not extend it)

## Rules

0. **Smallest change wins.** Every change must make the project simpler or carry a clearly
   documented benefit. Delete instead of add. A replaced file is deleted or archived, never
   kept as a second truth. A task without an AC or ROADMAP reference and a Write-Scope does
   not start.
1. **Unknown means ask.** If a value, limit, or requirement is missing, write `BACKLOG` and
   report it. Never insert a plausible number.
2. **Registry is protected.** Do not change any value, uncertainty, or status in
   `registry.py` without written approval from the owner. A registry value change always
   requires a DECISIONS.md entry. If a comment contradicts an entry, report it; a
   contradictory comment may be deleted only inside an approved task with a DECISIONS
   entry.
3. **Every external number needs a source entry** in `SOURCES.md`: page, table, a short
   verbatim quote, and a **transferability** line (source conditions such as pressure,
   drive type, load versus our plant: same or different). No entry means status `GUESS`.
   Never reuse a number from a review text or chat without recomputing it.
4. **Tests must not be tautological.** Expected values must never be computed by the model
   under test. Use a hand calculation (`tests/reference/hand/`) or a cited source. Change a
   test only in its own commit, with the reason in the commit message. Weakening an
   assertion, widening a tolerance, or adding skip/xfail is forbidden without approval.
   The legacy tests `test_01` to `test_12` are regression of the frozen state; they are
   NOT derived from the SPEC and must not be "fixed" to match the SPEC.
5. **No plug terms (new code).** Energy and mole balances must close without a residual
   term; each loss is computed from its own physics, not as input minus output. An
   unexplained remainder is reported as "unexplained residual" with a warning, never booked
   as a bar. Known legacy violations of this rule are listed in `docs/94` and are NOT fixed
   inside the frozen legacy; do not "repair" them.
6. **Stay in scope.** Edit only files listed in the task's Write-Scope. Direct technical
   dependencies (import fix, type fix) are allowed but must be listed in your report.
   Protected paths (see section below) are never covered by this exception.
7. **Units in names for physical quantities** that cross function or file boundaries
   (`pressure_barg`, `energy_kWh`, `flow_mol_s`, `power_W`, `time_s`). Indices and local
   helper variables are exempt. README numbers are generated, never typed by hand.
8. **No invented requirements (new code).** Do not introduce limits, defaults, clamps, or
   operating assumptions unless they come from a source or are approved. Any `clip`, `min`,
   or `max` on a physical quantity needs a registry entry AND must be reported in the
   output; silent clamping is a defect (see docs/94), never acceptable. Known legacy
   violations are listed in `docs/94` and are NOT fixed inside the frozen legacy.
9. **Finish with evidence.** Every final report uses this format:
   - **Result:** what changed, in two or three lines
   - **Files:** every file changed, with the reason
   - **Evidence:** commands run after your last edit, with output (at minimum the
     mandatory commands from Commands)
   - **Commit:** hash or diff reference of what you propose
   - **UNVERIFIED:** everything you could not reproduce or read in code, explicitly marked
   - **Risk / Assumptions:** what could still be wrong; everything you assumed

   Separate analysis from code changes: while a finding is unverified, do not edit code
   because of it. After two failed attempts without new findings: stop and report. Do not
   weaken a test to get green.

## SPEC primacy
- Tests for new code are derived from the SPEC; the SPEC defines intended behavior.
- On conflict between SPEC and test, or SPEC and code: stop and report. Tests and code are
  corrected per task with owner approval, never silently.
- The SPEC itself changes only via an entry in `DECISIONS.md`.

## Legacy freeze (D2)
- The files existing at tag `legacy-1.0` under `src/verlustmappe/` are frozen, EXCEPT
  `loaders/` (loader and data corrections are allowed if they change no physics parameter
  or limit, with the data state noted in the commit).
- Text-only edits (comments, docstrings, warning strings) inside the frozen scope are
  allowed only per approved task and change no behavior.
- The NEW core lives in `src/verlustmappe/models/`, `src/verlustmappe/sim/`,
  `src/verlustmappe/scenarios/` and `src/verlustmappe/calibration/`. It is not part of the
  freeze; the Write-Scope (rule 6) still applies.
- New-core modules must not import legacy modules, with ONE exception: the adapter
  `src/verlustmappe/models/params.py` may import `src/verlustmappe/registry.py` read-only.
  It copies the values into immutable per-run parameter objects and never writes back to
  the registry. This rule applies to core modules; tests may import legacy code.
- Ported physics (constants, z_realgas, temperature_model) exists twice until the legacy
  teardown in M6. A regression test under `tests/` compares the ported values against the
  legacy values; a mismatch is a defect, never a reason to edit the legacy file.
- Before any work on legacy topics, read `docs/94_known_defects_legacy.md`.

## Agents and calibration
- Calibration code lives in `src/verlustmappe/calibration/`; calibration data lives at the
  repository root: drafts in `calibration/drafts/`, approved overlays in
  `calibration/overlays/`.
- Agents deliver fit proposals and overlay drafts only, into `calibration/drafts/`.
  Approved overlays and registry values are written by the owner, never by an agent.
- Fit and hold-out windows stay separate. SMA legacy telemetry is never F8 evidence.
- Tests must reset any global state they change (try/finally). Agents never write random
  draws or run-local parameters into the global registry; parameter sets are materialized
  per run and immutable (model details: SPEC).

## Branches and review
- Agents work on a branch, never push directly to `main`, never merge their own PR. The
  owner integrates and merges.

## Status vocabulary (decision pending in DECISIONS.md)
- Evidence status: `MEASURED > CALIBRATED > DATASHEET > DERIVED > PRELIM/ENVELOPE > GUESS >
  BACKLOG`.
- `NAMEPLATE` is not an evidence status; a nameplate value is a `DATASHEET` value.
- `NOT OBSERVED` is an observation flag, not an evidence status; do not mix it into the
  same column until D5 is decided.
- A result carries the weakest status of the inputs that drive it. A calculated value must
  never look like a measured one.

## Protected paths (human approval required)

`src/verlustmappe/registry.py`, `SPEC.md`, `ROADMAP.md`, `tests/` (including
`tests/reference/`), `SOURCES.md`, `DECISIONS.md`, `AGENTS.md`, `CLAUDE.md`, `.github/`,
`pyproject.toml`, `conftest.py`, `tools/ci_guard.py`, `calibration/overlays/`
(this section is the single list; rule 6 refers to it; `.github/CODEOWNERS` must match it)

## Session handoff
At the end of a session, update `HANDOFF.md`: done / blocked / decisions needed / next step.
Start the next session by reading `HANDOFF.md`, `SPEC.md`, and the task file.
