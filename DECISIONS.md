# Plant and design decisions

Record human-approved choices that affect the plant model here. Do not use this file to
replace source evidence; source-backed values also need an entry in `SOURCES.md`.

## 2026-10-21 – Agent-governance bootstrap

- Added repository-level agent instructions and CI checks as described by the project
  owner.
- No plant configuration, registry value, uncertainty, or technical model decision was
  changed or approved in this change.

## 2026-10-23 – Governance migration (baseline commit d060c9b, tag legacy-1.0)

Baseline: the unmodified state at commit d060c9b, tagged `legacy-1.0` and verified
remotely on 2026-10-23 (refs/tags/legacy-1.0^{} resolves to the baseline commit).

- **D1 – Compressor efficiency: transferability to 35-bar suction. Status: OPEN.**
  Decision of 2026-10-21, recorded here: comp.overall_efficiency stays registered at
  0.03 ±40 % (GUESS); the registered value is not re-opened. Open: whether it transfers to
  the plant's own 35-bar suction. Rationale: Bovo IJHE 48 (2023) part 1, Tab. 3 (CSU),
  columns nominal / full power / half power, lists compression energies 60.28 / 56.36 /
  100.2 kWh for 33.22 Nm³, tank 40 -> 200 bar, booster fed at 10 bar (read in the
  full-text copy in the owner's library; SOURCES.md entry pending). Repo fill integral
  (isothermal_work_mol_integral), same window and volume: 2.406 kWh at 10-bar suction,
  1.149 kWh at 35 bar, 1.015 kWh at 40 bar. Implied eta (full / half / nominal):
  4.3 / 2.4 / 4.0 % at 10 bar, 2.0 / 1.1 / 1.9 % at 35 bar. The registered band
  0.018–0.042 overlaps the 35-bar range (0.011–0.020) only in 0.018–0.020. PROPOSAL
  (owner decides): specific energy as primary quantity, eta recomputed per suction
  pressure; requires measurement (Kaeser current + booster air consumption). Scope: the
  plant compresses with a two-stage HULC rack (owner workbook, UNVERIFIED-in-repo); ideal
  isothermal work is staging-independent, so the comparison stands. Authorization: a
  separate approved task may (a) delete the registry.py comment block arguing 0.014 from
  "78.4 + 4.6 kWh" (these figures do not appear in Tab. 3), (b) align the booster.py
  docstring and the ±50 % warning with the registered ±40 %, and (c) change
  tools/ci_guard.py to compare parsed registry entries (value, uncertainty, status)
  instead of file text, so that (a) needs no unrelated test change.
- **D2 – Legacy freeze and baseline tag. Status: DECIDED.**
  The files existing at tag `legacy-1.0` under `src/verlustmappe/` are frozen, EXCEPT
  `loaders/`; legacy physics is NOT patched. Loader and data corrections are allowed only
  if they change no physics parameter or limit, with the data state noted in the commit.
  Text-only edits (comments, docstrings, warning strings) inside the frozen scope are
  allowed only per approved task and change no behavior. The NEW core lives in
  `src/verlustmappe/models/`, `src/verlustmappe/sim/`, `src/verlustmappe/scenarios/` and
  `src/verlustmappe/calibration/` and is not part of the freeze; the Write-Scope
  discipline still applies. The new core must not import legacy modules, with ONE
  exception: the adapter `src/verlustmappe/models/params.py` may import
  `src/verlustmappe/registry.py` read-only; it copies the values into immutable per-run
  parameter objects and never writes back to the registry. Tests may import legacy code;
  the import rule applies to core modules. Enforcement of the freeze and of the import
  rule is planned as ci_guard checks (compare frozen files against the tag; allow exactly
  the one adapter import). The AC8 reference values are computed AT the tagged state, at
  points where the characteristic curves are clamped to legacy constants; the intended
  deviations (plug bar, standby missing in E_in, booster clipping, Route-2 guard) are
  documented in `docs/94_known_defects_legacy.md`. The older wording "M0-patched 1.0
  reference" (Rev. D concept, decision list) is superseded by this entry.
- **D3 – Compressed air in the RTE. Status: OPEN.**
  Counted proportionally inside the RTE or reported separately; until decided, the Kaeser
  energy line is reported separately and is not silently included in a single RTE value.
- **D3b – FC-side inverter discharge efficiency. Status: DECIDED (rule).**
  The PV-AC datasheet values do not cover the discharge path; it must be measured via the
  Solis channel. Until measured, it is never marked CALIBRATED or MEASURED.
- **D4 – First calibrated device (AC4). Status: OPEN.**
  Realistic candidate today: the FC TERMINAL characteristic from independent Regatron
  sweeps. F8-Solis becomes a candidate only once complete measured DC/AC inputs for the F8
  path exist. SMA legacy telemetry is never F8 evidence.
- **D5 – Status vocabulary. Status: OPEN (proposal below; owner decides).**
  Proposal: three separate fields. evidence_status: MEASURED > CALIBRATED > DATASHEET >
  DERIVED > PRELIM > ENVELOPE > GUESS > BACKLOG. observation_status: OBSERVED / NOT
  OBSERVED / MISSING (whether the quantity was captured in the period; NOT OBSERVED is not
  a quality value and not zero). result_origin: SIMULATED / RECONSTRUCTED / MEASURED
  (whether a reported number comes from simulation, reconstruction, or direct measurement).
  NAMEPLATE is a device description mapped to DATASHEET, not a separate evidence status.
  The final decision is recorded here before AC1/AC7 checks are implemented.
- **D6 – F8 inverter identity and S6 datasheet. Status: OPEN.**
  Current repo state (d060c9b README and registry): 2 × Solis S6-GR1P6K for F8.
  Primary evidence: the SolisCloud inverter metadata (library CSV, export 2026-10-08) lists
  exactly two inverters for station "F8_Fachada Leste", SN 1802060225250007 and
  1802060225250009, both model code 0206 (S6-GR1P6K family). The older owner note naming
  S5-EO1P5K-48 for F8 is contradicted by this metadata. Open: S6-GR1P6K datasheet; until
  then inv_pv.eta_pv_ac_peak stays BACKLOG.
- **D7 – SPEC rebuild and governance migration. Status: DECIDED.**
  SPEC.md is rebuilt per the accepted revision: system boundary (storage chain AC in -> AC
  out and island RTE; PV source F8, 28 × BYD455MGEK-36 = 12.74 kWp, vertical east facade;
  the SMA dataset 5.19 MWh / 22 days excluded); Layers 1/2/3 with step() in Layer 2; frozen
  reference (AC8) with tolerances (bars ±2 %, RTE ±0.5 percentage points); AC1–AC8 with a
  traceability table (AC -> layer -> test file -> reference source); status per AC in
  docs/04_validation_log.md; bridge invariants (L2 reproduces the L1 map in stationary
  windows; independently computed losses sum to E_in − E_out − ΔE_storage). CODEOWNERS
  gains /SPEC.md, /ROADMAP.md, /tools/ci_guard.py and /calibration/overlays/, matching the
  protected-paths list in AGENTS.md. AGENTS.md is replaced accordingly (SPEC primacy,
  legacy freeze per D2 with the adapter exception, evidence report format, branch rule).
  This entry is the DECISIONS authorization required for changing SPEC.md and AGENTS.md.
- **D8 – Tank instrumentation deferred. Status: DECIDED.**
  For the 2.0 core, tank gas temperature and tank pressure are SIMULATED state variables
  (computed from n, V, Z, T); no Pt100 and no pressure-sensor-based calibration or
  validation of the tank happens in this phase. No sensor-related registry key is deleted;
  the sensor keys keep their current status and the DCT 541 remains installed but unused
  for model calibration. Route 2 stays legacy-only in hydrogen/route2_tank_pv.py; the tank
  STATE (n, p, T) remains a core model variable of the new tank model. Consequence,
  accepted and stated per path: without a measured counter-path the H2 balance in 2.0 is
  model-supported. EL production labeling ends via stack-current export or a water meter;
  FC consumption labeling ends via FC stack current (Faraday), via tank instrumentation
  retrofit (re-enabling the Route-2 measured path), or via an H2 flow meter on the FC
  side.
- **D9 – Test-runner policy for new tests. Status: DECIDED.**
  New tests (test_20 onward) live at the top level of tests/, are written in pytest style,
  and are collected by pytest; CI runs `pytest -q` with zero collected tests treated as
  failure (pytest exits 5 in that case). All of the following land in ONE owner-approved
  commit together with the first new test file (planned: tests/test_20_static_map.py in
  M1), not earlier; until then CI stays green with run_all, ci_guard and the README check:
  (a) pyproject.toml declares pytest as a dependency, and the fixed package list in the
  ci.yml install step (`pip install numpy pandas scipy matplotlib requests`) gains
  `pytest`, because CI installs from that list, not from pyproject.toml; (b) ci.yml gains
  a `pytest -q` step; (c) tests/run_all.py is restricted to the legacy regression files
  test_01 to test_12 by explicit name (it currently globs tests/test_*.py, which would
  execute new pytest-style files as scripts and pass them silently - docs/94, C12);
  (d) tools/ci_guard.py keeps its top-level scan, which still covers test_20 and later;
  AGENTS.md Commands are updated accordingly.

## Pending decisions

- POA source for the vertical east facade (before M3 PV scenarios).
- Kaeser metering: approve an energy meter on the Kaeser plus booster air-consumption
  measurement (unblocks D1).
- Tank instrumentation retrofit: whether and when (Pt100 status: README says planned, not
  purchased; deferred per D8).
- tools/fuelcell_analyzer.html: archive to docs/ or delete.
- GitHub branch protection: owner configures it (CODEOWNERS enforce only after that).
