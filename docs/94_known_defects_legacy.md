# Known defects of the frozen legacy state

Baseline: commit d060c9b, tagged `legacy-1.0` (unmodified legacy, tests ALL PASS).
These entries describe the defects of the tagged baseline. The tag remains unchanged.
D2 freezes src/ model behavior; C11/C13 text cleanup executed in P04 (D16, D17); booster.py docstring and warning text cleaned (D18).
C9 is fixed in the P03 working version by a separate, owner-reviewed tests-only change
under AGENTS.md rule 4, not by an exception to D2. See its entry for acceptance.
This file is the intended-deviations list referenced by SPEC.md (AC8) and must be read
before any work on legacy code (AGENTS.md). New-core tests must cover the relevant
invariants independently.

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
- **C9 - Registry leak in tests.** [read: baseline; executed: P03 acceptance]
  At the tagged baseline, `tests/test_02_hydrogen_routes.py` and
  `tests/test_03_full_chain.py` set `stor.volume_L` to 1000 without restoring it.
  Separate-process execution in `run_all.py` hides the leak; calling main functions
  in one process exposes it. Fixed in P03: the original bodies are renamed `_body`
  without edits; `main()` restores the entry value in a finally block, also on failure.
  Tests are outside D2's src/ freeze but protected by AGENTS.md rule 4: use a dedicated
  tests-only commit with owner approval. Acceptance is in
  `tasks/P03_c9_registry_leak_fix.md` (both modules, normal and exceptional paths).
  The tagged baseline and C4 remain unchanged.
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
  Status: executed in P04: registry.py comment block deleted (D16b); booster.py docstring
  and warning text cleaned (D18).
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
  (registry.py comments, devices/__init__.py, pv_measured.py, pv_inverter.py,
  pv_prelim_channel.py, live_feed.py, loaders/solis_live.py) in task P04 under the D2 text
  exception (D16c, amended by D17; D16 named loaders/grafana.py in error). Status:
  executed in P04; the registry carries no SMA reference. tests/test_08* keep the SMA name
  (frozen legacy regression, falls in M6). AC8 treatment: none.
  docs/01-04 evidence-attribution statements fixed in P02b.
  C13 is terminology-only and does not affect AC8 physics.

- **C14 – No range/sign guard on model inputs.** [read]
  Device models accept out-of-range or wrongly signed inputs without a guard: the EL
  standby classifier books negative power (E_in = -0.3 kWh at P = -50 W, 361 samples at
  60 s), WaterSystem accepts duty > 1 and wcf <= 0, no plausibility band on any physical
  input. Impact: silent nonsense results possible in the legacy chain. Fix: the new core
  validates input ranges and signs at the model boundary (M1/M2 tests); legacy is not
  modified. AC8 treatment: none.

- **C15 – cycle_closed compares production with the charge-window tank delta.** [executed]
  `balance/d_loss_map.py` sets cycle_closed when the tank window holds ~100% of produced H2
  (abs(h2_in - h2_stored)/h2_in < 0.05), not when n_end ~ n_start. The test_03 demo asserts
  cycle_closed=True while FC consumption is 132% of production (11.66 vs 8.84 kWh LHV).
  Impact: the h2_balance flag and note misdescribe the cycle; the RTE number itself is not
  derived from this flag. Fix: the new core compares tank states (n_start, n_end) and
  reports a closure verdict with its uncertainty. AC8 treatment: none (the flag is not an
  AC8 quantity).

- **C16 – rte_closed omits the FC control energy; different boundary than rte_open.** [executed]
  rte_open uses E_out = (E_fc - E_ctrl) * eta_inv. rte_closed multiplies the stored-H2
  energy by eta without subtracting E_ctrl. Demo: rte_open 0.2528, code rte_closed 0.2178;
  with the control energy subtracted the value would be 0.183 (full subtraction, DC side,
  same place as rte_open) or 0.192 (allocated in proportion to the consumed hydrogen).
  Which allocation is correct is an owner definition (measurement point of the control
  energy), not derivable from the code. Fix: one netting rule for every RTE variant,
  decided before M1. AC8 treatment: none (rte_closed is not an AC8 quantity).

