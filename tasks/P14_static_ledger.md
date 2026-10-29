# P14 - Immutable run parameters, ledger and first static calculation

**Status:** Case-specific reference contract approved in owner chat on 2026-10-29;
reference document/script writes and two local commits approved in owner chat
on 2026-10-29. Implementation, other test writes, push and PR remain unauthorized.
**References:** ROADMAP M1; SPEC Layers, Ledger scope, AC1/AC5/AC7 and traceability;
D23/D25/D26/D28/D31/D34/D35; P12 decomposition.
**Recording date:** 2026-10-29.
**Preparation branch:** `docs/p14-task-preparation`.
**Preparation base:** `601a42b` plus the then-uncommitted P13c/P13d/P13e documentation.
**Current local decision baseline:** `4316753` (D32), `17118ab` (D34),
`f23d9f8` (D35), committed under separate owner authorization; not pushed.

## Current authorized Write-Scope

- `tasks/P14_static_ledger.md`: preparation, owner decisions, proposed implementation
  contract, unresolved items and verification evidence.
- `HANDOFF.md`: preparation outcome, deferred obligations and next step.

No code, test, reference-fixture, registry, SOURCES, SPEC, DECISIONS or validation-log
write was authorized by the initial preparation. The later reference-only
authorization below supersedes its reference-write and local-commit restriction.
No push or PR creation.
Preserve all existing documentation changes and unrelated untracked files.

## Goal and acceptance boundary

Build an immutable per-run parameter set, a centrally defined ledger and a first
limited static calculation. A separate full-scope report exposes all required
items and their blockers. A complete report is not a complete calculation.

The normative acceptance scope is SPEC/D23, retaining explicit conditions such as
FC-inverter standby "once measured". P14 cannot narrow AC1 acceptance. A limited
intermediate case can be non-INVALID within its declared scope without satisfying
AC1. The full-scope case remains INVALID while required bases are unresolved.
No RTE or M1-acceptance claim is introduced.

## Owner authorization (verbatim)

The owner authorizes the unchanged registry parameters `el.n_cells` (120,
GUESS, u = 0.05) and `el.faradaic_efficiency` (0.98, GUESS, u = 0.03)
exclusively for this labelled P14 intermediate case. Both values are
declared assumptions, not confirmed facts: `n_cells` is a back-calculation
from the datasheet power (2400 W / (120 x 2.0 V) = 10 A) whose registry
entry demands confirmation from Enapter (stack spec not public; no
Enapter contact is currently possible), and `faradaic_efficiency` is a
PEM-to-AEM literature extrapolation (Yodwong et al. 2020,
DOI 10.3390/en13184792) whose registry entry demands validation from the
stack-current route. The uncertainty fields are stated assumption bands
without documented basis. Dependent results retain the GUESS evidence
status; the uncertainty fields are input classifications and must not be
presented as completed output uncertainty propagation. This authorization
permits neither headline use nor any claim of measured plant performance,
and it closes neither of the two open validation obligations.

Recording note: supplied by the owner on 2026-10-29 and recorded on that date.
This is case-specific permission, not a registry or status amendment. The
provenance description is owner-supplied; this task has not independently
verified the manufacturer's specification or the cited paper.

The registry check confirmed both positive uncertainty fields and `assessed`
input classification. GUESS and uncertainty classification are distinct axes.
Positive input uncertainty fields do not establish propagated output uncertainty.
P14 must explicitly report that output uncertainty propagation is not performed,
without displaying zero or borrowing input `assessed` as an output assessment.

## Explicit first-scope decisions

- Quantify electrical EL input, explicit standby energy, Faraday hydrogen amount
  and hydrogen LHV transport. Do not book all these quantities as additive losses.
- No EL conversion-loss decomposition in this first case. Do not invent an
  input-minus-output loss bar. The later device task must define the independent
  loss physics; no particular characteristic-curve form is mandated here.
- Defer dryer quantification: source coverage and model applicability are unresolved.
- Explicit decision under D35 section 6: defer use of the existing ideal-gas
  fill-work function in this first scope because it has no consumer here.
  Revisit its separate physical/accounting role when gas-side calculations are
  introduced. Do not equate ideal work with electrical compression energy.
