# Session handoff
At the end of a session, update this file: done / blocked / decisions needed /
next step. Read this file, SPEC.md, and the assigned tasks/Pxx_*.md before
starting work.

## Done

- Tagged the unmodified baseline `d060c9b` as `legacy-1.0` (frozen legacy state).
- Repo hygiene: `.gitignore` added, 66 binary artifacts untracked (`9d9ae80`),
  minimal `pyproject.toml` added (`b483fd4`).
- `AGENTS.md` rebuilt (`543548a`, `6830fd4`): SPEC primacy, tag-based legacy
  freeze with the `models/params.py` adapter exception, protected paths,
  branch rules, ci_guard limits, calibration paths split.
- `DECISIONS.md`: D1-D9 (+D3b) with status fields (`6c161a4`, `01af2df`);
  see `DECISIONS.md` for titles and status.
- Bundle commit (`9dc7476`): rebuilt `SPEC.md`, new `ROADMAP.md` (M0-M6), new
  `docs/94_known_defects_legacy.md` (C1-C12), `.github/CODEOWNERS` extended to
  all 13 protected paths, matching AGENTS.md.

- P05 is complete (PR #1, merge `3ceb62e`): D11-D15, 22 SOURCES entries
  (20 with verbatim quotes), registry `comp.*` REJECTED + 22 workbook entries, `make_register.py`
  (D11 exception), docs/01 note, tests `test_30`-`test_34` (pytest), D9 (a)-(d).
  `python3 tests/run_all.py` covers test_01-12 only; `pytest -q` covers test_30+.

## Blocked

- GitHub branch protection cannot be configured from repository files. A
  repository administrator must require pull requests, code-owner review, and
  passing status checks for `main`. Until then, CODEOWNERS is preparation only.

## Decisions needed

- Open in `DECISIONS.md`: D1, D3, D4, D5, D6, and the "Pending decisions"
  section (POA source, Kaeser metering, tank retrofit, fuelcell_analyzer.html).
- Battery registry conflict: `bat.capacity_Ah` is a BACKLOG placeholder (100 Ah)
  and `bat.nominal_V` is set to 52 V, but the GTEM-48V5000-E datasheet says
  105 Ah / 5 kWh and 48 V nominal (52 V is the Regatron bus setpoint). Needs a
  DECISIONS entry (D10) before any registry change.

## P05 open points (owner)

- SOURCES quotes: 20 of 22 entries carry verbatim quotes (owner transcription 2026-10-28).
  `sys.n_rotex` and `sys.p_h2_out_project_barg` stay BACKLOG (owner decisions, no
  document). Pressure convention (gauge) is an assumption (P-2); old Maximator repair
  manual shows lower limits (150/300 bar), question P-3.
- `kaeser.p_package_dealer_kw` (6.2 kW): uncertainty not assessed, owner to set.
- Air consumption (D13): Maximator inquiry (chart conditions, continuous vs intermittent,
  gauge vs absolute) and site readout (SC2 load hours + kWh counter, stroke counters, EL
  production) are open; nothing registered.
- Workbook hash `0aa9f8ed...` should replace the original in "Master RTE sheets".
- README note about the rejected assumption is not added (generated block); decide where.
- ci_guard registry false alarm (registry change without tests change) not reproduced
  with the P05 diff; P04 (merged, PR #3) upgraded ci_guard to parsed entries.
- Test guard for `comp.*` is a weak text scan until `models/params.py` exists.

## Next step

- Follow-up after P05 (`chore/p05-followup`): stale texts and the D9(a)/(c) remainder
  (pytest test extra in pyproject.toml, explicit legacy list plus stray-file guard in
  run_all.py) are done there.
- P04 is merged (PR #3: ci_guard parsed entries, C11/C13 text cleanup, D16/D17/D18).
- P02b is merged (PR #4: docs/01-04 attribution, README legacy note and FAQ, make_register
  items 4/4b per D19, demo summary note, docs/02 regenerated).
- P06 is merged (PR #5: Z-value docs quote the `test_02` assertions and the CoolProp 8.0.0
  cross-check; CoolProp is a verification tool, not a dependency).
- P07 is merged (PR #6: docs/94 C14-C29 with AC8 rows, numbers recomputed from repo code).
- P08 is merged (PR #7: D20-D30 pre-M1 definition gates, D5 closed by D26, AGENTS status
  vocabulary and freeze amendment; text only).
- P09 is merged (PR #8: SPEC matches D20-D31, D31 sign rule added).
- P09b is merged (PR #9: register column "u class" per D26 in docs/02, tests/test_35_u_class.py;
  59 NOT ASSESSED, 4 exact, 46 assessed).
- P10 is merged (PR #10: hand references constants.md, isothermal_work.md, p10_hand_calc.py;
  two work definitions A/B documented, A has no active consumer).
- P11 is merged (PR #11: src/verlustmappe/models/ constants, fill-integral work with
  FillWork exact-zero flag, minimal params adapter; tests/test_36 incl. general D28 guard).
  The 0.0/max semantics are domain properties, not rule 8 clamps (owner decision, task file).
  Open: Z source (C25) before z_realgas can be ported.
- docs/94 candidates (own task, pattern of P07): booster.account() docstring vs behavior;
  isothermal_work_kWh without active consumer.
- M1 split (tasks/P12): P12 status ranking/u_class/weakest; P13 integration (D24) + gate
  predicates (D25/D31); P14 ledger, balances, ParamSet, test_20; P15 netting/RTE; P16 fault
  injection. Dependencies: real-gas items wait for the Z source (C25); compression-air items
  are BACKLOG until the Kaeser measurement (E3); D22 measurement point is carried as a
  documented assumption, not a blocker. Hand references go into the task that introduces the
  function. Test count now: pytest 77 passed.
- P12 is merged (PR #14: models/status.py with D26 ranking, total u_class, weakest; Param.u_class;
  tests/test_37, parity with the register column over all 109 entries; pytest 88 passed).
- P13 draft (tasks/P13): integration D24 + sign/time predicates; findings: docs/03 lacks nominal
  intervals and the mandatory-channel list, registry has no REQUIRED flag, Route-2 has no new-core
  consumer. Open owner questions in the task file.
- P13 runs as three PRs (task draft #16, hand references #17 merged; code + test_38 #18 merged). P13 merged.
- D33 recorded (owner, 2026-10-28): F8 is the only PV source; Sept 2026 PV dataset excluded and `pv_merged.csv` + test_08b deleted; F8 SolisCloud history deposited as 528 per-day `.json.gz` files plus `MANIFEST.sha256` in `data/raw/solis_f8/`, with parsed CSVs in `data/processed/solis_f8/` (2026-01-01..10-27; API returned empty lists 09-17..10-22, cause unknown). The gzip files round-trip byte-identically to the saved compact JSON; manifest hashes those JSON bytes, not original HTTP response bytes. 74,832 API records; none lacked `dataTimestamp`. API cadence observation: 74,304 intervals, raw `dataTimestamp` values sorted within each daily response before UTC conversion; median 299.965 s, 97.8% within 290-310 s, 13 intervals >900 s; no non-positive intervals. The earlier count of 11 was an incorrect calculation; raw and parsed series both give 13. The portal export `Daily+Power+Station+Chart_29-10-2026.xls` is not ignored; its chart date is 2026-10-28 and it establishes the 300-s grid under D32(a). Official SolisCloud API docs checked 2026-10-29: no endpoint-specific `inverterDay` resolution; the general 5-minute device-upload statement is not the basis. `inv_pv.eta_euro` stays PRELIM.
- Environment observation (2026-10-29): During verification, `report_cli.py pvf8` failed once with `ModuleNotFoundError: numpy`, then succeeded on direct retry and with `-v`. `make_readme_demo.py --check` failed twice without `-v` and succeeded with `-v`; a later run failed again, including on retry after capturing diagnostics. At that failure, `sys.path` included the venv `site-packages`, `pip show` reported NumPy 2.5.4, and `find_spec` located it. The newest top-level `site-packages` entries were dated Oct 24; the `numpy` package and metadata were dated Oct 20; no pip process was observed. These snapshots do not establish the cause or rule out transient activity between checks. If this recurs, capture interpreter path and `sys.path`, `.venv/bin/python -m pip show numpy`, and `numpy` directory/metadata timestamps immediately after failure and before retry.
- Native API timestamps must not be rounded or merged onto an artificial grid before applying the D24 duplicate-timestamp rule; the deposited F8 data contain no non-positive intervals.
- Bridging BACKLOG: reconstructed bridging share on the PV path, to be quantified on the first measured week; a per-source multiplier remains a DECISIONS option.
- Merge policy: preserve native source timestamps; never snap them onto an artificial grid before applying D24 timestamp validation.
- P13b is complete (PR #20 merged to `main`, merge `271310e`): `docs/03` nominal-cadence table, D24/C20 note, and the owner-approved F8 portal-chart source entry are recorded in `tasks/P13b_nominal_cadence_docs.md`.
- Later: adapt the copilot-brief workflow (outside the repo) to D29; also check the D23 text against code in M1.
- Audit backlog (D26): the 63 entries with u = 0.0 are classified, not migrated; first
  candidate kaeser.p_package_dealer_kw; open source/status item fc.poc_max_duration_s
  (DERIVED, sourced from a manual).
- Station id `...567877` is consistency-verified against solis_live.py/test_10/docs/03 only;
  the check against the SolisCloud export is still open (non-blocking).

- P02 is complete (implementation commits `1f0a0e7`, `7047101`; merge via main).
- P03 is complete: C9 fixed (tests `1afd616`, docs `b705ae3`, merge `8bd06ef`).
  Both tests restore `stor.volume_L` in a finally wrapper; owner acceptance
  (same-process leak check, both-modules failure path) executed before merge.
- Next: see the order above (P10, P11, P12).
  

Later:
- D9 (a)-(d) done in P05 (test_20-26 stay reserved by the SPEC).
- M1 per `ROADMAP.md`.
- Backlog: migrate the 87 registry citations into complete `SOURCES.md` entries.

## Current handoff (2026-10-29)

### Done in the current session

- PR #20 was merged by the owner; `main` is at merge commit `271310e`.
- Post-merge checks: `tests/run_all.py` passed with the project `.venv` on `PATH`
  (`ALL PASS`); `pytest -q` passed (109 tests); `ci_guard.py` passed (22 test files).
  The README demo check passed in 20 alternating Dev/Desktop pairs (40 successful runs),
  but failed again during this handoff update with `No module named 'numpy'`. An immediate
  `-v` rerun succeeded. A separate diagnostic process used the expected Desktop venv,
  had that venv's `site-packages` on `sys.path`, found NumPy 2.5.4, and reported package
  and metadata timestamps of 2026-10-20. These diagnostics are not the failing process's
  own `sys.path`; the failure cause remains unknown.
- The incomplete copy at `~/dev/verlustmappe` was brought up to date for project files
  using rsync while excluding `.git`, `.venv`, `.pytest_cache`, root `Differenz/`, and
  names matching `* 2.*`. A subsequent dry-run showed only the root-directory timestamp
  difference; `tools/make_readme_demo.py` exists in the copy and NumPy/Pandas import there.
- The README demo check passed in 20 alternating Dev/Desktop pairs (40 successful runs).
  This is evidence that the earlier failure did not reproduce in that test window; it
  does not establish that the cause is fixed.
- The owner confirmed iCloud Desktop & Documents synchronization is enabled. This is an
  observation only, not evidence that iCloud caused the import failure.
- The two rsync processes (PIDs 94188 and 94189) are no longer running.

### Open / do not assume resolved

- The intermittent `ModuleNotFoundError: numpy` cause remains unknown. If it recurs,
  capture the failing interpreter path, `sys.path`, NumPy package/metadata timestamps, and
  `pip show numpy` immediately before retrying; retain the existing capture protocol.
- Do not delete or commit the untracked `Differenz/` tree or files with ` 2` in their
  names. Earlier inspection found 529 such entries in `data/raw/solis_f8/` and 231 in
  `data/processed/solis_f8/`; only two pairs were compared and those two were identical.
  The remaining pairs have not been verified. The duplicate files' origin is unknown.
- The Dev/Desktop synchronization is adequate for the demo-check experiment, not a proof
  that every file in both worktrees is identical: `.git`, `.venv`, caches, `Differenz/`,
  and `* 2.*` were intentionally excluded.
- Existing owner decisions/backlogs remain open as listed above, including the Z-source
  clarification (C25), the 12.780 kWp portal text versus 12.74 kWp registry value, and
  the station-ID cross-check against the SolisCloud export.

### Next work

1. Prepare a separate, bounded docs/94 task for the two candidates recorded above
   (`booster.account()` documentation/behavior and `isothermal_work_kWh` without an
   active consumer). Establish the AC/reference and Write-Scope before implementation,
   per AGENTS.md.
2. Resolve the Z-source clarification before porting `z_realgas` (C25).
3. Continue M1 with P14 (ledger, balances, `ParamSet`, and `test_20`), following its
   dependency and Write-Scope requirements. The docs/94 task and P14 task files do not
   yet exist; do not treat this handoff list as authorization to edit outside an
   approved task scope.

## D32 recording (P13c, 2026-10-29)

- Done: recorded the exact owner-approved D32 text in DECISIONS.md and in
  tasks/P13c_record_d32.md, including the merged-file/dropout restriction,
  deposit-or-BACKLOG rule and prohibition on new status labels.
- Approval and recording date: 2026-10-29. No historical owner-approved record
  is claimed to have been recovered. The missing D32 entry is now recorded.
- Before editing: no unstaged or staged HANDOFF changes; the only pre-existing
  local difference from origin/main was HANDOFF-only commit 601a42b. Its content
  is preserved separately from this appended task outcome.
- Read-only consistency checks: docs/03 and P13b agree on the D32(a) source-grid
  criterion, F8 portal-export basis, native timestamp preservation and open
  bridging share. No changes to those files were required.
- Verification: exact task/decision text equality, unchanged prior decision text
  and HANDOFF prefix, unchanged read-only files, and portal-export hash match.
  Legacy suite ALL PASS; pytest 109 passed; CI guard passed (22 test files,
  BASE_REF=origin/main); README demo check matches. See P13c for commands.
  No commit or push authorized or performed; owner review remains pending.
- Decisions needed / next step: review the P13c diff, then finalize the separate
  D34/D35 text package and its Write-Scope. D34/D35 and the AC8 option remain
  unrecorded and undecided by this task; no P14 implementation is authorized.

## D34 recording (P13d, 2026-10-29)

- Done: recorded D34 after the owner's translation review, including the restored
  model-result reporting sentence, explicitly approved descriptive terminology,
  reservation of D35 run-level semantics and separate system-validation decision.
- D34 records the staged roadmap direction; it changes no existing acceptance,
  compression, allocation, validity or RTE gate. No README/code/test change.
- Existing P13c/D32 changes and all prior HANDOFF content are preserved. The
  P13c statement about unrecorded D34 describes the earlier task state; this
  section records the subsequent D34 completion.
- Verification: final English task/decision text equality; SHA-256 confirms
  unchanged prior decision text, HANDOFF prefix and P13c task. Legacy ALL PASS;
  pytest 109 passed; CI guard passed (22 files, BASE_REF=origin/main); README
  demo check matches. Commands are recorded in P13d.
  No commit or push authorized or performed.
- Decisions needed / next step: owner review, then the separate D35 text package
  with the full SPEC/D23 acceptance scope and run-level validity rule. AC8 remains
  an open decision; this task authorizes neither a D35 entry nor P14 implementation.

## D35 recording (P13e, 2026-10-29)

- Done: recorded D35 and explicit amendments to D25, D26(c) and D31(a);
  synchronized SPEC AC1/AC7, Layer 1, validity/status and Layer-2 evaluation rules.
  Historical decision wording and all prior P13c/P13d content are preserved.
- AC1 still requires a non-INVALID full applicable SPEC/D23 calculation. Narrow
  intermediate runs and complete reports of incomplete calculations do not pass AC1.
  "Partial" is a scope description, not a new status. P14 cannot reduce D23.
- Independent valid results remain visible; missing required bases propagate to
  dependent results without numeric defaults. D28 readability is unchanged.
- Open AC8 positions are now explicit in docs/04. No fixture exception, RTE
  deferral, compression GUESS or partial M1 acceptance has been approved.
- Acknowledged consequence: implementation may progress while full M1 acceptance
  remains blocked. D13 air demand and D14 electrical input/allocation are separate;
  their closure does not itself establish historical AC8 RTE comparability.
- Verification: old/new task quotations match their sources after whitespace
  normalization; prior D32/D34 and their task files are preserved; SPEC AC8 is
  unchanged. Legacy ALL PASS; pytest 109 passed; CI guard passed (22 files,
  BASE_REF=origin/main); README demo check matches. See P13e for commands.
  These checks do not prove future ledger behavior or AC8 acceptance.
  No commit or push authorized or performed.
- Decisions needed / next step: review P13e; then prepare the scoped P14 task and
  separate AC8 reference/decision task. P14 must decide labelled ideal-gas fill-work
  use versus deferral; real-gas port still waits for C25. No code task is authorized
  by this text update. Earlier P13c/P13d next-step notes describe their task-time state.

## P14 task preparation (2026-10-29)

- Done: created tasks/P14_static_ledger.md with the owner's verbatim case-specific
  EL-GUESS permission, SPEC/D23 coverage/dependencies, scope declaration, proposed
  implementation/tests and reference-before-implementation order.
- Current permission covers task preparation and this handoff only. No code,
  protected tests/references, registry changes, commit or push authorized.
- Explicit choices: defer dryer quantification and ideal-gas fill-work use in the
  first scope (D35 section 6); no EL conversion-loss decomposition or RTE.
- Deferred: confirm el.n_cells with Enapter when contact becomes possible; owner
  reports no current contact route. Revisit el.faradaic_efficiency with the
  existing E1 stack-current export work. Neither validation obligation is closed;
  stack current alone is not independent validation of Faradaic efficiency.
- The two EL uncertainty fields remain assumption bands without documented basis.
  GUESS evidence and assessed input fields do not establish propagated output
  uncertainty. No headline or measured-plant claim is permitted by this permission.
- Dryer follow-up: complete missing dry.* source entries, then resolve applicability
  of the power-envelope versus throughput approach. Registry remains unchanged;
  no new parallel measurement backlog is created.
- Documented boundary clarification: SPEC's older D3 compressed-air wording versus
  its decided D14/D23 allocation. Do not omit air or implement disputed boundary
  behavior; resolve if that behavior is needed. The isolated EL case is unaffected.
- Clarified for this P14 intermediate case only: el_ac_input_power_W,
  stack_current_A, operating_time_s, el_ac_standby_power_W and standby_time_s
  are GUESS scenario
  assumptions with unassessed input uncertainty; results are SIMULATED with
  GUESS evidence. Existing EL input fields and owner-only error handling remain
  unchanged. No general scenario classification or new status is introduced.
- Owner-approved reference contract is now recorded in the task: 2100 W AC,
  8 A DC stack, 2700 s operation; separate 20 W AC standby for 1800 s. These
  synthetic values are not defaults or verified device conditions. No stack
  voltage or loss difference is formed from AC power and DC current.
- Approved comparison tolerances, exact complete-zero case, missing-result
  semantics and a concrete test-only measurement fixture are recorded there.
  Zero results remain GUESS/SIMULATED; uncomputed results have no origin.
  Perturbation must exercise any actual measurement-access boundary, not a
  wrapper that discards data by construction; future execution is unverified.
- Registry ParamSet and immutable scenario inputs stay separate. Protected
  reference/test writes, concrete implementation scope and typed absence
  representation still require approval. No code or git operation is authorized.
- Sources: constants remain under the existing SOURCES migration backlog,
  not a new P14 blocker. Yodwong has its own citation/transferability backlog.
  Dryer DATASHEET labels conflict with missing source coverage; report that
  discrepancy without changing the registry or quantifying a dryer result.
  Missing D25 mandatory-channel list is a separate measurement-data backlog,
  not a blocker for the synthetic scalar case.
- Verification: exact owner-block comparison and SHA-256 preservation checks pass.
  Legacy ALL PASS; pytest 109 passed; CI guard passed (22 files,
  BASE_REF=origin/main); README demo check matches; git diff --check clean.
  These results cover the unchanged software, not future P14 functionality.
  Existing D32/D34/D35 changes and prior handoff are preserved.
- Next: obtain explicit git authorization to version the existing decision
  package before a separately authorized hand-reference commit; code and tests
  follow only with their own write approval. External originals are needed for
  the deferred Yodwong/dryer full citations, not for recording this contract.
  AC8 reference/option work remains separate and unresolved.

## Local decision-package versioning (2026-10-29)

- Owner explicitly authorized local commits of the existing D32/D34/D35
  documentation package only, with no push. Earlier no-commit statements above
  and in the task files describe their task-time permissions and outcomes.
- Done on docs/p14-task-preparation, in order:
  - 4316753: D32, P13c task and matching handoff.
  - 17118ab: D34, P13d task and matching handoff.
  - f23d9f8: D35 amendments, SPEC, open AC8 positions, P13e task and handoff.
- D32/D34 index snapshots were matched against the previously recorded SHA-256
  values before committing. Shared files were staged without modifying their
  working-tree contents. No P14 preparation, source code, tests, registry or
  unrelated data files were included; no push or PR was performed.
- P14 task preparation and this current handoff remain local uncommitted work.
  Protected P14 reference/test writes and implementation are still unauthorized.
- Next: obtain explicit protected-reference write and reference-commit approval
  before creating the approved hand calculation files. A push or PR still needs
  its own authorization; the owner integrates. AC8 choices remain unresolved.
- P14 wording follow-up: blocked outputs have no computed-result evidence_status
  or origin; the report retains SPEC/D35's BACKLOG indication for unquantified
  items. Tolerances are tied to current rounded code constants; fixture times
  deliberately match the scenario endpoints as an accidental-consumption trap.
  The task now identifies the committed local decision baseline separately from
  its historical preparation base. No additional commit or push authorized.

## P14 reference-only approval (2026-10-29)

- Owner approved the reviewed reference document and stdlib script for the two
  named hand-reference paths, plus task/handoff status updates. Numeric zeros
  are compared numerically, not by string/repr; F display rounding is explicit.
- Authorized order: commit the task preparation/handoff first, then execute
  and separately commit the reference files after all mandatory checks.
  The second commit remains pending owner comparison against the chat text.
- No model implementation, other test-file writes, push, PR or additional
  protected-path changes. Prior no-write/no-commit notes are historical.
- Next: create and verify the hand references, report both hashes and output;
  await owner review before treating the reference commit as final.

## P14 hand-reference delivery (2026-10-29)

- Task preparation committed as f743e4d before creating either reference file.
- Created the approved reference document and stdlib Decimal script only.
  Script differences from the chat draft: F precision note, numeric-zero note,
  display-only formatting to print the approved reference rounding.
- Missing/status/measurement-perturbation requirements are documented, not
  implemented in the arithmetic script. D35 section 2 at f23d9f8 is the precise
  reference for the unquantified-item BACKLOG indication.
- Verification is to run after this last edit: script and independent numeric
  zero/display assertions; legacy suite; pytest; CI guard with origin/main;
  README demo; working-tree and staged diff checks. Report actual results in
  the delivery, not as evidence of future model functionality.
- Reference commit remains pending owner comparison. No source/model changes,
  other test edits, constant changes, push or PR. Next: owner review of hashes,
  script output and files before separate implementation approval.

## P14 reference acceptance (owner chat, 2026-10-29)

- Owner completed comparison of both reference files with the approved chat text
  and accepted 80fb225 as final for the reference-only scope. This supersedes
  the pending-review notes above; no full-chain or plant-validation claim follows.
- Prior execution evidence: reference script and numeric zero/display checks
  passed; legacy ALL PASS; pytest 109 passed; CI guard with BASE_REF=origin/main
  passed; README demo matched; working-tree and staged diff checks were clean.
- Owner's remote verification of D35 section 2 remains outstanding until
  separately authorized publication. No push or PR has been authorized.
- Future P14 commit messages use the prefix `P14:`. Do not amend existing commits.
- Next: present the concrete implementation scope in chat before any code/test
  write: registry-only ParamSet plus separate immutable scenario inputs,
  models/ledger.py, models/static_map.py, SPEC-reserved test_20 and test_40
  (recheck availability). Include typed missing-result semantics and the
  section-8 minimal measurement fixture without a tautological wrapper.
- Implementation, protected test writes and further commits require separate
  approval. Reference files, registry and constants remain unchanged.

## P14 implementation approval and delivery (2026-10-29)

- Owner approved the model files, test_20/test_40, task/handoff and validation log,
  with K1-K4: distinct input-domain/D31 cause codes, enum dependency causes,
  explicit open full-chain AC1, and nonfinite/type checks as data integrity.
  Zero remains valid. Scenario resides in static_map.py, not the registry adapter.
- Two local commits authorized: additive implementation first, independent
  focused tests second. Each commit must pass all mandatory checks; no push/PR.
- Implementation adds frozen registry capture, five scalar quantities and central
  computed/blocked ledger reporting. Full report retains unresolved/conditional
  items; no loss residual, RTE, hidden defaults or constant changes.
- The scalar path has no measurement boundary. Report that limit honestly;
  no fake production fixture argument or discarded-fixture perturbation claim.
- Next: verify implementation baseline, then add independent tests and report
  actual per-commit gates and diffs for owner review. References remain unchanged.

## P14 bounded test delivery (2026-10-29)

- Implementation commit 887b8c9 is independently suite-green before/after commit:
  legacy ALL PASS, pytest 109 passed, BASE_REF=origin/main guard passed, README
  matches, diff checks clean.
- Added only test_20_static_map.py and test_40_static_ledger.py: 28 focused cases
  pass against committed hand literals, numeric zeros, missing/domain/sign cause
  codes, immutable requested snapshots, status/bands, inventory and accounting.
- Bounded case verified, full-chain AC1 remains open. AC8 also remains open.
  Measurement fixture trap and architecture are checked; actual measurement
  data-path perturbation is not exercised because no such boundary exists.
- Run all final gates at the test commit and deliver both diffs/hashes to owner.
  No push/PR, reference changes or constants/registry changes. Next: owner final
  text/numeric review, not automatic scope expansion or full M1 acceptance.

## P14 W1-W4 follow-up (owner chat, 2026-10-29)

- Four commits authorized, separately suite-green before/after, no amend/push:
  A a4da7cf test-setup only (restored registry fixtures, assertions unchanged);
  B e92459c public ParamSet creation restricted to from_registry;
  C 03608e0 existing D31 signed classification, no new physics limit;
  D regressions and these W3/W4 limits. A/B/C each pass all 137 tests.
- W1 is an API guarantee, not a security boundary. Python internals can be
  deliberately bypassed; individual Param replacements remain possible.
  No public ParamSet injection path remains. Registry/constants unchanged.
- W3 accepted for the current chain: metadata merging is linear only;
  aggregation does not generally detect parent/child double booking.
  Reassess before P15 grouping/netting; no general-infrastructure claim.
- W4 architecture tripwire is deliberately bound to current code structure.
  Deferred obligation: when a real measurement-access path appears in P15/P16
  or loader integration, run the defined no/present/varied measurement tests
  with fixed scenarios. Do not retain the tripwire as a substitute.
- Next: deliver complete git-show diffs, regression outputs and per-commit gates
  for owner final review. Full-chain AC1/AC8 remain open. No further building
  or scope expansion before that review.

## P14 infrastructure corrections: red checkpoint (2026-10-29)

- Owner approved test preparation, then red regressions shown before code commit E,
  then separate regression/documentation commit F; no amend/push.
- Preparation cb6cda2 removes the false assertion that a one-item bounded report
  is valid. Negative signed storage remains checked as Computed with value -1.
  Mandatory gates before/after: legacy ALL PASS, 148 pytest passed, guard and
  README check passed.
- Uncommitted regressions cover missing required items, negative-result status
  definition errors and complete/order-independent aggregate blockers.
- Red outputs delivered: 7 failures, existing 148 tests pass. Owner clarified
  successful sums remain numeric, not Computed; no metadata merge is authorized.
- E 33a476a fixes report completeness, status short-circuit and aggregate cause
  preservation. Before/after gates: legacy ALL PASS, 155 pytest passed, guard,
  README and diff checks pass. Both checks include uncommitted regression tests
  and this HANDOFF checkpoint; E itself contains ledger.py only.
- D31 inventory audit closed: the sole signed inventory item is storage change;
  all other 17 items are nonnegative. Explicit regression mapping belongs to F.
- F adds the full status matrix, canonical requiredness, optional-item coverage,
  signed numeric sums, stable aggregate identity, shared-cause deduplication and
  explicit D31 mapping, plus task/validation/handoff evidence.
- P15 decision deferred: whether mixed SIGNED/NONNEGATIVE aggregates should be
  rejected. Blocked synthetic items currently use any-SIGNED; W3/W4 unchanged.
- Next: deliver full git-show output of preparation/E/F and green gates for
  owner final review. Full-chain AC1/AC8 remain open. No push or final acceptance.

## P14 deep-dive findings and next decisions (owner chat, 2026-10-29)

No code changes authorized by this note. Owner asked that this handoff preserve
the recent adversarial review for the next agent/session. Current HEAD at review:
2f33898; branch docs/p14-task-preparation; tracked worktree was clean.

### Confirmed test gaps and evidence

- Mutation evidence was rerun on an unmutated temporary copy containing src,
  tests and pyproject.toml. Baseline: 168 passed, pytest exit 0; all 168
  collected test IDs matched the repository. No conftest.py exists.
- Positive controls in that same harness: M3 (hardcoded standby time) and M8
  (HHV in place of LHV) each failed 1 test, exit 1.
- Full-suite survivors, each 168 passed / exit 0: M1 hardcoded operating_time_s
  in Faraday formula; M2 hardcoded operating_time_s in operating-energy formula;
  M4 removed negative registry-parameter gate; M5 removed result.item.required
  handling; M6 removed aggregate finite check; M14 removed Report scope check.
  Logs were under /tmp/p14_mut5_logs and are temporary, not repository evidence.
  Mutants were hand-selected; this is not a completeness percentage.
- M1/M2 are genuine gaps: current perturbations never vary operating_time_s
  while numeric, so both formula paths can hardcode 2700 and pass. A missing-time
  test blocks before calculation and does not test the factor. No second complete
  reference scenario is required to close this specific gap.
- M6 is not equivalent: two finite Computed values of 1e308 can be built through
  the public helper; aggregation currently raises on inf, whereas removing its
  check returns inf. Add a regression with a complete otherwise-valid bounded
  report and replace two compatible results with individually finite values.
- M5 exposed a missing required-extra validity check. The approved P14 report
  contract (task section "Report integrity contract") permits unknown extra
  items, requires them to remain visible, and makes a required Blocked extra
  invalidate; an optional Blocked extra remains visible without invalidating.
  This contract supersedes the earlier open wording.
- M4 and M14 need isolated tests: negative registry parameter must assert the
  exact invalid_input_domain code and parameter dependency through dependants;
  invalid Report scope must be tested with complete results so completeness does
  not mask the scope guard.
- Do not claim a complete transitive import audit: text search found no other
  importers, but did not prove dynamic/transitive access. This is unnecessary for
  the mutation conclusion because the full test suite was run.

### Further review findings

- The P14 dependency contract (task lines 138-144) names Faraday constant for
  H2 amount and molar mass/LHV for LHV transport. Current Item dependencies and
  output provenance do not carry these constants. Treat this as a likely
  traceability/contract gap, not yet a settled field-design decision. Formula
  dependency, provenance (name/value/unit/numerical basis), and evidence/
  uncertainty policy are separate questions. F's displayed value is rounded;
  molar mass is conventional; LHV is a rounded thermochemical basis. Do not
  invent D26 statuses or put constants into Item.dependencies without clarifying
  that field's namespace/semantics.
- Current Report checks required-key presence but does not check canonical
  Item definitions or duplicate keys. Reproduced: known operating-energy item
  changed to SIGNED permits -1 as Computed in a non-INVALID report; removing
  hydrogen_mass dependencies is accepted; duplicate Computed/Blocked entries
  under one key make lookup/aggregation depend on result order. Proposed fix:
  reject duplicate keys and reject known-key Item definitions that differ from
  ITEMS; do not silently normalize. The later P14 report contract permits
  unknown synthetic items and defines how required and optional Blocked extras
  affect validity; no further decision is open on that point.
- Eta=98 and n_cells=120.5 currently produce a non-INVALID H2 result (~1321.83
  mol); eta=-0.98 is blocked as invalid_input_domain. Nominal-value definition
  checks are distinct from uncertainty distributions: an unbounded MC draw does
  not make an invalid nominal value valid. Owner must decide exception versus
  blocking/INVALID, preferably at the EL-specific consumer; for cell count test
  the value is positive/integral (120.0 may be valid), not Python int type.
  Do not invent bounds for scenario current/power (e.g. 80 A) without a source.
  This nominal EL-domain question was subsequently decided in D36; its
  implementation remains separately authorized.
- LHV relative model deviation from the independent hand basis is about
  -6.6676 ppm with a symmetric +/-7 ppm tolerance around the reference. Remaining
  headroom is about 0.3324 ppm further negative and 13.6676 ppm positive (~41x).
  Do not recenter tolerance on code constants or change approved tolerance.
- Float 1.575 and 0.01 are not exactly binary-representable; equality with Python
  literals only demonstrates identical float rounding.
- Lower priority/unresolved: direct vs transitive input metadata semantics in
  Computed; Scenario subclass fields may accumulate ignored causes; Decimal and
  numpy.int64 are rejected while numpy.float64 works; passing a string to
  ParamSet.from_registry iterates characters; Item.dependencies mixes actual
  keys and unresolved-basis labels; public Computed construction can forge
  value/status/origin. These are not authorized fixes in the current block.
- Underflow to Computed(0.0) is not a contract violation: task requires type
  distinction from Blocked, not preservation of arbitrarily small nonzero values.
- SIMULATED/data-path limit is already disclosed in report limits. A possible
  D26 clarification (pure scalar independence by construction; perturbation
  test when a measurement boundary exists) is a separate owner decision.
- Tolerance error budget is directional: a positive implementation error can
  compensate the negative code-constant offset. Ratio perturbations test
  dependency only, not a wrong fixed factor; the hand reference remains needed.

### Suggested next sequence; no implementation approval implied

1. The P14 task decides the Report contract for unknown extras; D36 decides
   nominal EL parameter domains. Constants dependency/provenance semantics
   remain an owner decision.
2. If approved, add only scoped regressions for operating_time_s x2 and zero,
   negative registry cause propagation, direct invalid scope, and finite-sum
   overflow. These tests are expected to pass on correct current code; verify
   their value by showing the relevant mutants survive before and fail after.
   Assertions must isolate each cause; no unrelated formula/tolerance changes.
3. Keep the mutation evidence exact and reproducible: codebase, exact patch,
   same config and collected test IDs, baseline, positive control, per-run log
   and actual pytest exit code. No new mutation framework or CI requirement is
   implied.
4. Resolve Report canonical-item/duplicate-key policy and constants traceability
   design before implementing either. Keep reference values, registry and
   constants unchanged absent separate approval.

No package-A changes, new reference scenario, CI tooling, D26/SPEC amendment or
package-B decision is authorized by this handoff. Full-chain AC1/AC8 and final
P14 owner acceptance remain open. No push/PR.

## P14 verification and Report contract fix (owner chat, 2026-10-29)

### Done
- b4bb21f: deep-dive section above committed unchanged (docs only).
- a23c1e9: Report rejects duplicate keys and noncanonical known items
  (contract and rule-4 exception in the P14 task). Regressions and docs follow
  in the next P14: commit (16 new cases). Red before a23c1e9: 15 DID NOT RAISE
  = 14 new cases + the changed requiredness test; 2 new cases pin behavior.
- Review corrections (no amend): 337c45e message miscounts and wrongly says the
  canonical-check mutant survives without the new regressions (the changed
  requiredness test kills it). The old session gate helper exited 0 on failure;
  corrected helper verified (negative control exit 1) and fresh gates at
  b4bb21f, a23c1e9, 337c45e all pass. Details in docs/04.
- Prior check closed: sum_compatible() rejects duplicate summand keys;
  test_sum_roles_units_duplicate_and_blocking guards it (mutant: 1 failed,
  pytest exit 1). This is separate from Report-entry duplicates (now fixed).
- Prior check closed: weakest(()) and weakest(("OWNER_DECISION",)) raise the
  D26 ValueError, guarded by test_37 (mutant: 1 failed, exit 1). computed(...,
  statuses=()) raises the same error before the sign check, but no test pins it
  at computed() level: a silent "GUESS" default survives (168 passed, exit 0).
  Test gap for package A, not a code defect.
- Deep-dive survivor M5 is now killed by the unknown-extra regression.

### Evidence status (do not overstate)
- The deep-dive mutation figures (/tmp/p14_mut5_logs) come from a local run
  report; full logs were not given to an independent reviewer and are temporary.
  Earlier pipeline exit codes (pytest | tail) must not be read as pytest exit
  codes. All exit codes in this section were captured from pytest directly.
  One mutation script in this session first printed tail's exit code; it was
  rerun with the real pytest exit before any result was recorded.

### Unchanged P14 base (verified against files, not copied from chat)
- Scenario: 2100 W AC operation, 8 A DC stack current, 2700 s; separately
  20 W AC standby over 1800 s. Constant over each period; non-overlap is a
  stated assumption, not checked by code (scenario holds durations only).
- el.n_cells 120 and el.faradaic_efficiency 0.98, both GUESS, u 0.05 / 0.03,
  input classification only; no output uncertainty propagation.
- Constants, hand reference vs model code: F 96485.33212 vs 96485.332 C/mol;
  M_H2 0.002016 vs 2.016e-3 kg/mol; LHV 119.96/3.6 vs 33.322 kWh/kg.
  References: tests/reference/hand/p14_static_ledger.md, p14_hand_calc.py.
  SOURCES migration of constants does not block the accepted reference.
- Already in place: ParamSet only via from_registry() (API guarantee, not a
  security boundary; scenario inputs separate). computed() distinguishes SIGNED
  and NONNEGATIVE; 18 inventory items, only storage_change_kWh SIGNED;
  nonfinite/wrong-type values are data-integrity errors. Blocked results carry
  no value and no computed origin; successful sums stay numeric.

### Next (each needs its own write approval)
- Package A, independent of package B decisions: regressions for
  operating_time_s x2 and zero (M1/M2), negative registry parameter cause (M4),
  direct invalid scope with complete results (M14), finite-sum overflow (M6),
  and computed() with empty / OWNER_DECISION-only statuses. Show each relevant
  mutant surviving before and failing after.
- Package B: nominal eta/cell-count behavior at the EL consumer is decided by
  D36; constants dependency/provenance semantics and public Computed
  construction still await owner decisions. P15 mixed-sign aggregation remains
  deferred.
- Full-chain AC1/AC8 and final P14 owner acceptance remain open. No push/PR.

## P14 type-identical canonical items (owner chat, 2026-10-29)

- 4461dc8: docs-only corrections of counts, mutation statement and gate helper.
- ebff573: canonical Report check compares recursively with identical types
  (str-based enums and 1 == True no longer pass). Code only; existing suite green.
- Next commit: four retyped-item regressions plus task/docs. Red before ebff573
  (4 DID NOT RAISE, exit 1); mutant reverting to == survives without them
  (184 passed, exit 0) and fails with them (4 failed, exit 1).
- Gate helper versioning is owner-approved. `tools/run_local_gates.py` is a
  local Python development helper, explicitly separate from CI; it preserves
  per-check logs outside the repository and exits nonzero on any failed gate.
- Package A tests delivered in bcb5cd4 (test-only): operating-time x2/zero,
  negative registry cause propagation, invalid direct scope, finite-sum
  overflow, empty and OWNER_DECISION-only computed statuses, ITEMS key
  uniqueness. Mutants ran in temporary copies with direct pytest exit codes;
  results and the lower-bound caveat are in docs/04. Ratio tolerance 1e-14 is
  dependency evidence only. Gates before/after: 198 pytest, legacy ALL PASS,
  guard, README and diff checks exit 0.
- Next: resolve Package B decisions (nominal EL parameter domain, constants
  provenance semantics, public Computed construction) before implementation.
  Full-chain AC1/AC8 and final P14 acceptance remain open. No push.

## P14 reproducible Package A mutation runner (2026-10-30)

- Added `tools/run_package_a_mutants.py` within the agreed tools/docs/HANDOFF
  scope. The initial runner ran seven mutations, including the inventory-
  uniqueness mutation later moved behind an opt-in flag, in a temporary
  source/test copy; each selector must first pass the exact expected baseline
  count. A kill requires pytest exit 1 and exactly the expected failed cases,
  with no errors, skips, or other outcomes. The runner now parses exactly one
  complete pytest summary, self-checks with actual passing/failing/no-selection/
  empty-suite pytest output, and asserts the exact `no_selected_tests` reason.
  No tests or production files were changed.
- Before hardening, seven baseline selectors passed (2, 2, 1, 1, 1, 4, 1
  cases); all seven mutants failed with those exact counts and pytest exit 1.
  This prior run is not evidence for the hardened runner. The
  six core source replacements cite bfdaf38; inventory uniqueness uses the
  later explicit opt-in scope agreement, not bfdaf38.
  The external run manifest records interpreter, pytest, HEAD, source hashes,
  anchors, selectors, outcomes and exit codes. Logs and manifest are temporary.
  This remains a targeted lower bound, not a full-suite mutation result.
- Reproduce with `.venv/bin/python tools/run_package_a_mutants.py --log-dir
  /tmp/verlustmappe-p14-package-a-mutants`. Hardened runner rerun passed all
  parser self-checks and all seven mutants (manifest status passed; exact
  outcomes and pytest exits recorded in docs/04).
- Legacy interpreter incident: recent `python3 tests/run_all.py` and
  `.venv/bin/python tests/run_all.py` attempts returned 12 for missing
  NumPy/Pandas in test children; the direct README check also failed to import
  NumPy. Pytest 198, CI guard, diff checks, and mutation runner passed. A
  diagnostic `runpy` run passed legacy and README checks, but does not replace
  the documented invocations. At that point the cause was unresolved:
  `run_all.py` uses `sys.executable`, and instrumenting a run with temporary
  PYTHONPATH changed the environment. The later canonical PATH-prefixed gate
  run passed; see the review-correction section below. The exact cause of the
  earlier parallel venv import failures remains unverified.
- Decision D36 now records the nominal EL parameter domains. Constants
  provenance semantics and public `Computed` construction remain open.
- Runner and validation evidence were committed in `c7032b0`; the Handoff
  correction is committed in `03f662e`. No push or PR has been made.
- Next: resolve remaining Package B decisions. Full-chain AC1/AC8 and final
  P14 acceptance remain open.

## P14 mutation-runner review corrections (2026-10-30)

- The runner now excludes `M_items_key_uniqueness` from its default Package A
  run. Use `--include-inventory-uniqueness` to run it explicitly. The earlier
  seven-mutation default-run evidence above predates this scope correction;
  a new default run passed six mutations, and a separate opt-in run passed all
  seven.
- The inventory-uniqueness mutation's manifest provenance now cites the
  2026-10-30 owner-chat opt-in agreement, not bfdaf38. All pytest subprocesses
  set `PYTHONDONTWRITEBYTECODE=1`, and copied source trees exclude
  `__pycache__`.
- Parser self-checks now assert `summary_invalid` for duplicate categories.
  Direct `_validate_mutant` self-checks require the exact rejection reasons for
  exit 0, `failed` plus `error`, too many/few failures, and no selected tests.
- Pass/fail self-check fixtures use distinct module filenames. A same-file
  rewrite could reuse timestamp-based bytecode and made the failing fixture
  appear to pass; the separate-file correction was rerun successfully.
- `_source_hashes()` resolves `__file__` before making it relative to the repo
  root, avoiding a relative-path `ValueError`.
- Canonical sequential gates with `.venv/bin` first on PATH and
  `PYTHONDONTWRITEBYTECODE=1` all passed: legacy `ALL PASS`, pytest 198,
  CI guard, README check, diff checks, and both mutation runs (six default,
  seven with opt-in). This explains the red naked-`python3`/`pytest` runs:
  those commands resolved outside the project venv or were absent from PATH.
  The earlier parallel `.venv` import failures were not reproduced in the
  canonical invocation; their exact cause remains unverified. Final gate logs
  and both manifests are at `/tmp/verlustmappe-p14-canonical-final-20261030`.
- Runner and evidence documentation were committed as `c7032b0`
  (`P14: harden Package A mutation evidence`); no push or PR was made.
- Next: review the committed runner evidence and continue with the separately
  pending Package B decisions. Full-chain AC1/AC8 and final P14 acceptance
  remain open.

## D36 nominal EL domain implementation (2026-10-30)

- Done: `static_map.calculate()` enforces the D36 nominal domains before the
  hydrogen calculation. Invalid finite values block the hydrogen chain with
  `INVALID_INPUT_DOMAIN` and the relevant parameter key; electrical outputs
  remain visible. Integrity errors remain `ValueError`.
- Tests: red-first focused run reproduced four failures before the fix; after
  the fix, all 25 focused cases passed. The full pytest suite reports 223
  passed. The registry, uncertainties, constants and hand references are
  unchanged.
- Commits: implementation `18de0e2`; separate tests `593b6b9`.
- Mutation evidence: M4's anchor remains intact. The D36 mutation is in the
  default run; seven default pairs and eight pairs with inventory uniqueness
  opt-in passed. Logs and manifests are recorded in `docs/04_validation_log.md`.
- Decisions still needed: constants provenance semantics and public
  `Computed` construction. Next work should continue with those Package B
  contracts, independently of this completed D36 implementation.
- Full-chain AC1/AC8 and final P14 acceptance remain open. No push or PR was
  made.
