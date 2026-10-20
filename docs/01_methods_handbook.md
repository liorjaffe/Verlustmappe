# Methods handbook

Every calculation in this project, one card each. Same structure every time so
you can answer "where does this number come from?" in under a minute.

Card fields: **What** it computes. **Formula.** **Source** of the formula.
**Assumptions** it rests on (with registry status). **Error if wrong.**
**Code** location. **Verified by** which test and which ground truth.

Notation: E = energy [kWh], P = power [W], I = current [A], V = voltage [V],
n = amount of substance [mol], m = mass [kg], p = absolute pressure [bar],
T = temperature [K], F = Faraday constant, R = gas constant, Z = compressibility.

---

## A. Energy from power telemetry

**What.** Electrical energy in a time window from sampled power.
**Formula.** $$E = \int P\,dt \approx \sum_i \tfrac{1}{2}(P_i + P_{i+1})(t_{i+1}-t_i)$$ (trapezoidal rule), result divided by 3.6·10⁶ for kWh.
**Source.** Numerical integration, any numerical-methods text (e.g. Press et al., *Numerical Recipes*, §4.1).
**Assumptions.** Power telemetry is correct (registry `meas.power_rel_unc`, GUESS 2%, propagated in the Monte-Carlo band as a scale factor on E_in and E_out). **Gap policy (external review 2026-10): gaps are EXCLUDED from the integral, never bridged.** The first draft interpolated across data gaps, which counted unobserved time as production and overstated energy; the opposite of what this card originally claimed. `data_coverage` in every device dict reports the observed fraction of the window. **Alignment rule:** power and current must sit on the same samples; unmatched rows are dropped, never filled (a wide Grafana frame with interleaved timestamps otherwise halves the efficiency).
**Error if wrong.** Directly proportional: 2% power error → 2% energy error → 2% in every efficiency.
**Code.** `conversions.energy_kWh_from_power`.
**Verified by.** `test_01`: 2000 W for 3600 s must equal 2.000 kWh.

## B. Hydrogen mass from stack current (Route 1, Faraday)

**What.** Hydrogen produced (electrolyser) or consumed (fuel cell) at the stack.
**Formula.** Production (electrolyser): $$n_{H_2} = \eta_F \, N_{cells} \frac{\int I\,dt}{2F}$$. Consumption (fuel cell): $$n_{H_2} = N_{cells} \frac{\int I\,dt}{2F\,\eta_F}$$. Then $$m = n M_{H_2}$$.
The direction matters: lower Faradaic efficiency means MORE hydrogen consumed per unit charge in a fuel cell (reviewer 2026-10; the first draft multiplied in both directions and biased FC consumption low).
**Source.** Faraday's laws of electrolysis (1834); Bard & Faulkner, *Electrochemical Methods*, ch. 1.
**Assumptions.** `el.n_cells` (GUESS 120, ±5%), `el.faradaic_efficiency` (GUESS 0.98, ±2%; literature for AEM/PEM 96–99%, Yodwong et al. 2020), the current is the STACK current.
**Error if wrong.** Linear in both: 5% wrong cell count → 5% wrong hydrogen. Faradaic losses (shunt currents, crossover) make the true hydrogen LOWER than the formula says; the route is blind to purge and vent losses downstream.
**Code.** `hydrogen/route1_faraday.py`.
**Verified by.** `test_02`: 10 A × 6 h × 120 cells × 0.98 must equal 0.98·120·10·21600/(2F) mol.
**Data status today.** Electrolyser: stack current not yet exported (firmware collects `stack_amperage`; request extended telemetry). Fuel cell: telemetry 'Amperage' is the DC/DC output current, NOT stack current → route unavailable for the FC until stack values are obtained.

## C. Hydrogen mass from tank pressure (Route 2, real gas)