- Preserve existing fill-work code and tests.
- No measured data requirement for this static scenario.

## SPEC/D23 coverage and dependency contract

The table is the task's requirements record, not a second runtime list.
Implement the approved list centrally in the ledger; test it against independent
requirements. IDs and final typed interfaces are to be fixed in the implementation
review, without changing physical scope.

| Required item or role | Dependency / basis | First-scope treatment |
|---|---|---|
| EL operating electrical input | Explicit power and operating duration | Quantify; input energy, not automatically a loss |
| EL standby within EL energy | Explicit standby power and wall-clock standby duration | Quantify only from supplied, provenance-labelled inputs; no default durations or overlap with operating time |
| EL-produced H2 | Explicit stack current, operating duration, authorized cell count and Faradaic efficiency | Quantify by Faraday; GUESS-derived, model-supported, not measured |
| H2 LHV transport | Produced amount, molar mass, LHV from new-core constants | Quantify as transport, not an additional loss |
| Dryer electrical | Candidate operating envelope versus throughput model; source evidence | Unquantified in full-scope report |
| Dryer vent (H2) | Vent model, regeneration/throughput basis and allowed inputs | Unquantified; EL permission does not authorize `dry.vent_fraction` |
| Water system including RO standby | Explicit process and wall-clock standby basis; applicable source/model | Unquantified in this first implementation |
| Filter train inside E_in | Quantified supported power/time basis | Unquantified; numeric GUESS zero is not silently accepted |
| Compression-air variable share | D13 air demand/conditions plus D14 Kaeser input and allocation | Unquantified, with distinct D13/D14 blockers |
| READY standby | D14 separate standby basis and allocation | Unquantified; not merged into variable HULC energy |
| Network leakage in distribution | D14 leakage basis and separate booking | Unquantified; not assigned to HULC |
| FC control | D22 control-energy basis and stated DC-bus assumption | Unquantified; P15 performs netting |
| FC inverter loss | Terminal/control basis and inverter model under D22 | Unquantified; no guessed curve |
| FC inverter standby | D23 condition "once measured" | Show condition and current applicability explicitly; no invented measurement or unconditional new requirement |
| EL/FC conversion-loss decomposition | SPEC purpose/loss-chain requirement; independent device loss physics | Not implemented; visibly outstanding, no residual substitute |
| Storage change and hydrogen transfers | Defined process boundaries and gas-side state model | Outside the narrow case; full-chain reconciliation outstanding, not a loss bar |

D23 is not an exhaustive specification of every device's loss physics. Conversion
and storage roles above are outstanding coverage requirements, not newly approved
loss formulas or grounds to claim a complete static chain. AC3's event and tank-heat
requirements remain later work under their existing Layer-2 allocation; no new
event model is smuggled into P14.

Read-only consistency finding: SPEC's System boundary still says compressed-air
generation is separate pending D3, while its Ledger scope, D14 and D23 already
specify the decided allocation. Record this as a normative wording-clarification
candidate; do not silently repair it or reinterpret it as permission to omit air.
Stop before implementing any boundary behavior that depends on resolving this
wording. This does not block recording the task or the isolated EL scenario.

Stop and ask on any normative conflict, unclear requirement or necessary
Write-Scope extension. Document non-blocking coverage findings as well; do not
silently reduce SPEC/D23 or amend decisions.

## Concrete intermediate case and provenance

The report declares its actual item list and limited scope as structured data.
"Partial" is a scope description, not a new verdict. Full-scope reporting uses
the central item definition and includes unquantified required items.

Inputs are el_ac_input_power_W, stack_current_A, operating_time_s,
el_ac_standby_power_W and standby_time_s, each with provenance. The powers refer
to the EL AC input boundary; stack_current_A is a distinct DC-stack quantity.
The approved synthetic reference values below are not operating defaults or
inferred plant conditions. Do not infer stack current from AC power, form a stack
voltage from AC power and DC current, or book their difference as a loss.

The narrow-case dependencies are:

- operating electrical energy <- el_ac_input_power_W, operating_time_s;
- standby energy <- el_ac_standby_power_W, standby_time_s;
- produced amount <- stack_current_A, operating_time_s, el.n_cells,
  el.faradaic_efficiency, Faraday constant;
