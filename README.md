# Verlustmappe: an energy loss map of a PV → hydrogen → fuel cell island system

This repository computes **where the energy goes** in the Fotovoltaica/UFSC green-hydrogen
island plant, and **how sure we are about each number**. It is written so that one person
can read it top to bottom, understand every formula, and defend every result.

If you read only one thing, read Part 1. If you need to defend a number, go to
`docs/01_methods_handbook.md` and find its card.

---

## Part 1 · The idea in one page

### The question
Solar electricity is turned into hydrogen (electrolyser), the hydrogen is dried, compressed
and stored, and later turned back into electricity (fuel cell). Every step loses energy.
The **loss map** is the ordered list of those losses, in kWh, for one charge/discharge cycle.
The **round-trip efficiency (RTE)** is what is left at the end divided by what went in.

### The problem that shapes everything
**There is no hydrogen flow meter.** Nothing in this plant measures how much hydrogen
actually flows. Electricity is measured well (telemetry from every device). Hydrogen is not.
Yet every loss between the electrolyser and the fuel cell is a hydrogen loss.

### The solution: estimate hydrogen several independent ways and compare
| Route | Uses | Independent of electricity? | Status today |
|---|---|---|---|
| 1 Faraday | stack current · time · number of cells | no | needs stack-current export (EL) / unavailable (FC) |
| 2 Tank pressure | pressure change · tank volume · real-gas law | **yes** | tank 800 L (nameplate), DCT 541 sensor; temperature via 3-tier model |
| 3 Telemetry | device-reported H₂ flow | no (same source as 1) | available, correlated with Route 1 |
| 4 Water | water consumed / 8.94 | **yes** | needs a scale or water meter |
(The water SYSTEM feeding the EL - BWT bestaqua 14ROC COFFEE RO unit + Popular Filtros cartridge train - is now an energy bar in the loss map; see docs/07_water_system.md.)
| N Nameplate | energy × datasheet specific consumption | n/a | always available, **constant efficiency by construction** |

When independent routes agree, the hydrogen number is trustworthy. When they disagree, the
**disagreement is the uncertainty** we report. This replaces the missing meter with an honest
error bar. It is the scientific contribution of the project.

### The tank, its sensor, and its temperature (Storage H2 folder)
The storage tank is a **VITKOVICE 800 L steel cylinder** (nameplate: PS
300 bar at 65 C, safety valve 330 bar, -20/+65 C). Pressure is measured by a
**BD Sensors DCT 541** (H2-rated 316L, Modbus RTU): 0.5% FSO accuracy, 0.2%
FSO per 10 K thermal error, 500 Hz capability. That replaces the manual-gauge
assumption and improves Route 2's pressure term by roughly a factor of two.

The remaining weak input is the **gas temperature**: an 800 L steel tank sits
far from ambient for hours after a cycle. The pipeline implements three tiers
(`docs/05_tank_thermal_sensing.md`, handbook card C): ambient assumption with
an isothermal/adiabatic honesty bracket (~4% for 15 K), measured top/bottom
sensors when installed (the papers say: gas is uniform during fill,
stratified during hold/empty; bottom-pipe tracked the mean best in the Nexo
study), and a Nexo-style heat-exchange model whose GS_tank is fitted from
resting-period pressure decay. The temperature sensor itself is a planned
option, not yet purchased; the pipeline is ready for it the day it exists.

### The three rules that keep it honest
1. **Every number has a status.** DATASHEET, MEASURED, DERIVED, GUESS or BACKLOG. No number
   enters a calculation without one (`src/verlustmappe/registry.py`).
2. **Every formula has a card.** What, formula, source, assumptions, error-if-wrong, code, test
   (`docs/01_methods_handbook.md`).
3. **Every result says how it was obtained.** Each device returns `efficiency_is_measured`;
   each loss-map bar carries MEASURED / ENVELOPE / GUESS / NAMEPLATE. A figure may never show a
   nameplate constant as if it were a measurement.

---

## Part 2 · What you are looking at (folder by folder)

