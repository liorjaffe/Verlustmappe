# P13d - Record D34 staged model development

**Status:** Complete; pending owner review. Not committed or pushed.
**References:** ROADMAP M1-M4; SPEC Layers 1-3 and AC4/AC5; D13/D14/D20-D22/D25/D26/D31.
**Approval:** Owner coordination chat, 2026-10-29: translation corrections and
the Write-Scope below approved; no commit or push authorized.
**Base:** `601a42b` plus the uncommitted P13c/D32 changes.
**Branch:** `docs/p13d-record-d34`.

## Goal and Write-Scope

Record D34 without changing existing acceptance or validity rules:

- `tasks/P13d_record_d34.md`: task, translation review, final English wording and evidence.
- `DECISIONS.md`: append D34; preserve D32 and every preceding entry.
- `HANDOFF.md`: append the D34 outcome and separate next decision.

Out of scope: D35, AC8 option selection, SPEC, ROADMAP, AGENTS, README, code,
tests, registry, raw data, commits and pushes. The existing P13c task is read-only.

## Translation review and approval

Content differences were reported to the owner before recording:

- Restore: "Model results are reported with their result origin, evidence status,
  assumptions and limits."
- Retain the five descriptive distinctions as a deliberate addition approved
  with this task, not as new D26 vocabulary. Explicitly reserve run-level
  validity semantics for the separate D35 decision.
- Explicitly state that a system-level plant-validation acceptance requires a
  separate owner decision.
- Use "limits on interpretation" in the title and retain the expanded list of
  existing decisions that remain applicable.
- Mark the decision approved and recorded on the actual date, 2026-10-29,
  rather than inferring a historical approval.

The recorded text is a faithful translation of the approved content; any content
deviation (omission, addition, or changed emphasis) is reported to the owner
before recording. The additions above were explicitly identified in the review
and included in the owner's conditional approval.

## Final English text

**D34 — Staged model development and limits on interpretation. Status: DECIDED (owner, 2026-10-29).**

Development follows the existing roadmap: static device physics and the Layer-1 loss map first, dynamic simulation using the same device models next, followed by component calibration and an independent hold-out check under M4/AC4.

A general hydrogen measurement campaign is not a prerequisite for implementing Layer 1 or Layer 2. This does not waive source requirements, software verification, or evidence required to quantify a particular item or accept a milestone. Model results are reported with their result origin, evidence status, assumptions and limits. No system-level plant-validation acceptance is introduced by this decision; introducing one requires a separate owner decision.

Hand calculations, balance checks, synthetic tests and legacy regression provide verification evidence within their stated scope. They do not establish measured plant performance or independent validation of the plant.

"Report completeness", "calculation validity", "software verification", "calibration and independent hold-out checking", and "RTE publication eligibility" are descriptive distinctions, not additions to the D26 vocabulary. Calculation validity remains subject to D25/D31 and their expressly approved amendments; this does not pre-decide the run-level validity semantics reserved for the separate D35 decision. No broader "validated" claim is introduced beyond the existing AC4/AC5 framework.

Descriptions of current capabilities must distinguish the new core from frozen legacy demonstrations and future calibration or hold-out work. Any necessary README change requires its own approved scope. The generated legacy block and its existing generator gate remain unchanged until the roadmap-authorized transition.

This decision changes no acceptance criterion, parameter value, compression basis, allocation rule or RTE gate. D13, D14, D20, D21, D22, D25, D26 and D31 remain applicable. Any subsequent change to incomplete-calculation reporting or validity aggregation requires a separate, explicitly approved decision.

Recording note: approved and recorded on 2026-10-29 following the owner's translation review in the coordination chat, including the deliberate descriptive-terminology addition and the explicit reservation of D35.

## Pre-edit state

The working branch contained only the existing uncommitted P13c changes to
DECISIONS and HANDOFF and its untracked task file. No other tracked changes
were present. The prior HANDOFF wording about D34/D35 is preserved as the P13c
task's historical outcome; the new D34 section updates the current state.

Pre-edit SHA-256:

- DECISIONS: `4dc5ea1c701630e4debd4e83ab2dc20e38367a351fe47035454c9fd599b6b2a8`
- HANDOFF: `30908f1139ee90ab8256425c9171a0bb68f58f20d3822bb391fa759b570d74d9`
- P13c task: `fd126eb575224076b8e7d6a961ec0252def703de23e4cb8a9a894c5b6f98c993`

## Acceptance

- Faithful translation and disclosed content differences as specified above.
- The recorded decision matches the final English text in this task.
- D32 and every pre-existing decision and HANDOFF section remain unchanged.
- No new Handoff publication-unlock rule or D35 verdict is introduced.
- Only the three Write-Scope files are edited by this task.
- Mandatory repository checks pass after the last edit.

## Outcome and verification

- Final English text and recorded D34 are identical. Translation review and
  approved content differences are documented above.
- SHA-256 checks confirm that all pre-existing decision text, the entire prior
  HANDOFF and the P13c task remain byte-for-byte unchanged.
- Only the three Write-Scope files were edited by P13d.
- Validation on 2026-10-29, with `.venv/bin` on PATH and
  `PYTHONDONTWRITEBYTECODE=1`:
  - `python3 tests/run_all.py`: `ALL PASS`.
  - `pytest -q -p no:cacheprovider`: 109 passed.
  - `BASE_REF=origin/main python3 tools/ci_guard.py`: passed, 22 test files.
  - `python3 tools/make_readme_demo.py --check`: generated demo matches.
  - `git diff --check`: passed.
- No commit or push. Next: review the P13d changes, then prepare the separate
  D35 approval text; no D35 or AC8 option is decided by P13d.
