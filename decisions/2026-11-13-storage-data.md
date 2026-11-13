# 2026-11-13 - Owner storage data decisions

Evidence: `plant/sources/Storage_H2_System_Specs_Master.xlsx`, all five sheets
reviewed; SHA-256 `ce2cab4c9e42d9cffcddc759e27d750393a971c7897b43e4dd35eebe27657c99`.
Owner explicitly authorizes the following changes only:

- Withdraw `stor.p_work_barg`. Master row 6 / Sources S7 is an installer statement,
  not a valid working-pressure source for this plant; the UFSC analogy is not evidence.
  No new setpoint or silent fallback. `stor.p_max_barg` remains 300 barg PS only;
  pressure is an explicit input, measured for validation.
- Keep `stor.steel_mass_kg` = 1430 kg, DATASHEET: Master row 28 / Sources S1,
  nameplate photo `20261001_083001`, TARA including the frame. This is NOT
  thermally effective steel mass. Effective mass stays open; GS fit already runs
  gas-only without it. Using TARA thermally requires an explicit upper-bound assumption.
- Replace the superseded multi-point/type-K concept with one Pt100, 4-wire,
  class A on the insulated cylinder shell, lower/middle near the outlet valve:
  Master row 56 / Sources S7 (`00 CURRENT STATE`, decision 2026-10-08),
  Corrections row 8. Keep BACKLOG. Owner confirms NOT installed, no hardware ordered,
  no measured tank temperature. Wall temperature is a gas-temperature proxy only in
  equilibrated states. Inline thermowell remains open (Master rows 57-58 / Sources S13).
- Update the snapshot and pinned count only for these corrections (109 to 108 keys),
  replacing the guard for the withdrawn key. No numerical uncertainty or tolerance changes.
  PS text loses its reference to the removed key; PS value/status remain unchanged.

Current-tree equivalents: `tests/test_plant_blocked_keys.py` and
`tests/test_plant_snapshot.py`. The cited `d_loss_map.py`, `test_34`, `test_35` and
`test_37` files are not present; no current source reads the withdrawn working-pressure key.
`registry.py` loads TOML; no second storage section is added there.

Calculated/EOS workbook rows are not imported. Other storage parameters and existing
uncertainties stay unchanged; this approval is not a full certification of those entries.
Sources are traced through the workbook; original photos/PDFs/notes/correspondence are
not independently available/verified here.

## Follow-up owner approval: provisional temperature and reference naming

- Suspend only the Pt100 data path (no integration or required channels), not procurement
  planning. The single shell Pt100 concept and inline alternative remain BACKLOG.
  Enapter telemetry must not be substituted for tank temperature.
- Register `stor.T_assumed_C` = 20 degC, GUESS, for provisional storage/booster calculations.
  Uncertainty remains NOT ASSESSED, not zero error. Missing explicit temperature is resolved
  from that entry; usage is identified in results. Route 2 flags its uncertainty incomplete
  when this unassessed assumption contributes. Existing numeric allowances stay unchanged.
- Sensitivity is independently derived from n = pV/(ZRT): at fixed p, V, Z,
  d(ln n)/dT = -1/T; -100/293.15 = -0.34112195 %/K at 20 degC.
  This is a local sensitivity, not a permissible temperature band or uncertainty; actual
  real-gas sensitivity also contains -d(ln Z)/dT. No new EOS constant is imported.
- Use an approved real tank-temperature source in place of the assumption when available.
  Other device temperatures and telemetry remain unchanged. GS-fit ambient temperature
  is not a tank measurement and its separate interface remains unchanged.
- Keep generic/synthetic temperature functions; reject Route 2 tier=2 without its explicit
  T_top_C/T_bottom_C input instead of silently returning the ambient assumption as tier 2.
  Pylance references and source search found only test callers, including one tier=2 call
  with both inputs supplied; no current report caller depends on the missing-input fallback.
- Rename the parameter reference to `tests/reference/plant_parameter_reference.json`;
  update its test reference and description. It is a consciously owner-approved drift
  baseline, not a historical freeze or physical proof; Git retains past versions.
  Existing numerical expectations and tolerances stay unchanged. The additional approved
  assumption brings the parameter count back to 109; no withdrawn working pressure returns.

## Follow-up owner approval: sensitivity and temperature uncertainty