```
verlustmappe/
├── README.md                      you are here
├── AGENTS.md                      binding agent rules; CLAUDE.md and Copilot point here
├── SPEC.md, SOURCES.md             project scope and cited numeric evidence
├── DECISIONS.md, RULES_LOG.md      approved plant choices and rule rationale
├── HANDOFF.md                      current session handoff
├── tasks/                          scoped assignments (read the active task first)
├── .github/                        CODEOWNERS and CI test/guard workflow
├── docs/                          LIVING DOCUMENTS (reading order)        | HISTORY (90+)
│   ├── 01_methods_handbook.md     one card per formula                    | 90 roadmap original
│   ├── 02_uncertainty_register.md every assumption, weakest first         | 91 roadmap decisions
│   ├── 03_data_dictionary.md      every column, unit, source, caveat      | 92 critical reviews
│   ├── 04_validation_log.md       which test proves what; bugs caught     |
│   ├── 05_tank_thermal_sensing.md tank temperature: papers + sensor option|
│   ├── 06_pv_preliminary_channel.md  the "vorerst" PV channel             |
│   ├── 07_water_system.md          water-system energy bar                 |
│   └── 94_known_defects_legacy.md  frozen legacy defects                   |
├── src/verlustmappe/              the Python package, ordered like the ENERGY PATH
│   ├── constants.py               physical constants with sources   ← FACTS
│   ├── registry.py                device parameters with status     ← ASSUMPTIONS
│   ├── conversions.py             textbook formulas (Faraday, gas law, work, integral)
│   ├── hydrogen/                  the five routes, NUMBERED BY HANDBOOK CARD:
│   │                              route1_faraday -> route2_tank_pv -> route3_telemetry
│   │                              -> route4_water -> routen_nameplate
│   │                              z_realgas (Z table), temperature_model (3 tiers),
│   │                              z_closure (route agreement + gas loss)
│   ├── devices/                   one file per device, NAMED BY ENERGY-FLOW ORDER:
│   │                              pv_measured -> pv_prelim_channel ->
│   │                              pv_inverter -> electrolyzer -> booster ->
│   │                              dryer -> tank -> fuel_cell -> inverter
│   ├── balance/                   accounting, ORDERED: a_modes -> b_segments ->
│   │                              c_events -> d_loss_map -> e_rte
│   ├── analysis/                  paper methods, ORDERED: a_polarization ->
│   │                              b_efficiency -> c_dynamics -> d_purge_recovery ->
│   │                              e_degradation -> f_compare
│   ├── uncertainty/               RSS propagation (GUM) + Monte-Carlo (GUM S1)
│   ├── loaders/                   raw Grafana/Regatron exports -> pipeline columns
│   │                              PV data: Solis F8 only (history in data/raw/solis_f8/); Sept 2026 dataset excluded, D33
│   ├── reporting/                 tables and figures into results/ + register generator
│   └── live_feed.py               rolling-window wrapper for a live plotter
├── tools/                         INTERACTIVE helpers (display & control, no paper numbers)
│   ├── regatron/                  tested G5.BT blueprint + bridge + analyzer
│   ├── fuelcell_analyzer.html     interactive CSV inspection
│   ├── make_readme_demo.py        generate/check README demo values from test_03
│   ├── ci_guard.py                enforce test, registry, and source rules
│   └── server.py, simulate_data.py  live feed server
├── tests/                         run_all.py; each test states its ground truth
├── data/raw/                      untouched exports (evidence; never edited)
├── data/processed/                merged, unit-labelled datasets
└── results/plots, results/tables  everything generated; safe to delete and regenerate
```

**Reading order for a newcomer:** this README → `constants.py` → `registry.py` →
`conversions.py` → `hydrogen/route1..4` + `z_closure` → `devices/` (numbers ARE the
energy path) → `balance/d_loss_map.py` → `docs/01_methods_handbook.md`. About two hours.

**The ordering principle, one sentence:** wherever a list of things exists, its order
is the order the energy flows (devices 01→52) or the order the handbook discusses them
(routes 1→N), so the folder alphabetics, the code, and the paper tell the same story.
History lives at 90+ and is never read top-to-bottom.

---

## Part 3 · The chain, device by device

```
 F8 PV array ──DC──▶ 2 Solis S6-GR1P6K inverters ──AC──▶ Electrolyser EL 2.1 ──H₂ 35 bar──▶ Dryer DRY 2.1
   [measured]             [measured]                         [measured E_in]                   [envelope E, GUESS vent]
                                                                                │
                                                        ┌───────────────────────┘
                                                        ▼
                Fuel cells 2×IE-LIFT 802 ◀──H₂ 0.6 bar── Storage tank ◀──H₂ 200 bar── Air-driven booster
                [measured E_out; H₂ by route]  [Route 2 anchor]              [GUESS efficiency; meter the Kaeser]
                        │
                        ▼ 48 V DC bus (battery in parallel)          ┌──────────────────────────┐
                 AC inverter ──▶ island load                         │ Regatron G5.BT as load   │
                 [assumed 0.96 until metered]                        │ 20 Hz fast log = MEASURED│
                                                                     │ load-branch current      │
                                                                     └──────────────────────────┘
```

F8 is the PV source of the storage chain: 28 × BYD455 modules (12.74 kWp) and
two Solis S6-GR1P6K inverters (serials 1802060225250007 and 1802060225250009).
Only PV AC energy entering the storage path counts at the PV-to-AC boundary
(SPEC.md).

