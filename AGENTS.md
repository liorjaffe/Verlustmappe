# Verlustmappe agent rules (binding)

This file applies to every AI agent working in this repository (Copilot, Codex, Claude Code).
Keep it short. Anything a tool can enforce is enforced in CI, not here.

## Commands
- Run all tests: `python3 tests/run_all.py` (must end with `ALL PASS`)
- Run one test: `python3 tests/test_XX_<name>.py`
- (After the pytest migration: `pytest -q`)

## Source of truth (one place per fact)
- Concept and acceptance criteria: `SPEC.md`
- Parameters, uncertainty, status: `src/verlustmappe/registry.py`
- External sources for every number: `SOURCES.md`
- Plant and design decisions: `DECISIONS.md`
- Why each rule exists: `RULES_LOG.md`
- Your current assignment: `tasks/Pxx_*.md` (read it first; do only that)

## Rules

1. **Unknown means ask.** If a value, limit, or requirement is missing, write `BACKLOG`
   and report it. Never insert a plausible number.
2. **Registry is protected.** Do not change any value, uncertainty, or status in
   `registry.py` without written approval from the owner. If a comment contradicts an
   entry, report it. Do not delete either one.
3. **Every external number needs a source entry** in `SOURCES.md`: page, table, a short
   verbatim quote, and a **transferability** line (source conditions such as pressure,
   drive type, load versus our plant: same or different). No entry means status `GUESS`.
4. **Tests must not be tautological.** Expected values must never be computed by the
   model under test. Use a hand calculation (`tests/reference/`) or a cited source.
   Change a test only in its own commit, with the reason in the commit message.
   Weakening an assertion, widening a tolerance, or adding skip/xfail is forbidden
   without approval.
5. **No plug terms.** Energy and mole balances must close without a residual term.
   Each loss is computed from its own physics, not as input minus output. An unexplained
   remainder is reported as "unexplained residual" with a warning, never booked as a bar.
6. **Stay in scope.** Edit only files listed in the task's Write-Scope. Direct technical
   dependencies (import fix, type fix) are allowed but must be listed in your report.
   Never touch protected paths through this exception: `registry.py`, `tests/`,
   `SOURCES.md`, `DECISIONS.md`, `AGENTS.md`, `.github/`.
7. **Units in names for physical quantities** that cross function or file boundaries
   (`pressure_barg`, `energy_kWh`, `flow_mol_s`, `power_W`, `time_s`). Indices and local
   helper variables are exempt. README numbers are generated, never typed by hand.
8. **No invented requirements.** Do not introduce limits, defaults, clamps, or operating
   assumptions (for example capping an efficiency at 92 %) unless they come from a source
   or are approved. Any `clip`, `min`, or `max` on a physical quantity needs a registry entry.
9. **Finish with evidence.** Every final report uses this format:
   - **Result:** what changed, in two or three lines
   - **Evidence:** command output captured after your last edit
   - **Risk:** what could still be wrong
   - **Assumptions:** everything you assumed, and anything you were unsure about

   After two failed attempts without new findings: stop and report. Do not weaken a test
   to get green.

## Status hierarchy (strongest to weakest)
`MEASURED` > `CALIBRATED` > `DATASHEET` > `DERIVED` > `PRELIM` / `ENVELOPE` > `GUESS` > `BACKLOG`

A result carries the weakest status of the inputs that drive it. A calculated value must
never look like a measured one.

## Protected paths (human approval required, enforced by CODEOWNERS)
`src/verlustmappe/registry.py`, `tests/`, `tests/reference/`, `SOURCES.md`, `DECISIONS.md`,
`AGENTS.md`, `CLAUDE.md`, `.github/`, `pyproject.toml`, `conftest.py`

## Session handoff
At the end of a session, update `HANDOFF.md`: done / blocked / decisions needed / next step.
Start the next session by reading `HANDOFF.md`, `SPEC.md`, and the task file.
