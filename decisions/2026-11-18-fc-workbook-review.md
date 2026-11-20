# 2026-11-18 - FC workbook review

The owner approved a review edit set for
`plant/sources/Fuel_Cell_System_Specs_Master_2026-11-12.xlsx` (file name kept;
Overview A2 states the 18 Nov revision; Notes 18 lists the edits). Only the
workbook changed; no TOML, code or test values changed.

Owner decisions recorded here:

- The 34 SLPM nominal H2 flow per FCM-802 is owner-confirmed. Sources: manual
  p. 18 (at the manual rated power 2.4 kW) and Intelligent Energy
  correspondence of 16 Sep 2026 (verbatim, Sources No. 18). It is a
  manufacturer reference point, not a plant calibration. The SLPM T/p basis
  is not confirmed; the 25 Sep 2026 email exists only as a fragment.
- Fuel Cell row 31 (reference conditions) has the role "Model constant".
- The Hybrid Control undervoltage test-abort criterion (row 19) is ASSUMED:
  a project check against the factory restart logic (48 V / 60 s, 46 V,
  manual p. 24), not an FCM function; its duration stays undefined until the
  control code is frozen.
- Manufacturer and site confirmations are deferred, not dropped: Intelligent
  Energy (SLPM basis, two-module purge peak, meaning of the 150 W rated input,
  telemetry units), CAN read-back of the installed factory parameters, Green
  Tech (200 A vs 100 A, cell chemistry/count), site checks (battery variant,
  Solis AC input and grid charging, Lynx RJ10 supply, 1/4 in supply line vs IE
  1/2 in recommendation) and manual p. 12 (PFC inputs/outputs).
- The H2 mass flow meter is out of scope and is not reconsidered.

Later the same day the owner approved the D3b wording in `CONTRACT.md` §6
(`decisions/2026-11-18-fc-inverter-discharge-working-value.md`) and the
workbook row-structure repair: Fuel Cell merged header ranges and row heights
realigned, own rows for telemetry units (59) and Restart Delay (82),
Instruments rows moved up; no Fuel Cell rows deleted (Notes 18).

Known TOML errors for the later rewrite from this workbook: `fc_battery.toml`
calls 48 V the target-voltage factory default (manual p. 24: 52 V);
`fc_inverter.toml` calls the PV-AC 93-95% range the discharge efficiency and
its +/-0.02 band has no source; `fc.toml` marks the manual POC duration as
DERIVED; workbook and TOML keys differ; workbook statuses must be mapped to
the CONTRACT §8 scheme.

2026-11-19, owner-approved status mapping for the FC TOML rewrite (workbook
status -> active D26 vocabulary): Measured -> MEASURED; Datasheet ->
DATASHEET; Calculated -> DERIVED, with the derivation in the source text;
Literature -> DATASHEET_SECONDARY; Assumed -> GUESS; Unknown -> no value
(MISSING). The mapping only translates labels; no value gains an evidence
status it does not have.

2026-11-19, owner decisions for the FC TOML rewrite: (A) an uncertainty
without a source is set to 0.0 (NOT ASSESSED), as for PV on 2026-11-13; this
applies to fc.h2_consumption_g_per_kWh, fc.n_cells, fc.faradaic_efficiency,
fc.control_input_W_max, inv_fc.eta_peak_pv_ac and inv_fc.standby_W. (B)
bat.nominal_V = 48 V, DATASHEET (battery nameplate); the 52 V bus voltage is
not a battery nominal value and would need its own key.

2026-11-19, FC TOML rewrite applied (owner-approved value list):
`plant/fc.toml`, `plant/fc_battery.toml`, `plant/fc_inverter.toml`. Existing
keys kept; two new keys `inv_fc.eta_envelope_lower` / `_upper`; registry 107
-> 109 entries; `tests/reference/plant_parameter_reference.json` updated for
the FC keys only. Result effect: the nameplate FC H2 route reports
uncertainty 0.0 (NOT ASSESSED) instead of 0.05; inverter energies unchanged.
Follow-up maintenance: the `fc_inverter.py` docstring/note still says
"DERIVED 0.94". Next steps: POC plan, then POC implementation; key renaming
separately.

2026-11-19, owner decisions after the independent review of `07d2bf1`:
- FC inverter measured mode follows the PV inverter rule (CONTRACT §6): AC/DC
  of the supplied window is that window's eta; DC - AC is a diagnostic, never
  a booked loss; the booked loss is always modelled, DC x (1 - inv_fc.eta). A
  measured AC of 0 is a measurement, not a missing value; DC = 0 with AC != 0
  is flagged `dc0_ac_nonzero`. A window eta is MEASURED only with an
  independent cross-check (D3b).
- `bat.nominal_V` source/effect text reworded (value unchanged): 52 V is the
  FCM factory-set target, installed setting not read back, bus voltage not
  measured; not a basis for P = V x I on the bus.
- Fixed with tests: FC module channels only `fcN_current_A` /
  `fcN_stack_current_A` (a `batt_current_A` column was counted as a module);
  POC layer 1 rejects negative case rate, duration and power limit.
- The 97% battery round-trip efficiency status belongs to the deferred
  "status of base-type data" decision (START.md).

2026-11-19, owner: automatic FC transfer check instead of key renaming
(`tests/test_plant_fc_vs_workbook.py`). It checks, for `plant/fc.toml`,
`plant/fc_battery.toml` and `plant/fc_inverter.toml`: every key mapped to a
workbook row or explained; row label and workbook key; status per the
approved mapping; FC sources cite their row; every keyed workbook row
classified; known duplicate keys. Status only; values need machine-readable
value/unit columns in the FC workbook (separate owner decision). Key renaming
is not done. Inverter2 workbook findings, update pending owner approval: row
44 still says DERIVED (D3b: GUESS); row 3 says MEASURED for the model identity
read from the nameplate photo (workbook convention, Overview B10) while the TOML
says DATASHEET (owner decision open); row 46 still says measured mode "flips the post to MEASURED"
(superseded by the 2026-11-19 diagnostic rule); duplicate keys in rows 47/80,
50/81, 51/82, 66/85.

2026-11-19, Inverter2 workbook text corrections applied (owner-approved, no
value changes; 27 cells, Notes 13): 0.94 GUESS with the provisional envelope
(rows 44, 79; Sources 6; Notes 2; Overview B6), measured-mode rule (row 46),
FCM 52 V factory target vs 48 V Delayed Start Under-Voltage (row 11), code
file name `devices/fc_inverter.py`, duplicate keys in rows 80-82 and 85
renamed. Owner 2026-11-19: nothing on this unit has been measured; rows 3-5
and 75 (nameplate photo readings) relabelled MEASURED -> Nameplate (=
DATASHEET, as in the compressor workbook). Still open: rows 6 and 65 (site
and project observations) still say MEASURED (owner decision);
standby "20 W +/-50%" in rows 50 and Overview B7 while the TOML has
u = 0.0 under rule A (not changed).
