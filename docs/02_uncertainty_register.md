# Uncertainty register

All assumptions in the model, sorted from weakest to strongest. Generated from
`src/verlustmappe/registry.py` by `reporting/make_register.py`; edit the registry, not this file.

Status: BACKLOG = placeholder, MUST be replaced. GUESS = assumption bounded only by literature/physics.
PRELIM = typical-market value, real hardware not yet chosen. DERIVED = computed from
other entries. DATASHEET = manufacturer claim. MEASURED = measured by us.
OWNER_DECISION = project decision by the owner. DATASHEET_SECONDARY = secondary source with a known conflict.
REJECTED = legacy-only, device basis wrong; never an input of the new core (DECISIONS D11).

u class (computed, DECISIONS D26): `assessed` = u > 0. With u = 0.0: `exact` only for OWNER_DECISION and the TOLERANCE_BAND keys `meas.p_sensor_fso_bar`, `meas.p_sensor_thermal_bar_per_10K`; every other entry is `NOT ASSESSED` (value exists, uncertainty unquantified; DERIVED alone does not mean exact). Currently 59 of 109 entries are NOT ASSESSED and 4 are exact with u = 0.0. Computation is never blocked; headline numbers are gated (D21/D26).

| Status | Key | Value | Unit | Rel. unc. | u class | Source | What it drives |
|---|---|---|---|---|---|---|---|
| REJECTED | `comp.overall_efficiency` | 0.03 | - | 0.4 | assessed | Bovo IJHE 48 (2023) part 1, Tab. 3: 56.36 / 100.2 kWh compression for 33.22 Nm3 (full / half load), 10-bar booster inlet, fill-integral ideal work -> overall 1.9-4.3%; decision 2026-10-21: 0.03 +-40%. Our Kaeser+Maximator chain may differ. MEASURE it. | compression loss bar; MUST be replaced by Kaeser energy measurement |
| REJECTED | `comp.specific_energy_kWh_per_Nm3` | 2.3 | kWh/Nm3 | 0.4 | assessed | Bovo IJHE 2023 Tab. 3: 60.28/56.36/100.2 kWh per 33.22 Nm3 -> 1.81/1.70/3.02; midpoint of full/half power. Cross-check only; the model uses comp.overall_efficiency | pressure-independent sanity check of the compression bar |
| REJECTED | `comp.pressure_ratio` | 60 | - | 0.0 | NOT ASSESSED | Maximator DLE 30-2 TDS | stall pressure check |
| REJECTED | `comp.stroke_volume_cm3` | 120 | cm3/double stroke | 0.0 | NOT ASSESSED | Maximator DLE 30-2 TDS | flow capacity check |
| REJECTED | `comp.max_cycles_per_min` | 100 | 1/min | 0.0 | NOT ASSESSED | Maximator DLE 30-2 TDS | flow capacity check |
| REJECTED | `comp.min_suction_bar` | 20 | bar | 0.0 | NOT ASSESSED | Maximator DLE 30-2 TDS | storage lower pressure limit |
| BACKLOG | `bat.capacity_Ah` | 100 | Ah | 0.05 | assessed | PLACEHOLDER - enter the real battery capacity | SoC bookkeeping route for the battery branch |
| BACKLOG | `stor.temp_sensor_planned` | multi-point (top + bottom) PT100 class A or type-K, surface + gas-well; papers recommend bottom-pipe region as closest to mean gas temp (Nexo study: T3) and top/bottom pair for stratification (de Miguel IJHE 2015) | - | 0.0 | NOT ASSESSED | see handbook card C and docs/05_tank_thermal_sensing.md | Route 2 temperature input; replaces the ambient-T assumption |
| BACKLOG | `inv_pv.eta_pv_ac_peak` | 0.966 | - | 0.0 | NOT ASSESSED | S6-GR1P6K datasheet pending - the registered 0.966 / 0.93-0.95 belong to the S5-EO1P5K-48 (FC-side inverter) and must not be used for the F8 PV inverter | not valid for the F8 PV inverter; retain only as historical S5-EO1P5K-48 data |
| BACKLOG | `inv_pv.eta_manual_range` | 0.93-0.95 | - | 0.0 | NOT ASSESSED | S6-GR1P6K datasheet pending - the registered 0.966 / 0.93-0.95 belong to the S5-EO1P5K-48 (FC-side inverter) and must not be used for the F8 PV inverter | not valid for the F8 PV inverter; retain only as historical S5-EO1P5K-48 data |
| BACKLOG | `cable.distance_pv_inverter_m` | None | m | 0.0 | NOT ASSESSED | UNKNOWN - to be measured once layout exists | drives cable losses |
| BACKLOG | `cable.distance_inverter_EL_m` | None | m | 0.0 | NOT ASSESSED | UNKNOWN - to be measured once layout exists | drives cable losses |
| GUESS | `dry.vent_fraction` | 0.04 | fraction of throughput | 0.5 | assessed | ASSUMPTION: TSA/PSA regeneration vents the cartridge hold-up; unmeasured | gas loss bar in the loss map; bound it via long-run tank-pV vs Faraday residual |
| GUESS | `inv_fc.standby_W` | 20 | W | 0.5 | assessed | ASSUMPTION: datasheet/manual do not publish idle consumption; 20-50 W typical for 48 V off-grid class | FC inverter standby bar |
| GUESS | `meas.power_rel_unc` | 0.02 | - | 0.5 | assessed | ASSUMPTION: device-reported power (Enapter (EL) and legacy building-array telemetry), no independent power analyser yet | floor of every efficiency's uncertainty |
| GUESS | `el.n_cells` | 120 | - | 0.05 | assessed | ASSUMPTION consistent with 2400 W / (120 x 2.0 V) = 10 A; CONFIRM from Enapter (stack spec not public) | Faraday route scales linearly with this number |
| GUESS | `fc.n_cells` | 120 | - | 0.05 | assessed | ASSUMPTION (IE-LIFT stack spec not public); CONFIRM | reverse-Faraday route |
| GUESS | `el.faradaic_efficiency` | 0.98 | - | 0.03 | assessed | ASSUMPTION: PEM literature current efficiency >96% (Yodwong et al., Energies 2020, 13, 4792, DOI 10.3390/en13184792). CAVEAT: the paper is PEM; our device is AEM with 35 bar output pressure, where crossover raises faradaic losses; 0.98 is carried as an extrapolation and must be validated from the stack-current route | Faraday route H2 mass; blind to shunt current and crossover |
| GUESS | `fc.faradaic_efficiency` | 1.0 | - | 0.02 | assessed | ASSUMPTION: all stack current from H2 oxidation (no crossover) | reverse-Faraday route |
| GUESS | `water.filter_train_power_W` | 0.0 | W | 0.0 | NOT ASSESSED | ASSUMPTION: Popular Filtros cartridge train is purely hydraulic; BUT a pump control panel (bomba) was photographed in the water path - verify on site | pre-treatment energy bar; NOT 0 if the pump feeds the RO |
| GUESS | `pv.string_config` | 2 strings x 7 modules per inverter (assumed; verify at the DC junction boxes) | - | 0.0 | NOT ASSESSED | ASSUMPTION from array design 2026-10-21 | string design checks only (Voc cold, Vmp window) |
| PRELIM | `pv.shading_rel` | 0.02 | - | 0.8 | assessed | PRELIMINARY: shading/snow/edge 0-5%, site-specific, UNKNOWN until layout exists | shading bar |
| PRELIM | `pv.soi_uncertainty_rel` | 0.03 | - | 0.5 | assessed | PRELIMINARY: irradiance-sensor uncertainty on capture-ratio (thermopile/pyranometer class) | capture-ratio bar once a pyranometer exists |
| PRELIM | `inv_pv.standby_W` | 5 | W | 0.5 | assessed | PRELIMINARY: typical standby/night consumption 1-10 W | PV inverter standby bar |
| PRELIM | `cable.dc_loss_rel` | 0.01 | - | 0.5 | assessed | PRELIMINARY: typical DC-side wiring loss 1-2% for short, well-sized runs; DISTANCES UNKNOWN - placeholder until real lengths/gauges exist | DC cable bar |
| PRELIM | `cable.ac_loss_rel` | 0.005 | - | 0.5 | assessed | PRELIMINARY: typical AC-side loss 0.5-1% for short runs | AC cable bar |
| PRELIM | `pv.soiling_rel` | 0.02 | - | 0.5 | assessed | PRELIMINARY: typical soiling 1-4% (rainy coastal climate, no cleaning contract); Florianopolis is coastal+rains, low end plausible | soiling bar |
| PRELIM | `pv.mismatch_rel` | 0.01 | - | 0.5 | assessed | PRELIMINARY: module mismatch 0.5-2% | mismatch bar |
| PRELIM | `inv_pv.eta_euro` | 0.98 | - | 0.01 | assessed | PRELIMINARY: typical Euro efficiency 97-98% for modern string inverters; no F8-specific datasheet yet (D6 open). F8 cross-checks must come from Solis data (f8_day_balance) | PV DC->AC conversion bar |
| PRELIM | `inv_pv.eta_peak` | 0.985 | - | 0.005 | assessed | PRELIMINARY: typical max efficiency 98-98.5% | peak reference only, NOT for energy accounting |
| PRELIM | `inv_pv.mppt_efficiency` | 0.995 | - | 0.005 | assessed | PRELIMINARY: typical MPPT efficiency >99% | folded into conversion bar unless measured separately |
| DERIVED | `el.startup_duration_s` | 990 | s | 0.15 | assessed | UFSC PV-electrolysis study: EL2.1 ramp to nominal after ~990 s | operating-mode partition: startup window length |
| DERIVED | `bat.nominal_V` | 52 | V | 0.02 | assessed | Regatron README (tested): FCM-802 regulates the bus to 52 V; 48 V is only the factory default. CONFLICTS with the earlier 48 V assumption - CONFIRM at the plant | battery SoC energy conversion; P=V*I bookkeeping |
| DERIVED | `inv_fc.eta` | 0.94 | - | 0.02 | assessed | DERIVED: midpoint of the instruction-manual range (93-95%) as the battery->AC discharge efficiency; the datasheet 96.6% refers to the PV-AC path which we do NOT use for the FC discharge. MEASURE on the installed unit | FC DC->AC conversion bar (discharge side) |
| DERIVED | `water.spec_water_L_per_NL_stoich` | 0.0008037 | L/NL | 0.001 | assessed | DERIVED from M_H2O/M_H2 x molar volume (18.015/2.016/22.414); cross-check for the datasheet value | stoichiometric water demand per NL H2 (route4_water.py ratio) |
| DERIVED | `meas.p_sensor_fso_bar` | 2.0 | bar | 0.0 | exact | 0.5% FSO x 400 bar (IEC 61298-2), derived from range and accuracy | absolute pressure error per reading |
| DERIVED | `meas.p_sensor_thermal_bar_per_10K` | 0.8 | bar/10K | 0.0 | exact | 0.2% FSO / 10 K x 400 bar, derived | pressure error during fast fills (not yet in the Route 2 budget) |
| DERIVED | `fc.poc_max_duration_s` | 12 | s | 0.0 | NOT ASSESSED | FCM802_Test research plan / user manual | POC event window |
| OWNER_DECISION | `sys.n_rotex` | 4 | - | 0.0 | exact | owner decision 2026-10-27, SOURCES.md | none yet |
| OWNER_DECISION | `sys.p_h2_out_project_barg` | 300 | barg | 0.0 | exact | owner decision 2026-10-27 (D12), SOURCES.md | none yet |
| DATASHEET_SECONDARY | `kaeser.p_package_dealer_kw` | 6.2 | kW | 0.0 | NOT ASSESSED | dealer listing, conflicting pressure basis, SOURCES.md | none yet; uncertainty NOT assessed (owner to set) |
| DATASHEET | `water.ro_power_standby_W` | 3.0 | W | 0.33 | assessed | BWT EBA sec. 2: '<3 W standby'; unit stays powered -> continuous base load | water-system energy bar, standby share |
| DATASHEET | `stor.steel_mass_kg` | 1430 | kg | 0.2 | assessed | nameplate TARA 1430 kg per bundle (16 cylinders + frame); upper bound, the frame is not fully at gas temperature | thermal mass of the tank in the GS fit |
| DATASHEET | `el.water_consumption_mLh` | 400 | mL/h | 0.1 | assessed | Enapter EL 2.1 datasheet | Route 4 (water balance) expectation |
| DATASHEET | `water.spec_water_L_per_NL` | 0.0008037 | L/NL | 0.1 | assessed | EL 2.1 datasheet '~400 mL/h' at 500 NL/h nominal, rounded to 0.4 L/h; exact value = stoichiometric minimum 9.0 g H2O / g H2 (same ratio as hydrogen/route4_water.py: 0.4019 L/h at 500 NL/h) | scales the water demand with the ACTUAL H2 production (part load) |
| DATASHEET | `pv.degradation_per_year` | 0.0071 | 1/year | 0.1 | assessed | BYD MGK-36 datasheet Rev.06 linear power warranty -0.71 %/yr. Superseded PRELIM: 0.004 | multi-year studies only |
| DATASHEET | `el.power_standby_W` | 15 | W | 0.05 | assessed | Enapter EL 2.1 datasheet | standby loss bar in the loss map |
| DATASHEET | `dry.power_standby_W` | 10 | W | 0.05 | assessed | DRY 2.1 datasheet | standby loss |
| DATASHEET | `water.ro_perm_Lh` | 120.0 | L/h | 0.05 | assessed | BWT bestaqua 14ROC COFFEE EBA sec. 2.2 (2 L/min at 15 C) | RO production capacity; sets RO duty for the EL water demand |
| DATASHEET | `fc.h2_consumption_g_per_kWh` | 70 | g/kWh | 0.05 | assessed | IE-LIFT 802 nameplate: '<70 g per kWh' at 25 C, beginning of life | nameplate H2 route. NOTE: it is an UPPER BOUND on consumption, hence a LOWER BOUND on efficiency (42.9% LHV), and makes FC efficiency a constant by construction. Load dependence needs the stack-current route. |
| DATASHEET | `fc.control_input_W_max` | 150 | W | 0.05 | assessed | IE-LIFT 802 nameplate 'Rated Input 150 W max' | auxiliary/control energy on discharge; nameplate MAX, so an upper envelope |
| DATASHEET | `pv.noct_C` | 45 | degC | 0.05 | assessed | BYD MGK-36 datasheet Rev.06: 45 +-2 degC. Superseded PRELIM: 43 | cell temperature model: T_cell = T_amb + (NOCT-20)/800 * G |
| DATASHEET | `el.spec_energy_kWh_per_Nm3` | 4.8 | kWh/Nm3 | 0.03 | assessed | Enapter EL 2.1 datasheet, beginning of life | FALLBACK H2 estimate when no stack current is logged; WARNING: makes EL efficiency a constant 62.4% by construction |
| DATASHEET | `dry.spec_energy_kWh_Nm3` | 0.045 | kWh/Nm3 | 0.03 | assessed | DRY 2.1 datasheet | alternative dryer energy estimate: flow-proportional |
| DATASHEET | `pv.p_tc_pmax_per_K` | -0.0038 | 1/K | 0.03 | assessed | BYD MGK-36 datasheet Rev.06: -0.380 %/degC (2021 brochure lists -0.352; Rev.06 is the newer official document). Superseded PRELIM: -0.0029 | cell-temperature derating |
| DATASHEET | `el.production_rate_NLh` | 500 | NL/h | 0.02 | assessed | Enapter EL 2.1 datasheet (ELE21-DTS-COM02) | nominal H2 output; cross-check for Faraday route |
| DATASHEET | `el.power_operative_W` | 2400 | W | 0.02 | assessed | Enapter EL 2.1 datasheet | nominal AC input; steady-state expectation |
| DATASHEET | `dry.power_operative_W` | 200 | W | 0.02 | assessed | DRY 2.1 datasheet | dryer electrical loss bar; NOTE datasheet also states 0.045 kWh/Nm3 at 2.5 Nm3/h = 112 W average, so 200 W is an UPPER envelope |
| DATASHEET | `water.ro_power_op_W` | 200.0 | W | 0.02 | assessed | 14ROC COFFEE nameplate 'Leistung 200 W' + EBA sec. 2 | water-system energy bar, production share |
| DATASHEET | `pv.module_efficiency_STC` | 0.209 | - | 0.01 | assessed | BYD MGK-36 datasheet Rev.06 (2024), 455 W class; Inmetro 006667/2021 class A 20.90 %. Superseded PRELIM: 0.220 (typical TOPCon) | nominal DC power per m2 of array |
| DATASHEET | `inv_fc.eta_peak_pv_ac` | 0.966 | - | 0.01 | assessed | Solis datasheet: peak efficiency PV-AC path (MPPT + inverter) | PV-AC peak reference; NOT the battery-discharge path |
| DATASHEET | `stor.volume_L` | 800 | L | 0.005 | assessed | VITKOVICE cylinder nameplate (photo 20261001_083001): water volume 800 L. Status DATASHEET, not MEASURED: a nameplate is a manufacturer claim per this project's own status definitions. Hydrostatic or geometric confirmation still open | Route 2 (tank pV) mass scales linearly with this |
| DATASHEET | `el.h2_purity` | 0.999 | mol fraction | 0.0005 | assessed | Enapter EL 2.1 datasheet (35 bar) | mass bookkeeping: impurities are not H2 |
| DATASHEET | `el.output_pressure_barg` | 35 | barg | 0.0 | NOT ASSESSED | Enapter EL 2.1 datasheet | compressor inlet pressure |
| DATASHEET | `dry.rate_Nm3h` | 2.5 | Nm3/h | 0.0 | NOT ASSESSED | DRY 2.1 datasheet (35 bar version) | capacity check |
| DATASHEET | `dry.max_h2_content_NL` | 47 | NL | 0.0 | NOT ASSESSED | DRY 2.1 datasheet (safety: max H2 in device) | upper bound of H2 lost per regeneration blow-down |
| DATASHEET | `water.wcf` | 0.5 | - | 0.0 | NOT ASSESSED | BWT EBA sec. 2.2: Water Conversion Factor, factory setting approx. 50% | raw feed = permeate / WCF; concentrate = feed - permeate |
| DATASHEET | `sys.p_h2_out_nameplate_barg` | 400 | barg | 0.0 | NOT ASSESSED | HULC system nameplate, SOURCES.md | none yet |
| DATASHEET | `sys.p_h2_in_barg` | 35 | barg | 0.0 | NOT ASSESSED | HydroHulc TDS p.2, SOURCES.md | none yet |
| DATASHEET | `hulc.mod.q_h2_max_nm3h` | 5 | Nm3/h | 0.0 | NOT ASSESSED | HydroHulc TDS p.2 ('up to'), SOURCES.md | none yet |
| DATASHEET | `hulc.m140.limits` | 140 | barg | 0.0 | NOT ASSESSED | HydroHulc TDS p.2, SOURCES.md | none yet |
| DATASHEET | `hulc.m400.limits` | 400 | barg | 0.0 | NOT ASSESSED | HydroHulc TDS p.2, SOURCES.md | none yet |
| DATASHEET | `hulc.pl_max_barg` | 10 | barg | 0.0 | NOT ASSESSED | Maximator catalog, upper end of range 1-10, SOURCES.md | none yet |
| DATASHEET | `hulc.s1.i` | 15 | - | 0.0 | NOT ASSESSED | DLE 15 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s1.v_disp_cm3` | 244 | cm3 | 0.0 | NOT ASSESSED | DLE 15 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s1.f_max_min` | 120 | 1/min | 0.0 | NOT ASSESSED | DLE 15 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s1.pa_min_barg` | 7 | barg | 0.0 | NOT ASSESSED | DLE 15 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s1.pb_max_barg` | 300 | barg | 0.0 | NOT ASSESSED | DLE 15 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s2.i` | 30 | - | 0.0 | NOT ASSESSED | DLE 30 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s2.v_disp_cm3` | 120 | cm3 | 0.0 | NOT ASSESSED | DLE 30 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s2.f_max_min` | 120 | 1/min | 0.0 | NOT ASSESSED | DLE 30 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s2.pa_min_barg` | 15 | barg | 0.0 | NOT ASSESSED | DLE 30 base type, SOURCES.md | none yet |
| DATASHEET | `hulc.s2.pb_max_barg` | 600 | barg | 0.0 | NOT ASSESSED | DLE 30 base type, SOURCES.md | none yet |
| DATASHEET | `kaeser.p_rated_nameplate_kw` | 5.85 | kW | 0.0 | NOT ASSESSED | Kaeser SXC 8 nameplate 5.5 + 0.35 kW (sum, assignment open), SOURCES.md | none yet |
| DATASHEET | `kaeser.ps_barg` | 11 | barg | 0.0 | NOT ASSESSED | Kaeser SXC 8 nameplate, SOURCES.md | none yet |
| DATASHEET | `kaeser.q_fad_m3min` | 0.67 | m3/min FAD | 0.0 | NOT ASSESSED | Kaeser brochure P-651/26D, 10 bar working pressure, SOURCES.md | none yet |
| DATASHEET | `stor.type` | 2 bundles x 16 x 50 L steel cylinders (Type I equivalent); sensors on bundle 1 | - | 0.0 | NOT ASSESSED | nameplate + visual inspection | thermal behaviour: steel = high wall conductivity, less gas stratification than Type III/IV (de Miguel IJHE 2015) |
| DATASHEET | `stor.p_max_barg` | 300 | barg | 0.0 | NOT ASSESSED | VITKOVICE nameplate: maximum allowable pressure PS 300 bar at 65 C; safety valve 330 bar | range check; working pressure set by the process (see stor.p_work_barg) |
| DATASHEET | `stor.p_work_barg` | 200 | barg | 0.0 | NOT ASSESSED | installer H2 Core Systems: stored at 200 bar (UFSC paper confirms operation at 200 bar, DoD 80% analogon) | working upper pressure for cycles |
| DATASHEET | `stor.T_max_C` | 65 | degC | 0.0 | NOT ASSESSED | VITKOVICE nameplate TS max +65 C (STRICTER than the 85 C SAE J2601 vehicle-tank limit) | fast-fill safety limit for Route 2 temperature checks |
| DATASHEET | `stor.T_min_C` | -20 | degC | 0.0 | NOT ASSESSED | VITKOVICE nameplate TS min -20 C | low-temperature limit |
| DATASHEET | `meas.p_sensor_model` | DCT 541, RS485 Modbus RTU, 316L, H2-rated (ISO 15001 oil/grease free) | - | 0.0 | NOT ASSESSED | BD Sensors DCT 541 datasheet in the Storage H2 folder | Route 2 pressure input |
| DATASHEET | `meas.p_sensor_fso_rel` | 0.005 | - | 0.0 | NOT ASSESSED | DCT 541 datasheet: accuracy per IEC 61298-2 (limit point adjustment: non-linearity, hysteresis, repeatability) | Route 2 pressure uncertainty: 0.5% of FULL SCALE (FSO), not of reading |
| DATASHEET | `meas.p_sensor_range_bar` | 400 | bar gauge | 0.0 | NOT ASSESSED | DCT 541, 0...400 bar gauge, ordered per plan 2026-10-08 | Route 2 pressure input; confirm against the delivered sensor label |
| DATASHEET | `meas.p_sensor_thermal_rel` | 0.002 | - | 0.0 | NOT ASSESSED | DCT 541 datasheet: thermal error +-0.2% FSO / 10 K in compensated range -20..80 C | extra pressure error during fast fills (gas temperature swing) |
| DATASHEET | `meas.p_sensor_drift_rel` | 0.001 | - | 0.0 | NOT ASSESSED | DCT 541 datasheet: long-term stability <= +-0.1% FSO / year | annual recalibration budget |
| DATASHEET | `meas.p_sensor_rate_Hz` | 500 | Hz | 0.0 | NOT ASSESSED | DCT 541 datasheet: measuring rate 500 Hz, delay 500 ms | far above the 20 Hz fast-log requirement; latency budget |
| DATASHEET | `fc.rated_power_W` | 2500 | W at 48 V | 0.0 | NOT ASSESSED | IE-LIFT 802 nameplate | load-bin normalisation |
| DATASHEET | `fc.has_internal_dcdc` | True | bool | 0.0 | NOT ASSESSED | IE-LIFT 802 telemetry exposes 'DC/DC Voltage Set Point' and 'DC/DC Current Limit'; output 20-56 V follows the bus | Terminal V/I is NOT stack V/I. Terminal V-I curve is a converter characteristic, not a polarisation curve. |
| DATASHEET | `pv.module_model` | BYD455MGEK-36 | - | 0.0 | NOT ASSESSED | Nameplate photos; technical basis BYD MGK-36 series datasheet DS.PD.E.003 Rev.06 (2024) until the official MGEK-36 datasheet is obtained from BYD Energy do Brasil (proxy) | identifies the F8 module; all pv.* values below follow it |
| DATASHEET | `pv.n_modules` | 28 | - | 0.0 | NOT ASSESSED | user specification 2026-10-21 (PV F8 workbook, Notes 3); count on site to confirm | array power = n_modules x 455 Wp |
| DATASHEET | `pv.p_dc_stc_W` | 12740 | W | 0.0 | NOT ASSESSED | 28 x 455 Wp BYD455MGEK-36 nameplate (PV_F8_System_Specs_Master.xlsx). Superseded: BACKLOG/None | capture ratio in PVSystem.account; now ACTIVE for F8 (NOT valid for the removed legacy ~184 kWp building array) |
| DATASHEET | `pv.bifacial_gain_frac` | 0.0 | - | 0.0 | NOT ASSESSED | MGK-36 series is monofacial (single glass); NOTE nameplate OCR hints at 'MGEK' suffix - bifacial status to be confirmed on the module frame. Superseded PRELIM: 0.05 | DC energy bonus; 0 while monofacial (pending confirmation) |
| DATASHEET | `inv_pv.model` | 2 x Solis S6-GR1P6K string inverter, F8 facade PV-side (SN 1802060225250007 / 1802060225250009) | - | 0.0 | NOT ASSESSED | SolisCloud API inveterList 2026-10-22 (inverterSeries S6-GR1P(2.5-6)K, machine S6-GR1P6K); metadata CSV model code 0206 | identifies the F8 inverters |
| DATASHEET | `inv_fc.model` | Solis S5-EO1P5K-48 off-grid, 230 V, pure sine, CAN/BMS comm | - | 0.0 | NOT ASSESSED | Solis datasheet + nameplate photo (S/N 2051010224220020) | the real FC-side inverter |
| DATASHEET | `inv_fc.nominal_power_W` | 5000 | W | 0.0 | NOT ASSESSED | Solis datasheet: rated output 5 kVA / 5 kW (+-1%) | matches the 2x 2.5 kW FC bank; load-bin normalisation |
| DATASHEET | `inv_fc.battery_V_range` | 40-60 | V | 0.0 | NOT ASSESSED | Solis datasheet + nameplate (battery voltage range) | bus compatibility: FCM-regulated 52 V bus sits inside |
| DATASHEET | `inv_fc.eta_manual_range` | 0.93-0.95 | - | 0.0 | NOT ASSESSED | Solis instruction manual series table: peak efficiency PV-AC 93-95% (differs from the datasheet 96.6% - discrepancy documented, both quoted) | bracket for the discharge-path estimate |
| DATASHEET | `inv_fc.transfer_time_ms` | 10 | ms | 0.0 | NOT ASSESSED | Solis datasheet: transfer time 10 ms typical, 20 ms max | UPS-like transfer behaviour, relevant to POC analysis context |

