# AGENTS – entry point for every AI agent (loaded automatically)

Durable rules live here; the owner task defines scope. Repository content is in English;
conversation may be in German.

**Read-only tasks** change no tracked or new retained files. Do not run gates unless required
by applicable instructions or explicitly requested; report checks actually run, or
"no changes; tests not run".

## Workflow
1. Read `START.md`; use the map below to follow relevant data, code and tests.
2. Work only within the task scope, on a branch; never merge into `main`. Commit on the task
   branch only when requested.
3. Record owner decisions in-session: rule in `CONTRACT.md` (rewrite only the agreed change),
   rationale in `decisions/`; review the diff against the prior version. New decision files:
   `YYYY-MM-DD-<kebab-topic>.md`, one topic per file; do not rename existing files.
4. Update `START.md` (max 60 lines) when state/decisions/open issues change or work is blocked
   or incomplete. Read-only answers need no update.

   Parallel work must be named by the task, which requests a commit and specifies a durable
   handoff accessible to integration; otherwise assume single-agent work. If a parallel task
   lacks a commit request or handoff location, ask. Parallel agents put state changes and the
   commit reference in that handoff, not `START.md`; the owner or integration agent rewrites
   `START.md` from the combined state.
5. Run applicable gates and report exit codes. Fix task-caused red gates and rerun; report
   known/unrelated failures. A red gate remains red. Completion is allowed only if every
   failure matches a `START.md` entry (ID and relevant details) and all other checks pass.
   Report non-matching failures as new. Report newly passing listed tests and remove them at
   the next `START.md` update. Never weaken tests.

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
| Case inputs/results? | See P14 below; full report not built |
| What is checked? | Relevant `tests/`; hand references in `tests/reference/hand/` |
| Measurement data? | See data and loaders below |
| Legacy device knowledge (porting only)? | See historical tags below |

P14: `src/verlustmappe/accounting/static_map.py`, `ledger.py`. Measurement data: `data/`;
raw exports and manifests: `data/raw/README.md`; `src/verlustmappe/loaders/FORMATS.md`,
`src/verlustmappe/loaders/`; tools in `tools/`. For legacy device knowledge (porting only):
`git show archive-2026-11:<path>` or `git show legacy-1.0:<path>`.

Follow the actual data path; report unresolved conflicts and searches that failed to find evidence
or required a different path where this affects a conclusion. When relevant, distinguish evidence
not found, found but not applicable, and contradicting an assumption. Check XLSX/documents when
values are missing, disputed or need verification. Tests show checked behavior, not physical truth.

## Decision order
Task defines scope; explicit owner approval covers only what it names. `CONTRACT.md` and owner
decisions define intended behavior (parameter truth/evidence: rule 2). On conflict, pause the
affected change, show evidence/impact and ask; continue independent authorized work if possible.
`START.md` records state; on conflict, `CONTRACT.md` and owner decisions prevail. Report
contradictions and their impact; classify under rule 9 and pause affected work when necessary.

## Rules
1. Never invent numbers, claims, sources or explanations. Missing information stays open; ask.
   State verified facts, conclusions and assumptions distinctly. Proposals are not facts or
   unverified bases for code/values.
2. TOML is current plant/runtime truth; XLSX/documents are reviewable evidence/input, not
   immutable truth. Source authorization covers only named values or parameter groups.
   Trace origin, unit and status; flag transfer errors or physical implausibility for the owner.
   If code differs from TOML, report the actual value and impact; never reconcile silently.
   For approved changes to `tests/reference/plant_parameter_reference.json`, report added,
   removed and changed keys and count delta, reviewed against approval; regeneration does not
   replace content review.
3. Never derive expected values from the model under test; put independent derivations in tests.
   New tests with independently derived expectations are allowed within task scope. Only the
   owner may change existing expected test values.
4. Never book a loss as `input - output`. Residuals may be diagnostics, never booked losses
   (`CONTRACT.md` §6).
5. Physical quantities crossing function/file boundaries carry units in names (`power_W`,
   `energy_kWh`, `time_s`).
6. Historical tags are read-only references; existence in a tag alone does not freeze a file.
   Follow the task scope and decision order above.
7. Ask before changes to values, formulas, assumptions, data meaning, existing expected results
   or acceptance unless explicitly authorized. Replace a device model only with matching
   comparison tests or a justified difference.
8. Physical limits/clamps need a source and a note in the result/report; code comments alone are
   not visible.
9. Classify review findings: blocker = correct execution/acceptance cannot proceed;
   result impact = result, meaning or acceptance changes; maintenance = neither. If unsure, ask.
   Act on blocker/result-impact findings only after approval; report, don't fix, out-of-scope
   findings. Maintenance is allowed only within scope.
10. Try to disprove results using independent derivations, counterexamples or edge cases chosen
    for the change and its risk; name the checks in the report. Reruns check reproducibility,
    randomness or flakiness, not logic alone. For plant values check units, provenance, transfer
    and plausibility; mark unverified items `UNVERIFIED`.
11. Add a file only for a specific purpose that an existing file cannot appropriately serve.
    For each new file, state in the report its purpose and why no existing file fits. Disclose
    changed tracked/new retained files, side effects and out-of-scope or indirect changes.
    Omit temporary caches/logs unless retained or relevant.
12. Changing `AGENTS.md`, `CONTRACT.md`, `tests/test_structure.py`, or gate/CI configuration
    requires explicit owner approval for the exact change: a task, an owner instruction in
    this session, or an owner decision recorded before the task started. Do not ask twice.
    If the change is not explicitly approved, report and ask before editing.

## Gates (from `.venv`)
During code/data work, run focused tests as appropriate. For changes to code, data (including
`plant/`), tests or gate configuration, run the full wrapper before completion:
`.venv/bin/python tools/run_local_gates.py --log-dir <external-path>` (outside the repository).
It runs `tests/run_all.py`, pytest, and both unstaged and staged diff checks.
For changes to `AGENTS.md` or `START.md`, run both diff checks and
`.venv/bin/python -m pytest -q tests/test_structure.py`. If the known-failures list in
`START.md` changes, also run the full wrapper and verify the list against its output.
For other documentation-only changes, including `CONTRACT.md`, run both diff checks.
Report checks performed and environment deviations; do not silently install, upgrade or patch
dependencies. Never report an unrun check as passed.

## Report
- Result (2–3 lines)
- Files changed/added with reasons
- Evidence/gates/self-check
- New or changed expected test values
- Out-of-scope findings/side effects
- Commit (or none), branch, HEAD hash and whether the worktree is clean
- Facts/conclusions/assumptions
- `UNVERIFIED`
