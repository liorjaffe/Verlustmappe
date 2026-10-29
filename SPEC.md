# Project specification

## Purpose

Verlustmappe estimates the energy losses and round-trip efficiency of the UFSC
photovoltaic-to-hydrogen-to-fuel-cell island system. It must expose the source, uncertainty,
and status of every result rather than present assumptions as measurements. The system is
built in three layers: a static loss map (Layer 1), a dynamic simulator (Layer 2), and a
calibration/validation layer (Layer 3). Computation is the normal case; measurement is the
correction.

## Sources of truth

- Project overview and reading guide: `README.md`
- How humans and agents work here: `AGENTS.md`
- Device parameters, values, uncertainty, status: `src/verlustmappe/registry.py`
- External sources for every number: `SOURCES.md`
- Owner decisions: `DECISIONS.md` (this SPEC changes only via a DECISIONS entry)
- The repository (SPEC, DECISIONS, registry, SOURCES) is the single authority for the model.
  The library note "00 CURRENT STATE" only records plant facts not yet in the repo (D29).
- Known legacy defects: `docs/94_known_defects_legacy.md`
- Acceptance evidence per criterion: `docs/04_validation_log.md`
- Milestones: `ROADMAP.md`
- Independent hand calculations: `tests/reference/hand/`; frozen AC8 reference values:
  `tests/reference/legacy-1.0/` (created with the first reference values; both protected)

## System boundary

- Primary boundary: AC energy entering the hydrogen storage path, to AC energy returned by
  the fuel-cell side. Exactly two named numbers exist (D21): RTE_storage (AC-bus-to-AC-bus
  storage chain) and RTE_island (input = PV AC entering the storage path, output = AC after
  the FC inverter). Under the slice principle the island input coincides with the
  storage-chain input, so the two numbers coincide by definition; RTE_island is informative
  only for an input basis that differs (PV DC, whole-bus input), which needs a new DECISIONS
  entry. A headline RTE (README, paper) requires a CLOSED cycle (below) or an explicitly
  H2-normalized number (RTE netting); otherwise E_in, E_out and the tank delta are reported
  separately, each with status.
- PV source of the storage island: F8 (28 x BYD455MGEK-36 = 12.74 kWp, vertical east
  facade). The island RTE counter uses the slice principle: only the PV AC energy that
  enters the storage path.
- The Sept 2026 PV dataset (`pv_merged.csv`) is excluded per D33 (owner statement: not produced by
  the F8 inverters; exact provenance unresolved). It is NOT part of this boundary and is never
  F8 calibration evidence.
- Compressed-air generation (Kaeser) is reported separately as long as no DECISIONS entry
  includes it in the RTE (D3).
- Tank gas temperature and tank pressure are simulated state variables of the Layer 2 tank
  model, computed from n, V, Z, T (D8). The tank state (n, p, T) is a core state variable;
  the Route-2 measured path (tank pV from sensor readings) stays legacy-only analysis until
  tank instrumentation is retrofitted.
- The connected storage volume is an explicit model input, never an assumption: the
  instrumented bundle holds 800 L only while it is valved off from the second bundle,
  otherwise the connected volume is 1600 L (isolation flag as input).
- The H2 balance must be labeled model-supported as long as no measured counter-path
  exists, PER PATH: EL production labeling ends via stack-current export or a water meter;
  FC consumption labeling ends via FC stack current (Faraday), tank instrumentation
  retrofit (re-enabling the Route-2 measured path), or an H2 flow meter on the FC side
  (D8).
- Cycle closure (D20): a cycle is CLOSED iff |n_end - n_start| <= eps * n_ref and
  u(dn) <= eps * n_ref, with eps = 5 % (owner choice carried over from the legacy flag, not
  a derived value) and n_ref = max(n_tank_in, n_tank_out). n_tank_in and n_tank_out are the
  amounts of substance (mol) entering and leaving the tank in the window; u(dn) is the
  standard uncertainty (mol) of n_end - n_start. Otherwise the verdict is NOT VERIFIABLE.
  Measured closure uses the tank-pressure sensor (DCT 541) for the closure verdict only,
  never for tank-state calibration or validation, and stays NOT VERIFIABLE until the sensor
  repeatability test exists. In Layer 2 the tank state is simulated and closure is exact by
  construction; the Layer-2 gate is the separate balance invariant below. A non-closed
  cycle reports the storage delta separately, never absorbed into a loss bar.

## RTE netting

- E_out_net = (E_fc_terminal - E_ctrl) * eta_inv in EVERY RTE variant (D22). The control
  energy is assumed drawn on the DC bus before the inverter; the measurement point is open
  and must be confirmed. It is booked once: the ledger item "FC control" and the inverter
  loss split E_fc_terminal into E_ctrl and (E_fc_terminal - E_ctrl) * (1 - eta_inv).
- H2-normalized variant: RTE_H2norm = E_out_net * (n_stored / n_fc) / E_in, with n_stored =
  tank inflow over the charge window and n_fc = hydrogen consumed over the discharge window.

## Ledger scope

