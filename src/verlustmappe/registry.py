"""Device parameter registry: every number the model needs that is NOT a
physical constant. This is the project's "list of assumptions".

Each entry carries:
  value        the number used
  unit         its unit
  source       where it comes from (datasheet page, paper, measurement, or
               the honest word ASSUMPTION)
  status       how much to trust it, one of:
                 DATASHEET  manufacturer claim, not verified by us
                 MEASURED   we measured it with a named instrument
                 DERIVED    computed from other entries
                 GUESS      an assumption; must be bounded by data later
                 BACKLOG    placeholder; MUST be replaced before any paper number
  uncertainty  relative (fraction) unless the unit says otherwise
  effect       what result this number drives (so you know what breaks if
               it is wrong)

Rule: no calculation may hard-code a number that belongs here.
"""

def P(value, unit, source, status, uncertainty, effect):
    return dict(value=value, unit=unit, source=source, status=status,
                uncertainty=uncertainty, effect=effect)

REGISTRY = {
    # ===================== ELECTROLYSER: Enapter AEM EL 2.1 =====================
    "el.production_rate_NLh": P(500, "NL/h", "Enapter EL 2.1 datasheet (ELE21-DTS-COM02)", "DATASHEET", 0.02,
                                "nominal H2 output; cross-check for Faraday route"),
    "el.power_operative_W":   P(2400, "W", "Enapter EL 2.1 datasheet", "DATASHEET", 0.02,
                                "nominal AC input; steady-state expectation"),
    "el.power_standby_W":     P(15, "W", "Enapter EL 2.1 datasheet", "DATASHEET", 0.05,
                                "standby loss bar in the loss map"),
    "el.spec_energy_kWh_per_Nm3": P(4.8, "kWh/Nm3", "Enapter EL 2.1 datasheet, beginning of life", "DATASHEET", 0.03,
                                "FALLBACK H2 estimate when no stack current is logged; "
                                "WARNING: makes EL efficiency a constant 62.4% by construction"),
    "el.output_pressure_barg": P(35, "barg", "Enapter EL 2.1 datasheet", "DATASHEET", 0.0,
                                "compressor inlet pressure"),
    "el.h2_purity":           P(0.999, "mol fraction", "Enapter EL 2.1 datasheet (35 bar)", "DATASHEET", 0.0005,
                                "mass bookkeeping: impurities are not H2"),
    "el.water_consumption_mLh": P(400, "mL/h", "Enapter EL 2.1 datasheet", "DATASHEET", 0.10,
                                "Route 4 (water balance) expectation"),
    "el.n_cells":             P(120, "-", "ASSUMPTION consistent with 2400 W / (120 x 2.0 V) = 10 A; "
                                "CONFIRM from Enapter (stack spec not public)", "GUESS", 0.05,
                                "Faraday route scales linearly with this number"),
    "el.faradaic_efficiency": P(0.98, "-", "ASSUMPTION: PEM literature current efficiency >96% "
                                "(Yodwong et al., Energies 2020, 13, 4792, DOI 10.3390/en13184792). "
                                "CAVEAT: the paper is PEM; our device is AEM with 35 bar output "
                                "pressure, where crossover raises faradaic losses; 0.98 is carried "
                                "as an extrapolation and must be validated from the stack-current "
                                "route", "GUESS", 0.03,
                                "Faraday route H2 mass; blind to shunt current and crossover"),
    "el.startup_duration_s":  P(990, "s", "UFSC PV-electrolysis study: EL2.1 ramp to nominal after ~990 s", "DERIVED", 0.15,
                                "operating-mode partition: startup window length"),

    # ===================== DRYER: Enapter DRY 2.1 (35 bar) =====================
    "dry.power_operative_W":  P(200, "W", "DRY 2.1 datasheet", "DATASHEET", 0.02,
                                "dryer electrical loss bar; NOTE datasheet also states 0.045 kWh/Nm3 "
                                "at 2.5 Nm3/h = 112 W average, so 200 W is an UPPER envelope"),
    "dry.power_standby_W":    P(10, "W", "DRY 2.1 datasheet", "DATASHEET", 0.05, "standby loss"),
    "dry.rate_Nm3h":          P(2.5, "Nm3/h", "DRY 2.1 datasheet (35 bar version)", "DATASHEET", 0.0, "capacity check"),
    "dry.spec_energy_kWh_Nm3": P(0.045, "kWh/Nm3", "DRY 2.1 datasheet", "DATASHEET", 0.03,
                                "alternative dryer energy estimate: flow-proportional"),
    "dry.max_h2_content_NL":  P(47, "NL", "DRY 2.1 datasheet (safety: max H2 in device)", "DATASHEET", 0.0,
                                "upper bound of H2 lost per regeneration blow-down"),
    "dry.vent_fraction":      P(0.04, "fraction of throughput", "ASSUMPTION: TSA/PSA regeneration vents the cartridge "
                                "hold-up; unmeasured", "GUESS", 0.5,
                                "gas loss bar in the loss map; bound it via long-run tank-pV vs Faraday residual"),

    # ============ COMPRESSOR: Maximator DLE 30-2 air-driven gas booster ============
    "comp.pressure_ratio":    P(60, "-", "Maximator DLE 30-2 TDS", "DATASHEET", 0.0, "stall pressure check"),
    "comp.stroke_volume_cm3": P(120, "cm3/double stroke", "Maximator DLE 30-2 TDS", "DATASHEET", 0.0, "flow capacity check"),
    "comp.max_cycles_per_min": P(100, "1/min", "Maximator DLE 30-2 TDS", "DATASHEET", 0.0, "flow capacity check"),
    "comp.min_suction_bar":   P(20, "bar", "Maximator DLE 30-2 TDS", "DATASHEET", 0.0, "storage lower pressure limit"),
    # Anchor, verified against the FULL TEXT of Bovo, Poli, Trovo, Marini,
    # Guarnieri, "Hydrogen energy storage system in a Multi-Technology
    # Microgrid: technical features and performance", IJHE 48 (2023), part 1
    # (DOI 10.1016/j.ijhydene.2022.11.346), Tab. 3 (CSU):
    #   compression 78.4 kWh + auxiliaries 4.6 kWh for 33.22 Nm3 (tank 40->200
    #   bar, 200 L, DoD 80%). Ideal work for that fill = 1.0-1.3 kWh depending
    #   on the assumed suction pressure (40 bar tank-start vs 35 bar EL output),
    #   computed with the correct mole-weighted fill integral.
    #   -> overall efficiency 1.2-1.6%; registered 0.014 +-30%.
    # This SUPERSEDES both the earlier "56-100 kWh consumed" reading (that
    # number never appears in the paper; the first draft mixed it up with the
    # HGU purifier energy) and the 2.4% figure computed with the single-shot
    # ideal work (nRT ln(p2/p1) overstates a fill, see temperature_model).
    # NOTE on the paper's own eta_CSU = 54.5%: that is H2 energy / (H2 energy +
    # compression electricity), a DIFFERENT quantity, not a contradiction.
    # The paper's booster (Hydraulics Int.) is rated for up to 220 bar like ours.
    "comp.overall_efficiency": P(0.03, "-", "Bovo IJHE 48 (2023) part 1, Tab. 3: 56.36 / 100.2 kWh compression for "
                                "33.22 Nm3 (full / half load), 10-bar booster inlet, fill-integral ideal work "
                                "-> overall 1.9-4.3%; decision 2026-10-21: 0.03 +-40%. Our Kaeser+Maximator "
                                "chain may differ. MEASURE it.",
                                "GUESS", 0.4,
                                "compression loss bar; MUST be replaced by Kaeser energy measurement"),
    "comp.specific_energy_kWh_per_Nm3": P(2.3, "kWh/Nm3", "Bovo IJHE 2023 Tab. 3: 60.28/56.36/100.2 kWh per 33.22 Nm3 "
                                "-> 1.81/1.70/3.02; midpoint of full/half power. Cross-check only; the model "
                                "uses comp.overall_efficiency", "GUESS", 0.4,
                                "pressure-independent sanity check of the compression bar"),

    # ===================== STORAGE =====================
    # Tank identity from the nameplate photo (VITKOVICE CYLINDERS S-16-50-22-27):
    # UN 1049 compressed hydrogen, PS 300 bar / 65 C, safety valve 330 bar,
    # permissible temperature -20/+65 C, water volume 800 L, steel cylinder.
    # This RESOLVES the former BACKLOG on tank volume and the 200/300 bar conflict.
    "stor.volume_L":          P(800, "L", "VITKOVICE cylinder nameplate (photo 20261001_083001): water volume 800 L. "
                                "Status DATASHEET, not MEASURED: a nameplate is a manufacturer claim "
                                "per this project's own status definitions. Hydrostatic or "
                                "geometric confirmation still open", "DATASHEET", 0.005,
                                "Route 2 (tank pV) mass scales linearly with this"),
    "stor.type":              P("2 bundles x 16 x 50 L steel cylinders (Type I equivalent); sensors on bundle 1", "-", "nameplate + visual inspection", "DATASHEET", 0.0,
                                "thermal behaviour: steel = high wall conductivity, less gas stratification than Type III/IV (de Miguel IJHE 2015)"),
    "stor.steel_mass_kg":     P(1430, "kg", "nameplate TARA 1430 kg per bundle (16 cylinders + frame); upper bound, the frame is not fully at gas temperature", "DATASHEET", 0.2,
                                "thermal mass of the tank in the GS fit"),
    "stor.p_max_barg":        P(300, "barg", "VITKOVICE nameplate: maximum allowable pressure PS 300 bar at 65 C; safety valve 330 bar", "DATASHEET", 0.0,
                                "range check; working pressure set by the process (see stor.p_work_barg)"),
    "stor.p_work_barg":       P(200, "barg", "installer H2 Core Systems: stored at 200 bar (UFSC paper confirms operation at 200 bar, DoD 80% analogon)", "DATASHEET", 0.0,
                                "working upper pressure for cycles"),
    "stor.T_max_C":           P(65, "degC", "VITKOVICE nameplate TS max +65 C (STRICTER than the 85 C SAE J2601 vehicle-tank limit)", "DATASHEET", 0.0,
                                "fast-fill safety limit for Route 2 temperature checks"),
    "stor.T_min_C":           P(-20, "degC", "VITKOVICE nameplate TS min -20 C", "DATASHEET", 0.0, "low-temperature limit"),

    # ---- pressure sensor: BD Sensors DCT 541 (folder: DCT 541 datasheet) ----
    "meas.p_sensor_model":    P("DCT 541, RS485 Modbus RTU, 316L, H2-rated (ISO 15001 oil/grease free)", "-", "BD Sensors DCT 541 datasheet in the Storage H2 folder", "DATASHEET", 0.0,
                                "Route 2 pressure input"),
    "meas.p_sensor_fso_rel":  P(0.005, "-", "DCT 541 datasheet: accuracy per IEC 61298-2 (limit point adjustment: non-linearity, hysteresis, repeatability)", "DATASHEET", 0.0,
                                "Route 2 pressure uncertainty: 0.5% of FULL SCALE (FSO), not of reading"),
    "meas.p_sensor_range_bar": P(400, "bar gauge", "DCT 541, 0...400 bar gauge, ordered per plan 2026-10-08", "DATASHEET", 0.0,
                                "Route 2 pressure input; confirm against the delivered sensor label"),
    "meas.p_sensor_fso_bar":  P(2.0, "bar", "0.5% FSO x 400 bar (IEC 61298-2), derived from range and accuracy", "DERIVED", 0.0,
                                "absolute pressure error per reading"),
    "meas.p_sensor_thermal_bar_per_10K": P(0.8, "bar/10K", "0.2% FSO / 10 K x 400 bar, derived", "DERIVED", 0.0,
                                "pressure error during fast fills (not yet in the Route 2 budget)"),
    "meas.p_sensor_thermal_rel": P(0.002, "-", "DCT 541 datasheet: thermal error +-0.2% FSO / 10 K in compensated range -20..80 C", "DATASHEET", 0.0,
                                "extra pressure error during fast fills (gas temperature swing)"),
    "meas.p_sensor_drift_rel": P(0.001, "-", "DCT 541 datasheet: long-term stability <= +-0.1% FSO / year", "DATASHEET", 0.0,
                                "annual recalibration budget"),
    "meas.p_sensor_rate_Hz":  P(500, "Hz", "DCT 541 datasheet: measuring rate 500 Hz, delay 500 ms", "DATASHEET", 0.0,
                                "far above the 20 Hz fast-log requirement; latency budget"),

    # ---- temperature sensing on the tank (PLANNED, option prepared) ----
    "stor.temp_sensor_planned": P("multi-point (top + bottom) PT100 class A or type-K, surface + gas-well; "
                                  "papers recommend bottom-pipe region as closest to mean gas temp "
                                  "(Nexo study: T3) and top/bottom pair for stratification "
                                  "(de Miguel IJHE 2015)", "-", "see handbook card C and docs/05_tank_thermal_sensing.md", "BACKLOG", 0.0,
                                  "Route 2 temperature input; replaces the ambient-T assumption"),

    # ============ FUEL CELL: Intelligent Energy IE-LIFT 802 (x2) ============
    "fc.rated_power_W":       P(2500, "W at 48 V", "IE-LIFT 802 nameplate", "DATASHEET", 0.0, "load-bin normalisation"),
    "fc.h2_consumption_g_per_kWh": P(70, "g/kWh", "IE-LIFT 802 nameplate: '<70 g per kWh' at 25 C, beginning of life",
                                "DATASHEET", 0.05,
                                "nameplate H2 route. NOTE: it is an UPPER BOUND on consumption, hence a "
                                "LOWER BOUND on efficiency (42.9% LHV), and makes FC efficiency a constant "
                                "by construction. Load dependence needs the stack-current route."),
    "fc.n_cells":             P(120, "-", "ASSUMPTION (IE-LIFT stack spec not public); CONFIRM", "GUESS", 0.05,
                                "reverse-Faraday route"),
    "fc.faradaic_efficiency": P(1.00, "-", "ASSUMPTION: all stack current from H2 oxidation (no crossover)", "GUESS", 0.02,
                                "reverse-Faraday route"),
    "fc.control_input_W_max": P(150, "W", "IE-LIFT 802 nameplate 'Rated Input 150 W max'", "DATASHEET", 0.05,
                                "auxiliary/control energy on discharge; nameplate MAX, so an upper envelope"),
    "fc.poc_max_duration_s":  P(12, "s", "FCM802_Test research plan / user manual", "DERIVED", 0.0, "POC event window"),
    "fc.has_internal_dcdc":   P(True, "bool", "IE-LIFT 802 telemetry exposes 'DC/DC Voltage Set Point' and "
                                "'DC/DC Current Limit'; output 20-56 V follows the bus", "DATASHEET", 0.0,
                                "Terminal V/I is NOT stack V/I. Terminal V-I curve is a converter "
                                "characteristic, not a polarisation curve."),

    # ===================== BATTERY (no sensor) =====================
    "bat.capacity_Ah":        P(100, "Ah", "PLACEHOLDER - enter the real battery capacity", "BACKLOG", 0.05,
                                "SoC bookkeeping route for the battery branch"),
    "bat.nominal_V":          P(52, "V", "Regatron README (tested): FCM-802 regulates the bus to 52 V; 48 V is only the factory default. CONFLICTS with the earlier 48 V assumption - CONFIRM at the plant", "DERIVED", 0.02, "battery SoC energy conversion; P=V*I bookkeeping"),

    # ===================== PV / INVERTER =====================
    # PRELIMINARY VERSION ("vorerst"): no real hardware chosen yet. Every entry
    # here is a TYPICAL-MARKET value, not a datasheet claim, and is marked
    # status PRELIM so it is visually distinct from DATASHEET. When real
    # modules/inverters/cables are selected, replace each entry and flip its
    # status. The pv_account() function computes the same loss bars regardless
    # of which tier of inputs it receives.

    # --- module: typical 2025/26 N-type TOPCon monocrystalline, bifacial dual glass ---
    # (market anchors: Trina Vertex N series, 21.0-23.3% module efficiency,
    #  temp coefficient of Pmax -0.29%/K, NOCT ~43 C - datasheets in web search
    #  2025; NOT a commitment to Trina)
    # F8 integration 2026-10-21: the entries below were flipped from PRELIM to
    # DATASHEET with the real BYD455MGEK-36 data (PV_F8_System_Specs_Master.xlsx).
    # The superseded PRELIM values stay reproducible as PLANT_PROFILES
    # "reference_184kWp" in devices/pv_prelim_channel.py (eta 0.220, gamma -0.0029,
    # NOCT 43, bifacial 0.05, degradation 0.004) and are listed in docs/06.
    "pv.module_model":            P("BYD455MGEK-36", "-", "Nameplate photos; technical basis BYD MGK-36 series datasheet DS.PD.E.003 Rev.06 (2024) until the official MGEK-36 datasheet is obtained from BYD Energy do Brasil (proxy)", "DATASHEET", 0.0,
                                "identifies the F8 module; all pv.* values below follow it"),
    "pv.n_modules":               P(28, "-", "user specification 2026-10-21 (PV F8 workbook, Notes 3); count on site to confirm", "DATASHEET", 0.0,
                                "array power = n_modules x 455 Wp"),
    "pv.string_config":           P("2 strings x 7 modules per inverter (assumed; verify at the DC junction boxes)", "-", "ASSUMPTION from array design 2026-10-21", "GUESS", 0.0,
                                "string design checks only (Voc cold, Vmp window)"),
    "pv.module_efficiency_STC":   P(0.209, "-", "BYD MGK-36 datasheet Rev.06 (2024), 455 W class; Inmetro 006667/2021 class A 20.90 %. Superseded PRELIM: 0.220 (typical TOPCon)", "DATASHEET", 0.01,
                                "nominal DC power per m2 of array"),
    "pv.p_dc_stc_W":              P(12740, "W", "28 x 455 Wp BYD455MGEK-36 nameplate (PV_F8_System_Specs_Master.xlsx). Superseded: BACKLOG/None", "DATASHEET", 0.0,
                                "capture ratio in PVSystem.account; now ACTIVE for F8 (NOT valid for the legacy ~184 kWp SMA array)"),
    "pv.p_tc_pmax_per_K":         P(-0.0038, "1/K", "BYD MGK-36 datasheet Rev.06: -0.380 %/degC (2021 brochure lists -0.352; Rev.06 is the newer official document). Superseded PRELIM: -0.0029", "DATASHEET", 0.03,
                                "cell-temperature derating"),
    "pv.noct_C":                  P(45, "degC", "BYD MGK-36 datasheet Rev.06: 45 +-2 degC. Superseded PRELIM: 43", "DATASHEET", 0.05,
                                "cell temperature model: T_cell = T_amb + (NOCT-20)/800 * G"),
    "pv.bifacial_gain_frac":      P(0.0, "-", "MGK-36 series is monofacial (single glass); NOTE nameplate OCR hints at 'MGEK' suffix - bifacial status to be confirmed on the module frame. Superseded PRELIM: 0.05", "DATASHEET", 0.0,
                                "DC energy bonus; 0 while monofacial (pending confirmation)"),
    "pv.degradation_per_year":    P(0.0071, "1/year", "BYD MGK-36 datasheet Rev.06 linear power warranty -0.71 %/yr. Superseded PRELIM: 0.004", "DATASHEET", 0.10,
                                "multi-year studies only"),
    "pv.soi_uncertainty_rel":     P(0.03, "-", "PRELIMINARY: irradiance-sensor uncertainty on capture-ratio (thermopile/pyranometer class)", "PRELIM", 0.5,
                                "capture-ratio bar once a pyranometer exists"),

    # --- TWO SEPARATE INVERTERS (kept apart, they are different devices and
    #     must stay separately analysable: PV-side vs FC-side) ---

    # NOTE F8: inv_pv.eta_euro below is still the PRELIM typical string-inverter
    # value. The F8 units are off-grid Solis inverters with NO published Euro
    # efficiency (96.6 % datasheet peak vs 93-95 % manual), see inv_pv.eta_pv_ac_peak.
    # PV-side inverter: string inverter, PV DC -> AC bus. The SMA Sunny
    # Tripower telemetry already exists; when its measured data is used these
    # PRELIM entries become cross-checks only.
    # F8 PV-side inverters: SAME model as the FC-side Solis (see inv_fc.*).
    "inv_pv.model":               P("Solis S5-EO1P5K-48 off-grid, PV-side units of the F8 facade (2 units, SN 1802060225250007 / 1802060225250009)", "-", "Solis cloud metadata CSV 2026-10-08; Solis S5-EO1P5K-48 datasheet + S5 EO manual (Inverter 1 folder)", "DATASHEET", 0.0,
                                "identifies the F8 inverters"),
    "inv_pv.eta_pv_ac_peak":      P(0.966, "-", "Solis S5-EO1P5K-48 datasheet: PV-AC peak 96.6 %", "DATASHEET", 0.0,
                                "peak reference; discrepancy with manual range kept, see inv_pv.eta_manual_range"),
    "inv_pv.eta_manual_range":    P("0.93-0.95", "-", "Solis S5 EO manual (quoted, not averaged)", "DATASHEET", 0.0,
                                "energy accounting may need the DERIVED midpoint as on the FC side (decision open, docs/06)"),
    "inv_pv.eta_euro":            P(0.980, "-", "PRELIMINARY: typical Euro efficiency 97-98% for modern string inverters (Deye SUN-18/20K 98.0%; SMA core class similar). MEASURED cross-check from own 22-day SMA telemetry: 0.9719 energy-weighted", "PRELIM", 0.01,
                                "PV DC->AC conversion bar"),
    "inv_pv.eta_peak":            P(0.985, "-", "PRELIMINARY: typical max efficiency 98-98.5%", "PRELIM", 0.005,
                                "peak reference only, NOT for energy accounting"),
    "inv_pv.standby_W":           P(5, "W", "PRELIMINARY: typical standby/night consumption 1-10 W", "PRELIM", 0.5,
                                "PV inverter standby bar"),
    "inv_pv.mppt_efficiency":     P(0.995, "-", "PRELIMINARY: typical MPPT efficiency >99%", "PRELIM", 0.005,
                                "folded into conversion bar unless measured separately"),

    # FC-side inverter: CHOSEN DEVICE - Solis S5-EO1P5K-48 off-grid inverter
    # (datasheet + instruction manual in the "Inverter 2" folder; nameplate photo
    # with S/N 2051010224220020 confirms the physical unit is on site).
    # Rated battery voltage 48 V (range 40-60 V) matches the FC bus; the tested
    # Regatron README says the FCM-802 regulates the bus to 52 V - inside range.
    # Rated 5 kVA/5 kW matches the 2x 2.5 kW FC bank exactly.
    # EFFICIENCY - two sources disagree, registered separately (honest handling):
    #   datasheet: peak efficiency (PV-AC path) 96.6%
    #   instruction manual (series table): peak efficiency (PV-AC) 93-95%
    # Both numbers refer to the PV->AC path (MPPT boost + inverter). The
    # BATTERY->AC (discharge) path efficiency is NOT explicitly published.
    # Working value: 0.94 (middle of the manual range), DERIVED status, to be
    # replaced by measurement on the installed unit.
    "inv_fc.model":               P("Solis S5-EO1P5K-48 off-grid, 230 V, pure sine, CAN/BMS comm", "-",
                                "Solis datasheet + nameplate photo (S/N 2051010224220020)", "DATASHEET", 0.0,
                                "the real FC-side inverter"),
    "inv_fc.nominal_power_W":     P(5000, "W", "Solis datasheet: rated output 5 kVA / 5 kW (+-1%)", "DATASHEET", 0.0,
                                "matches the 2x 2.5 kW FC bank; load-bin normalisation"),
    "inv_fc.battery_V_range":     P("40-60", "V", "Solis datasheet + nameplate (battery voltage range)", "DATASHEET", 0.0,
                                "bus compatibility: FCM-regulated 52 V bus sits inside"),
    "inv_fc.eta_peak_pv_ac":      P(0.966, "-", "Solis datasheet: peak efficiency PV-AC path (MPPT + inverter)", "DATASHEET", 0.01,
                                "PV-AC peak reference; NOT the battery-discharge path"),
    "inv_fc.eta_manual_range":    P("0.93-0.95", "-", "Solis instruction manual series table: peak efficiency PV-AC 93-95% (differs from the datasheet 96.6% - discrepancy documented, both quoted)", "DATASHEET", 0.0,
                                "bracket for the discharge-path estimate"),
    "inv_fc.eta":                 P(0.940, "-", "DERIVED: midpoint of the instruction-manual range (93-95%) as the battery->AC discharge efficiency; the datasheet 96.6% refers to the PV-AC path which we do NOT use for the FC discharge. MEASURE on the installed unit", "DERIVED", 0.02,
                                "FC DC->AC conversion bar (discharge side)"),
    "inv_fc.standby_W":           P(20, "W", "ASSUMPTION: datasheet/manual do not publish idle consumption; 20-50 W typical for 48 V off-grid class", "GUESS", 0.5,
                                "FC inverter standby bar"),
    "inv_fc.transfer_time_ms":    P(10, "ms", "Solis datasheet: transfer time 10 ms typical, 20 ms max", "DATASHEET", 0.0,
                                "UPS-like transfer behaviour, relevant to POC analysis context"),

    # --- cables and wiring (DC side PV->inverter, AC side inverter->EL bus) ---
    "cable.dc_loss_rel":          P(0.01, "-", "PRELIMINARY: typical DC-side wiring loss 1-2% for short, well-sized runs; DISTANCES UNKNOWN - placeholder until real lengths/gauges exist", "PRELIM", 0.5,
                                "DC cable bar"),
    "cable.ac_loss_rel":          P(0.005, "-", "PRELIMINARY: typical AC-side loss 0.5-1% for short runs", "PRELIM", 0.5,
                                "AC cable bar"),
    "cable.distance_pv_inverter_m": P(None, "m", "UNKNOWN - to be measured once layout exists", "BACKLOG", 0.0, "drives cable losses"),
    "cable.distance_inverter_EL_m": P(None, "m", "UNKNOWN - to be measured once layout exists", "BACKLOG", 0.0, "drives cable losses"),

    # --- soiling / mismatch / availability (site loss family) ---
    "pv.soiling_rel":             P(0.02, "-", "PRELIMINARY: typical soiling 1-4% (rainy coastal climate, no cleaning contract); Florianopolis is coastal+rains, low end plausible", "PRELIM", 0.5,
                                "soiling bar"),
    "pv.mismatch_rel":            P(0.01, "-", "PRELIMINARY: module mismatch 0.5-2%", "PRELIM", 0.5, "mismatch bar"),
    "pv.shading_rel":             P(0.02, "-", "PRELIMINARY: shading/snow/edge 0-5%, site-specific, UNKNOWN until layout exists", "PRELIM", 0.8,
                                "shading bar"),

    # ===================== MEASUREMENT CHAIN =====================
    "meas.power_rel_unc":     P(0.02, "-", "ASSUMPTION: device-reported power (Enapter/SMA telemetry), "
                                "no independent power analyser yet", "GUESS", 0.5,
                                "floor of every efficiency's uncertainty"),
}

def get(key):
    return REGISTRY[key]["value"]

def entry(key):
    return REGISTRY[key]

def by_status(status):
    return {k: v for k, v in REGISTRY.items() if v["status"] == status}
