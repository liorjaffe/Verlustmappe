# Verlustmappe: implementation brief (verified against main, HEAD 99b48d9, 2026-10-21)

You are implementing verified fixes in this repository. All findings below were confirmed by
reading and EXECUTING the current `main`. All existing tests pass, so none of these are caught
by the suite today. Work item by item; do not refactor unrelated code.

## Ground rules

- Test runner: `python3 tests/run_all.py` from the repo root (custom runner, no pytest).
- `src/verlustmappe/registry.py` is the single source of truth. Every entry has a `status`
  (DATASHEET / MEASURED / GUESS / ENVELOPE / DERIVED) and an `uncertainty`. Never change a
  registered VALUE without an explicit decision note; you MAY fix comments that contradict
  the entry (item 6 tells you which side is correct).
- Do not hand-edit derived numbers in README.md where a test produces them; item 7 automates that.
- Keep the existing uncertainty discipline in `route2_tank_pv.py` (GUM-style, absolute FSO per
  reading, `amp = p/dp` only for relative terms). Extend it; do not rewrite it.
- Every behavior change gets a test in `tests/`, following the existing numbered-file style.
- Final gate: `python3 tests/run_all.py` must end with `ALL PASS`.

## Item 1 (A3): standby energy is accepted and then thrown away

Files: `src/verlustmappe/balance/e_rte.py` (lines 15-23), `src/verlustmappe/balance/d_loss_map.py`
(around line 91), `src/verlustmappe/devices/electrolyzer.py` (line 71).

Confirmed failure: `storage_chain_rte(10,1,1,5,0.3,0.94,E_standby_kWh=100)` returns `E_in_kWh`
= 12.0. `e_in` (line 17) omits standby; standby appears only in `breakdown` (line 22). The
docstring of `e_rte.py` PROMISES "E_in = E_EL + E_dryer + E_compression + E_standby(charge side)".
Additionally, `electrolyzer.py` line 71 counts standby only from samples with
`P <= 3 * el.power_standby_W` (45 W) INSIDE the charge window, so idle time between charge end
and discharge start is in neither dataframe and is lost even if line 17 were fixed. There is no
"Standby" bar anywhere in `bars`.

Do:
1. In `storage_chain_rte`, add `E_standby_kWh` to `e_in`.
2. In `loss_map()`, compute cycle-level standby from WALL-CLOCK time:
   `standby_kWh = sum(standby_power_W) * ((t_cycle_end - t_cycle_start) - t_active) / 1000`,
   where t_cycle_start/t_cycle_end span charge AND discharge plus everything in between.
   Use registry standby powers: `el.power_standby_W` (15 W, DATASHEET),
   `dry.power_standby_W` (10 W, DATASHEET). The FC-side and PV-side inverter standby powers
   are NOT in any datasheet: add registry entries `inv_fc.standby_W` = 20 W status GUESS and
   `inv_pv.standby_W` = 5 W status GUESS (flagged as assumptions, to be measured).
3. Add a bar `dict(stage="Standby (all devices)", kWh=..., status="GUESS")` to `bars`
   (mix: EL/dryer parts DATASHEET, inverter parts GUESS; pick the weakest status, i.e. GUESS).
4. Pass the cycle-level standby into `storage_chain_rte` so `e_in` includes it.
5. Test: constructing a cycle with standby > 0 must increase `E_in_kWh` by exactly the
   standby amount; the bar must appear with the right kWh.

## Item 2 (A4): compression energy silently under-counted when production exceeds the tank window

File: `src/verlustmappe/devices/booster.py` lines 48-62.

Confirmed failure: with `p_tank_start_barg=50, p_tank_end_barg=66` (1000 L), feeding 5x the
window mass returns the IDENTICAL `ideal_work_kWh` as 1x (0.1629 kWh both times). The surplus
gas is dropped from the compression energy with no warning.

Do: remove the clip. Compute `w_ideal` for the FULL throughput against the window; if
`throughput` exceeds the window mass, keep the full-throughput work and set
`warning="throughput exceeds the tank window mass; window span may not match the production
span"` (and include both masses). Do NOT silently reduce `mol`/`throughput_NL`.
Test: 5x window mass must yield (near-)5x the work of the 1x case, with a warning set.

