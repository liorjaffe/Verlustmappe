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

- **D1 – Compressor: comp.overall_efficiency and suction-pressure assumption. Status: OPEN.**
  This entry records the decision of 2026-10-21 that previously existed only as a registry
  annotation: registered baseline 0.03 ±40 % (GUESS). The registered value is not re-opened.
  The open part is transferability at the plant's own 35-bar suction. Bovo IJHE 48 (2023)
  part 1, Tab. 3 (CSU) reports compression energies 56.36 kWh (full load), 100.2 kWh (half
  load), 60.28 kWh (nominal) for 33.22 Nm³, tank 40 → 200 bar, booster fed at 10 bar.
  Recomputed with the repo fill integral (isothermal_work_mol_integral) for the same window
  and 33.22 Nm³: 2.406 kWh (suction 10 bar), 1.149 kWh (suction 35 bar), 1.015 kWh
  (suction 40 bar). These imply η = 4.3/2.4/4.0 % at 10-bar suction and 2.0/1.1/1.9 % at
  35-bar suction. The registered band 0.018–0.042 overlaps the 35-bar range (0.011–0.020)
  only in 0.018–0.020; a sensitivity band on the registered value alone would be
  systematically shifted high. PROPOSAL (owner decides): specific energy as primary
  quantity, η recomputed per suction pressure. Requires measurement (Kaeser current +
  booster air consumption). Note on the as-built plant: the installed compression is the
  HULC rack, two-stage (stage 1 DLE 15-2, inlet <=35 bar → 140 bar; stage 2 DLE 30-2,
  140 bar → 400 bar; source: Compressor_System_Specs_Master.xlsx). The single-stage Bovo
  analogue is an approximation; the two-stage ideal work for 35 → 200 bar is approx.
  1.044 kWh (implying η 1.85/1.04/1.73 %), same conclusion. Related cleanup, executed only
  as an approved task under this decision: delete the unsupported comment block
  ("78.4 + 4.6 kWh" → 0.014) in registry.py; align the booster.py docstring (0.014) and
  the ±50 % warning with the registered ±40 %.
- **D2 – Legacy freeze and baseline tag. Status: DECIDED.**
  The unmodified tagged state is the AC8 baseline; legacy physics is NOT patched. Everything
  under `src/verlustmappe/` is frozen except `loaders/`. Loader and data corrections are
  allowed only if they change no physics parameter or limit, with the data state noted in
  the commit. Exception: text-only edits (comments, docstrings, warning strings) inside the
  frozen scope are allowed only per approved task and change no behavior (this is what D1's
  cleanup uses). The AC8 reference values are computed AT the tagged state, at points where
  the characteristic curves are clamped to legacy constants; the intended deviations (plug
  bar, standby missing in E_in, booster clipping, Route-2 guard) are documented in
  `docs/94_known_defects_legacy.md`. The older wording "M0-patched 1.0 reference" (Rev. D
  concept, decision list) is superseded by this entry.
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
  SPEC.md is rebuilt per the accepted revision: system boundary (storage chain AC in → AC
  out and island RTE; PV source F8, 28 × BYD455MGEK-36 = 12.74 kWp, vertical east facade;
  the SMA dataset 5.19 MWh / 22 days excluded); Layers 1/2/3 with step() in Layer 2; M0
  freeze with tolerances (bars ±2 %, RTE ±0.5 percentage points); AC1–AC8 with a
  traceability table (AC → layer → test file → reference source); status per AC in
  docs/04_validation_log.md; bridge invariants (E2 reproduces the E1 map in steady state;
  independently computed losses sum to E_in − E_out − ΔE_storage). CODEOWNERS gains
  /SPEC.md and /ROADMAP.md. AGENTS.md is replaced accordingly (SPEC primacy, legacy freeze
  per D2, evidence report format, branch rule). This entry is the DECISIONS authorization
  required for changing SPEC.md and AGENTS.md.
- **D8 – Tank instrumentation deferred. Status: DECIDED.**
  For the 2.0 core, tank gas temperature and tank pressure are SIMULATED state variables
  (computed from n, V, Z, T); no Pt100 and no pressure-sensor-based calibration or
  validation of the tank happens in this phase. No sensor-related registry key is deleted;
  the sensor keys keep their current status and the DCT 541 remains installed but unused
  for model calibration. Route 2 (tank pV) stays a legacy-only analysis, flagged defective
  in docs/94; it is NOT carried into the new core until instrumentation is retrofitted.
  Consequence, accepted: without Route 2 the new core has no independent measured
  H2-consumption path; the H2 balance in 2.0 rests on Faraday/water routes until retrofit.

## Pending decisions

- GitHub branch protection (CODEOWNERS enforce only after it is configured).
- POA source for the vertical east facade (before M3 PV scenarios).
- Kaeser electrical energy + booster air consumption measurement (unblocks D1).
- Tank instrumentation retrofit (Pt100 purchase/commissioning, DCT 541 readout): re-enables
  Route 2 calibration/validation and leak-rate/GS_tank separation; deferred per D8.
- Tank temperature Pt100 hardware: decided, but NOT yet purchased (README: "planned option,
  not yet purchased"); purchase and commissioning are open steps, not a given.
- tools/fuelcell_analyzer.html: archive to docs/ or delete – owner decides.