For each device the code answers the same three questions, in a dict with the same keys:
energy in, energy/hydrogen out, what was lost and with what status. The loss map
(`balance/d_loss_map.py`) simply puts the dicts in a row.

**Where the energy goes in the synthetic demo** (`tests/test_03_full_chain.py`).
Charge: 14.4 kWh AC into the electrolyser. Discharge: 5.0 kWh at the FC
terminals. The test is the source of the values below; regenerate them with
`python3 tools/make_readme_demo.py`. CI checks that the table remains in sync.

The synthetic demo has no PV section. Bars are listed in energy-flow order.
The code also reports open-cycle and hydrogen-limited RTEs with an H₂ balance; the
generated summary below reports the test's open-cycle RTE and sensitivity band.

The demo table and plots below are generated by the frozen legacy code (`legacy-1.0`); they retain
known defects listed in `docs/94_known_defects_legacy.md`, notably C3 (the plug bar).

<!-- BEGIN GENERATED DEMO TABLE -->
| Stage | kWh | Status |
|---|---:|---|
| EL conversion (AC->H2) | 5.557 | MEASURED |
| Dryer electrical | 1.200 | ENVELOPE |
| Dryer vent (H2) | 0.000 | NOT OBSERVED |
| Water system (RO unit) | 0.022 | DATASHEET model |
| Water filter train (resin/carbon/micron) | 0.000 | GUESS |
| Compression (air-driven) | 1.086 | GUESS |
| FC conversion (H2->DC) | 6.664 | MEASURED |
| FC control (aux) | 0.600 | ENVELOPE |
| FC inverter (48V DC->AC out) | 0.176 | PRELIM |
| H2 storage change (open cycle: +stored / -drawn) | -2.821 | DERIVED |

**Demo summary:** PASS 03 full chain: EL eta 61.4%, FC eta 42.9%, RTE 25.3% [MC 22.4-26.6], H2 spread 0.0%

*(Legacy open-cycle demo: the FC draws more hydrogen than the cycle produces, and the compressor value is REJECTED, D11. See the FAQ below.)*
<!-- END GENERATED DEMO TABLE -->

Read the status column first, the kWh column second. That is the discipline.

---

## Part 4 · What the real data says so far (and what it cannot say)

**Fuel cell, 22 Sept 2026, 2.7 h with power flowing.** 14 steady segments at ≈1.38 kW, 8 purge candidates
from anode-pressure drops, 2.93 kWh delivered, terminal voltage rising 47.8→50.8 V while power stays roughly constant (I falls as V rises, CV 5%). The first draft called this warm-up; a linear rise with constant power and flat coolant temperature fits battery charging on the bus at least as well. Interpretation open (reviewer 2026-10). What it **cannot** say: the fuel-cell efficiency. The telemetry
current is the DC/DC output, not the stack current, so only Route N applies, and Route N is
the constant 42.9% by construction. The pipeline therefore labels this result `nameplate_fc`
and refuses `efficiency_is_measured`.

**Regatron load branch (controlled input, to come).** The tested
`tools/regatron/` bridge + blueprint drives the G5.BT as a programmable load
(CC/CV/CP, polarization sweeps with round-trip hysteresis, load steps) and
logs the bus at 20 Hz on a real clock. In the pipeline this is the measured
`load_current_A` that turns the battery branch from a guess into a residual
over three measured branches, and the polarization sweep is a swept (not
segment-derived) V-I characteristic. Loader: `loaders/regatron.py`.

**Legacy building-array PV telemetry, 9–30 Sept 2026, 22 days (removed from this project; not F8 and
not the storage-chain PV source).** The legacy dataset records 5.19 MWh AC by the energy counter
(the earlier 4.14 MWh daily-sum figure dropped everything accrued across data gaps, one of which is
38.7 h); inverter efficiency measured from DC and AC, energy-weighted: 0.67 below 2 kW, 0.92 at
2–10 kW, 0.97 at 10–30 kW, 0.98 above 30 kW. The fitted loss has a ~346 W constant term (an
offset worth investigating on a long clean day, reviewer 2026-10). These legacy-array values are
not a measurement of the F8 storage-chain PV source.

**Electrolyser.** Only daily aggregates of H₂ production and pressures so far. No electrical
or stack data. Route 1 waits for the `stack_amperage` export (firmware 1.12 collects it).

---

### The preliminary PV channel ("vorerst")

No PV modules, inverter, cables or distances are chosen yet. The pipeline
therefore has a PRELIM channel (`devices/pv_prelim_channel.py`, registry status
PRELIM): typical-market values anchored on 2025/26 datasheet ranges (TOPCon
modules ~22% efficiency, -0.29%/K; string inverter ~98% Euro efficiency;
DC cable 1%, AC 0.5%; site losses soiling/module variation/shading as placeholders).
It computes the same loss bars the real system will have, with every bar
labelled PRELIM, and it must never be used for absolute yield claims.
Details and the replacement table: `docs/06_pv_preliminary_channel.md`.

