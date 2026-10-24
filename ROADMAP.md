# Roadmap

Milestones for the 2.0 build. Each milestone lists the acceptance criteria (AC) it
fulfils; the AC definitions live in SPEC.md, their evidence status in
docs/04_validation_log.md. Owner decisions referenced here are identified by ID; see
DECISIONS.md. AC5 and AC6 apply from M1 onward; every milestone ships its own
fault-injection test; final acceptance of AC5 is in M5, of AC6 in M6. Session status
(done / open) lives in HANDOFF.md, not here.

- **M0 – Governance migration and hygiene.** DECISIONS entries D1-D9, SPEC rebuild,
  AGENTS.md rules, CODEOWNERS additions, docs/94 defect list (C1-C12), the README
  boundary fix and the hygiene items (.gitignore, pyproject.toml, baseline tag
  `legacy-1.0`), and the C9 registry-leak fix as an owner-approved tests commit.
  Fulfils no AC directly; it enables every later milestone.
- **M1 – Static loss map (Layer 1).** Starts with the port of the core pieces into
  `src/verlustmappe/models/` (constants, z_realgas, temperature_model, immutable
  per-run parameter objects; CODEOWNERS and ci_guard paths updated). Then
  characteristic curves for every device, loss-ledger booking, evidence status per
  bar. Freezes the AC8 reference values (`tests/reference/legacy-1.0/` + generator
  script committed) and the legacy-bar to ledger-item mapping (docs/94). Fulfils AC1
  and AC8.
- **M2 – Dynamic simulator (Layer 2).** step(state, inputs, dt), state vector, ledger
  in the time loop, balance invariants per step, profile-driven without dispatch.
  Fulfils the load part of AC2. Exit criterion: the bridge invariant L2 -> L1 passes
  (stationary reproduction of the Layer 1 map at the same operating point).
- **M3 – Scenarios and sensitivity.** Load series, clear/cloudy day, two-week run,
  Monte-Carlo with fixed seed, tornado output. Fulfils AC2 completely (the PV-profile
  part requires the decided POA source).
- **M4 – Calibration.** Overlay mechanism with provenance, first device per D4, fit
  and hold-out separation. Fulfils AC4.
- **M5 – Quality completion and model limits.** Fault injection and boundary tests
  completed, model limits documented. Fulfils AC5. No "validated" claim beyond
  AC4/AC5; a system-level validation criterion would be a separate owner decision and
  is not promised here.
- **M6 – Report and operation, then legacy teardown.** README and tables generated
  from the new code; the README gate switches here, NOT earlier (make_readme_demo
  --check compares against legacy test_03 output until then). Status shares per
  evidence status and, once D5 is decided, per result origin; model limits stated.
  Fulfils AC6 and AC7. After the gate switch: legacy teardown - ERSETZEN files
  (devices, balance, superseded hydrogen routes) are deleted or archived; `loaders/`
  and `analysis/` stay (BEHALTEN); legacy tests are retired or migrated per D9.
