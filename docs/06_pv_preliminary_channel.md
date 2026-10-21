# Preliminary PV channel ("vorerst")

Status: **PRELIM**. No real modules, inverter, cables, distances or layout
exist yet. Everything here is a typical-market placeholder that the pipeline
computes with the SAME loss-bar structure it will use for the real system.
When hardware is chosen: replace the registry entries, flip the status, done.

## The status "PRELIM"

A new evidence level between GUESS and DATASHEET: typical-market values
anchored on published 2025/26 datasheet ranges (see sources below), but
NOT a claim about the hardware we will buy. Registered as `PRELIM`, visible
in the uncertainty register, replaced one-for-one later.

## Market anchors used (2025/26 datasheets, web)

- Modules: N-type TOPCon monocrystalline (bifacial dual glass) dominates the
  market; Trina Vertex N class: module efficiency 21.0-23.3%, temperature
  coefficient of Pmax -0.29%/K, NOCT ~43 C, bifacial gain 10-20% (we take 5%
  conservative). We did NOT commit to Trina; these are class anchors.
- Inverter: modern string inverters: peak 98-98.5%, Euro efficiency 97-98%
  (Deye SUN-18/20K: 98.0% Euro / 98.5% peak; SMA core class similar). MPPT
  efficiency >99%. Euro efficiency weights partial load (3% at 5% load, 48%
  at 50%, 20% at 100%) - the right single number for energy accounting.
- Cables: DC 1-2%, AC 0.5-1% for short well-sized runs. DISTANCES UNKNOWN ->
  these bars stay PRELIM with +-50% until the real layout exists.
- Site losses: soiling 1-4% (coastal, rains regularly -> low end), mismatch
  0.5-2%, shading site-specific (UNKNOWN, placeholder 2%).

## The loss chain (standard PV decomposition, IEC 61724 / PVsyst family)

    POA irradiation -> soiling/mismatch/shading -> DC at cell temperature
    -> DC cable -> inverter (Euro eta) -> AC cable -> AC to the bus

Cell temperature: T_cell = T_amb + (NOCT-20)/800 * G (Sandia/NOCT model).
With 43 C NOCT, 25 C ambient and 800 W/m2: T_cell = 43 C, derating
-0.29%/K * 18 K = -5.2% - the single largest bar in the preliminary chain.

## How to run it now

    python3 src/verlustmappe/reporting/report_cli.py pvprelim

Uses a reference plant of 184 kWp (the UFSC array size per H2 Core Systems;
836 m2 at 22% efficiency) and 160 kWh/m2/month POA (Florianopolis annual
mean, coastal subtropical). Output: `pv_prelim_losses.csv` +
`pv_prelim_summary.csv`. Example output: STC potential ~29.4 MWh/month ->
AC ~26.5 MWh/month, capture ratio 0.93.

## What changes when the real design exists

| Registry entry | Replace with | Status becomes |
|---|---|---|
| pv.module_efficiency_STC | chosen module datasheet | DATASHEET |
| pv.p_tc_pmax_per_K, pv.noct_C | module datasheet | DATASHEET |
| pv.bifacial_gain_frac | monofacial? -> 0; bifacial? -> site estimate | DATASHEET/GUESS |
| inv.eta_euro, inv.eta_peak, inv.standby_W | chosen inverter datasheet | DATASHEET |
| cable.dc_loss_rel, cable.ac_loss_rel | computed from real lengths + gauges (Rho_cu, cross-section, length) | MEASURED/DERIVED |
| cable.distance_* | measured | MEASURED |
| pv.soiling_rel | measured (soiling station or cleaning-cycle yield comparison) | MEASURED |
| pv.shading_rel | shading study / layout | DERIVED |
| pv.p_dc_stc_W (was BACKLOG) | real array size | DATASHEET |

The measured SMA telemetry channel (devices/pv_measured.py) stays as is: when it
exists, DC and AC are measured and the bars for soiling/mismatch/shading/
temperature become the only modelled items - exactly as the loss map treats
them today.