- LHV transport <- produced amount, molar mass, LHV.

### Case-specific scenario classification

Owner coordination chat, 2026-10-29: proceed with the clarified scenario
classification and reference plan; do not independently decide open matters.

Exclusively for the labelled P14 intermediate case, the run inputs
`el_ac_input_power_W`, `stack_current_A`, `operating_time_s`,
`el_ac_standby_power_W` and `standby_time_s`
are declared scenario assumptions with evidence status GUESS and unassessed
input uncertainty.

This classification applies to these run inputs only. It creates no registry
entries, changes no registry value or uncertainty, and establishes no general
rule that scenario inputs must always be GUESS. It does not change the
separately authorized EL parameters or their existing input classifications.

Successfully computed results of this measurement-independent case have result
origin SIMULATED, subject to the perturbation test below. Uncomputed results
have no result origin; the typed absence representation remains to be approved.
Dependent results retain GUESS under the existing weakest-wins rule. Tests
must verify evidence status and result origin as well as numerical values.
No OWNER_DECISION-to-exact treatment is inferred. No numerical uncertainty
band is invented; output uncertainty propagation is not performed or implied.
No headline or measured-plant claim is authorized.

The alternative of treating these inputs solely as OWNER_DECISION and
separately classifying owner-only results was considered but is not selected
for this case. Existing handling of genuinely owner-only evidence sets remains
unchanged: no default is introduced, and unresolved classification requires an
explicit decision. Such a decision can cover multiple results; a separate
entry for every result is not required by this task.

## Proposed implementation contract (not yet a write approval)

- Extend immutable `Param`/`get_param()` with an immutable requested-key ParamSet,
  without loading unrelated registry entries or mutating global state.
- Keep scenario inputs in a separate immutable typed object with units,
  provenance and the approved classification. The computation receives both
  objects explicitly. No scenario registry keys, overlay merge or adapter bypass.
- Preserve the existing code classification string `NOT ASSESSED`; do not
  introduce `UNCERTAINTY_NOT_ASSESSED` as a new code value.
- Reuse status and sign helpers; D28 still blocks REJECTED/SUPERSEDED reads.
  Do not convert errors in the model definition to ordinary BACKLOG.
- Use typed results with explicit units, roles, numeric absence, reasons and
  machine-readable dependency causes. The concrete absence representation must
  prevent NaN/skipna/default-zero loss of blockers.
- Aggregate only compatible quantities in declared accounting groups; never add
  electrical input, chemical transport and losses into one loss total. Do not
  count a group total and its children twice.
- Required unquantified inputs invalidate the relevant declared scope and block
  downstream totals. Unrelated valid results stay visible. NOT ASSESSED alone
  does not invalidate.
- No dynamic Layer-2 balance implementation, RTE, production CLI or AC8 shim.

Proposed future files, requiring implementation approval and explicit protected
test/reference approval before writing:

- `src/verlustmappe/models/params.py`
- `src/verlustmappe/models/ledger.py` (new)
- `src/verlustmappe/models/static_map.py` (new)
- `tests/reference/hand/p14_static_ledger.md` (new)
- `tests/reference/hand/p14_hand_calc.py` (new)
- `tests/test_20_static_map.py` (new, AC1 allocation)
- `tests/test_40_static_ledger.py` (new; recheck number availability before writing)
- `HANDOFF.md`, `docs/04_validation_log.md`, this task

## Reference and implementation order

1. Review the dependency/role contract, remaining blockers and future Write-Scope.
2. With protected-path approval, prepare and verify independent hand calculations
   and their stdlib script before implementing the corresponding computation.
3. Implement parameters, ledger and the bounded scenario.
4. Add focused tests and grow test_20 without claiming full AC1 acceptance.
5. Run checks and record actual coverage, open AC1/AC8 positions and limits.

When commits are separately authorized, hand-reference changes precede the
implementation commit; test changes use their own reasoned commit under rule 4.
No commit is authorized by the current task preparation.

### Independent reference plan (files not yet authorized)

The future hand document and stdlib-only calculation script derive:

- operating energy: el_ac_input_power_W * operating_time_s / 3.6e6;
- standby energy: el_ac_standby_power_W * standby_time_s / 3.6e6, with a
  separately identified, non-overlapping standby period;
