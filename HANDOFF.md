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
- P09 (SPEC translation of D20-D26, D29, D30 plus new D31 sign rule) is executed on branch
  task/p09-spec-from-gates, awaiting merge; the SPEC now matches D20-D31. The register column
  "u not assessed" and its enforcement test are the code task P09b (after P09, before P10).
- Next: merge P09, then P09b, then M1 (P10 hand references, P11 port with the params
  adapter, P12 ledger and gates).
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
- Next: see the order above (P09, P09b, M1).
  

Later:
- D9 (a)-(d) done in P05 (test_20-26 stay reserved by the SPEC).
- M1 per `ROADMAP.md`.
- Backlog: migrate the 87 registry citations into complete `SOURCES.md` entries.
