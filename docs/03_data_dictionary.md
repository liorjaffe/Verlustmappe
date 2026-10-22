# Data dictionary

Column vocabulary of the pipeline. Loaders (`src/verlustmappe/loaders/`) translate
raw export names into these. Units are part of the name so a mismatch is visible.

## Time index
All DataFrames are indexed by a timezone-aware UTC `DatetimeIndex`. Grafana exports
carry `-03:00` (Brazil); the loader converts to UTC.

## Fuel cell (IE-LIFT 802 via Enapter/Grafana), one module = one prefix `fc1_`, `fc2_`
| Column | Unit | Raw name | Meaning / caveat |
|---|---|---|---|
| `fc_power_W` | W | Power | terminal (DC/DC output) power |
| `fc1_voltage_V` | V | Voltage | TERMINAL voltage (bus), not stack |
| `fc1_current_A` | A | Amperage | TERMINAL current, not stack; cannot be used for Faraday |
| `fc1_stack_current_A` | A | (not available yet) | stack current; needed for Route 1 |
| `anode_pressure_mbar` | mbar | Anode Pressure | supply-side pressure; drops mark purges |
| `t_in_C`, `t_out_C` | °C | Inlet/Outlet Temperature | coolant/air temperatures |
| `fan_duty`, `louver_pos` | %, - | Fan SP duty, Louver Position Open | thermal management state |
| `dcdc_i_limit`, `dcdc_v_sp` | A, V | DC/DC Current Limit, DC/DC Voltage Set Point | converter set points (proves the DC/DC exists) |
| `run_hours` | s | Run Hours | counter; the name is misleading: it advances 1.0 per SECOND of operation (median d/dt = 1.000). Divide by 3600 for hours |
| `total_run_energy` | ? (~20 J/count, inferred) | Total Run Energy | counter; unit UNCONFIRMED. Terminal energy tracks it at ~19.96 J/count (2026 run). Needs a comparison with a known meter reading; do not use for efficiency |
| `fault_a..d` | bitmask | Fault Flags A-D | decode against the FCM-802 manual |
| `load_current_A` | A | (Regatron, future) | needed for the battery residual |

## Electrolyser (Enapter EL 2.1)
| Column | Unit | Raw name | Meaning / caveat |
|---|---|---|---|
| `power_W` | W | (AC power, to be exported) | AC input incl. power supply |
| `el_stack_current_A` | A | Stack Amperage / stack_amperage | STACK current, Route 1 input; firmware 1.12 collects it |
| `el_stack_voltage_V` | V | Stack Voltage / stack_voltage | stack voltage (electrolyte-change indicator) |
| `h2_flow_NLh` | NL/h | H2 Production, NL/hour | device-computed, Route 3 (correlated with electrical) |
| `h2_total_NL_cum` | NL | Total H2 Produced | cumulative counter |
| `stack_p_bar`, `outlet_p_bar` | bar | H2 Stack / Outlet Pressure | |
| `el_T_C`, `down_T_C` | °C | Electrolyte Tank / Downstream Temperature | |

## PV (SMA Sunny Tripower CORE2 via SunSpec/Enapter blueprint)
| Column | Unit | Raw name | Meaning |
|---|---|---|---|
| `dc_power_W`, `dc_V`, `dc_A` | W, V, A | DC Power/Voltage/Current | array side (SunSpec model 103, both MPPTs summed) |
| `ac_power_W` | W | Real-time Active Power (W) | inverter output |
| `ac_energy_Wh_cum` | Wh | Total Yield (Wh) | cumulative; preferred for daily energies (no integration noise) |
| `inv_T_C`, `grid_Hz` | °C, Hz | Inverter Temperature, Grid Frequency | |

## Solis inverter (loaders/solis.py)
| Column | Unit | Meaning / caveat |
|---|---|---|
| `ac_out_W` | W | inverter AC output to the island load |
| `bus_voltage_V` | V | battery-side bus voltage |
| `batt_current_A` | A | + = battery discharging into the bus |
| `fc1_current_A`, `fc2_current_A` | A | FC terminal currents feeding the same bus (optional) |
| `dc_input_A` | A | measured inverter DC input current (optional, preferred) |

`inverter_eta_measured` uses the WHOLE bus draw: `bus_V * (I_FC1 + I_FC2 + I_batt)`,
or `bus_V * dc_input_A`. Without FC currents or a DC current it returns `eta = None`
(a battery-only DC side would give eta > 1 whenever the FC feeds the bus).

## Regatron G5.BT fast log (bridge fast_sample_loop, 20 Hz, tools/regatron/)
The bridge measures the BUS/LOAD side. Never present `load_current_A` as fuel
cell output: on the hybrid bus the battery also sources/sinks the same bus.
Bridge sign convention: `current_signed_a < 0` = sinking from the bus; the
loader flips it so `load_current_A > 0` = current drawn by the load.

| Column | Unit | Raw fastlog name | Meaning / caveat |
|---|---|---|---|
| `bus_voltage_V` | V | voltage_v | bus voltage at the Regatron terminals (+ SENSE_VOLTAGE_OFFSET_V) |
| `load_current_A` | A | current_signed_a (sign flipped) | load-branch current, positive = drawn by load |
| `load_power_W` | W | power_w | magnitude V x |I| |
| `commanded_value` | A or V | commanded_value | setpoint of the active test mode |
| `mode` | - | mode | cc / cv / cp / idle |
| `output_on`, `estop_latched` | bool | | test state |