- hydrogen amount: eta_F * N_cells * stack_current_A * operating_time_s / (2 * F);
- hydrogen mass: amount_mol * M_H2_kg_per_mol;
- hydrogen LHV transport: mass_kg * LHV_kWh_per_kg.

Separate synthetic scenario choices, the authorized EL assumptions, and
independently sourced constants in the reference. Do not import production
or legacy code or copy its outputs. Explain rounded-constant differences
before choosing test tolerances.

Owner chat approved the following reference contract on 2026-10-29, including
input names, numbers, comparison tolerances, missing-value semantics and the
complete zero case. This is not permission to write protected files or code.

| Synthetic input | Approved reference value |
|---|---|
| el_ac_input_power_W | 2100 W |
| stack_current_A | 8 A |
| operating_time_s | 2700 s |
| el_ac_standby_power_W | 20 W |
| standby_time_s | 1800 s |

Power and current are constant within their respective periods; operating and
standby periods do not overlap. These are synthetic inputs, not verified device
conditions. In particular, 2100 / (120 * 2.0) = 8.75 A, not the chosen 8 A;
the registry's cell-count consistency calculation is not the current source.

Use the existing hand-constant basis: F = 96485.33212 C/mol,
M_H2 = 0.002016 kg/mol and LHV = 119.96 / 3.6 kWh/kg. The displayed F is a rounded
representation of the exact SI product e * N_A = 96485.3321233100184 C/mol.
Do not import model/legacy code to generate expectations.

| Output | Independent reference | Relative comparison tolerance |
|---|---|---|
| Operating AC energy | 1.575 kWh | 1e-12 |
| Standby AC energy | 0.010 kWh | 1e-12 |
| H2 amount | 13.1634516054770 mol | 2e-9 |
| H2 mass | 0.0265375184366417 kg | 2e-9 |
| H2 LHV transport | 0.884289086572095 kWh | 7e-6 |

For positive references use abs(actual - reference) <= rtol * abs(reference).
These are comparison tolerances for known constant rounding plus numerical
execution, not physical uncertainty bands. F rounding contributes about
1.244e-9 relatively; F plus LHV rounding contributes about 6.668e-6 to LHV energy.
The tolerances are tied to the current rounded code constants, including
LHV = 33.322 kWh/kg. The 7e-6 threshold has about 5% headroom over the known
combined difference; reassess its rounding basis if those constants change.
They do not change AC8 tolerances or any general acceptance criterion.

Zero and missing cases:

- Complete zero case: set both AC powers and stack current to zero, retain
  durations. All five outputs are exactly zero, evidence GUESS, origin SIMULATED;
  the narrow calculation is not INVALID solely because these values are zero.
  Compare these direct-product zeros exactly, without a relative division or
  invented near-zero threshold.
- Isolated zero-current case: retain the nonzero AC powers. H2 amount, mass and
  LHV are exactly zero; electrical energies are unchanged. This tests algebraic
  dependencies only, not a plausible operating point or energy-balance closure.
- Missing stack current: H2 amount, mass and LHV have no numeric value, carry a
  blocked/absent marker and a dependency reason, and have no result origin or
  computed-result evidence_status. Retain the report's BACKLOG indication
  required by SPEC/D35 as an unquantified-item indication, not an assignment
  of evidence_status to a computed result that does not exist.
  Electrical results remain visible; the declared scope is INVALID.
- Missing standby duration: standby energy is similarly blocked; operating
  energy and H2 results remain visible; the declared scope is INVALID.
- Keep observation_status = MISSING for absent expected observations, distinct
  from an absent scenario input and from its blocked dependent result. Do not
  relabel synthetic inputs as observations. No zero, NaN, skipna or `or 0`
  substitute; approve the concrete typed absence representation before coding.

None of these cases proves a full energy balance.

### Measurement-independence fixture and perturbation

Define test-only measurement records with columns time_s, el_ac_input_power_W
and stack_current_A. Use three environments at the same test-side invocation
boundary: no records (`None`); records (0, 900, 3) and (2700, 1100, 4); and
perturbed records (0, 300, 1) and (2700, 1800, 6). All fixture numbers are synthetic.
The fixture times deliberately match the scenario operating interval endpoints
(0 and 2700 s), making the records a plausible accidental-consumption trap.
Keep the approved scenario inputs identical across the three runs. All five
computed outputs, evidence and origin must remain identical.