## Item 3 (A1): Route 2 cannot resolve one charge cycle - add a validity guard

Files: `src/verlustmappe/hydrogen/route2_tank_pv.py` (whole function), registry
`meas.p_sensor_range_bar` = 400, `meas.p_sensor_fso_bar` = 2.0.

Confirmed failure: running the real function,
- 3 bar swing -> uncertainty_rel 96.0%
- 4.5 bar swing -> 64.1%
- 8 bar swing -> 36.1%
- 100 bar swing -> 3.4%
The 3.4% often quoted for Route 2 only holds near 100 bar swings (test_07 asserts it on exactly
that). A demo cycle (14.4 kWh in, ~0.26 kg H2) is a ~4 bar swing in an 800 L tank: unusable.

Do:
1. In `h2_from_tank_pressure`: if `abs(p2 - p1) < 10 * fso_abs` (i.e. < 20 bar with the DCT
   541), return a result dict with `valid=False`, the usual keys set to `None` (or NaN) and a
   `warning` string explaining the minimum swing; do NOT return a usable mass number.
2. Make downstream consumers handle it: `loss_map()` must treat an invalid tank route as
   "route excluded" (drop it from `routes`, set `tank_kWh=None`, add a warning), NOT crash.
3. Define the intended use in the module docstring: Route 2 is a MULTI-DAY window method
   (swings >= 50 bar), not a per-cycle check.
4. IMPORTANT ripple: test_03's synthetic cycle charges 14.4 kWh into `stor.volume_L = 1000`,
   which is a ~3.6 bar swing. After the guard exists, the demo becomes invalid. Extend the
   synthetic charge window (e.g. longer duration or higher power) so the tank swing is >= 50 bar,
   and keep all other test_03 assertions meaningful (recompute the expected bar values).
5. Test: a 4 bar swing returns `valid=False`; a 100 bar swing returns `valid=True` with
   uncertainty_rel in the known range (0.01-0.06).

## Item 4 (A2): split the temperature uncertainty into common + independent per-reading terms

File: `src/verlustmappe/hydrogen/route2_tank_pv.py` lines 45-48, 62, 75-78;
`src/verlustmappe/hydrogen/temperature_model.py`.

Confirmed failure: `u_T_frac = u_T_start / T` is added to `u` ONCE and unamplified, and
`T_end = T_start` is assumed. That treats temperature error as a COMMON offset scaling n1 and
n2 equally, which is only valid for a calibration offset. The real problem after a fill is that
gas and wall temperatures differ (tier 1 uses ambient; measured wall temp is a proxy only in
equilibrated states). The fast-fill information exists only as a separate
`fast_fill_bracket` output that is never combined into `u`. (Quantitative reference point:
a ~15 K gas/wall disequilibrium at one reading moves a small demo swing by roughly -15 to
-20%; a 1 K error moves it by only a few percent. Do not attribute the large effect to 1 K.)

Do:
1. Split temperature into (a) the existing COMMON offset term (keep current treatment) and
   (b) an INDEPENDENT per-reading term `u_T_ind_frac`, added to `u` as
   `(u_T_ind_frac * amp)**2` with `amp = p/dp`, exactly like the Z term.
2. Registry or module constants: `u_T_ind` ~ 1 K for tier 2 (equilibrated), ~ 10-15 K for
   tier 1 right after a fill. Keep the existing +-3 K (tier 1) / +-2 K (tier 2) placement
   values as the common term.
3. For tier 1, additionally fold the existing `hot_end_fill_bracket` spread into `u`
   (quadrature) so the bracket is not a separate, forgettable output.
4. Update test_07 expectations; keep the 100-bar case inside a few percent only if the
   numbers still support it (they may widen slightly; state the new value in the test comment).

## Item 5 (A5): the "H2 storage change" bar is a plug; make the residual honest

File: `src/verlustmappe/balance/d_loss_map.py` lines ~159-171; `tests/test_03_full_chain.py`
(closure assert).