- **C17 – Filter-train energy is booked as a bar but excluded from E_in.** [executed]
  `loss_map()` emits the filter bar and passes only wat["energy_kWh"] into
  storage_chain_rte; the difference is absorbed by the C3 residual (100 W pump: filter bar
  +0.6 kWh, storage-change bar -2.821 -> -3.421 kWh, closure still 0.0). The residual hides
  booking errors in a seemingly physical storage-change bar. Fix: the ledger books every
  consumer of E_in as an input item; an unexplained remainder becomes BALANCE_ERROR.
  AC8 treatment: reference points have filter power 0 W; none beyond C3.

- **C18 – FuelCellSystem treats stack-current COLUMNS as validity.** [executed]
  Existence check only: with all stack columns NaN the account returns E_out = 0,
  efficiency_is_measured=True, eta=None, no warning; a fully NaN module zeroes both
  modules. Partially NaN rows are silently dropped: with a scattered NaN pattern the
  dropped energy is bridged by the larger dt of the remaining rows (nearly lossless, 4.917
  vs 5.000 kWh for every second row of one module), with a contiguous NaN block the block
  is treated as a gap and its energy is lost (4.833 kWh for 3 rows). Either way the failure
  is silent and per-module accounting is wrong. The EL analogue checks column existence too
  but then fails loudly. Impact today: none (no stack columns in real exports); critical
  once the D8 export path exists. Fix: per-quantity validity (power channel vs per-module
  currents), loud INVALID or labelled nameplate fallback. AC8 treatment: none.

- **C19 – compare_routes is order-dependent.** [executed]
  The production route is chosen with next(); with Faraday 1.0 kg / water 0.8 kg / tank
  0.7 kg the gas-loss estimate is 0.300 kg, with the first two swapped 0.100 kg. Impact
  today: none (loss_map never passes the water route). Fix: explicit production-route
  argument in the new core. AC8 treatment: none.

- **C20 – Two integration rules and contradicting gap documentation.** [executed/read]
  Devices integrate with left rectangles (gap weight 0 s); conversions.py, route3 and
  report_cli use the trapezoidal rule; route3 bridges data gaps (2.78 NL integrated across
  a 999 s hole at 10 NL/h where the device policy books 0); report_cli interpolates power
  without labelling it as estimated; the electrolyzer.py module docstring describes a
  "mean power over max_gap_s" policy the code does not implement. Impact: small at 60 s
  telemetry, large at 20-min PV data (ramp 0-3 kW over 1 h: 1.0 vs 1.5 kWh, left
  rectangles vs trapezoid). Fix: one integration function with segment-wise gap handling
  and reported coverage. AC8 treatment: none.

- **C21 – Truthiness treats 0.0 measurements as missing.** [read]
  `inverter.py`, `pv_inverter.py` and `pv_prelim_channel.py` gate on `if e_x and ...`, so
  a genuine 0.0 kWh switches the path. Fix: explicit None checks in the new core.
  AC8 treatment: none.

- **C22 – Route-2 uncertainty model gaps (extends C6/C7).** [executed/read]
  Z-table errors are treated as independent per endpoint and amplified by p/dp (11 at
  200->220 bar; the 1% Z term then contributes 11% of the mass) while the model-vs-CoolProp deviation of the mass difference there is
  0.61%: endpoint correlation is unmodelled, the term is conservative, not proven wrong.
  The sensor thermal coefficient (0.8 bar/10 K) is not propagated (self-cancelling at equal
  sensor temperature; 0.8% beside the 2.8% pressure term at dp=100 bar and 10 K). Tier 1
  fixes T = 20 degC when nothing is passed; the docstrings still carry a 250-bar FSO,
  +-1.25 bar (registry: 400 bar, 2.0 bar) and "+1 K registered" (code: 3.0 K). Fix:
  covariance-aware Z term, thermal term for differing sensor temperatures, ambient as
  explicit input, docstrings aligned (text task). AC8 treatment: none (Route 2 is
  legacy-only per D8).

- **C23 – Monte-Carlo scope beyond C8.** [read]
  MEASURED uncertainties are never propagated; the power-measurement factors s_in/s_out
  also scale modelled energies (the modelled CSU energy); uncertainty parameters themselves
  are drawn as values (meas.power_rel_unc, pv.soi_uncertainty_rel); bars are not scaled by
  s_in/s_out, so bar band and RTE band describe different stochastic models;
  bars[:len(rtes)] assumes positional bar identity and would misalign if a NaN RTE
  (e_in <= 0) were filtered out (latent, verified by reading, not reproducible without
  fault injection). Fix: M3 Monte-Carlo rebuilds this per the new-core ledger.
  AC8 treatment: none (uncertainty layer only).