The scalar calculation accepts scenario inputs, not these measurement records.
Do not add a production measurement channel just for this test. Merely discarding
a fixture in a test wrapper or calling the same function twice is not evidence
against hidden measurement dependencies: the later test must expose the fixture
at any actual measurement-access boundary used by the invoked path and verify
that it is not consumed. If no such boundary exists, report that architectural
limit explicitly; do not claim a data-path perturbation that was not exercised.

With the same measurement fixture, double stack_current_A: H2 amount, mass and
LHV double, while electrical energies remain unchanged. Double AC operating
power: only operating energy doubles. Double standby duration: only standby
energy doubles. These dependency checks accompany the measurement perturbation,
not replace it. The fixture description does not authorize test-file writes.

The decision package has been locally versioned in the commits identified above;
it has not been pushed. Remaining integration order, subject to separate git
authorization: version the approved P14 scope;
commit verified hand references before the corresponding implementation;
commit tests separately with their rationale; run final checks and create a
PR only when authorized. The owner merges. Prior prohibitions on commit/push
are not overridden by customary project practice.

## Required independent tests for the later implementation

- Hand-checked electrical energy, Faraday amount and LHV transport.
- Immutable run parameters and no global registry writes.
- Limited complete case is not INVALID solely because other routes are absent,
  but explicitly does not satisfy full-chain AC1.
- Full-scope report with unresolved required compression remains INVALID;
  computed independent items remain visible.
- Missing input blocks exactly its declared dependants; no numeric downstream
  sum, NaN omission, `or 0` fallback or plausible default.
- Genuine computed zero is distinct from unquantified; do not require a consumer
  of the deferred fill-work function just to test this distinction.
- NOT ASSESSED alone does not invalidate; output uncertainty is not falsely
  inferred from input classifications.
- REJECTED/SUPERSEDED errors are not caught and relabelled BACKLOG.
- Missing required item and omitted dependency are detected against independent
  requirements, not against expectations generated by the ledger itself.
- Compatible-unit sums and no double booking of parents, children or transports.
- GUESS evidence, scenario provenance, stated scope and blocking causes are
  present in the report; no total-loss percentage without a valid named basis.

## Deferred obligations and existing backlog links

- Cell count: obtain Enapter confirmation when a contact route exists. Owner
  reports no current contact route; the obligation is deferred, not closed.
- Faradaic efficiency: revisit with existing E1 EL stack-current export work.
  Stack current enables that route but is not itself independent evidence of
  efficiency; a validation design needs an independent hydrogen basis. No E1
  campaign or new measurement is authorized here.
- Dryer: missing `dry.*` SOURCES entries are a rule-3 evidence backlog. Registry
  values/status remain protected and unchanged. Required report reason:
  "Registry candidates are labelled DATASHEET: a 200 W operating-power envelope
  and a 0.045 kWh/Nm3 throughput-based estimate. Required SOURCES entries are
  missing, leaving a discrepancy with rule 3. Applicability is unresolved; no
  model is selected and no dryer result is quantified."
  Do not inherit DATASHEET as the status of an uncomputed dryer result or
  silently relabel the protected registry entries.
- Yodwong: record its own source backlog for the newly authorized EL use: locate
  the exact passage, quotation and PEM-to-AEM transferability assessment for
  DOI 10.3390/en13184792. Do not invent citation details or treat this as
  validation of 0.98; the parameter remains GUESS.
- Constants: existing hand derivations and source hints for F, M_H2 and LHV
  fall under the existing SOURCES migration backlog declared in its introduction.
  This is not a new P14 migration requirement or a retroactive reference-approval
  blocker. It does not waive rule 3, establish a completed central source entry,
  or authorize changes to constants or their evidence classification.
- D25 measurement-data backlog: docs/03 lacks the mandatory-channel list.
  Keep this separate from the static ledger inventory. It is not a blocker for
  this measurement-free synthetic case; do not implement channel-based
  completeness claims against an invented list.