Confirmed failure: `residual = rte["E_in_kWh"] - chain_sum - rte["E_out_kWh"]` is appended as
the bar "H2 storage change (open cycle: +stored / -drawn)", status DERIVED. Algebraically it
equals H2 produced - vent - filter energy - H2 consumed, so any error in any other bar is
absorbed there and the map always closes. test_03's
`assert abs(out["rte"]["E_in_kWh"] - chain - out["rte"]["E_out_kWh"]) < 1e-9` is a tautology.
Also verify whether `wat["energy_kWh"]` includes the filter-train energy
(`water.filter_train_energy_kWh` is a separate field); if it does not, that energy currently
leaks into the residual - include it in `E_in` explicitly.

Do:
1. Compute the storage change INDEPENDENTLY, two ways: (a) from the tank (Route 2, respecting
   the new validity guard), (b) from H2 produced - H2 consumed - vent. Report both in
   `h2_balance`.
2. Rename the plug bar to "Unexplained residual" (status DERIVED), and add a plausibility
   warning when |residual| exceeds a stated tolerance (e.g. 5% of E_in).
3. Replace the tautological closure assert in test_03 with an injection test: build the
   synthetic tank with a deliberate -5% gas loss (e.g. subtract 5% from the solved end mass)
   and assert the code RECOVERS the loss (routes disagree by ~5%, residual stays small, and
   the discrepancy is reported, not absorbed).

## Item 6 (B): compression number - fix the contradictory documentation, keep the value

Files: `src/verlustmappe/registry.py` comment block (~lines 99-111) vs entry (line 112);
`src/verlustmappe/devices/booster.py` docstring (lines 14-21); `README.md` lines 157, 164.

Confirmed state: the registry file contains TWO incompatible readings of Bovo IJHE 48 (2023)
Tab. 3, EACH claiming to supersede the other:
- comment block: "78.4 + 4.6 kWh -> 1.2-1.6% -> registered 0.014 +-30%" and calls the
  56-100 kWh reading "withdrawn";
- entry + booster docstring flip-flop: entry line 112 says "56.36/100.2 kWh -> 1.9-4.3% ->
  decision 2026-10-21: 0.03 +-40%" while the booster docstring still argues for 0.014.
DECISION (do not re-litigate): the registered value is `comp.overall_efficiency = 0.03 +-40%,
status GUESS` from the 56.36/100.2 kWh reading with 10-bar booster inlet and fill-integral
ideal work. The "78.4 + 4.6 kWh" reading is the misreading.

Do:
1. Delete the 78.4+4.6 comment block from registry.py and the corresponding argument in the
   booster.py docstring; leave ONE reading (the 0.03 one) in each file.
2. In the booster docstring and `README.md` lines 156-168, replace "1.4%" / "8.79 kWh" with
   the current behavior (eta 0.03, and whatever the regenerated demo table says - item 7
   will fill it in).
3. Until the Kaeser is metered, report the compression bar as a RANGE: emit the bar kWh
   computed at both 0.014 and 0.03 (or the +-40% band) in the bar's note/warning. Do not
   change the registered nominal value.
4. Do NOT attempt to model eta vs pressure ratio; that needs measurements (out of scope).

## Item 7 (D): generate the README demo table instead of hand-editing it

Files: `src/verlustmappe/reporting/make_register.py` (extend) or a new
`src/verlustmappe/reporting/make_readme_demo.py`; `README.md`.

Confirmed mismatches (README says vs test_03 produces): vent 0.35 kWh vs 0.000
("NOT OBSERVED"); compression 8.79 kWh at 1.4% vs 1.086 kWh at 3%; FC aux 0.30 vs 0.600 kWh;
RTE_open 24.6% / RTE_closed 19.9% vs 25.3%; and the route2 docstring's +-1.25 bar claim.

Do:
1. Write a script that reproduces the test_03 synthetic demo and prints/writes the bar table
   (stage, kWh, status) plus RTE_open, RTE_closed and the MC band into README.md between
   markers you add, e.g. `<!-- BEGIN GENERATED DEMO TABLE -->` / `<!-- END -->`.