Time base: the loader builds the index from `epoch_s` (exact UTC). `timestamp_iso`
is naive local time written by the bridge and is used only as a fallback.

Merge rule: join Enapter (~1 Hz) and fastlog (20 Hz) on the UTC clock
(`loaders/regatron.align_with_enapter`); never merge fast events on the
Enapter clock. `analyze_fastlog.py` (tools/regatron) produces plateau means
per commanded setpoint, the measured terminal V-I characteristic.

## Tank instrumentation (DCT 541 + planned temperature sensors)
| Column | Unit | Source | Meaning |
|---|---|---|---|
| `tank_pressure_barg` | barg | DCT 541 via Modbus RTU | storage pressure, range 0-400 bar gauge, 0.5% FSO = 2.0 bar, 500 Hz capable |
| `tank_T_top_C`, `tank_T_bottom_C` | degC | planned surface PT100s | stratification pair (de Miguel) |
| `tank_T_gaswell_C` | degC | planned bottom-pipe PT100 | best single estimate of mean gas T (Nexo T3) |

Store: 2 bundles x 16 x 50 L steel cylinders; the sensors sit on bundle 1. The
800 L volume holds only while that bundle is valved off from the second one; Route 2
requires the flag `bundle_isolated`.

## Manual readings (no telemetry)
| Quantity | How | Used by |
|---|---|---|
| tank pressure at window boundaries | photo of the analog gauge with timestamp | Route 2 |
| tank gas temperature | ambient thermometer unless a tank probe exists | Route 2 |
| Kaeser air-compressor energy | energy meter reading before/after booster run | compression bar |
| feed-water mass | scale on the feed tank | Route 4 |
| battery SoC before/after test | BMS display | battery bookkeeping |

## F8 plant profile and `pv_f8_*` tables
`pv_account(profile=...)` returns `profile` (`reference_184kWp` default or `F8_12.74kWp`).
Profile fields: `eta_module`, `gamma_pmax` (1/K), `noct_C`, `bifacial_gain`, `p_dc_stc_W`,
`A_array_m2`, `module_status`, `warning`.

| File | Columns |
|---|---|
| `results/tables/pv_f8_losses.csv` | `stage`, `kWh`, `status` (PRELIM/DERIVED/MEASURED), `note` (DERIVED label of the temperature bar) |
| `results/tables/pv_f8_summary.csv` | `quantity`, `value`, `unit`: profile, bars (status composition), STC potential, DC, AC, capture ratio, eta DC-to-AC, warning |

`PVSystem.account(..., p_stc_W=None)` adds `p_stc_source` whenever `H_poa_kWh_m2` is given:
"explicit p_stc_W argument" or "registry default (12740 W, F8 array) - override p_stc_W for other plants".

SolisCloud: `loaders/solis_live.STATION_F8_A` / `STATION_F8_B` (SN ...0007 / ...0009,
station id 1298491919449567877, API-verified 2026-10-22; the metadata CSV rounds 17-digit ids
and must not be used for station ids). Always filter per inverter SN (`f8_inverters()`,
`f8_live_dfs()`); station-level calls mix all inverters.

### SolisCloud live + history (`loaders/solis_live.py`)

| Function | Returns | Notes |
|---|---|---|
| `solis_live_df` | Single-row UTC DataFrame, `ac_power_W` | Prints STALE WARNING when `dataTimestamp` is older than 15 min; the endpoint returns the LAST value for offline inverters, so a stale row is not live data. |
| `solis_day_df(sn, date)` | 5-min day curve: `ac_power_W`, `e_today_Wh`, `dc_V_mppt1..4`, `dc_A_mppt1..4`, `dc_power_W` | `dc_power_W` is the sum of `uPv*iPv` channels. |
| `f8_day_dfs(date)` / `f8_range_dfs(start, end)` | Curves for both F8 inverters | Each inverter is requested by serial number. |
| `f8_day_balance(start, end)` | Per-day table: `e_ac_counter_kWh`, `e_dc_channel_kWh`, `eta_dc_ac` | E_AC is MEASURED from the `eToday` counter; E_DC is PRELIM from DC channels; `eta_dc_ac` is diagnostic only. |
| `energy_kWh(series, dt_s=300)` | Integrated series energy in kWh | Uses the nominal sample interval. |

Verified unit conventions: `inveterDetail` reports `pac` in kW and `eTotal` is
assumed MWh (verify `eTotalStr` when the device reports again); `inverterDay`
reports `pac` in W and `eToday` in kWh. Unit strings are EMPTY in inverterDay
records, so fixed factors are used with no unit-string normalisation.

E_DC from the `uPv`/`iPv` channels runs ~+3-4% above the `eToday` counter
(verified 2026-09-10..15, both inverters). `eta` derived as
`e_dc_channel/e_ac_counter` is NOT a valid efficiency; the F8 inverter
efficiency stays DERIVED from the registry until an S6-GR1P6K datasheet or a
dedicated measurement exists. `eToday` (counter) is the E_AC reference at the
F8 boundary.

## Unit conventions
NL = normal litre at 0 °C, 101 325 Pa (European convention; Enapter uses it, verified from
their 500 NL/h = 1.0785 kg/day). barg = gauge pressure; the code adds 1.01325 bar for
absolute. Efficiencies are LHV unless labelled HHV. kWh everywhere for energy; the code
converts J internally (1 kWh = 3.6·10⁶ J, 1 Wh = 3600 J).
