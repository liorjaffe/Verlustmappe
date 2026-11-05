# AGENTS – entry point for every AI agent (loaded automatically)

This repository is the project's only memory. What is not written here does not apply.
All repository content is in English; conversation with the owner may be in German.

## Workflow
1. Read `START.md` (state, next step, open questions).
2. Place the question in the map below; read only the file named there.
3. Work only within the task's scope, on a branch; never merge into `main` yourself.
4. Record agreements with the owner **in the same session** in `CONTRACT.md` (rewrite,
   do not append); the reason goes to `decisions/`.
5. Overwrite `START.md` at the end (at most 60 lines).
6. Run the gates and report exit codes.

## Map: question → file
| Question | File |
|---|---|
| Where are we, what is next? | `START.md` |
| What applies (goal, scope, accounts, balance, status)? | `CONTRACT.md` |
| Why was something decided? | `decisions/` (only if needed) |
| Which value, which source, what is open? | `plant/<device>.toml` (read via `src/verlustmappe/registry.py`) |
| How does device X compute? | `src/verlustmappe/devices/<device>.py` (docstring explains physics and assumptions) |
| Hydrogen amounts, real gas, temperature? | `src/verlustmappe/hydrogen/` |
| Constants, unit conversions, time integration? | `src/verlustmappe/physics/` |
| Status, validity, item list, static case (P14)? | `src/verlustmappe/accounting/` |
| Is it proven? | `tests/test_<package>_<topic>.py` (e.g. `test_devices_water.py`); hand values in `tests/reference/hand/` |
| How are measurement files read? | `src/verlustmappe/loaders/` and `loaders/FORMATS.md` |
| Device knowledge from the legacy state (only when porting) | `git show archive-2026-11:<path>` |

**Stop rule:** If the answer is not settled after the map, ask or mark it UNVERIFIED; do
not keep searching. Debugging may follow the call path; justify any deviation from the map
in the report.

## Rules
1. Never invent a number. A missing value is MISSING; ask.
2. Only the owner changes values and expected test values; the agent submits a proposal.
3. Never compute expected test values with the model under test; the derivation is in the
   test.
4. No loss as a difference "input minus output".
5. Physical quantities crossing function or file boundaries carry their unit in the name
   (`power_W`, `energy_kWh`, `time_s`).
6. No limiting of physical quantities without a source and a visible note.
7. A new file only if another one is removed or merged. A device model is replaced only
   when the new one gives the same numbers in a test or the difference is justified; until
   then the old one stays.
8. Reviews: at most one round per draft. Classify findings as blocker, result impact or
   maintenance; only the first two are acted on.

## Gates (from `.venv`)
`.venv/bin/python tests/run_all.py` · `.venv/bin/python -m pytest -q` · `git diff --check`
(all together: `tools/run_local_gates.py`)

## Report
Result (2–3 lines) · files with reason · evidence (commands and exit codes) · commit ·
UNVERIFIED and assumptions.