- **C24 – Ledger gaps at the system boundary.** [read]
  inv_fc.standby_W is registered and unused; the battery path has no loss item; standby and
  idle of all devices are accounted only inside the charge/discharge windows, never over
  wall-clock time; Kaeser idle is not modelled. Whether these belong inside the reported
  boundary is an owner decision; until then the storage-chain RTE is a window-boundary RTE,
  not a whole-system RTE. AC8 treatment: none.

- **C25 – z_h2 clamps silently above 350 bar abs; the source comment overstates.** [executed]
  np.interp holds the 350-bar value above the table end (-2.4% at 400 bar abs vs CoolProp).
  The comment "the same EOS CoolProp/NIST REFPROP implement" is too strong: it is a table
  cross-checked against CoolProp with max deviation 0.46% over 0-350 bar, 0-40 degC.
  Practically unreachable (PS 300 barg, valve 330 bar), but silent clamping is a defect per
  AGENTS rule 8. Fix: range guard in the ported module. AC8 treatment: none.

- **C26 – Dead and duplicate registry entries.** [read]
  comp.specific_energy_kWh_per_Nm3 duplicated the compressor truth (now REJECTED with the
  comp.* group); stor.steel_mass_kg, bat.* and inv_fc.standby_W have no active consumer.
  Fix: owner decision to delete, mark RESERVED, or assign to a model (M1).
  AC8 treatment: none.

- **C27 – Route 2 requires mutating the global registry for connected bundles.** [read]
  The error message of `h2_from_tank_pressure` instructs the caller to "set stor.volume_L to
  the connected volume and pass False". That contradicts the per-run immutability rule.
  Fix: the new core takes the connected volume as an explicit input (SPEC).
  AC8 treatment: none.

- **C28 – Compression energy inside E_in without the D14 allocation and without measurement.** [executed]
  Legacy books the air-driven compression energy inside E_in directly; D14 decides
  allocation rules (volume share, separate standby/leakage) that the legacy model does not
  implement, and no measurement exists. The README demo window (50 -> 53.4 barg) is a
  low-pressure best case: for the same daily mass (0.2654 kg, suction 35 barg) the ideal
  work at 295 -> 300 barg topping is ~0.19 kWh vs ~0.034 kWh in the demo window (about
  5.5x). Fix: the new core books the air system per D14 and reports the compression item
  from the air-chain model or measurement. AC8 treatment: reference values at the tagged
  state as documented; none beyond C3.

- **C29 – Bar status does not inherit the weakest input status.** [executed/read]
  The EL and FC conversion bars are labelled MEASURED while depending linearly on GUESS
  parameters (el.n_cells, fc.n_cells, el./fc.faradaic_efficiency); together they are ~80%
  of the demo's physical loss bars (5.557 + 6.664 of 15.31 kWh). This violates the
  weakest-status rule for the legacy output. Fix: the new core derives every result status
  from its inputs. AC8 treatment: none (status display only; AC8 compares values).

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
| C9 registry leak | none for AC8; fixed in P03; tagged baseline unchanged |
| C10 README boundary | none for AC8; fixed by the README task |
| C11 eta doc conflict | none for AC8 numerics; cleanup executed in P04 |
| C12 test architecture | none for AC8; decision D9 covers the new tests |
| C13 SMA terminology | none: documentation only |
| C14 no input guard | none: new-core concern; legacy unmodified |
| C15 cycle_closed flag | none: the flag is not an AC8 quantity |
| C16 rte_closed boundary | none: rte_closed is not an AC8 quantity |
| C17 filter bar outside E_in | none: reference points have filter power 0 W; none beyond C3 |
| C18 FC stack-column validity | none: no stack columns in the reference data |
| C19 compare_routes order | none: loss_map never passes the water route |
| C20 integration rules | none: new-core concern; legacy unmodified |
| C21 truthiness of 0.0 | none: new-core concern; legacy unmodified |
| C22 Route-2 uncertainty gaps | none: Route 2 is legacy-only (D8) |
| C23 Monte-Carlo scope | none: uncertainty layer only |
| C24 ledger boundary gaps | none: owner boundary decision |
| C25 z_h2 clamp | none: reference points stay below 350 bar abs |
| C26 dead registry entries | none: no AC8 consumer |
| C27 Route-2 registry mutation | none: Route 2 is legacy-only (D8) |
| C28 compression allocation | none: reference values at the tagged state as documented; none beyond C3 |
| C29 bar status inheritance | none: status display only; AC8 compares values |

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