- Supersede the prior unassessed-temperature-uncertainty convention only: keep
  `stor.T_assumed_C` at 20 degC, GUESS. The chosen +/-10 K band has a rectangular
  distribution, standard uncertainty 10/sqrt(3) = 5.773502691896 K. No measured
  or seasonal coverage is claimed. Registry `uncertainty` stores its standard
  relative value with respect to absolute 293.15 K: 0.019694704731012306.
  Code converts it back to K when needed; no additional temperature parameter
  or uncertainty semantics change for other devices.
- Propagate the approved fixed-Z first-order u_T/T approximation into stock mass
  and Route 2's budget. Keep the existing 3 K allowance as a separate independent
  term. For two assumed states use a fully common offset by explicit owner model
  choice, not a factual claim about real temperature errors. Different pressures
  have different Z(T) sensitivities; u_T/T is an approximation, not the exact
  derivative of the project's real-gas mass difference.
- Mixed explicit/assumed states remain incomplete pending correlation/propagation
  reassessment. Only the newly quantified temperature contribution is completed;
  other inputs/uncertainty terms and the open hydrostatic volume check are unchanged.
  Model uncertainty completeness never means measured or validated closure.
- Workbook Master row 42: C/D/E/G/O updated, status F unchanged. Estimated-mass
  sensitivity at fixed measured pressure and assumed temperature, 300 bar absolute /
  20 degC: -100/(1.192*293.15) = -0.28617641975 %/K, displayed as -0.286.
  The 1.192 project Z-table anchor supersedes fixed-Z context for this row only;
  other workbook EOS rows and their separate review remain untouched.
  Updated workbook SHA-256:
  `d248c0d1c4781795af055a6ca09d01d2eedde3c54d8ba7bbebf721145ee1ee51`.
- Independent stdlib-only reference `tests/reference/hand/storage_temperature.py`
  committed as `4e84a05` BEFORE its regression test was written. It derives both
  the project-formula local derivative and ideal/fixed-Z context without importing
  implementation output. The test compares a central log-mass derivative to this
  independent reference, and verifies the uncertainty budget and mixed-state flag.
- No Noble-Abel range or constant adopted; no other device changes or tolerance
  widening. Snapshot change is limited to the released temperature entry's metadata
  and uncertainty; existing masses, temperatures, limits and statuses stay unchanged.

## Follow-up owner approval: separate static modelling and band analysis

The owner approves keeping 20 degC as the defined provisional static scenario
temperature while moving the freely chosen +/-10 K band out of the main run.
Stock and Route 2 perform band propagation only when explicitly requested with
`analyze_temperature_uncertainty=True`. Nominal masses and temperatures are identical
between the main and analysis runs; existing Route 2 uncertainty terms, including
3 K, are preserved. Mixed-source correlation blocks only the requested band analysis,
not a calculation at two explicitly defined model states.

Keep the registered band and independent sensitivity reference for optional analysis;
do not delete or silently reinterpret them. Results identify whether analysis was
requested, remain computed/modelled, and never claim measured temperature or validation.
Pt100 remains suspended with planning retained as BACKLOG. No thermal dynamics or new
measurement integration is implemented by this change. For future dynamics, scenario
temperatures can be supplied by a time profile or approved thermal model; measurement
evaluation remains a separate layer.

## Follow-up owner approval: pause independent Route 2

Owner confirms DCT 541 is not installed, like Pt100. The device title now names
storage only; instrumentation remains separately documented as planning.
Independent `h2_from_tank_pressure` returns UNAVAILABLE with no numerical quantities
or uncertainty. It cannot be reactivated by supplying scenario values.

Retain existing pVT and hypothetical uncertainty physics as the explicitly synthetic
`model_tank_pressure_change`, with a distinct route identity and no validation
eligibility. Tests use this model explicitly; no physics tolerance is changed.
`compare_routes` excludes paused tank routes and synthetic/non-eligible entries before
numeric access, and reports the reason for unavailability. No tank residual is formed.
Synthetic legacy residual assertions are replaced by explicit absence assertions;
independent same-quantity non-tank comparison tests remain active.

Reactivation is a future owner-approved implementation, not an automatic hardware flag:
independent pressures, suitable gas-temperature determination, active volume and valve
state, aligned time windows and gas-flow accounting must be established. The shell
Pt100 concept alone does not establish suitable transient gas temperature.
