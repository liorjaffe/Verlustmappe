# P13e - Record D35 incomplete calculation bases and validity

**Status:** Complete; pending owner review. Not committed or pushed.
**References:** ROADMAP M1/M2; SPEC AC1/AC7/AC8; D23/D25/D26/D31/D34.
**Approval:** Owner coordination chat, 2026-10-29, after the D31 verbatim check:
incorporate the D25-as-clarified-by-D31 references and implement the discussed
text package. No commit, push or AC8 option selection.
**Base:** `601a42b` plus the uncommitted P13c/D32 and P13d/D34 changes.
**Branch:** `docs/p13e-record-d35`.

## Goal and Write-Scope

- `tasks/P13e_record_d35.md`: task, old/new normative wording and evidence.
- `DECISIONS.md`: append D35 and explicit D25/D26(c)/D31(a) amendment references.
- `SPEC.md`: consistent AC1, AC7, Layer-1, validity and status wording.
- `HANDOFF.md`: separate outcome, outstanding decisions and next step.
- `docs/04_validation_log.md`: open AC8 positions and blocking references only.

Out of scope: choosing an AC8 option, historical-parameter exceptions, RTE
deferral, partial M1 acceptance, code, tests, registry, raw data, AGENTS, ROADMAP,
README and unrelated documentation cleanup. No P14 implementation.

## Pre-edit report and preservation

Existing unstaged DECISIONS/HANDOFF changes belong to P13c/P13d; their task
files are untracked. No other tracked changes were present. Existing content
is preserved; only explicit amendment references are inserted into the older
decisions. D32, D34 and the prior task files remain unchanged.

Pre-edit SHA-256:

- DECISIONS: `a7168fe8e300246c4ea16d9dfc36e9f6c8c198c7fa298b5828ef866d7d94232a`
- HANDOFF: `958329a8054df64226a6587cb704cdbc6a658b6b537fecb0fb220debc76324ef`
- P13c: `fd126eb575224076b8e7d6a961ec0252def703de23e4cb8a9a894c5b6f98c993`
- P13d: `125110dc475117c11fc85a20a2023d3dd1ef69abc8a24b4aadb820d475c5b758`

## Normative old/new wording

Quoted passages below are verbatim apart from line wrapping. Historical decision
wording is retained, not silently replaced. D35 is the approved amendment.

### D25, REQUIRED-BACKLOG clause

Old:

> A run or result is INVALID (never a plausible number) when: a REQUIRED parameter is BACKLOG without an owner-approved GUESS (AC1);

New effective rule (D35 sections 1-2):

> A REQUIRED BACKLOG parameter without an owner-approved, clearly labelled GUESS permitted by the applicable specific decisions makes the declared run INVALID. An unresolved model, operating-point or allocation basis required for that run likewise prevents a valid overall calculation.

### D26(c), BACKLOG boundary

Old:

> BACKLOG = no value, a REQUIRED backlog parameter makes the run INVALID (AC1); UNCERTAINTY_NOT_ASSESSED = value exists, uncertainty unquantified, the run computes and the result is not publishable as valid. Numeric BACKLOG placeholders are themselves not-assessed.

New effective rule (D35 section 4):

> For a required parameter, a numeric BACKLOG placeholder does not count as an available value unless an owner-approved, clearly labelled GUESS is permitted by the applicable specific decisions. This is a calculation-validity rule, not an adapter read restriction. D28 remains unchanged.
>
> UNCERTAINTY_NOT_ASSESSED alone neither blocks computation nor makes the calculation INVALID. Its publication consequences remain governed by D26 and D21.

### D31(a), channel clarification of D25

Old:

> (a) a missing mandatory channel makes only the affected route or item INVALID, not automatically the whole run; mandatory channels are enumerated per source in docs/03.

New effective rule (D35 section 2):

> Under D25 as clarified by D31(a), a missing mandatory channel first makes the affected route or item INVALID. It also makes the declared run INVALID if a required result cannot be supplied by an explicitly permitted alternative. An unavailable route that is not required for the declared scope does not automatically invalidate the run. The separate labelled NAMEPLATE result under D25 as clarified by D31(b) remains subject to its existing rules.

The sign rule and D31(b)/(c) are not amended.

### SPEC validity: required parameter

Old:

> a REQUIRED parameter is BACKLOG without an owner-approved GUESS;

New:

> a parameter required for the declared calculation scope is BACKLOG without an owner-approved, clearly labelled GUESS permitted by the applicable specific decisions;

### SPEC validity: missing channel

Old:

> a mandatory channel is missing (per source in `docs/03`; only the affected route or item is INVALID).

New:

> a mandatory channel is missing (per source in `docs/03`; the affected route or item is INVALID, and the declared run is INVALID if a required result cannot be supplied by an explicitly permitted alternative).

Added immediately after the gate list:

> Under D35, an unresolved model, operating-point or allocation basis required for the declared run also prevents a valid overall calculation. Independent valid partial results must remain visible; missing required values and their dependent numerical results remain unquantified. Narrow intermediate scopes do not satisfy full-chain AC1 acceptance.

### SPEC Layer-1 result

Old:

> No DataFrames, no global state, no measured-data requirement. Result: loss chain per operating point and an RTE map, every bar with evidence status.

