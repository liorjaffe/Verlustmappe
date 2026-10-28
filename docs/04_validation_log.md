# Validation log

Which test proves what. Run everything with `python3 tests/run_all.py`.

| Test | What it proves | Ground truth used |
|---|---|---|
| `test_01_constants_and_conversions` | constants match references; Faraday, gas law, isothermal work, trapezoid integration are implemented correctly | Enapter datasheet self-consistency (500 NL/h = 1.0785 kg/day), h2data.de (3.00 kWh/Nm³), hand-computed 1 A·h, 44.615 mol/m³ at STP, RT ln10, 2 kWh |
| `test_02_hydrogen_routes` | Z table hits NIST checkpoints; Routes 1, 2, 4 agree to <1e-6 when fed the same physical truth; closure spread ≈ 0; nameplate route is the 62.4% constant | Z(350 bar,15 °C)=1.234, Z(200,20)=1.132, ρ(200 bar,20 °C)≈14.6 kg/m³; algebraic construction |
| `test_03_full_chain` | whole loss map runs; EL and FC efficiencies come out in physical ranges; RTE ≈ 26%; MC band brackets the estimate; a consistent tank reading closes to 0% spread | synthetic cycle 2.4 kW × 6 h charge, 2.5 kW × 2 h discharge |
| `test_04_real_fc_data` | pipeline runs on real 2026-09-22 FC telemetry; finds ≥10 steady segments and ≥3 purge candidates; correctly refuses to call FC efficiency "measured" (terminal ≠ stack current) | the real log (3 h, 2161 rows) |
| `test_05_analysis_methods` | characteristic-curve extraction, reference deviation, efficiency vs T, ramp/cycle energies, purge recovery, degradation regression and lifetime projection, relative-difference table | constructed linear V–I; discrete-signal energies; −0.4 mV/h synthetic degradation |

## Bugs found by tests during development (kept here on purpose)
- J→kWh instead of J→Wh in start/stop energies (factor 1000). Caught by `test_05`.
- Tank end pressure inconsistent with produced hydrogen produced a 644% closure spread. Caught by `test_03`. This is the closure doing its job.
- Constant Z = 1.10 at 200 bar underestimated the real-gas correction; replaced by the NIST table (1.132).
- Fuel-cell "polarisation curve" was computed from DC/DC output terminals; relabelled "terminal V–I" everywhere.
- HTML analyzer assumed NL/min for flow; Enapter exports NL/hour (factor 60). Detector extended, warning added.
- Two LHV constants (2.995 vs 2.998 Wh/NL) in two tools; unified through `constants.py`.

## What is NOT validated yet (needs data, not code)
- Route 1 on the real electrolyser (needs `stack_amperage` export).
- Route 2 on the real tank (needs volume and gauge readings).
- Dryer and compression bars (need meters).
- Any statement about part-load efficiency of the fuel cell (needs stack current or an H₂ meter).

## External review round (2026-10): fixes applied

Full external review by a second AI found 30+ issues; all verified against the
code and fixed. Highlights with the test that now guards each:

- Loss map now reports the H₂ balance (`h2_balance`) and both `rte_open` and
  `rte_closed`; the synthetic demo is openly labelled an OPEN cycle. Guarded by `test_03`.
- Nameplate route can no longer enter the closure after renaming
  (`base()` strips `_minus_vent`). Guarded by `test_03`.
- FC Faraday direction: η_F now DIVIDES on the consumption side; per-device
  registry entries for uncertainty. Guarded by `test_02`.
- Data alignment: devices drop unmatched rows, gaps are excluded from
  integrals (never bridged), `data_coverage` reported. Guarded by `test_01/03`.
- Z table corrected to CoolProp-consistent values, ±1%. Guarded by `test_02`.
- Tank uncertainty: T and Z terms now amplified by p/Δp like the gauge term.
- Compressor: pressure-swing-average instead of fixed top pressure.
- Closure: loss (produced−delivered) returned as `gas_loss_estimate`, no
  longer conflated with uncertainty.
- MC: η_F draws clipped to (0,1], energies clipped positive, failed draws
  counted, `meas.power_rel_unc` applied to E_in/E_out. Guarded by `test_03`.
- Efficiency vs temperature: direction-aware (was 1/η for the EL).
- PV totals: daily-resample method replaced by counter differences across
  gaps (5190 vs 4137 kWh discrepancy explained); energy-weighted inverter
  efficiency. NOTE: re-run report_cli to regenerate `pv_daily_yield.csv`.
