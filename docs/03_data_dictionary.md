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
| `run_hours`, `total_run_energy` | h, ? | Run Hours, Total Run Energy | counters; energy unit not confirmed, do not use for efficiency |
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

Merge rule: join Enapter (~1 Hz) and fastlog (20 Hz) on the UTC clock
(`loaders/regatron.align_with_enapter`); never merge fast events on the
Enapter clock. `analyze_fastlog.py` (tools/regatron) produces plateau means
per commanded setpoint, the measured terminal V-I characteristic.

## Tank instrumentation (DCT 541 + planned temperature sensors)
| Column | Unit | Source | Meaning |
|---|---|---|---|
| `tank_pressure_barg` | barg | DCT 541 via Modbus RTU | storage pressure, 0.5% FSO, 500 Hz capable |
| `tank_T_top_C`, `tank_T_bottom_C` | degC | planned surface PT100s | stratification pair (de Miguel) |
| `tank_T_gaswell_C` | degC | planned bottom-pipe PT100 | best single estimate of mean gas T (Nexo T3) |

## Manual readings (no telemetry)
| Quantity | How | Used by |
|---|---|---|
| tank pressure at window boundaries | photo of the analog gauge with timestamp | Route 2 |
| tank gas temperature | ambient thermometer unless a tank probe exists | Route 2 |
| Kaeser air-compressor energy | energy meter reading before/after booster run | compression bar |
| feed-water mass | scale on the feed tank | Route 4 |
| battery SoC before/after test | BMS display | battery bookkeeping |

## Unit conventions
NL = normal litre at 0 °C, 101 325 Pa (European convention; Enapter uses it, verified from
their 500 NL/h = 1.0785 kg/day). barg = gauge pressure; the code adds 1.01325 bar for
absolute. Efficiencies are LHV unless labelled HHV. kWh everywhere for energy; the code
converts J internally (1 kWh = 3.6·10⁶ J, 1 Wh = 3600 J).