```
python3 src/verlustmappe/reporting/report_cli.py pvprelim   # no path needed
```

### Live data channels (status)

| Device | Hardware channel | Pipeline status |
|---|---|---|
| Regatron G5.BT | Enapter blueprint -> bridge, 20 Hz fast log | **running** (tools/regatron, loaders/regatron) |
| EL 2.1 | Enapter cloud ~1 Hz + local Modbus TCP | loader + live layer ready; stack-current export still missing |
| Legacy building array (removed; outside F8 boundary) | SunSpec/Enapter telemetry | legacy loader kept for reference only; not part of the storage chain |
| Solis S6-GR1P6K (F8 PV, 2 units) | SolisCloud API (live + daily history) | loader `loaders/solis_live.py` live; measured E_AC counter verified 2026-10-22 |
| Solis S5-EO1P5K-48 (FC-side) | CAN/BMS built-in, datalogger optional | loader `loaders/solis.py` ready; waiting for the channel + first CSV |

`live_feed.py` consumes any of these once they are in pipeline columns and
feeds a plotter at rolling-window cadence.

## Part 5 · How to run it

```bash
python3 tests/run_all.py                       # all tests, each prints its ground truth
python3 src/verlustmappe/reporting/report_cli.py fc data/processed/fc_retro/fc_merged.csv
python3 src/verlustmappe/reporting/report_cli.py pvf8
```
Outputs land in `results/tables/*.csv` and `results/plots/`. Open any CSV in
`tools/fuelcell_analyzer.html` (double-click the file, drag the CSV in) to inspect
interactively. The HTML tool displays; it never produces a paper number.

---

## Part 6 · Defending the project: the questions you will be asked

**"You have no hydrogen meter. How can you claim any hydrogen number?"**
We do not measure hydrogen; we estimate it by routes that share no inputs (Faraday from
current, real-gas law from tank pressure, stoichiometry from water) and report their
disagreement as the uncertainty. This is standard closure practice when a direct measurement
is missing (see handbook card G). The comparison set in the literature uses a single derived
route with no stated uncertainty; ours is more conservative.

**"Why is the fuel-cell efficiency exactly 42.9%?"**
Because with today's telemetry only the nameplate route exists, and that route is the
datasheet constant. The code says so (`efficiency_is_measured = False`). Getting a
load-dependent efficiency requires the stack current or an H₂ meter. We state this as a
limitation, not a result.

**"Why do you trust Faraday's law with an assumed cell count?"**
We do not trust it blindly: cell count and Faradaic efficiency are GUESS entries with stated
uncertainties, they enter the Monte-Carlo band, and Route 2 (tank) is designed to check
Route 1 independently. When the two disagree, the residual is the gas lost between stack and
tank, itself a loss-map entry.

**"Is 200 bar hydrogen an ideal gas?"**
No. Z = 1.125 at 200 bar, 20 °C (CoolProp/Leachman EOS). Ignoring it overstates stored mass
by about 12.5%. The code uses the tabulated Z with ±1% (0–300 bar, 0–50 °C).

**"Why two RTE numbers?"**
Storage-chain RTE (AC in → AC out) is comparable with the literature. Island RTE (PV-AC in →
AC out) tells the story of this plant. Same pipeline, two boundaries (card K).

**"What is the weakest number in the whole map?"**
Today: the compression energy. Its registered estimate is REJECTED (D11: wrong device
basis, Maximator DLE 30-2); it is replaced by the air-chain model (D13/D14) and the
planned Kaeser metering. The demo RTE below is a frozen legacy result that still uses
that rejected value. The full ranking is in `docs/02_uncertainty_register.md` ("five
weakest numbers"); the tank volume is a DATASHEET value (hydrostatic check open, not a
placeholder).

**"What did you do that the Veritas paper did not?"**
Explicit hydrogen-side uncertainty via independent routes; event-resolved (startup, standby,
POC, purge) energy accounting instead of two steady-state points; provenance status on every
number; a Monte-Carlo band over the assumptions.

---

## Part 7 · Conventions (memorise these)

- **NL** = litre at 0 °C, 1 atm. 1 NL H₂ = 89.9 mg = 2.997 Wh (LHV). 1 kg = 11.1 Nm³ = 33.32 kWh.
- **LHV everywhere** unless a label says HHV. HHV/LHV = 1.183.
- **barg** in the data, absolute in the formulas (+1.01325).
- **kWh** for energy in every returned dict; joules only inside `conversions.py`.
- Efficiency **η = useful out / in** on the same energy basis; RTE = discharged / charged.
- **Uncertainties are relative** (fractions) unless the unit says otherwise; combined by
  root-sum-square when independent.