## The five weakest numbers and how to fix each

1. `comp.overall_efficiency` (REJECTED, legacy-only, wrong device basis). The Kaeser air-compressor energy needs a meter (SIGMA CONTROL 2 kWh counter) during booster runs; no registry value replaces it until measured.
2. `dry.vent_fraction` (GUESS +-50%). Bound with a long charge window: Faraday - tank-pV - known leaks.
3. `el.n_cells` / `fc.n_cells` (GUESS). Ask the manufacturers; Faraday routes scale linearly with them.
4. `meas.p_sensor_fso_bar` (DERIVED from the 0-400 bar range). Confirm the delivered DCT 541 label; the Route-2 pressure term scales linearly with it.
5. `stor.volume_L` (DATASHEET, was wrongly labelled MEASURED). Hydrostatic or geometric confirmation of the 800 L nameplate value; valid only with `bundle_isolated`.

## F8 PV array: open uncertainties (weakest first)

1. Facade POA placeholder (dominant). The reference POA (160 kWh/m2/month) assumes near-optimal tilt; an east-vertical facade is morning-weighted with lower annual yield. Needs PVGIS, the Solis irradiance channel or a pyranometer.
2. East-vertical shading (`pv.shading_rel`, PRELIM): unknown until the layout is surveyed.
3. Soiling (`pv.soiling_rel`, PRELIM): vertical facade soils less than a tilted array; unmeasured.
4. F8 PV inverter (2 x Solis S6-GR1P6K) efficiency: no datasheet registered yet; `inv_pv.eta_pv_ac_peak` and `inv_pv.eta_manual_range` are BACKLOG placeholders - the numbers 0.966 / 0.93-0.95 in them belong to the FC-side Solis S5-EO1P5K-48 and must NOT be used for the F8 S6 inverters (D6). `inv_pv.eta_euro` stays PRELIM (generic literature value, no F8-specific datasheet yet).
4b. F8 station id 1298491919449567877 also hosts F7 (SN ...0011); per-inverter-SN filtering is mandatory before the measured channel goes live.
5. String layout (`pv.string_config`, GUESS): 2 x 7 per inverter assumed; verify at the junction boxes.
6. Imp discrepancy: nameplate 10.50 A vs MGK-36 datasheet 10.90 A (does not affect RTE, matters for fusing).
7. Bifacial status (`pv.bifacial_gain_frac` = 0): 'MGEK' suffix on the nameplate vs monofacial MGK series.

## Constants by construction (never present as measurements)

- EL efficiency via the nameplate route = 62.4% LHV for any data.
- FC efficiency via the nameplate route = 42.9% LHV for any data (a lower bound: nameplate says '<70 g/kWh').