**What.** Change of hydrogen stored in the tank between two manual gauge readings.
**Formula.** $$\Delta n = \frac{V}{R}\left[\frac{p_2}{Z(p_2,T_2)\,T_2} - \frac{p_1}{Z(p_1,T_1)\,T_1}\right]$$
**Source.** Real-gas equation of state pV = ZnRT; Z from the Leachman et al. (2009) EOS (NIST REFPROP / CoolProp), tabulated at 20 °C, cross-checked against CoolProp (Z(350 bar, 15 °C) = 1.227, Z(200 bar, 20 °C) = 1.125); stated uncertainty ±1%.
**Assumptions.** `stor.volume_L` (DATASHEET, nameplate; hydrostatic confirmation open), pressure sensor DCT 541 ±0.5% FSO = ±1.25 bar absolute per reading on a 250-bar range (ASSUMPTION on the range, CONFIRM), gas temperature = ambient unless measured, Z table ±1%.
**Error if wrong (2026-10, corrected twice — read carefully).** The pressure term is ABSOLUTE (±1.25 bar per reading, √2 for two readings) relative to the swing; Z, T and V are RELATIVE errors amplified by p/(p₂−p₁). Version 1 amplified only the gauge term, version 2 (first fix) also multiplied the absolute term by p/Δp (double-amplification), the current version applies amp only to the relative terms. Current numbers: 20-bar swing 10.4%, 50-bar 4.7%, 100-bar 2.9%, 150-bar 2.4%. Plan swings > 100 bar. Ignoring Z at 200 bar overstates mass by 12%. Gas temperature ≠ ambient on fast fills: a tank 10 K warmer than assumed biases a 50→200 bar fill by +3.5%.
**Code.** `hydrogen/route2_tank_pv.py`, `hydrogen/z_realgas.py`.
**Verified by.** `test_02`: Z(350 bar,15 °C)=1.234, Z(200 bar,20 °C)=1.132, density(200 bar,20 °C)=14.6 kg/m³; Route 2 reproduces Route 1 when the pressure rise is constructed from the same mass.
**Why it matters.** This is the only estimate independent of electrochemistry. Faraday minus tank-pV over a charge window equals all gas lost between stack and tank.