- Follow-up dryer clarification: first establish datasheet locations, quotations,
  conditions and transferability; then decide model applicability. This is a
  separate bounded follow-up, not a prerequisite for the isolated EL case.
- C25 still precedes real-gas porting. D13/D14 and historical AC8 are separate
  unresolved bases. Use existing workbook/L3 backlogs, not parallel measurement
  plans.

## Preparation acceptance and verification

- Owner authorization above is reproduced verbatim.
- SPEC/D23 cross-check, stop conditions, first scope and deferred choices are explicit.
- Only this task and an appended HANDOFF section are changed in preparation;
  prior P13c/P13d/P13e work is preserved.
- No future code/test authorization or acceptance result is implied.
- Mandatory repository checks are run after the last edit; existing-suite success
  does not verify the proposed P14 behavior.

Preparation verification on 2026-10-29, project `.venv/bin` on PATH and
`PYTHONDONTWRITEBYTECODE=1`:

- Exact comparison: owner authorization block matches the supplied text,
  including line breaks.
- SHA-256: existing DECISIONS, SPEC, validation log and P13c/P13d/P13e task
  contents are unchanged; the prior HANDOFF is preserved as an exact prefix.
- `python3 tests/run_all.py`: `ALL PASS`.
- `pytest -q -p no:cacheprovider`: 109 passed.
- `BASE_REF=origin/main python3 tools/ci_guard.py`: passed, 22 test files.
- `python3 tools/make_readme_demo.py --check`: generated demo matches.
- `git diff --check`: passed.

Preparation updated with the owner-approved case-specific reference contract.
Numbers, names and comparison tolerances above are approved only for that case.
## Reference-only execution approval (owner chat, 2026-10-29)

Additional Write-Scope: `tests/reference/hand/p14_static_ledger.md` and
`tests/reference/hand/p14_hand_calc.py`, plus this task and HANDOFF for status
and evidence. No model implementation, test_20/test_40 edits, other protected
paths, push or PR. First commit the approved task preparation and handoff;
then commit the checked reference files separately before implementation.
The reference commit remains subject to the owner's post-commit comparison.

Use the reviewed reference text and stdlib Decimal script, with the F-display
precision note and numeric zero comparisons (never string/repr comparisons).
Print the approved rounded base-case values without normalizing or rounding
the calculation intermediates. Cite D35 section 2 at f23d9f8 for the
unquantified-item BACKLOG indication, separately from computed-result status.
Tolerances remain tied to current rounded constants; no automatic widening.

After the last edit execute the script, legacy suite, pytest, CI guard with
BASE_REF=origin/main, README check and diff checks. Commit messages identify
the owner-chat date and numeric zero comparison. Report both commit hashes
and the script output for owner review. All implementation approval remains open.

## Implementation approval (owner chat, 2026-10-29)

The owner authorizes models/params.py, new models/ledger.py and
models/static_map.py, new tests/test_20_static_map.py and
tests/test_40_static_ledger.py, this task, HANDOFF.md and docs/04_validation_log.md.
Reference files, constants and registry remain unchanged. Two local commits:
implementation/documentation first, tests separately with rationale; prefix
`P14:`. Run all mandatory checks at each commit, not only after the test commit.
No push or PR. Final diffs and checks go to owner review.

- K1: input-domain validation and computed/modelled D31 sign validation have
  separate machine-readable causes. Both can invalidate; zero is valid.
- K2: dependency causes are enum codes with the affected dependency and a
  human-readable explanation, never freetext-only.
- K3: validation log explicitly states "bounded case verified, full-chain AC1
  remains open" only after the focused tests have actually passed.
- K4: owner-approved type/data-integrity clarification: reject wrong types,
  bool and nonfinite numeric inputs/results explicitly with exceptions.
  This is not a D25 physical threshold or new operating limit.
- R1: the immutable scenario object lives in static_map.py, separate from the
  registry-only ParamSet. Computed and blocked items are distinct frozen types;
  explicit None is permitted only for absent scenario inputs, not result values.
- R2: suite green at every commit, including the additive implementation commit.
- Measurement independence: do not introduce a production data argument or a
  fixture-discarding wrapper. If there is no measurement-access boundary, test
  and document the pure dependency architecture and scenario perturbations,
  and explicitly report that no measurement data-path perturbation was exercised.
