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

## 2026-10-27 – Compressor and air system, workbook v2 (D11–D15, owner decisions)

Source: owner workbook `Compressor_System_Specs_Master_v2.xlsx`, SHA-256
`0aa9f8ed0618d9bfd61123055674418969e0d7479d63b962afb18944cfd942ae`. Task: P05.
D10 stays reserved for the battery conflict (HANDOFF).

- **D11 – comp.* is marked REJECTED, not deleted (authorization to execute, task P05).
  Status: DECIDED.**
  The six keys `comp.pressure_ratio`, `comp.stroke_volume_cm3`, `comp.max_cycles_per_min`,
  `comp.min_suction_bar`, `comp.overall_efficiency`, `comp.specific_energy_kWh_per_Nm3`
  describe a Maximator DLE 30-2 (wrong device basis, not an uncertainty). The installed
  system is two-stage: HULC with DLE15-H2 (stage 1, 35 -> 140 barg) plus DLE 30-H2
  (stage 2; ratio 1:30, 120 cycles/min, minimum suction 15 bar). They get the status
  `REJECTED` ("legacy-only, device basis wrong (DLE 30-2)") and stay with their values
  ONLY so the frozen legacy-1.0 chain reproduces; the new core never reads them.
  Deletion happens at the legacy teardown (M6). Known consequence: legacy Monte-Carlo runs
  still sample the rejected values. D2 exception, text and ordering only, no physics:
  `reporting/make_register.py` (add the new status labels to `ORDER`; correct the
  hard-coded "weakest number 1" text). `devices/booster.py` and `balance/*` stay frozen.
  The README demo gets a note: its compressor value is a rejected legacy assumption.
  Guard until the adapter `models/params.py` exists: a text test only (weak, finds
  literal `comp.` / `REJECTED` reads under `models/`, `sim/`, `scenarios/`, `calibration/`).
  Supersedes D1 (2026-10-21): the question "which efficiency as INPUT" lapses; eta_iso,el
  becomes a derived quantity, eta = W_iso / E_el.
- **D12 – Working pressures. Status: DECIDED.**
  `stor.p_work_barg = 200` stays: it is the legacy-1.0 operating pressure used by the
  frozen `balance/d_loss_map.py`. For the new core the project case is
  `sys.p_h2_out_project_barg = 300` (OWNER_DECISION). `hulc.tank_limit_bar` is NOT
  registered separately; it refers to this key (workbook status Observed, tank does not
  exceed ~300 bar in practice). Different meaning, different key, both documented.
- **D13 – Air consumption of the HULC. Status: DECIDED.**
  Primary L1 model = the manufacturer air-consumption CURVE as a function of H2 flow
  (TDS p.2), evaluated at the plant operating point. The operating point is OPEN
  (continuous vs intermittent operation, chart conditions, series addition of both
  curves unconfirmed). 14.6 Nm3/Nm3 is the value at module maximum flow (83.3 NL/min), NOT a
  bound: at 10 NL/min (one EL2.1) the same readings give about 50. Path B (4.59 – 6.30,
  geometry only) is a physical lower bound. Nothing is registered until the manufacturer
  answer or an L3 readout (SIGMA CONTROL 2 load hours + kWh counter, HULC stroke counters,
  EL production, same period). Then the curve points are registered, status
  "Datasheet (chart reading)", conditions open. Revocation: manufacturer answer or L3 data.
- **D14 – D3 stage 1, Kaeser energy in the RTE. Status: DECIDED.**
  Boundary confirmed by the owner: the Kaeser supplies only the HULC and the four Rotex.
  Rules: variable air energy proportional to air quantity (HULC / Rotex 1–4 / other);
  READY standby and network leakage as separate items; leakage belongs to the distribution
  block, not to the HULC; standby by air draw, else equal split (assumption). Supersedes
  workbook row `energy.allocation_rule` (pending). Stage 1 yields NO RTE number (Kaeser
  input power Open; 6.2 kW is a dealer value). `balance/*` unchanged.
- **D15 – Status vocabulary, partial D5. Status: DECIDED for these labels only.**
  New: `OWNER_DECISION` (`sys.n_rotex`, `sys.p_h2_out_project_barg`),
  `DATASHEET_SECONDARY` (`kaeser.p_package_dealer_kw`, 6.2 kW at 11 bar vs 0.67 m3/min at
  10 bar; conflict in the SOURCES transferability line), `REJECTED` (D11). Other
  `Observed` rows stay unregistered (BACKLOG). Gauge pressures use `barg` in key names.
  Registry scope is an exact list of workbook statuses: `Datasheet`, `Nameplate`,
  `Datasheet (base type)` (transferred from DLE15/DLE30 catalog, said in the SOURCES
  transferability line), `Project decision`, `Dealer`. Everything else (Calculated*,
  Observed, Open, Assumption, "(conflicting)", "(scope to confirm)", "(identity assumed)",
  "(chart reading)") is workbook-only; `sim/` computes derived values itself.