- Ledger items (D23): EL energy incl. observed standby; dryer electrical; dryer vent (H2);
  water system incl. RO standby over wall-clock time; filter train (inside E_in);
  compression air system per D14 (variable share by air quantity, READY standby and network
  leakage as separate items); FC control; FC inverter loss; FC inverter standby once
  measured. Standby and idle are accounted over wall-clock time, not per window.
- The battery path is outside the storage-chain boundary. A whole-system number including
  the battery is a separate, separately named quantity and needs its own DECISIONS entry.
- Per D14, stage 1 of the compressed-air accounting yields NO RTE number while the Kaeser
  input power is open.

## Data integration and validity

- One integration function for the whole core (D24): trapezoidal within valid segments. A
  gap is dt > max(3 x nominal sampling interval, max_gap_s); max_gap_s = 30 s is the
  legacy-continuity value, not newly derived. Nominal intervals per source are documented in
  `docs/03`. Gaps segment the series and the covered fraction is reported; no minimum
  covered fraction is set (open, AGENTS rule 8). Non-monotonic time is INVALID.
- INVALID, never a plausible number (D25, D31): a REQUIRED parameter is BACKLOG without an
  owner-approved GUESS; a computed or modelled quantity is negative where the sign rule of
  D31 requires non-negative (energies and powers of a single path, masses, amounts and
  their flows, absolute pressure and temperature, water volumes; signed by definition:
  storage change, differences, relative and differential pressures; raw channel values
  with a sign convention are exempt); non-monotonic time; a mandatory channel is missing
  (per source in `docs/03`; only the affected route or item is INVALID).
- A missing FC module current with a valid power channel yields a separate labelled result
  with calculation_route = NAMEPLATE, never a silent replacement, subject to the D26
  publication lock.
- Route-2 limit: dp < 10 x FSO of the tank-pressure sensor in use is INVALID (20 bar with
  the registered 2.0 bar). It applies to the legacy Route-2 path and to any future path
  using tank pressure as a measurement; the new core does not use Route 2 (D8). It is
  separate from the 50 bar window condition for leak-rate separation (docs/94 C6).

## Layers

- Layer 1 (static loss map): device models evaluated at defined operating points from
  registry parameters. An operating point includes the state quantities it needs as
  inputs: tank pressure, gas temperature, wall temperature, battery SoC, connected storage
  volume. No DataFrames, no global state, no measured-data requirement. Result: loss chain
  per operating point and an RTE map, every bar with evidence status.
- Layer 2 (simulation): the same device models executed in a time loop with a state
  vector. Interface: step(state, inputs, dt) -> outputs, new_state, losses. Losses are
  booked into a loss ledger from each device's own physics; the ledger aggregates on
  booking. Runs are profile-driven; dispatch is optional and never blocks.
- Layer 3 (calibration/validation): parameter overlays with provenance fitted to measured
  data, validated on separate hold-out data. Registry defaults stay reproducible; fitted
  values live in approved overlay files, never silently change the registry.

## Frozen reference (AC8)

- The unmodified legacy state is tagged `legacy-1.0` and is the AC8 baseline. Legacy
  physics is not patched (D2).
- The 1.0 reference values for AC8 are computed AT the tagged state, at reference points
  defined under AC8, and stored in `tests/reference/legacy-1.0/`. The generator script
  that reproduces the reference values from the tagged state is committed in the repo
  alongside the values.
- Intended deviations from the legacy behavior (plug bar, standby missing in E_in, booster
  clipping, Route-2 guard) are documented in `docs/94_known_defects_legacy.md`, together
  with the mapping of legacy bars to the new ledger items.

## Functional criteria

- **AC1:** The static loss map computes a complete chain without measured data; every bar
  carries an evidence status derived from its inputs. A run with a REQUIRED BACKLOG
  parameter must be treated as invalid unless an owner-approved, clearly labeled GUESS
  placeholder exists.
- **AC2:** The simulation runs under at least five loads and two PV profiles; all balance
  invariants hold at every step. Acceptance of the PV-profile part requires a decided POA
  source recorded in DECISIONS.md; the load part is independent of it.
- **AC3:** Standby, start-up, purge, and tank heat appear as physically derived items.
  Purge and start/stop are booked as discrete events independent of dt. Tank heat (the
  heat the gas releases to the tank wall and ambient after a fill) is reported as an
  allocation within the compression loss chain, i.e. as part of the energy spent beyond
  ideal isothermal work; booking it as an additional loss on top of the compression item
  is double counting and forbidden.
- **AC4:** At least one device is calibrated with measured data; the overlay file, its
  provenance, and an independent hold-out check are documented. The first device is
  selected per DECISIONS.md (D4); AC4 acceptance is blocked until that selection is
  recorded.
- **AC7:** The report shows the share of loss energy per evidence status and per result
  origin (D26); loss bars whose weakest-wins status includes UNCERTAINTY_NOT_ASSESSED are
  reported as a separate share of the loss energy; it states the model limits (what the
  model cannot do).
