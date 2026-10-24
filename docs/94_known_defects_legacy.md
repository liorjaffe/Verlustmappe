# Known defects of the frozen legacy state

Baseline: commit d060c9b, tagged `legacy-1.0` (unmodified legacy, tests ALL PASS).
These defects are documented here; inside the frozen legacy they are NOT fixed, with TWO
exceptions, each requiring its own owner-approved commit: C11 (text-only cleanup under D1)
and C9 (registry-leak fix in a protected tests commit). This file is the intended-deviations
list referenced by SPEC.md (AC8) and must be read before any work on legacy code (AGENTS.md).
New-core tests must cover the relevant invariants independently.

The status labels emitted by `balance/d_loss_map.py` (NAMEPLATE, ENVELOPE, NOT OBSERVED) are
part of the pending vocabulary decision in DECISIONS.md (D5).

## Defects

Verification key: [executed] = reproduced by running code at the baseline; [read] = verified
by reading the code; [brief] = carried from the 2026-10-21 brief without re-verification.

- **C1 – Standby missing from E_in.** [executed]
  `balance/e_rte.py` receives `E_standby_kWh` and books it only into the breakdown, not into
  `e_in`; the docstring promises the opposite. Repro with full arguments:
  `storage_chain_rte(10, 1, 1, 6, 0.5, E_standby_kWh=100)` returns `E_in = 12.0`
  (E_el + E_dryer + E_comp; E_fc_out and E_ctrl sit on the output side).
- **C2 – EL standby counts only the charge window.** [read]
  `devices/electrolyzer.py` books standby only for charge-window samples with
  P <= 3 x `el.power_standby_W`; idle time between charge and discharge is missing. The new
  core books standby over wall-clock time.
- **C3 – Plug bar "H2 storage change".** [read]
  `balance/d_loss_map.py` books the residual (E_in - chain - E_out) as a bar (-2.821 kWh in
  the README demo), the third-largest bar. It violates AGENTS rule 5. It is a residual, NOT
  a physical bar; the AC8 comparison ALWAYS excludes it (SPEC).
- **C4 – Closure tautology in test_03.** [read]
  The assert `E_in - chain - E_out < 1e-9` is forced true by the plug bar itself (C3); the
  test proves nothing about the physics.
- **C5 – Booster silent clipping.** [executed: threshold and capped result; read: the silent
  path]
  `devices/booster.py` caps `mol` to `mol_window` when throughput exceeds the tank window
  (threshold ~12,945 NL for 100 -> 120 bar at 800 L); the capped run returns the window work
  with NO warning in the result. Compare AGENTS rule 8, which applies to new code; silent
  clamping is exactly the pattern it forbids.
- **C6 – Route 2 without validity guard.** [executed]
  `hydrogen/route2_tank_pv.py` has no guard against resolution-limited windows. A fill of
  0.26 kg into 800 L raises tank pressure by ~3.9 bar (ideal gas) to ~5.0 bar (repo Z-table,
  start pressure 200 bar abs; the rise grows with start pressure) - the start pressure
  matters and must be stated with any such figure. Two DIFFERENT thresholds apply, for
  different purposes: (a) the Route-2 validity guard needs >= 10 x FSO_abs = 20 bar of rise
  (sensor resolution, DCT 541 +/-2.0 bar per reading); (b) multi-day windows with >= 50 bar
  serve the SEPARATION of leak rate and GS_tank. Route 2 is valid only for large windows.
- **C7 – Temperature uncertainty terms.** [brief]
  `hydrogen/route2_tank_pv.py` propagates a single common temperature offset term instead of
  common + independent per reading; the fast-fill bracket is reported separately and not
  folded into `u`. Carried from the 2026-10-21 brief; re-verify before acting on it.
- **C8 – Monte-Carlo scope.** [executed: key enumeration; read: draw behavior]
  `uncertainty/montecarlo.py` perturbs ALL non-measured numeric registry entries including
  pv.* (46 keys, 8 of them pv.*) with independent draws; compressor eta is drawn
  symmetric-normal instead of log-normal; the result field is named `ci` where it is a
  sensitivity band, not a confidence interval.