- **Tests.** The first new test file is `test_30` instead of the planned `test_20`,
  because the SPEC reserves test_20–26 for AC1–AC8. New suites are pytest style; D9 (a)–(d)
  land in the same owner commit. The workbook is a hash-pinned fixture; editing it
  triggers the full re-review. The manual mutation check is not named `test_*`.- **D16 – ci_guard upgrade and C11/C13 text cleanup. Status: DECIDED (owner, 2026-10-28).**
  The D1 authorization for the registry text cleanup lapsed with D11; it is re-authorized
  here under D11. (a) `tools/ci_guard.py` compares parsed registry entries (key, value,
  unit, uncertainty, status) instead of file text, removing the false alarm for text-only
  registry edits. (b) The superseded comment block arguing 0.014 from "78.4 + 4.6 kWh" is
  DELETED (the value is REJECTED per D11; history lives in D11 and docs/94). (c) The
  remaining src/ SMA wording (registry comment `inv_pv.eta_euro`, `pv_measured.py`,
  `pv_inverter.py`, `live_feed.py`, `loaders/grafana.py`) is aligned with the P02b
  attribution wording. Text-only, no behavior change. Execution in task P04, one PR
  containing the ci_guard change and the registry text change together, so the upgraded
  guard applies within the same diff. The hard-coded items 4 and 4b in `make_register.py`
  ("weakest numbers" text) are NOT part of D16; they belong to the extended P02b task and
  need their own extension of the D11 exception.

- **D17 – SMA scrub in the registry (amends D16c). Status: DECIDED (owner, 2026-10-28).**
  SMA is out of the system boundary and out of every evidence role (SPEC, D4, D7). "Removed"
  means: physically removed (legacy ~184 kWp building array), textually isolated, kept only
  as a labelled legacy reference. (c) is replaced: `registry.py` carries NO SMA/Deye
  reference. `inv_pv.eta_euro` keeps the PRELIM literature value ("typical Euro efficiency
  97-98 % for modern string inverters; no F8-specific datasheet yet (D6 open)"); the
  comments and sources at the SMA mentions (inverter block comment, `pv.capture_ratio`
  note, `meas.power_rel_unc`) are reworded without SMA. The 0.9719 22-day cross-check
  remains ONLY in docs/04, attributed to the removed legacy building array, never F8
  evidence. The src/ docstrings (`pv_measured.py`, `pv_inverter.py`, `pv_prelim_channel.py`,
  `devices/__init__.py`, `live_feed.py`, `loaders/solis_live.py`) use the wording
  "legacy building array, not F8 evidence". D16 named `loaders/grafana.py` in error; it has
  no SMA text. NOT part of this decision: deleting `test_08b`, `pv_retro`, `results/pv_*`
  (frozen legacy regression, D2, rule 4); they fall with the legacy teardown in M6.
  Text-only, no behavior change; executed in P04.

- **D18 - C11 remainder: booster.py docstring and warning text. Status: DECIDED (owner, 2026-10-28).**
  The `devices/booster.py` module docstring drops the paragraph arguing 0.014 from
  "78.4 + 4.6 kWh" and the eta_CSU = 54.5 % remark; it states instead that the registered
  value is REJECTED (D11, wrong device basis DLE 30-2) and is used ONLY so the frozen
  legacy-1.0 chain reproduces; see docs/94 C11. The real-gas note stays unchanged. The
  warning string becomes "compression energy = ideal work / REJECTED legacy efficiency
  (D11); meter the Kaeser (D14)". Text-only, no behavior change; covered by the D2 text
  exception. Executed in task P04, same PR as D16/D17.

- **D19 - make_register.py weakest-numbers list, items 4 and 4b. Status: DECIDED (owner, 2026-10-28).**
  The D11 text exception for `reporting/make_register.py` (ORDER and the "weakest number 1"
  line) is extended by the two further hard-coded lines of the "weakest numbers" section:
  item 4 (Solis PV-AC 0.966 datasheet vs 0.93-0.95 manual, no Euro efficiency published,
  D6 open) and item 4b (the F8 station id must be the API-verified value from the SolisCloud
  export; the digits are verified against that export before committing). No other
  generator text is touched. docs/02 is regenerated in the same commit and the diff is
  reviewed. Text-only. Executed in task P02b.