- **AC8:** Layer 1 reproduces the frozen 1.0 reference points within tolerance (bars
  ±2 %, RTE ±0.5 percentage points) with characteristic curves clamped to legacy
  constants. Reference points are defined deviation-free: standby power = 0 and
  throughput within `mol_window` (no clipping). The legacy plug bar ("H2 storage change")
  is ALWAYS excluded from the comparison because it is a residual, not a physical bar;
  any further exclusion for a reference point that cannot be built deviation-free is
  compared against the documented offset from docs/94. AC8 demonstrates "no unintended
  change", not correctness. The legacy-bar-to-ledger mapping table in `docs/94` is
  normative for WHICH bars are compared (1:1 within tolerance; n:m as a group sum;
  no-counterpart bars excluded with a stated reason, D30); it is filled in M1 once the
  ledger names exist and is not operational before that.

## Quality criteria

- **AC5:** Tests detect deliberately injected faults (a missing loss item, a 5 % H2 loss,
  an inserted plug term). A test that does not report the fault is worthless.
- **AC6:** README and result tables are generated from code, never hand-edited.
- Test execution follows the test-runner policy in DECISIONS.md (D9).

## Balance invariants (every step, Layer 2)

- Electrical: input = output + independently booked losses + storage content change.
- Hydrogen: produced = consumed + vent + leakage + buffer/tank change, balanced in mol,
  not only in kWh.
- Tolerance: a balance violation beyond max(1e-6 x reference, 1e-9 kWh) for energy
  (reference = the largest of E_in, E_out, |dE_storage| in that step) or beyond
  max(1e-6 x reference, 1e-9 mol) for hydrogen invalidates the run. A diagnostics mode
  may continue to locate the error but never produces a result. A balance error is a
  program error, not a bar.
- **Stationary** means: a window of at least 60 s in which no device changes operating
  mode (EL, FC, booster stay in the same mode) and every state variable changes by less
  than 0.1 % of its value per hour (a rate, independent of dt). Exact thresholds are
  owner-adjustable via a DECISIONS entry.
- Bridge invariant L2 -> L1: in a stationary window under constant load, Layer 2
  reproduces the Layer 1 map at the same operating point (same state quantities: tank
  pressure, gas temperature, wall temperature, SoC, connected storage volume) within bars
  ±0.5 % and RTE ±0.1 percentage points (numerics-only tolerances; owner-adjustable via
  DECISIONS). A violation invalidates the run.

## Status vocabulary

- Normative per D26 (completes D5). evidence_status: MEASURED > CALIBRATED > DATASHEET >
  DATASHEET_SECONDARY > DERIVED > PRELIM/ENVELOPE > GUESS > BACKLOG. OWNER_DECISION is a
  registry source status; REJECTED and SUPERSEDED are registry states, not evidence
  statuses. observation_status: OBSERVED / NOT OBSERVED / MISSING. result_origin: MEASURED
  (direct channel read) / RECONSTRUCTED (changes when measurement data changes) / SIMULATED
  (independent of measurement data), decided by a perturbation test. calculation_route:
  FARADAY, NAMEPLATE, TANK_PV, ... The residual term is never DERIVED. A result carries the
  weakest evidence status of its inputs; a calculated value must never look like a
  measured one.
- Uncertainty classification (computed, applied to ALL numeric registry entries; no new
  status, no new field): u = 0.0 is exact only for (i) OWNER_DECISION entries, (ii) DERIVED
  entries that are pure arithmetic from assessed inputs, (iii) TOLERANCE_BAND entries,
  which are exactly `meas.p_sensor_fso_bar` and `meas.p_sensor_thermal_bar_per_10K`
  (additions only via a DECISIONS entry, D26(b)). For every other numeric entry u = 0.0
  means UNCERTAINTY_NOT_ASSESSED; DERIVED status alone does not establish exactness.
- Effect: computation is never blocked and results carry the condition. The publication
  lock applies only to headline candidates (README, paper numbers, D21); other outputs
  show their status through the AC7 share report. BACKLOG takes precedence: a REQUIRED
  BACKLOG parameter makes the run INVALID (AC1); a numeric BACKLOG placeholder is itself
  not-assessed. Existing u = 0.0 entries are classified, not migrated; assessing those
  that drive headline candidates is an audit backlog (HANDOFF). Register column and
  enforcement test: task P09b.

## Traceability

Acceptance allocation (binding; the STATUS per criterion lives in docs/04_validation_log.md):

| AC | Layer | Test file (planned name) | Reference source |
|---|---|---|---|
| AC1 | L1 | tests/test_20_static_map.py | tests/reference/hand/, registry + SOURCES |
| AC2 | L2 | tests/test_21_sim_invariants.py | SPEC invariants; profile fixtures |
| AC3 | L2 | tests/test_22_events_ledger.py | docs/94 baselines; Regatron purge data |
| AC4 | L3 | tests/test_23_calibration_holdout.py | measured dataset per D4; overlay file |
| AC5 | gate | tests/test_24_fault_injection.py | injected-fault fixtures |
| AC6 | gate | ci.yml (make_readme_demo --check, pytest -q) | README generator; pytest run |
| AC7 | report | tests/test_25_report_status.py | docs/04 |
| AC8 | L1 | tests/test_26_reference_regression.py | tests/reference/legacy-1.0/ |
