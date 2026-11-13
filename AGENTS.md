# AGENTS – entry point for every AI agent (loaded automatically)

Durable repository rules live here; the current owner task defines work scope. Repository
content is in English; conversation with the owner may be in German.

## Workflow
1. Read `START.md`; use the map below to follow relevant data, code and tests.
2. Work only within the task scope, on a branch; never merge into `main`.
3. Record owner decisions in-session: rule in `CONTRACT.md` (rewrite only the agreed change),
   rationale in `decisions/`; review the diff against the prior version.
4. Update `START.md` (max 60 lines) when state/decisions/open issues change or work is blocked
   or incomplete. Read-only answers need no update.
5. Code/data: run gates and report exit codes. Read-only: no gates; say "no changes; tests not run".
   Fix task-caused red gates and rerun; report known/unrelated failures. Never weaken tests to
   get green or claim a red gate passed.

## Map: question → starting point
| Question | Starting point |
|---|---|
| Where are we, what is next? | `START.md` |
| What applies (goal, scope, accounts, balance, status)? | `CONTRACT.md` |
| Why was something decided? | `decisions/` |
| Plant values/gaps and supporting evidence? | `plant/`; sources in `plant/sources/` |
| How does a device compute? | `src/verlustmappe/devices/`, inputs and dependencies |
| Hydrogen, real gas, temperature? | `src/verlustmappe/hydrogen/` |
| Constants, conversions, time integration? | `src/verlustmappe/physics/` |
| Case inputs/results? | P14: `src/verlustmappe/accounting/static_map.py`, `ledger.py`; full report not built |
| What is checked? | Relevant `tests/`; hand references in `tests/reference/hand/` |
| Measurement data? | `data/`, `src/verlustmappe/loaders/FORMATS.md`, `src/verlustmappe/loaders/`; tools in `tools/` |
| Legacy device knowledge (porting only)? | `git show archive-2026-11:<path>` or `git show legacy-1.0:<path>` |

Follow the actual data path; report unresolved conflicts and significant search deviations.
`plant/*.toml` is runtime parameter truth; code may use other values, so report the actual
value and impact—never reconcile silently. XLSX/documents are reviewable evidence/input.
Check them when values are missing, disputed or need verification. Tests show checked behavior,
not physical truth.

## Decision order
Task defines scope; explicit owner approval covers only what it names. `CONTRACT.md` and owner
decisions define intended behavior (parameter truth/evidence: rule 2). On conflict, pause the
affected change, show evidence/impact and ask; continue independent authorized work if possible.

## Rules
1. Never invent numbers, claims, sources or explanations. Missing information stays open; ask.
   State verified facts, conclusions and assumptions distinctly. Proposals are not facts or
   unverified bases for code/values.
2. TOML is current plant/runtime truth; XLSX/documents are reviewable evidence/input, not
   immutable truth. Source authorization covers only named values or parameter groups.
   Trace origin, unit and status; flag transfer errors or physical implausibility for the owner.
3. Never derive expected values from the model under test; put independent derivations in tests.
   New tests with independently derived expectations are allowed within task scope. Only the
   owner may change existing expected test values.
4. Never book a loss as `input - output`. Residuals may be diagnostics, never booked losses
   (`CONTRACT.md` §6).
5. Physical quantities crossing function/file boundaries carry units in names (`power_W`,
   `energy_kWh`, `time_s`).
6. Nothing is frozen by history. Historical tags are read-only references; what a change requires
   follows from the task and the decision order above.
7. Ask before changes to values, formulas, assumptions, data meaning, existing expected results
   or acceptance unless explicitly authorized. Replace a device model only with matching
   comparison tests or a justified difference.
8. Physical limits/clamps need a source and a note in the result/report; code comments alone are
   not visible.
9. Classify review findings: blocker = correct execution/acceptance cannot proceed;
   result impact = result, meaning or acceptance changes; maintenance = neither. If unsure, ask.
   Act on blocker/result-impact findings only after approval; report, don't fix, out-of-scope
   findings. Maintenance is allowed only within scope.
10. Try to disprove results with independent derivations, counterexamples and edge cases. Reruns
   check reproducibility/randomness/flakiness, not logic alone. For plant values check units,
   provenance, transfer and plausibility; report checks and mark unverified items `UNVERIFIED`.
11. Add files only for a clear purpose when no existing file is a better home; name and justify
    each in the report. Disclose changed tracked/new retained files, side effects and out-of-scope
    or indirect changes. Omit temporary caches/logs unless retained or relevant.
## Gates (from `.venv`)
`.venv/bin/python tests/run_all.py` · `.venv/bin/python -m pytest -q` · `git diff --check` (all via `tools/run_local_gates.py --log-dir <external-path>`)

## Report
Result (2–3 lines) · files changed/added with reasons · evidence/gates/self-check · new expected
test values · out-of-scope findings/side effects · commit (or none) · facts/conclusions/assumptions
· `UNVERIFIED`. Read-only: "no changes; tests not run".