New:

> No DataFrames, no global state, no general measured-data prerequisite. Result: a loss chain per operating point, each quantified item with evidence status or each unquantified item with no numeric value, a BACKLOG indication and a stated reason. Powers and flows at a point are distinguished from energies and amounts over a defined duration or process. The RTE map requires materially and energetically consistent paired charge/discharge reference cases defined in P15, subject to the applicable validity and publication gates (D35).

### SPEC AC1

Old:

> The static loss map computes a complete chain without measured data; every bar carries an evidence status derived from its inputs. A run with a REQUIRED BACKLOG parameter must be treated as invalid unless an owner-approved, clearly labeled GUESS placeholder exists.

New:

> The static loss map computes a complete chain without measured data being a general prerequisite. Acceptance requires a run that is not INVALID and covers the full applicable storage-chain scope specified by SPEC and D23, retaining D23's explicitly stated conditions. Each quantified item carries an evidence status derived from its inputs. Each required input must be available or supplied by an owner-approved, clearly labelled GUESS permitted by the applicable specific decisions.
>
> Every report identifies all required items in its stated scope. Unquantified items carry no numeric value, a BACKLOG indication and a stated reason. Independent valid partial results remain visible. Narrower intermediate calculations identify their limited scope; "partial" describes scope, not a new validity status. Such calculations, and complete reports of INVALID full-chain runs, do not satisfy AC1 acceptance (D35).

### SPEC AC7

Old:

> The report shows the share of loss energy per evidence status and per result origin (D26); loss bars whose weakest-wins status includes UNCERTAINTY_NOT_ASSESSED are reported as a separate share of the loss energy; it states the model limits (what the model cannot do).

New:

> The report shows the share of quantified loss energy per evidence status and per result origin (D26), explicitly naming the denominator. Quantified loss bars with UNCERTAINTY_NOT_ASSESSED inputs are reported as a separate share on that same basis. Unquantified items are listed separately with their blocking reasons and without energy percentages. An incomplete required loss chain must not be presented as a complete loss total, an overall loss ranking or a quantitatively complete Sankey diagram. The report states the model limits (D35).

### SPEC status: BACKLOG precedence

Old:

> BACKLOG takes precedence: a REQUIRED BACKLOG parameter makes the run INVALID (AC1); a numeric BACKLOG placeholder is itself not-assessed.

New:

> BACKLOG takes precedence: a parameter required for the declared calculation scope that is BACKLOG makes the run INVALID unless an owner-approved, clearly labelled GUESS is permitted by the applicable specific decisions (AC1/D35). Independent valid partial results remain visible; affected and dependent numerical results remain unquantified. A numeric BACKLOG placeholder is itself not-assessed and does not count as an available required value merely because it contains a number. This does not change adapter readability under D28.

### SPEC Layer-2 evaluation boundary

Added under balance invariants, without changing numeric tolerances:

> Under D35, a balance that cannot be evaluated because a required energy or mole quantity is unquantified is reported as not evaluated, never as passed. This is distinct from a computed balance violation and introduces no new D26 status name.

## Acceptance and acknowledged consequence

- The old/new passages above match the pre-edit wording and the effective amendments.
- D25/D31(a) references are explicit; D31's sign rule is unchanged.
- Full applicable SPEC/D23 scope remains the AC1 acceptance scope; P14 cannot reduce it.
- No new status, threshold, adapter restriction or compression GUESS is introduced.
- docs/04 lists blocked AC8 comparisons without claiming PASS or selecting an option.
- Only Write-Scope files change; D32/D34 and their task files remain unchanged.
- Mandatory repository checks pass after the final edit.

The owner-approved consequence of D35 is recorded with the decision:
implementation may progress while full M1 acceptance remains blocked. Closing
D13/D14 does not itself establish historical AC8 comparability. No partial
M1 acceptance is implied.

## Outcome and verification

- D35 recorded with the explicit D25-as-clarified-by-D31(a)/(b) references.
  SPEC and open AC8 positions agree with the recorded decision.
- Every old/new quotation above was checked against its source after whitespace
  normalization. The BACKLOG-precedence clause explicitly says "that is BACKLOG"
  so that required parameters with available values are not inadvertently invalidated.
- Hash checks confirm unchanged D32/D34 content and P13c/P13d tasks, preserved
  prior HANDOFF, and unchanged historical decision text except the three explicit
  amendment references. SPEC AC8 wording is unchanged.
- Only the five Write-Scope files were edited by P13e.
- Validation on 2026-10-29, with `.venv/bin` on PATH and
  `PYTHONDONTWRITEBYTECODE=1`:
  - `python3 tests/run_all.py`: `ALL PASS`.
  - `pytest -q -p no:cacheprovider`: 109 passed.
  - `BASE_REF=origin/main python3 tools/ci_guard.py`: passed, 22 test files.
  - `python3 tools/make_readme_demo.py --check`: generated demo matches.
  - `git diff --check`: passed.
- No new-core ledger behavior or AC8 regression has been implemented or verified
  by this text task. The existing suites verify the unchanged software baseline.
- No commit or push. Next: owner review, then scoped P14 and AC8-reference task
  preparation; the AC8 option remains pending.