- Known-weak tests flagged: `test_02`'s tank bisection is an internal
  consistency check of Route 2, NOT independent validation (documented).
- Cosmetic but real: `iter_windows` last window, `mock_stream` sub-second,
  plot key mismatches, recovery end-touch, MAD on quantized signals (documented
  as a known limitation: quantized telemetry needs the noise floor checked),
  comma-decimal exports now parse with a warning on empty files, mode
  defaults pulled from the registry, inverter status logic fixed.
- Doc 07 kept as history (contains outdated Z numbers on purpose); current
  truth is here and in the handbook.

Still open, needs hardware or new data (not code):
- G5 CV-mode current-limit sign (first real bench run).
- The 346 W constant loss term in the PV inverter fit (needs a long clean day).
- Warm-up vs battery-charging interpretation of the FC voltage drift.


## Cross-check against the papers in the folder (2026-10)

Every formula was checked against Veritas IJHE 48 (2023) 12072-12088 (the
reference loss-map paper) and the UFSC PV-electrolysis study.

Agreements (code follows the papers' logic):
- LHV 33.322 kWh/kg: identical to the paper.
- Faraday route with z=2 stoichiometry: the paper uses the same route from
  current via eqs (2)/(10) and carries the same blindness (no flow meter) -
  our triangulation is the stated improvement over exactly this weakness.
- RTE chain algebra: paper eq(17) multiplicative per-stage form is algebraically
  identical to our additive E_out/E_in.
- Tank pV: paper uses the manufacturer P-V table, same concept as Route 2;
  ours adds the real-gas Z correction.
- PV-electrolysis study: H2 flow "not measured directly, calculated from
  internally measured parameters" - the published admission our Route 2 is
  designed to close.

Discrepancies found in OUR numbers (fixed):
- bat.nominal_V was 48 V; the tested Regatron README says the FCM-802 regulates
  the bus to 52 V (48 V is only the factory default). Registry now 52 V, DERIVED,
  CONFIRM at the plant.
- [superseded by D11; comp.* REJECTED] comp.overall_efficiency GUESS was 0.10 +-50%. The Veritas raw data imply
  3.0-5.3% overall for an air-driven booster (33.22 Nm3, 10->200 bar, ideal
  isothermal 3.0 kWh, consumed 56-100 kWh). Re-anchored to 0.04 +-40%, i.e.
  our GUESS now brackets the only comparable datapoint in the folder.
  NOTE: the paper's own eta_Comp-id claim (79.3-91.5%) is irreconcilable with
  its raw numbers; we follow the raw numbers.
- stor.p_max_barg: UFSC paper says 300 bar, installer (H2 Core Systems) says
  200 bar. Working value 200 bar (conservative), CONFIRM at the plant.
- Isothermal compressor work ignores real-gas Z (+5-8% for 35->200 bar);
  documented in compressor.py, inside the GUESS band, corrected only if the
  booster is ever metered.

Not comparable (deliberately):
- EL nameplate 62.4% (ours, 2.4 kW AEM) vs paper 54.0% (22.3 kW industrial
  ELU incl. PSU and purifier): different device class, different boundary.
- Paper RTE 10.2-10.5% electric (real 22.3/31.5 kW system) vs our synthetic
  demo 28.6%: different scale, different boundary, demo cycle open.

## PV preliminary channel back-checks (2026-10)

`test_08_pv_preliminary.py` adds the missing back-checks:
- NOCT model verified at its DEFINITION point (20 C ambient, 800 W/m2 -> 43 C)
  and at the 25 C operating case (48 C). The first draft of the test used the
  wrong reference point - the formula was correct.
- Loss chain closes algebraically; every bar labelled PRELIM (Rule 3).
- Measured mode: AC follows the measurement; inverter bar flagged MEASURED.
- **Inverter back-check against telemetry of the removed legacy building array
  (not F8 evidence)**: energy-weighted
  conversion efficiency over the 22-day window = 0.9719; the PRELIM Euro
  assumption 0.98 deviates only 0.8%. The typical-market anchor is consistent
  with the legacy-array hardware (supports only the generic string-inverter assumption,
  not the F8 inverter; within the 2% sanity bound; note that Euro
  weighting vs our actual load distribution can legitimately shift this).
- Stated limit: the DC-cable bar cannot be verified from the legacy-array data (the
  inverter reports DC at its own terminals) - it stays PRELIM until the real
  cable lengths exist.

## Live-channel preparation round (2026-10-07)

Prepared without further hardware info:
- `loaders/solis.py`: Solis S5-EO1P5K-48 telemetry loader (cloud/datalogger
  CSV formats A/B), discharge-sign convention (+ = battery into bus),
  energy-weighted measured efficiency via battery-side reconstruction
  (E_in = V*I dt over discharge samples). Guarded by `test_09`: synthetic
  60-s export gives eta 0.962 and flips FCInverter to MEASURED.
- `live_feed.py` docstring: per-device live wiring map (EL = Enapter cloud /
  Modbus TCP, Regatron = 20 Hz bridge, Solis = cloud export, PV = SunSpec).
- `report_cli.py pv` now emits `pv_inverter_measured_bar.csv`: the MEASURED
  PV inverter loss bar (E_dc, E_ac, eta) ready to feed chain's loss_map via
  kw_e (E_pv_dc_kWh / E_pv_ac_kWh). Window integral: 7198.41 kWh DC ->
  7021.71 kWh AC, eta 0.9755 (note: differs slightly from the earlier
  load-bin analysis because the integral covers all samples > 0, not the
  >500 W bins).
- FC inverter: measured mode verified in test_09 (eta_is_measured flips).

## Deep-audit round (2026-10, second independent review): 11 fixes

Every finding reproduced numerically before fixing; each has a guard now.

1. **Route-2 pressure term (unit error, factor ~200).** `fso_abs` was
   `0.005 × 1.25 bar = 0.006 bar` instead of 1.25 bar. Fixed; then the first
   fix over-amplified the absolute term by p/Δp; final form: absolute term
   relative to the swing only, amp on the relative terms. Route 2 u now:
   20-bar swing 10.4%, 100-bar 2.9%. Guarded by `test_07`.
2. **Compressor ideal work (arithmetic-mean shortcut).** ln() evaluated at
   (p_in + p_top)/2 overstated a 20→200 bar fill by ~21%, understated
   100→200 bar by ~16%. Replaced by the mole-weighted fill integral
   `isothermal_work_mol_integral` (closed form, verified against brute-force
   summation to 1e-4). Guarded by `test_02`.
3. **Compression anchor corrected twice.** The "56–100 kWh consumed" never
   appears in Bovo et al. (mix-up with the purifier energy). Full text (Tab. 3):
   78.4 + 4.6 kWh for 33.22 Nm³, 40→200 bar. Correct fill-integral ideal work
   1.0–1.3 kWh → overall 1.2–1.6% → registry 0.014 ±30% [superseded by D11; comp.* REJECTED]. The paper's
   eta_CSU = 54.5% is a different quantity (H2/(H2+comp)), not a contradiction.
   DOI now registered: 10.1016/j.ijhydene.2022.11.346.
4. **Monte-Carlo n_cells clip (band artifact).** `_is_fraction` clipped EVERY
   dimensionless entry to [1e-3, 1], including `el.n_cells` = 120 and
   `fc.n_cells` = 120: every draw ran the plant with 1 cell, the compression
   bar collapsed to ~0.03 kWh, and the published band [26.8, 29.9]% sat near
   the point estimate BY ARTIFACT. Discovered because the corrected point
   estimate (24.6%) fell OUTSIDE the old band. Clip now applies only to
   entries whose nominal value ≤ 1. New band: [21.9, 26.6]%. Guarded by
   `test_03` (band must bracket the point estimate).
5. **PV inverter bar energies not reproducible.** Old bar: E_dc 7198 kWh,
   E_ac 7022 kWh (eta 0.9755). Counter over the window: 5190 kWh AC;
   gap-weighted DC integral: 4095 kWh. The old integration stretched night
   values across data gaps. New method: eta from the 16 gap-validated days
   (counter==integral within 2%), E_ac from the counter, E_dc = E_ac/eta
   → 5346 / 5190 kWh, eta 0.9709, loss 155.6 kWh, method recorded in the CSV.
6. **PV bars in the loss map (double count + dead code).** The "capture" bar
   was E_dc − E_ac (that is the inverter loss, mislabelled) and the inverter
   bar applied (1−η) to the AC energy. Additionally `kw_e.get("E_pv_ac_kWh")`
   was always None because E_pv_ac_kWh is a named parameter → the PV bars were
   dead code. Fixed: capture bar = E_stc − E_dc (needs E_pv_stc_kWh),
   inverter bar = E_dc − E_ac. Guarded by `test_03`.
7. **Closure max(statistical, spread) not implemented.** Card G promised it;
   `z_closure` returned both separately. Now `uncertainty_rel` is the max.
   Guarded by `test_02`.
8. **FC control energy bridged gaps** (len × mean-dt). Now observed-time only,
   consistent with the EL/FC gap policy.
9. **EL standby computed but never wired** into the RTE (E_standby_kWh=0.0
   hardcoded). Now `el.get("standby_kWh", 0.0)` feeds `storage_chain_rte`.
10. **test_03 tautology** (`assert X and Y or True`) replaced by explicit
    open-cycle semantics: the demo consumes 132% of production, so
    cycle_closed=True, consumed_matches=False, and rte_closed is asserted.
11. **Registry/doc drift**: volume re-labelled DATASHEET (a nameplate is not
    a measurement per the project's own rules), Yodwong caveat added (PEM
    anchor, AEM device, ±3%), `meas.p_sensor_fso_bar` documented as the
    confirmed-range dependency, five-weakest list regenerated.

Still needs hardware/data (unchanged):
- EL stack current export -> Route 1 live
- Solis channel physically connected (CAN/BMS or datalogger) -> first CSV
- Kaeser energy meter -> compression MEASURED
- Tank temperature sensors -> Route 2 tier 2

## Fix-list round (2026-10-21): 21 items, probes p1-p3 at 0 open

Each item was fixed, run through `tools/probes/run_probes.py` and
`tests/run_all.py`, and committed separately.

1. **Loss map.** `eta_fc` -> `eta_inverter`; plausibility guards (`warnings`,
   `plausible`); the dryer vent is booked only against gas that actually left the
   system; the open cycle closes through an explicit "H2 storage change" bar
   (E_in == sum(bars) + E_out), always present so Monte-Carlo bar shapes stay
   stable. Guarded by `test_03`.
2. **FC control energy** counts modules also for `*_stack_current_A` columns.
3. **PV channel.** `pv.p_dc_stc_W` (BACKLOG); site-loss bars plus a negative
   "Bifacial gain" bar so the bars sum exactly to STC -> AC; measured mode uses one
   MEASURED inverter bar (E_dc - E_ac) and no cable bars.
4. **Monte Carlo.** Negative entries (e.g. `pv.p_tc_pmax_per_K`) keep their sign;
   capped fractions use a truncated normal, so eta_F = 1.00 +- 2% is no longer
   one-sided.
5. **Loaders.** Grafana: duplicate timestamps averaged, thousand-separator dots
   handled, warning per dropped row. Solis: DC input = whole bus draw or `None`.
   Regatron: index from `epoch_s`, ISO only as fallback.
6. **Time bases.** `energy_by_mode` uses the gap-aware weights (no bridging); the
   live feed computes the H2 rate from the elapsed index time.
7. **Hydrogen.** Route 2 tier 3 raises `NotImplementedError`; volume and a common
   temperature offset enter 1:1, Z stays amplified by p/dp; booster work uses
   `G(p) = p ln(p/ps) - p`. The fast-fill bracket is now `hot_end_fill_bracket`.
   `compare_routes`: only same-quantity routes enter the mean and spread;
   production vs tank belongs to the gas-loss estimate only (`test_02`/`test_03`
   adjusted).
8. **Registry decisions.** `meas.p_sensor_fso_bar` = 2.0 bar (0-400 bar gauge,
   DERIVED), thermal 0.8 bar/10 K recorded but not yet in the Route-2 budget;
   `comp.overall_efficiency` = 0.03 +- 40% (Bovo Tab. 3) with
   `comp.specific_energy_kWh_per_Nm3` = 2.3 +- 40% as cross-check;
   `stor.steel_mass_kg` = 1430 kg per bundle (upper bound); `bundle_isolated` is
   required by Route 2 and `loss_map`.
9. **Docs.** `run_hours` corrected to seconds; `total_run_energy` marked
   unconfirmed (~20 J/count inferred); data dictionary extended (Solis, Regatron
   time base, tank).

Still open (needs data, not code):
- `data/processed/pv_retro/pv_merged.csv`: first rows have a counter-like value in
  `grid_Hz` (498728.95); regenerate from the raw export. The meter total
  (5190.3 kWh) starts only on 9 Sept 14:40, so the morning of day 1 is missing.
- Confirm the delivered DCT 541 label and the `bundle_isolated` practice.
- Rest windows after a fill (GS fit); Kaeser energy meter; EL stack current
  export; Solis export with FC currents or a DC current.