- **C9 – Registry leak in tests.** [read]
  `tests/test_02_hydrogen_routes.py` and `tests/test_03_full_chain.py` set `stor.volume_L`
  to 1000 without resetting it. Harmless under `run_all.py` (separate processes), a real
  leak under pytest. Fixing this requires an owner-approved tests commit (fixture /
  try-finally), because `tests/` is protected. EXCEPTION to the freeze: this is one of the
  two defects with a planned fix (see header).
- **C10 – README boundary.** [read]
  The PV system boundary is missing (F8 is the storage-chain PV source); the SMA dataset
  (5.19 MWh / 22 days) is presented as "genuinely measured" without a boundary note;
  docs/07 is missing from the README tree.
- **C11 – Compressor-eta documentation conflict.** [read: repo conflict; primary text:
  Tab. 3 read in the library full-text copy]
  Inside the repo the documentation contradicts itself: registry.py comment block argues
  0.014 ±30 % from "78.4 + 4.6 kWh", the registered entry is 0.03 ±40 % (decision
  2026-10-21); booster.py docstring argues 0.014; the warning text says ±50 %. Bovo IJHE 48
  (2023) part 1, Tab. 3 lists compression energies 60.28 / 56.36 / 100.2 kWh (nominal /
  full / half load, 33.22 Nm3) and "78.4 + 4.6 kWh" does not appear in that table. Final
  wording of the cleanup (delete comment block, align docstring and warning) is decided
  under D1 with the owner confirming the full-text reading.
- **C12 – Test architecture.** [executed: pytest collection; read: runner logic]
  The legacy tests are scripts defining `main()`; pytest collects no tests ("no tests ran").
  `tests/run_all.py` executes each `test_*.py` as a script and treats exit code 0 as PASS,
  so a pytest-style file without `main()` would pass silently. `ci.yml` calls run_all, not
  pytest. This is the factual basis for the open test-runner decision for the new tests
  (test_20 to test_26), recorded as D9 in DECISIONS.md.
- **C13 - Stale SMA terminology.** [read: repo-wide grep at 7a81918]
  The PV source of the storage chain is the F8 array with two Solis S6-GR1P6K inverters.
  SMA references throughout the legacy docs, README, device docstrings/comments and one
  test name describe the removed legacy building array (~184 kWp) or are plain leftovers.
  No physics impact. Text-only fix: README and docs/06 in task P02; remaining src/ text
  (pv_measured.py, pv_inverter.py, live_feed.py, loaders/grafana.py docstrings, registry
  comments) in task P04 under the D2 text exception. AC8 treatment: none.
  C13 is terminology-only and does not affect AC8 physics.

## AC8 treatment per defect (makes the SPEC exclusion rule operational)

| Defect | AC8 treatment |
|---|---|
| C1 standby missing in E_in | none: reference points have standby = 0 |
| C2 EL standby window | none: same reason |
| C3 plug bar | ALWAYS excluded (residual, not a physical bar) |
| C4 closure tautology | none for the map; AC8 uses the new regression test, not test_03 |
| C5 clipping | none: reference throughput stays within mol_window |
| C6 Route-2 guard | none: affects Route 2, not the Layer 1 map |
| C7 temperature terms | none: affects Route 2 |
| C8 Monte-Carlo scope | none: affects the uncertainty layer |
| C9 registry leak | none for AC8; open fix, owner-approved tests commit required |
| C10 README boundary | none for AC8; fixed by the README task |
| C11 eta doc conflict | none for AC8 numerics; cleanup task under D1 |
| C12 test architecture | none for AC8; decision D9 covers the new tests |
| C13 SMA terminology | none: documentation only |

## Legacy-bar to ledger-item mapping (for AC8, Layer 1 = milestone M1)

To be filled when the ledger item names are fixed in M1. Every legacy bar name (README demo
table) gets a row: legacy bar -> new ledger item -> intended deviation (C-number) -> AC8
treatment (exclude / compare with offset).

## Decisions affecting this file

- D1 (DECISIONS.md): compressor-eta cleanup task (C11) only under this decision.
- D2 (DECISIONS.md): freeze and baseline; this file is the intended-deviations list.
- D8 (DECISIONS.md): tank instrumentation deferred; tank T/P are simulated state variables
  in the new core; Route 2 stays legacy-only analysis.
- D9 (DECISIONS.md, to be recorded): test-runner policy for the new tests; basis is C12.
