# 2026-11-19 - FC POC plan (approved 2026-11-19, layer 1 implemented)

Step 2 of the three owner-approved steps (1 FC TOML rewrite - done 2026-11-19;
2 this plan; 3 implementation). Nothing here applies until the owner approves
it. Approved by the owner 2026-11-19; layer 1 implemented the same day
(section 8).

Revision 2026-11-19 (owner): layer 1 works from manufacturer data as given;
validation is layer 3 only (CONTRACT §3). The plan is split accordingly.

## 1 Question

What does the FCM-802 Performance Optimisation Cycle (POC) cost the plant,
first modelled from manufacturer data (layer 1), later checked against
measurement windows (layer 3)?

## 2 Manufacturer data used in layer 1

| Item | Value | Basis | Status |
|---|---|---|---|
| Suspension duration | up to 12 s | manual p. 14, sec. 8.3; Fuel Cell row 62; `fc.poc_max_duration_s` | DATASHEET (bound) |
| Frequency while running | fewer than 15 per hour | manual pp. 8, 14; Fuel Cell row 62 | DATASHEET (bound) |
| Power during POC | reduced or suspended | manual; Fuel Cell row 62 | DATASHEET (qualitative) |
| Load during POC | carried by the battery / external source | manual; Fuel Cell row 62 | DATASHEET (qualitative) |
| Start-up | several POCs in rapid succession | manual; Fuel Cell row 62 | DATASHEET (qualitative, no count) |
| Battery round-trip efficiency | approx. 97% | maker web listing; Internal Battery row 18 | status to be decided by the owner |
| H2 flow during POC | not stated | - | MISSING |

The manual gives bounds, not typical values. Using a bound as the case value
is a deliberate convention (CONTRACT §5: every phase duration needs a
justification) and is named as such in every result.

## 3 Layer 1 model (static, per FC operating point)

Case inputs (each with its justification):

- POC events per hour per module, n: proposed convention 15 (manual bound
  "fewer than 15", used as the conservative case value).
- Suspension duration per event, t: proposed convention 12 s (manual bound).
- Power during suspension: proposed convention "suspended" (0 W from the
  module), the conservative reading of "reduced or suspended".
- FC operating point P (W per module): from the case, as for every FC case.
- Start-up cluster: no count is published; stays open (no number), owner
  2026-11-19.

Computed (model, never presented as measured):

- E_bat per event = P x t per module (battery supplies the load, manual).
  Example: 2000 W x 12 s = 6.7 Wh. This is energy SHIFTED through the
  battery, not lost: the FC recharges it afterwards.
- Suspension phase only: the recovery ramp after a POC is not characterised
  by the manufacturer and is not modelled in layer 1; named as a limitation
  (E_bat may be underestimated).
- E_bat per hour = n x E_bat per event, per module; for two modules the
  hourly sum doubles whether or not their POCs coincide. Coincidence matters
  only for the battery peak power (2 x P), not for the energy.
- Recharge headroom: the FC must deliver the shifted energy in the remaining
  time, so the average module power is P x 3600 / (3600 - n x t). With n = 15,
  t = 12 s this is P x 1.053. If this exceeds the factory output power limit
  2400 W (Fuel Cell row 18), i.e. P above approx. 2276 W per module (with
  the recharge loss included), the
  battery is not recharged and its SoC falls by up to n x E_bat per hour;
  the model reports this as a battery stock change, not as a loss.
- Battery throughput loss: the round-trip loss is attributed to the
  recharge, E_in = E_out / eta_rt, loss = E_in - E_out (convention); shown
  separately, as required for battery throughput (CONTRACT §5). Example at
  2000 W: 100 Wh / 0.97 - 100 Wh = approx. 3.1 Wh per hour per module.
- H2 per event: no manufacturer statement, MISSING (owner 2026-11-19,
  CONTRACT §7). Dependent H2 totals stay open.

Status of every layer 1 POC result: at most the weakest input; with the
bound conventions and the 97% web value it is not DATASHEET.

## 4 Layer 3 validation (later, measurement windows)

Checks whether the layer 1 conventions hold for the measured windows:
events per hour, suspension and recovery duration, battery energy per event.

