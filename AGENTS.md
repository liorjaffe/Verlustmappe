# AGENTS – entry point for every AI agent (loaded automatically)

This repository is the project's only memory. What is not written here does not apply.
All repository content is in English; conversation with the owner may be in German.

## Workflow
1. Read `START.md` (state, next step, open questions).
2. Start with the map below; follow the relevant data, code and tests as needed.
3. Work only within the task's scope, on a branch; never merge into `main` yourself.
4. Record agreements with the owner **in the same session** in `CONTRACT.md` (rewrite,
   do not append); the reason goes to `decisions/`.
5. Update `START.md` (at most 60 lines) when work changes the project, records a decision,
   changes an open issue, or leaves work unfinished or blocked for a later session.
   Pure lookups and completed read-only answers do not require an update.
6. Run the gates and report exit codes.

## Map: question → starting point
| Question | Starting point |
|---|---|
| Where are we, what is next? | `START.md` |
| What applies (goal, scope, accounts, balance, status)? | `CONTRACT.md` |
| Why was something decided? | `decisions/` (only if needed) |
| Which plant values and gaps apply? | `plant/`; models may read them via `src/verlustmappe/registry.py` |
| Where is the supporting source? | Source reference in `plant/`; documents and compilations in `plant/sources/` |
| How does a device compute? | `src/verlustmappe/devices/`, then its actual inputs and dependencies |
| Hydrogen amounts, real gas, temperature? | `src/verlustmappe/hydrogen/` |
| Constants, unit conversions, time integration? | `src/verlustmappe/physics/` |
| Where are case inputs and results? | P14: `src/verlustmappe/accounting/static_map.py` and `ledger.py`; full case report is not built |
| What is checked? | Relevant `tests/`; independent hand references in `tests/reference/hand/` |
| How do measurement data enter? | `data/`, `src/verlustmappe/loaders/FORMATS.md`, `src/verlustmappe/loaders/`; tools in `tools/` |
| Device knowledge from the legacy state (only when porting) | `git show archive-2026-11:<path>` |

The map is a starting point, not a reading limit. Search narrowly and follow the actual
call path; report unresolved conflicts and significant search deviations. Use source
documents when inputs are missing, disputed or need verification, not for routine lookup.
TOML is the intended plant-parameter source, but code can use other values: report what a
calculation actually uses. Tests show what is checked, not physical validation by themselves.

## Rules
1. Never invent a number. A missing value is MISSING; ask.
2. The owner may explicitly authorize the agent to transfer values from named sources.
   Missing information remains open; origin, unit and status must be traceable. Without
   authorization, the agent submits a proposal. Only the owner changes expected test values.
3. Never compute expected test values with the model under test; the derivation is in the
   test.
4. No loss as a difference "input minus output".
5. Physical quantities crossing function or file boundaries carry their unit in the name
   (`power_W`, `energy_kWh`, `time_s`).
6. No limiting of physical quantities without a source and a visible note.
7. Add a file when it has a clear purpose and no suitable existing file is a better home.
   Name and justify it in the report; task scope and protected-path approvals still apply.
   A device model is replaced only when the new one gives the same numbers in a test or the
   difference is justified; until then the old one stays.
8. Reviews: at most one round per draft. Classify findings as blocker, result impact or
   maintenance; only the first two are acted on.

## Gates (from `.venv`)
`.venv/bin/python tests/run_all.py` · `.venv/bin/python -m pytest -q` · `git diff --check`
(all together: `tools/run_local_gates.py`)

## Report
Result (2–3 lines) · files with reason · evidence (commands and exit codes) · commit ·
UNVERIFIED and assumptions.
