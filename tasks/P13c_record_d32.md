# P13c - Record D32 source sampling interval qualification

**Status:** Complete; pending owner review. Not committed or pushed.
**References:** ROADMAP M1; D24; P13b; docs/03 nominal sampling interval table.
**Approval:** Owner coordination chat, 2026-10-29: exact D32 text, task creation,
DECISIONS and HANDOFF edits, and verification approved. No commit or push authorized.
**Base:** `601a42b`, one local HANDOFF-only commit after `origin/main` at `271310e`.
**Branch:** `docs/p13c-record-d32`.

## Goal

Record the exact owner-supplied D32 wording below. Resolve the missing decision
record without reconstructing or backdating a historical approval.

## Write-Scope

- `tasks/P13c_record_d32.md`: approved task, exact text, outcome and evidence.
- `DECISIONS.md`: insert D32 between D31 and D33; preserve all existing entries.
- `HANDOFF.md`: append a separate D32 outcome and remaining next steps.

## Read-only consistency checks

- `docs/03_data_dictionary.md`
- `tasks/P13b_nominal_cadence_docs.md`

Check D32/D32(a) references, F8 nominal basis, evidence requirements and timestamp
policy. If either file needs correction, stop and request a scope extension.

## Out of scope

D34/D35, SPEC, AGENTS, registry, code, tests, raw data, numerical-value changes,
new cadence analysis, historical approval reconstruction, unrelated documentation
cleanup, commits and pushes.

## First execution step: report HANDOFF differences before editing

Reported to the owner before any file edit:

- No unstaged or staged HANDOFF differences.
- The only local commit beyond `origin/main` was `601a42b`.
- Its HANDOFF-only diff contained 53 insertions and one deletion: replacing the
  stale P13b next step with its completion, plus the appended current-session,
  environment, unresolved-items and next-work sections.
- No additional uncommitted D33/D34/D35 status text was present.
- That existing content is preserved; this task appends its own outcome separately.

## Approved D32 text (verbatim)

**D32 — Qualification of source sampling intervals for D24. Status: DECIDED (owner, 2026-10-29).**

Nominal sampling intervals and gap-rule multipliers are data-analysis properties, not physics parameters. Their source-specific basis and limitations are documented in docs/03. Changes require a DECISIONS entry. D24's integration and gap rules remain unchanged.

**(a) Demonstrated source grid.** A source-export grid may establish the interval used as `nominal_dt_s` when every consecutive timestamp interval in the identified evidence series is exactly the proposed grid interval or a positive integer multiple of it, and that grid interval is itself the smallest observed interval. **A grid shown only in preprocessed or merged files does not qualify, and a grid without any dropout counts only for an API or portal export of the source system itself.** The evidence series, source provenance and applicability to the input series must be stated explicitly. This establishes an export grid, not a guaranteed device acquisition rate.

**(b) Distinguish specification, configuration and observation.** A documented source interval, a configured logging target and an observed cadence must not be presented as interchangeable. Configured targets must be labelled as such and must not be described as guaranteed device rates. An observed median, an API polling interval, a device capability or a grid introduced by merging or resampling does not by itself establish the source's nominal interval. **No new status labels.** Where no qualified basis exists, the nominal interval remains BACKLOG. **The basis must be verifiable from the repository: a cited export is deposited under `data/raw/`, and a row whose export is not deposited stays BACKLOG.**

**(c) Preserve timestamps.** The grid criterion in (a) introduces no rounding or jitter tolerance. Native timestamps of the calculation input must be preserved; they must not be snapped to an artificial grid to satisfy the criterion or before D24 timestamp-validity checks. An exact grid demonstrated by one export does not imply that another representation has exact-grid timestamps; its applicability and observed deviations must be documented separately.

**(d) Existing F8 application.** The F8 portal-chart export identified and cited in task P13b is accepted as the basis for the 300-s nominal interval used for the F8 daily PV source in docs/03. The API history's timestamp deviations remain observations and are not rounded away. This approval does not establish an endpoint-specific API guarantee.

**(e) No additional acceptance claim.** Qualification of a nominal interval does not establish completeness of a time series or validate energy reconstructed between samples. D24 continues to determine integration, gaps and covered fraction. The existing backlog for quantifying the reconstructed bridging share remains open.

Recording note: approved on 2026-10-29 in the owner's coordination chat, including the three restored rules from the earlier review round (merged-file exclusion, repository-verifiable basis, no new status labels); recorded in the repository on its actual date. It resolves previously existing references to D32; it does not assert that a historical approval record has been recovered.

## Acceptance

- D32 occurs exactly once as a decision entry, between unchanged D31 and D33.
- The recorded text matches this wording verbatim, including the merged-file
  exclusion and dropout clause in (a) and the deposit-or-BACKLOG and
  no-new-status-labels clauses in (b).
- Approval and recording are on the actual date, 2026-10-29, not backdated.
- Read-only references are consistent or any mismatch is reported as blocked.
- Only the three Write-Scope files change relative to the task base.
- Mandatory legacy, pytest, CI-guard and README checks pass; no tests are weakened.

## Outcome and verification

- D32 recorded once, verbatim to the approved text above. All pre-existing decision
  text is unchanged, and the pre-existing HANDOFF is preserved as an exact prefix.
- docs/03 and P13b are consistent with the decision and unchanged. The deposited
  portal export's SHA-256 matches the value documented in P13b. The chart data were
  not reanalysed; this task records the owner's explicit acceptance of that basis.
- Only the three Write-Scope files were edited. D34/D35 remain untouched.
- Validation on 2026-10-29, with the project `.venv/bin` on PATH and
  `PYTHONDONTWRITEBYTECODE=1`:
  - `python3 tests/run_all.py`: `ALL PASS`.
  - `pytest -q -p no:cacheprovider`: 109 passed.
  - `BASE_REF=origin/main python3 tools/ci_guard.py`: passed, 22 test files.
  - `python3 tools/make_readme_demo.py --check`: generated demo matches.
  - `git diff --check`: passed.
- No commit or push. Next: owner review of this task and diff, then the separate
  D34/D35 text package with its own approval and Write-Scope.