- Event definition: terminal current below a threshold fraction of the
  pre-event level while the load is unchanged; suspension until the current
  rises again; recovery until it is back to a threshold fraction. Separated
  from standby (below 4 A for 20 s, rows 63, 75, 76), purge (no power
  impact, row 30), fault (flags) and start-up. Events outside the manual
  bounds are flagged, never discarded or clipped (CONTRACT §7).
- Detection thresholds are owner choices: proposed starting values 50%
  (same convention as the Regatron POC backoff) and 90%.
- Data: both modules over CAN with a verified cadence and kept raw export;
  battery current either as residual (load minus FC terminal currents,
  time-aligned on UTC) or direct (option: Lynx Shunt VE.Can, DC
  Distribution row 13); Regatron fast log with the real battery connected
  and `poc_backoff_enabled: false`; constant load at representative levels,
  each at least one hour, plus a cold start.

Exploratory observation, NOT evidence (`data/processed/fc_retro/fc_merged.csv`,
22 Sep 2026, provenance BACKLOG): 12 POC-like dips, from 13:45 on every
9.0-9.2 min (about 6.6 per hour), current to about 0 A for one 5 s sample,
recovery ramp 40-60 s. The load was about 1.2-1.5 kW, well below the module
rating; per the owner the FC behaves differently at a matching load, so the
recovery time is not representative and is not used.

## 5 Step 3 scope (after approval)

- TOML (`plant/fc.toml`), new keys with workbook source: POC frequency bound
  15 per hour (row 62), standby threshold 4 A / 20 s (rows 75-76); case
  conventions (n, t, power during suspension) as owner decisions; battery
  round-trip efficiency with the status the owner sets. Names follow the
  later key renaming.
- Code: layer 1 POC function (E_bat per event and per hour, throughput loss,
  H2 open or from an explicit case assumption) with tests. The layer 3
  detection module follows when campaign data exist. `devices/fc.py` and
  `devices/fc_inverter.py` stay unchanged.
- The analyzer HTML stays the inspection tool; the result path is Python.

## 6 Not in scope

Standby stop/restart loss (Fuel Cell row 97, own later step); purge H2 loss
(row 95).

## 7 Owner decisions

Decided 2026-11-19:

1. Layer 1 conventions: n = 15 per hour, t = 12 s, "suspended" during POC.
2. H2 during POC: MISSING.
3. Start-up cluster: open.
4. Battery round-trip efficiency approx. 97% (maker web listing, Internal
   Battery row 18) is used, marked RECHECK: web cross-check, variant range
   96.8-97.8%, 25 degC, not confirmed for the installed unit.

Still open:

5. Approval of the plan as a whole (then step 3).
6. Layer 3 later: detection thresholds 50% / 90%, battery current residual
   or direct sensor, campaign.

Maintenance noted while preparing this plan: the Regatron README still says
"48 V is only the factory default" for the target voltage (manual p. 24:
52 V), the same error as the old `fc_battery.toml`.

## 8 Implementation (layer 1, 2026-11-19)

- `plant/fc.toml`: `fc.power_limit_W` (2400, DATASHEET), `fc.poc_max_rate_per_h`
  (15, DATASHEET, bound), `fc.poc_case_rate_per_h` (15, GUESS, owner
  convention), `fc.poc_case_duration_s` (12, GUESS, owner convention),
  `fc.standby_uc_A` (4) and `fc.standby_uc_qual_s` (20) (DATASHEET, for layer
  3). `plant/fc_battery.toml`: `bat.round_trip_efficiency` (0.97, DATASHEET,
  RECHECK). All u = 0.0. Registry 109 -> 116.
- The case values are separate GUESS keys because a manual bound used as a
  case value is an owner convention, not datasheet evidence (as for
  `stor.T_assumed_C`); the results are therefore GUESS (weakest wins).
- Code: `poc_layer1(P_W_per_module, n_modules)` in `devices/fc.py`, appended
  as its own section. Deviation from section 5: a separate module would
  break the architecture rule "every device model has a plant file of the
  same name" (`tests/test_structure.py`); the existing `FuelCellSystem` code
  is unchanged. Tests: `tests/test_devices_fc_poc.py`.
- Not done: layer 3 detection (needs campaign data).