2. Run it once so README matches the code; from now on nobody hand-edits those numbers.
3. Fix the stale "+-1.25 bar on 250 bar" text in the route2 module docstring (see item 3).

## Item 8 (E): Monte-Carlo band -> restricted, log-normal eta, honest name

File: `src/verlustmappe/uncertainty/montecarlo.py` (lines 24-25, 32-56, 55 keys selection).

Confirmed: (a) keys include every non-MEASURED numeric registry entry, including `pv.` entries
irrelevant to a storage cycle; (b) all draws are independent, ignoring that
`el.production_rate_NLh` and `el.spec_energy_kWh_per_Nm3` come from the same datasheet;
(c) `comp.overall_efficiency` is drawn from a symmetric relative normal although the energy
is ideal_work / eta, so the low-eta tail is under-represented; (d) registry uncertainties are
chosen ad hoc and treated as 1-sigma normals.

Do:
1. Restrict `keys` to the parameters actually used by the chosen boundary (storage chain:
   el./dry./comp./fc./inv_fc./meas. power + the ones loss_map reads for the cycle). Exclude
   `pv.*` unless an island-RTE band is requested.
2. Draw `comp.overall_efficiency` log-normally (match the +-40% band in log space).
3. Rename the output field/label from "confidence interval" language to "sensitivity band"
   and document that the band depends on the chosen registry uncertainties.
4. Add a per-entry registry field `unc_type` with values like "sigma" (1-sigma normal),
   "range" (min/max), "bound"; set it honestly for the entries the band uses (at minimum:
   comp.overall_efficiency = "range", the datasheet items = "sigma"). Do not silently
   reinterpret range-type entries as normals.

## Item 9 (F): repository hygiene

1. Add `.gitignore`: `.DS_Store`, `__pycache__/`, `*.pyc`. Then `git rm -r --cached` the
   committed `.DS_Store` files and `src/verlustmappe/__pycache__/*.pyc` (both cpython-312 and
   cpython-314 variants are committed).
2. `tests/test_03_full_chain.py` line 9 sets `stor.volume_L` to 1000 and never restores it
   (test_02 does the same pattern). Wrap each in try/finally (or a helper) restoring the
   registry value.
3. Add a minimal `pyproject.toml` so the package is pip-installable and pytest-runnable;
   keep `tests/run_all.py` working.
4. `data/raw/` holds only a README: add a checksum manifest (sha256) of the processed CSV
   inputs, or document the export location, so results can be regenerated.
5. In README, state the PV system boundary explicitly: F8 (28 x BYD455MGEK-36 = 12.74 kWp,
   vertical east facade) is THE PV source for the island RTE; only AC energy entering the
   storage path counts (slice principle); the legacy SMA dataset (5.19 MWh / 22 days) covers
   one inverter/sub-array of the building array and is NOT the storage-chain PV input.
6. Keep the 2026-09-22 FC voltage rise (47.8 -> 50.8 V at constant power) flagged as an open
   interpretation in README (battery charging on the bus is the leading hypothesis); do not
   use it in results.

## OUT OF SCOPE for Copilot (hardware / decisions by the human)

- Enabling the `stack_amperage` export (EL firmware 1.12) and collecting a full day of data.
- Scale or water meter for Route 4.
- Plug-in energy meter on the Kaeser compressor; flow/pressure log on the booster for 2-3
  fills at different start pressures; eventual eta(p-ratio) fit.
- Any second pressure transmitter decision (the 400 bar DCT 541 is installed and decided).

## Acceptance

- `python3 tests/run_all.py` -> ALL PASS, including the new tests.
- `E_standby_kWh > 0` strictly increases `E_in_kWh`.
- 5x window throughput no longer returns 1x work, and warns.
- 4 bar swing -> `valid=False` with warning; loss_map survives it.
- test_03 contains the -5% injection assertion, not a closure tautology.
- README demo table is generated between markers and matches test_03 output.
- Exactly one Bovo reading remains in registry.py and booster.py.