**Temperature model (2026-10, after the Storage H2 papers).** The gas temperature is the weak input, not the pressure: the DCT 541 transmitter (H2-rated, Modbus RTU) measures pressure to 0.5% FSO (IEC 61298-2), while the gas temperature inside an 800 L steel tank is not ambient for hours after a fill. Three tiers: (1) ambient assumption with the isothermal/adiabatic bracket from the Nexo on-board study; (2) measured top/bottom or bottom-pipe temperature (de Miguel IJHE 2015: gas uniform during fill, stratified during hold/empty; the Nexo's bottom-pipe sensor tracked the mean best); (3) lumped energy balance with GS_tank fitted from resting-period pressure decay (Nexo method; their GS = 70 W/K on a vehicle tank). Tank identity from the nameplate photo: VITKOVICE 800 L, PS 300 bar/65 C, safety valve 330 bar - volume BACKLOG resolved, and the temperature limit is 65 C, stricter than the 85 C SAE J2601 vehicle limit. Details and the sensor decision list: `docs/05_tank_thermal_sensing.md`.

## D. Hydrogen from device telemetry (Route 3)

**What.** Integral of Enapter's reported `h2_flow` (NL/h).
**Formula.** $$V_{H_2} = \int \dot V\,dt$$ with dt in hours.
**Source.** Enapter handbook, EL 2.1 collected data.
**Assumptions.** Enapter's internal calculation is correct. It is derived from electrical quantities, so it is CORRELATED with Route 1 and must not be treated as an independent confirmation.
**Error if wrong.** Unknown internally; assigned ±10%.
**Code.** `hydrogen/route3_telemetry.py`. Excluded from the closure mean by default.

## E. Hydrogen from water consumed (Route 4)

**What.** Hydrogen produced from the mass of feed water consumed.
**Formula.** 2H₂O → 2H₂ + O₂, so $$m_{H_2} = m_{H_2O}\,\frac{2.016}{18.015} = m_{H_2O}/8.94$$.
**Source.** Reaction stoichiometry.
**Assumptions.** All water consumed becomes H₂ + O₂. Water leaving as vapour in the gas streams makes this an UPPER bound on hydrogen.
**Code.** `hydrogen/route4_water.py`. Needs a water meter or a scale on the feed tank.

## F. Hydrogen from nameplate specific consumption (Route N)

**What.** Hydrogen from electrical energy using the datasheet number.
**Formula.** EL: $$V = E/4.8\ \mathrm{kWh/Nm^3}$$. FC: $$m = 0.070\,E$$ kg per kWh.
**Source.** Enapter EL 2.1 datasheet (beginning of life); IE-LIFT 802 nameplate "<70 g/kWh".
**Assumptions.** Device behaves like its datasheet.
**Error if wrong.** This route makes efficiency a CONSTANT by construction: EL η = 2.997/4.8 = 62.4% LHV, FC η = 1/(0.070·33.32) = 42.9% LHV, for any data. It cannot show part load, ageing or temperature. The FC value is a bound ("<70"), so 42.9% is a lower bound on efficiency.
**Code.** `hydrogen/routen_nameplate.py`. Every figure using it must say "nameplate".
**Verified by.** `test_02` checks the 62.4% constant.

## G. Closure of routes (the hydrogen uncertainty)

**What.** Combine independent routes into one estimate and one honest uncertainty.
**Formula.** Inverse-variance weighted mean $$\bar m = \frac{\sum w_i m_i}{\sum w_i},\ w_i = 1/\sigma_i^2$$ over routes measuring the SAME quantity; reported uncertainty = max(statistical, spread). **Implemented since 2026-10**: `z_closure` now returns `uncertainty_rel = max(weighted_statistical, max_spread_independent)`; the first draft returned both separately and every consumer silently used the smaller statistical value.
**Loss vs uncertainty (reviewer 2026-10):** Faraday measures gas PRODUCED, the tank route measures gas DELIVERED. Their difference is a physical loss estimate (purge+vent+leak), returned separately as `gas_loss_estimate`, never as an uncertainty. Relabelled routes (`*_minus_vent`) are caught by the exclusion list, so a constant-efficiency route cannot re-enter the independent vote.
**Source.** Taylor, *An Introduction to Error Analysis*, ch. 7; GUM (JCGM 100:2008).
**Assumptions.** Routes marked independent really are (faraday, tank_pv, water). Telemetry and nameplate are excluded from the mean.
**Code.** `hydrogen/z_closure.py`.
**Verified by.** `test_02` (spread ≈ 0 for consistent inputs); `test_03` (a mismatched tank reading produced a 644% spread during development, which is exactly the alarm this function exists for).

## H. Device efficiencies

**Electrolyser** $$\eta_{EL} = \frac{m_{H_2}\,LHV}{E_{AC,in}}$$. **Fuel cell** $$\eta_{FC} = \frac{E_{DC,out}}{m_{H_2}\,LHV}$$.
**Source.** IEA definitions; LHV = 33.32 kWh/kg (119.96 MJ/kg), HHV = 39.41 kWh/kg.
**Assumptions.** LHV basis. The hydrogen mass comes from Route 1 (measured-type) or Route N (constant-type); the returned dict says which via `efficiency_is_measured`.
**Code.** `devices/electrolyzer.py`, `devices/fuel_cell.py`.

## I. Compression work

**What.** Minimum work to move gas from p₁ to p₂ and the electrical energy it cost.
**Formula.** $$W_{ideal} = nRT\ln(p_2/p_1)$$ (isothermal, reversible). $$E_{el} = W_{ideal}/\eta_{overall}$$.
**Source.** Cengel & Boles, *Thermodynamics*, ch. 7.
**Assumptions.** The booster is AIR-driven; the electricity is consumed by the air compressor (Kaeser). `comp.overall_efficiency` GUESS 0.014 ± 30%.
**Anchor (2026-10, verified against the full text).** Bovo, Poli, Trovò, Marini, Guarnieri, IJHE 48 (2023) part 1, DOI 10.1016/j.ijhydene.2022.11.346, Tab. 3: compression 78.4 kWh + auxiliaries 4.6 kWh for 33.22 Nm³, tank 40→200 bar. Correct fill-integral ideal work: 1.0–1.3 kWh (suction 40 vs 35 bar) → overall 1.2–1.6%. The earlier "56–100 kWh consumed" reading mixed up the purifier energy (the number never appears in the paper); the intermediate 2.4% used the single-shot ideal work, which overstates a fill. The paper's eta_CSU = 54.5% is H2 energy/(H2 + compression electricity), a different quantity, not a contradiction.
**Formula note (2026-10).** The ideal work for FILLING a vessel is NOT nRT·ln(p2/p1) evaluated at an average pressure. Per mole: W = RT·[G(p2)−G(p1)]/(p2−p1) with G(p) = p·ln(p/p_suction) − p, implemented in `temperature_model.isothermal_work_mol_integral`. The single-shot form stays correct only when all gas is compressed at once to the top pressure. The arithmetic-mean shortcut overstated a 20→200 bar fill by ~21% and understated 100→200 bar by ~16%.
**Error if wrong.** The compression bar carries ±30% until the Kaeser is metered during booster operation. Isothermal is the theoretical minimum; real multi-stroke boosters are closer to adiabatic per stroke, which only widens the gap the efficiency parameter absorbs.
**Code.** `devices/booster.py`. **Verified by.** `test_01`: 1 mol, 1→10 bar, 293 K = RT ln10 = 5612 J.

## J. Dryer losses

**Electrical.** Two datasheet readings: 200 W "operative" (constant, envelope) vs 0.045 kWh/Nm³ (flow-proportional, 112 W at rated 2.5 Nm³/h). Both are returned; the envelope is used until the dryer is metered.
**Gas.** TSA/PSA regeneration blows down the off-line cartridge. Loss per regeneration ≤ device hold-up (47 NL, datasheet). Frequency unknown → modelled as `dry.vent_fraction` GUESS 4% ± 50%.
**How to bound it.** Over a long charge window, Faraday − tank-pV = total gas lost; subtract known leaks → dryer vent.
**Code.** `devices/dryer.py`.

## K. Round-trip efficiency at two boundaries

**Storage chain.** $$RTE = \frac{(E_{FC,out} - E_{ctrl})\,\eta_{inv}}{E_{EL} + E_{dry} + E_{comp} + E_{standby}}$$
**Island.** $$RTE_{island} = \frac{E_{AC,out}}{E_{PV,AC}}$$
**Source.** Energy-storage convention (discharged/charged electrical energy per cycle), IEC 62933-2-1 family; Veritas paper (IJHE 2023) for the storage-chain form.
**Assumptions.** Inverter efficiency (0.96 assumed until the SMA discharge inverter is metered), FC control energy at nameplate max (envelope).
**Code.** `balance/rte.py`. **Verified by.** `test_03` (synthetic cycle ~26%).

## L. Operating modes and steady segments

**Modes.** standby (P ≤ threshold), startup (first `startup_s` after off→on, 990 s for EL 2.1 from the UFSC measurement), event (POC/purge), steady (rest).
**Steady segments.** contiguous samples above a power floor with CV = σ/μ ≤ 0.15 and duration ≥ 120 s. Their means are the points of characteristic curves.
**Code.** `balance/a_modes.py`, `balance/b_segments.py`.

## M. Event detection

**Electrical events (POC, dips).** Robust z-score $$z = \frac{|x - \mathrm{med}_{60s}(x)|}{1.4826\,\mathrm{MAD}_{60s}(x)}$$, event if z > 4 for ≥ 2 s; events < 10 s apart merged; recovery when back within 1% of the pre-event plateau and holding 30 s.
**Source.** Median/MAD robust statistics (Rousseeuw & Croux, JASA 1993). The 1.4826 factor makes MAD a consistent estimator of σ for Gaussian data.
**Purge events.** First-difference of anode pressure < −150 mbar between consecutive samples, ≥ 10 s apart. Physical criterion; chosen because purges last 1–2 samples at 5-s sampling, below the MAD detector's resolution.
**Outputs are candidates.** Confirm visually (tools/fuelcell_analyzer.html) before naming them.
**Code.** `balance/c_events.py` + `_event_core.py`. **Verified by.** `test_04` on the 2026-09-22 FC log (8 purge candidates, 39 electrical events).

## N. Characteristic curves and key values

From steady segments: V–I and P–I tables, dV/dI, OCV (lowest-current point, not extrapolated), maximum power point, values at reference currents.
**Caution.** IE-LIFT telemetry V, I are TERMINAL values behind a DC/DC converter on a battery bus. The curve is a converter output characteristic, not a stack polarisation curve. Label it "terminal V–I".
**Code.** `analysis/a_polarization.py`. **Verified by.** `test_05` on a constructed linear curve.

## O. Dynamics, start/stop energy, degradation

Ramp rates (median and max slew), cycle detection by threshold on rated power, start-up energy (integral from threshold crossing to first peak, inclusive) and shutdown energy; degradation as V at fixed I across sessions with linear regression (DOE/NREL convention), lifetime projection to −X%.
**Code.** `analysis/c_dynamics.py`, `analysis/e_degradation.py`. **Verified by.** `test_05` against discrete ground truth (a J→kWh unit error was caught and fixed here during development).

## P. Uncertainty

**Analytic.** Root-sum-square of independent relative uncertainties (GUM eq. 10) for single quantities.
**Monte-Carlo.** Every non-measured registry entry drawn from N(value, value·u), loss map recomputed, 5–95% band reported (GUM Supplement 1). The band covers ASSUMPTIONS, not telemetry noise; the latter enters through `meas.power_rel_unc`.
**Code.** `uncertainty/propagate.py`, `uncertainty/montecarlo.py`. **Verified by.** `test_03` (band brackets the point estimate).

## Q. The load branch: Regatron fast log (third data source)

**What.** 20 Hz measurement of bus voltage and load-branch current by the
bridge's independent sampler thread (real wall-clock timestamps, decoupled from
Enapter's ~1 Hz cloud polling).
**Why it matters.** It is the first MEASURED load-branch current. The battery
residual method becomes a computation over three measured branches:
$$I_{bat} = I_{load} - \sum I_{FC,terminal}$$
(pipeline convention: `load_current_A` positive = current drawn by the load;
the residual `I_load - sum(I_FC,terminal)` is therefore positive when the
battery discharges into the bus, i.e. covers the shortfall).
**Source.** `tools/regatron/regatron_bridge.py`, fast_sample_loop at 20 Hz;
format documented in the bridge README. Direction check and watchdog are the
safety layer, not measurement.
**Assumptions.** CURRENT_SIGN_SINK = -1 (CONFIRM on first real run); bus
voltage at the Regatron terminals = bus voltage (sense-lead offset default 0).
**Error if wrong.** Sign error flips the battery residual sign: the check is
the first manual CC run at 2-3 A, watching signs by eye.
**Code.** `loaders/regatron.py` (loader, sign flip, Enapter merge), `tools/regatron/` (bridge + analyzer).
**Verified by.** `test_06`: sign flip, active-window filter, battery residual
(+10 A when load 30 A vs FC terminals 20 A), merge with Enapter clock.
**Scientific caution (from the bridge README, verified in code).** The
measurement is bus-side. On the hybrid bus it is the load branch of the
current balance, never "fuel cell output".

## R. Preliminary PV channel

**What.** Loss bars from irradiation to AC before any real PV hardware exists:
soiling, mismatch, shading, cell-temperature derating, DC cable, inverter
conversion, AC cable.
**Formula.** Standard PV loss decomposition (IEC 61724 performance-ratio
family; PVsyst/SAM loss trees): E_DC = H_POA * A * eta_STC * prod(1 - loss_i) *
[1 + gamma*(T_cell - 25)] * (1 + bifacial); T_cell = T_amb + (NOCT-20)/800 * G
(Sandia/NOCT model); E_AC = E_DC * (1 - dc_cable) * eta_Euro * (1 - ac_cable).
Euro efficiency: weighted across load points (3% at 5%, 48% at 50%, 20% at
100% - the partial-load reality of PV operation).
**Source.** IEC 61724; Sandia NOCT model; Euro-efficiency weighting
(EN 50524 family); market anchors: Trina Vertex N TOPCon datasheets 2025/26
(21.0-23.3%, -0.29%/K), Deye SUN-18/20K (98.0% Euro), solarmathlab/SurgePV
efficiency ranges.
**Assumptions.** ALL of them PRELIM status (typical-market, no real hardware):
module class, temp coefficient, NOCT, bifacial gain, cable losses (distances
UNKNOWN), soiling, mismatch, shading. The largest bar is cell temperature
(-5.2% at NOCT conditions).
**Error if wrong.** Every bar +-50% or worse; the channel exists so the loss
MAP has a PV section before the design exists, never for absolute claims.
**Code.** `devices/pv_prelim_channel.py`, `report_cli.py pvprelim`.
**Verified by.** `test_01`-style physics holds (temperature model tested
indirectly via cell_temperature); no dedicated synthetic test yet because the
channel is a placeholder - add one when the real design lands.

## S. The two inverters (kept deliberately separate)

**What.** Two DIFFERENT devices at two positions of the energy path:
- PV-side inverter (pv_inverter.py): PV DC (high voltage string) -> AC bus.
  Standard Euro efficiency 97-98%; measured on our own SMA telemetry at
  0.9719 energy-weighted over 22 days.
- FC-side inverter (inverter.py): 48-52 V DC bus -> 230 V AC island load.
  CHOSEN DEVICE: Solis S5-EO1P5K-48 off-grid (datasheet + manual + nameplate
  photo in the Inverter 2 folder; S/N on site). Rated 5 kVA/5 kW matches the
  2x 2.5 kW FC bank; battery range 40-60 V covers the FCM-regulated 52 V bus.
  Efficiency caveat, registered honestly: datasheet peak (PV-AC path) 96.6%
  vs instruction-manual range 93-95% - and both refer to the PV->AC path,
  NOT the battery->AC discharge path we need. Working value 0.94 (manual
  midpoint, DERIVED). Physics of low-voltage input stands: 48-52 V doubles
  the current versus a PV string, so I^2R losses scale ~4x at equal
  conductor resistance. Standby unpublished -> GUESS 20 W.

**Why separate.** Merging them into one "inverter efficiency" would hide the
physics: the two devices see different voltage classes and load profiles.
Registry blocks inv_pv.* and inv_fc.* stay separately analysable; when real
hardware is metered, each flips to MEASURED independently.

**Source.** Solis S5-EO1P5K-48 datasheet and instruction manual (Inverter 2
folder); inverter efficiency classes (Euro weighting, EN 50524 family) for the
PV-side context.

**Code.** `devices/pv_inverter.py`, `devices/inverter.py`;
chain uses inv_fc.eta for the discharge bar and inv_pv.eta_euro for the PV bar.
**Verified by.** `test_03` (FC inverter bar at 94% assumption);
`test_08b` (PV Euro assumption vs measured SMA telemetry, 0.8% deviation).