## What the preliminary channel must NOT be used for

- Any absolute yield claim for the plant (the reference irradiation is a
  placeholder, not a site measurement).
- Any comparison with the measured SMA telemetry (5.19 MWh over 22 days is
  the measured truth; the preliminary channel is a design aid until then).

## F8 integration 2026-10-21 (BYD 28 x 455 Wp = 12.74 kWp)

Real module and array data replace PRELIM values (source: PV_F8_System_Specs_Master.xlsx,
BYD MGK-36 datasheet Rev.06, Inmetro 006667/2021). Run: `report_cli.py pvf8`.
The preliminary channel and the 184 kWp reference (`pvprelim`) stay as the paper anchor.

| Registry entry | Superseded | New | Status |
|---|---|---|---|
| pv.module_efficiency_STC | 0.220 PRELIM | 0.209 (Inmetro class A 20.90 %) | DATASHEET |
| pv.p_tc_pmax_per_K | -0.0029 PRELIM | -0.0038 (Rev.06; 2021 brochure: -0.352) | DATASHEET |
| pv.noct_C | 43 PRELIM | 45 +-2 | DATASHEET |
| pv.bifacial_gain_frac | 0.05 PRELIM | 0.0 (MGK monofacial; 'MGEK' suffix to confirm) | DATASHEET (pending) |
| pv.degradation_per_year | 0.004 PRELIM | 0.0071 (linear warranty) | DATASHEET |
| pv.p_dc_stc_W | None BACKLOG | 12 740 W | DATASHEET |
| pv.module_model, pv.n_modules | new | BYD455MGEK-36 (MGK-36 proxy), 28 | DATASHEET |
| pv.string_config | new | 2 x 7 per inverter | GUESS |
| inv_pv.model, eta_pv_ac_peak, eta_manual_range | new | Solis S5-EO1P5K-48; 0.966; 0.93-0.95 | DATASHEET |

Unchanged (still PRELIM/GUESS): `cable.*`, `pv.soiling_rel`, `pv.mismatch_rel`,
`pv.shading_rel`, `pv.soi_uncertainty_rel`, `inv_pv.eta_euro`.
The former PRELIM module values remain reproducible as profile `reference_184kWp`.

Discrepancies kept, not resolved:
1. Nameplate BYD455MGEK-36 vs datasheets MGK-36/MIK-36: STC voltages match; Imp 10.50 A
   (nameplate) vs 10.90 A (datasheet). Request the MGEK-36 datasheet from BYD Energy do Brasil.
2. OCR dimensions/weight 2004 x 1098 x 35 mm / 27.6 kg vs datasheet 2094 x 1038 x 35 mm / 24.1 kg:
   verify on the frame; datasheet used.
3. Temperature coefficients Rev.06 (-0.380/-0.360/+0.070) vs 2021 brochure (-0.352/-0.285/+0.051): Rev.06 used.
4. Junction box IP68 (Rev.06) vs IP67 (2021); cable 450 mm vs +320/-260 mm: Rev.06 used.
5. Cell count wording 72 (Rev.06) vs 144 (2021): same module (72 wafers, 144 half-cells).
6. Bifacial hint in the nameplate OCR vs monofacial MGK series: open, registry carries the caveat.

`pv_prelim_losses.csv` was regenerated with the profile refactor; the previously committed CSV
was stale (missing bifacial bar, parallel instead of sequential mismatch/shading). Values now
match the code; the reference totals are unchanged. Monofacial profiles (F8) emit no bifacial bar.

Warning: the POA placeholder (160 kWh/m2/month) is NOT valid for an east-vertical facade.

Pending decisions (not implemented):
1. Island boundary: is F8 THE PV source for `island_rte`, or parallel to the big SMA array?
2. POA source for the facade: PVGIS, Solis irradiance channel or a pyranometer?
3. Bifacial vs monofacial from the module frame.
4. F8 telemetry already flowing (measured mode via SolisCloud) or design stage only?
5. MGEK-36 datasheet request to BYD Energy do Brasil.

