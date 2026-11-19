# CONTRACT – what applies

The single place for "what applies". **Rewrite on every change, never append.**
Reasons live in `decisions/`, never here. State: 2026-11-13.

**[E]** decided by the owner – applies. **[V]** proposal – applies only after an owner
decision; until then treat it as an open question, not as a rule.
`(Dnn)` names the old decision a rule was taken from (tag `archive-2026-11`); it does not
need to be read.

## 1 Goal [E]

Show for the real pilot plant where every kWh goes. For each chosen static load point, one
report: the energy path from PV DC to the AC output of the FC inverter with every loss and
its cause, next to the energy demand of the auxiliary consumers. Every number carries its
origin. Missing values are shown as missing. No research into cell or stack details:
market-standard devices may be black boxes with documented inputs and outputs.

## 2 Scope

- [E] Only devices with a **direct influence on production**. Room and building
  infrastructure is excluded: ventilation, gas detection, heating, frost protection,
  room equipment.
- [E] There is no central plant control (PLC, control computer). Controls are built into
  the devices and are not devices of their own. Their consumption belongs to the device;
  where a device reports it separately (FC control, §4), it is booked there.
- [V] Testable wording: a device is in scope if it converts energy to produce, convert,
  treat, move or store a process medium (chain electricity, H₂, process water, compressed
  air).
- [E] The only PV source is F8 ("F8_Fachada Leste", two Solis inverters). The Sept 2026 PV
  dataset (`pv_merged.csv`) is excluded and never evidence (D33).
- [E] PV generation modelling from irradiance and module characteristics is deferred for
  now; work focuses on the energy chain from available PV DC energy.
- [E] No sun-driven production. PV surplus is not part of the calculation and is not a loss.
- [E] The Regatron is a test bench, not a plant device. It is a measurement source (layer 3).
- [E] The comparison with the legacy state (formerly AC8) is dropped.

## 3 Layers [E]

| Layer | Input | Statement |
|---|---|---|
| 1 static | given load points (percentages are examples only) | modelled |
| 2 dynamic | **given load profile**; PV only as availability, no sun-driven control | modelled |
| 3 validated | measurement windows | "validated" only for those windows, within uncertainty |

Accounts A, B, C are defined identically in all layers. No validation is claimed before
layer 3 (D34).

## 4 Accounts

- **A – series path** [E]: PV inverter DC input → PV inverters →
  AC distribution and cable path → EL → dryer → booster → storage →
  FC → DC bus and H₂Core battery → DC cable → FC inverter → AC out.
  Until reviewed DC cable data is available, the PV DC cable is upstream and outside
  this provisional boundary; its loss is not assumed to be zero. Once suitable data
  is available, include the cable in the path with an explicitly reviewed model and
  boundary; do not silently change the meaning of existing results.
  The PV slice is an **allocation**, not proof of direct physical supply. The actual
  EL supply route, including the house distribution and any direct cable, is open.
  Battery throughput losses and stock change are separately visible.
- **B – auxiliary consumers** [E]: electrical consumption outside the series conversion,
  each with its actual supplier and phase, including consumption supplied by the house
  grid, the separate PV battery system or an internal bus. The separate PV battery
  system is only an external supplier; its internals are not modelled. The Kaeser
  (compression) is in B.
- [E] A case report has three named perspectives for the same case:
  - **PV-start path:** the A series path from PV DC to FC inverter AC output.
  - **EL-start path:** the same series path from EL AC input to FC inverter AC output.
  - **Auxiliary energy:** the B consumption associated with all parts of the full chain,
    including water treatment and the allocated compressed-air supply.
  The two paths overlap and are not additive. Separately identifiable auxiliary
  consumption is shown without double counting; embedded or inseparable consumption is
  identified as such. Missing inputs remain open, and storage and battery contributions
  must remain visible. Exact headline formulas are not defined by these names.
- [E] A/B boundary: A contains energy that flows through the series conversion. B contains
  every other electrical consumption, including standby of series-path devices (EL, PV
  inverter, FC inverter) and dryer electricity. The FC inverter's conversion is in A;
  its own auxiliary consumption is in B, with its source and measurement boundary
  identified. An internally supplied B item is not also counted as external input or
  deducted twice from the series path.
- [E] FC control is netted in the series path per D22:
  E_out_net = (E_fc_terminal − E_ctrl) · η_inv. Assumption: drawn from the DC bus before
  the inverter; measurement point open. Booked once.
- **C – system efficiency** [V name and formula; E reporting rule]:
  η_sys = E_AC,out / (E_PV,DC,share + E_B,external + ΔS_correction).
  [E] Reported only once compression and battery have a status. Until then A and B are
  shown side by side with their own totals, **without a summed total**; A never appears
  alone.
- [E] The H₂Core battery belongs to the FC system. It is not the separate PV battery system
  for auxiliary consumers. Battery discharge must not appear as reconversion from H₂.

## 5 Case (layer 1)

- [E] A case contains only inputs, assumptions and justifications. Everything computed
  comes from the model.
- [E] EL anchor: AC power, stack current, operating time, standby power, standby time.
  None of them is derived from another without a documented relation.
- [E] Unit grouping: plant inventory and case operation are separate. Each static phase
  states active, standby and off counts consistent with the installed inventory, and
  the operating point per active unit. Identical units may be grouped under an explicit
  identical-behaviour assumption; different operating points require separate groups.
  The EL anchor rule applies per group: per-unit inputs and group operating/standby
  durations remain independent inputs unless a documented relation is supplied.
- [E] Sum unit-group contributions; compute shared infrastructure once from its associated
  total demand, operating point and duration. Kaeser allocation remains D13/D14 (§6).
  State actual supply and applicable capacity limits; missing curves or inputs stay open.
  Standby of series-path devices belongs to B (§4), with actual supply and no double
  counting. Off is not standby and implies zero only under an explicit case assumption
  of full shutdown of the relevant supplies; otherwise residual consumption stays open.
- [E] A chosen Solis time window shows only that enough PV **energy** was available. It
  does not prove simultaneous power or real supply. [E] The window selection rule is
  recorded beforehand.
- [E] The PV total operating point comes from the window. The inverter is computed at
  total power or total current; its loss is allocated pro rata to the slice
  (a convention, named as such). No inverse function is needed for this allocation.
  Apply the same allocation to the DC cable when its
  model and boundary have been reviewed.
- [E] Every phase duration has a justification: operating requirement, measured
  observation or deliberate convention.
- [E] The FC operating point is set; the FC duration follows from the mole balance
  (otherwise the case is overdetermined). It is a derived result, not a free case input.
  Multiple FC groups with different durations require an explicit operating sequence or
  gas allocation; one total mole balance alone does not determine every group duration.
- [E] Cycle closure is a declared assumption in mol, not a measurement. Intermediate
  storage (dryer hold-up, buffer, tank) is lumped as an assumption.
- [E] Battery: share or ΔS is declared. Net zero is not loss-free; throughput losses are
  computed separately.
- [E] State quantities of an operating point are inputs: tank pressure, gas temperature,
  battery SoC, connected storage volume (800 L isolated, otherwise 1600 L).
- [E] Storage has no working-pressure constant or default setpoint: tank pressure is an
  explicit input, measured for validation. The withdrawn installer value is not a fallback;
  300 barg PS remains a permissible limit only.

## 6 Balance rules

- [E] Losses come from their own physics or from measurement, **never as a difference**
  "input minus output".
- [E] PV inverter measured mode (owner decision 2026-11-16): the interim constant
  EU-efficiency model may report DC × (1 − 0.971) as a modelled conversion loss;
  its uncertainty is not assessed. DC−AC and modelled-AC−measured-AC differences
  are separate diagnostics, never booked losses. For DC = 0 and AC ≠ 0, eta,
  modelled loss and DC−AC diagnostic are None; preserve both readings and flag
  `dc0_ac_nonzero`. The AC boundary and cause remain open; no tolerance is assumed.
  For DC = AC = 0, eta is None and interim modelled loss is 0, without this flag.
  Missing DC leaves eta and modelled loss None. This does not change the FC inverter.
- [E] Consumption is not a loss. A storage change is not a loss. An unexplained residual is
  not a loss.
- [E] Mole balance first: n_start + n_EL = n_end + n_FC + n_vent + n_leak + n_purge.
  Then energy: E_in = E_out + L + ΔS, with ΔS = S_end − S_start.
- [E] Identify H₂ purge, vent and leakage by component where applicable. Gas-line and
  storage leakage are not assumed zero without a justified basis; keep unknown
  contributions open. A pressure drop in a flowing line is not an H₂ leak.
- [E] For the gas lines from EL via HULC to storage, assume zero line pressure and
  enthalpy losses. This is a model assumption, not a measured result or a zero-leakage
  assumption; it does not cover device losses.
- [E] Residuals are diagnostic only and never booked as losses. Production minus delivered
  H₂ may be reported as `production_minus_delivered_residual`; its cause is NOT established
  (purge, vent and leakage are candidates, not findings). In a model case, EL consistency
  (AC versus V(I,T)·I plus rectifier loss) is another diagnostic residual.
- [E] Heat is an output in a full energy balance and part of the conversion loss in a
  useful-energy account – never both.
- [E] A consumption already contained in a higher-level reading is not added again
  (contained-in).
- [E] Compression is consumption (Kaeser electricity) and never part of the stored stock.
- [E] Ideal fill work may only appear as a named ideal-gas quantity, never as electrical
  compression energy (D35).
- [E] Kaeser (D14): supplies HULC stages 1 and 2 and the four Rotex. Variable share by
  air quantity (HULC / Rotex 1–4 / other); READY standby and network leakage as separate
  items; network leakage belongs to the distribution network, not to the HULC. Standby
  by air draw, otherwise split equally (assumption). Kaeser input power open; 6.2 kW is
  a dealer value.
- [E] HULC: distinguish HP-seal H₂ leakage from drive, check-valve, pilot and purge air.
  The documented HP-seal service limit is an upper bound, not an operating loss or a
  measurement; its applicability to the installed H₂ units remains open. Drive and
  control-air losses are not H₂ losses; they are candidates when investigating the
  unresolved air-demand discrepancy. Actual leakage needs measurement.
- [E] HULC air demand (D13): manufacturer curve as a function of H₂ flow at the plant
  operating point; operating point open. The historical estimate of 14.6 Nm³ air per
  Nm³ H₂ belongs to the former 5 Nm³/h example; the derivation of its underlying addends
  is unclear. Its retention as a historical comparison is provisional and UNVERIFIED,
  not approval as a plant parameter, runtime constant, general factor or operating
  limit. Reassess it with better evidence and in the overall-system review; do not
  substitute it for missing compression energy. Geometry (4.59–6.30) is a physical
  lower bound.
- [E] FC inverter, discharge path (D3b): PV-AC datasheet and manual values are not evidence
  for the discharge path. Until measured, `inv_fc.eta` may carry an owner-chosen working
  value with status ASSUMED and an owner-stated band; it is never MEASURED or DATASHEET and
  is never calibrated. While the §8 scheme is not in force, ASSUMED is recorded as GUESS in
  the active D26 vocabulary. This mapping changes only the label; it relaxes no rule: a
  value not proven by data is never given an evidence status, and every derivation and
  owner choice stays marked as such with its basis.

## 7 Missing values and validity [E]

- A missing value gives no number: not zero, not omitted, no default. Dependent totals,
  balances and figures stay open as well. Independent results stay visible (D35).
- Shares only over quantified items and with a named denominator. No "largest loss" and no
  complete Sankey while items are missing (D35).
- Computed path quantities (energy, power, mass, amount, flow, absolute pressure, absolute
  temperature) must not be negative. Changes and differences are signed. Signs of raw
  measurement channels are not an error (D25, D31).
- Non-monotonic time is invalid (D25).
- No limiting (clip, min, max) of physical quantities without a source and a visible note
  in the result.
- EL: Faraday efficiency finite in [0, 1]; cell count finite, positive, integer. Violations
  block the H₂ results; non-numeric, boolean or non-finite values are data errors and raise
  an exception (D36).
- A missing mandatory channel (layer 3) invalidates the affected route, not automatically
  everything (D31).

## 8 Status

- [V] New scheme: `status` = MEASURED > DATASHEET > SECONDARY > ASSUMED > MISSING; the
  weakest input determines the result. `origin` = measured | computed.
  `u_kind` = none | band | envelope. u = 0 means "not assessed" unless stated otherwise.
- `plant/<device>.toml` is the current project/runtime source of truth for plant parameters;
  Python loads it and does not import workbooks. XLSX files and referenced documents are
  evidence/input sources, not immutable truth. Transfers may be corrected or sources
  replaced with owner approval. Check provenance, transfer accuracy and physical plausibility;
  raise conflicts or unsupported values for owner review rather than silently accepting them.
- [E] Most values still lack a page reference and verbatim quote; that is open work, not a
  confirmation of the values.
- [E] The `comp.*` keys (wrong device, Maximator DLE 30-2) must never be used in new code
  (D11).

## 9 Measurement data (layer 3) [E]

- Integration: trapezoid within valid segments; gap if dt > max(3 × nominal interval,
  30 s); the covered fraction is reported (D24).
- Nominal sampling interval only from a demonstrated export grid of the source; F8: 300 s.
  Timestamps are not snapped to a grid (D32).
- Measured cycle closure: CLOSED if |Δn| ≤ 5 % · n_ref and u(Δn) ≤ 5 % · n_ref,
  n_ref = max(n_in, n_out); otherwise NOT VERIFIABLE. The DCT 541 pressure sensor serves
  only this verdict, not calibration; until the repeatability test, measured closure is
  NOT VERIFIABLE (D20, D8).
- Tank pressure and gas temperature are simulated states until the retrofit (D8).
- [E] Independent Route 2 is PAUSED: DCT 541 and Pt100 are not installed and independent
  tank-state data are missing. No countercheck quantity, sensor uncertainty, validation
  contribution or production-minus-delivered residual is reported from this route.
  Static storage modelling and synthetic pVT tests remain available, but cannot vote
  in independent route comparison. Reactivation requires owner-approved independent
  pressures, suitable temperature determination, connected volume/isolation, matching
  time boundaries and accounted gas inflows/outflows. Sensor specifications are planning,
  not installed-sensor evidence.
- [E] Storage temperature concept: one Pt100, 4-wire, class A on the insulated cylinder
  shell (lower/middle near outlet valve), a gas-temperature proxy only at equilibrium.
  Not installed, no hardware ordered, no measured tank temperature exists; inline well open.
  Pt100 data path is suspended: no data integration or required Pt100 channels. Planning
  remains BACKLOG. Enapter telemetry belongs only to its actual measurement points, not the tank.
- [E] Provisional storage/booster calculations without explicit temperature use registered
  `stor.T_assumed_C` = 20 degC, GUESS, owner-chosen rectangular band +/-10 K,
  u_T = 10/sqrt(3) K; registry uncertainty is relative to 293.15 K, not to degC.
  Static main runs calculate at defined scenario temperatures; no seasonal coverage,
  measured temperature or validation is claimed. The band is a separate optional analysis,
  requested by `analyze_temperature_uncertainty=True` in storage and the synthetic tank model, using
  fixed-Z first-order u_T/T. Default runs do not include this term or use its unknown
  correlation as an incompleteness gate. Route 2's other existing uncertainty terms,
  including its 3 K allowance, stay unchanged. In the optional analysis two assumed states
  use a fully common offset by model choice; mixed explicit/assumed states require
  reassessment and make that analysis uncertainty-incomplete. Numeric completeness is
  not volume confirmation or measurement validation; other uncertainty inputs are unchanged.
  Local project Z(T) mass sensitivity at 300 bar absolute / 20 degC is -0.286176 %/K;
  fixed-Z context is -0.341122 %/K. These are calculated references, not model inputs.
  For real-state/measurement evaluation replace the scenario assumption with an approved
  real tank-temperature source; other device temperatures
  are unchanged. Generic temperature functions and synthetic tests remain available;
  The synthetic tank model's tier=2 without explicit temperature input raises an error;
  supplying scenario temperatures does not reactivate independent Route 2.
- [E] Storage 1430 kg is nameplate TARA including the frame, not effective thermal mass.
  Effective thermal mass is open; GS fitting may run gas-only. TARA in a thermal fit requires
  an explicit upper-bound assumption.
- First calibration candidate: FC terminal characteristic from Regatron sweeps (D4). The
  Regatron current is bus/load side, never FC output.

## 10 Publication [E]

Every number appears with status, layer and assumptions. A computed value must never look
like a measured one. "Validated" only from layer 3 and only for the checked windows.

## 11 Agent workflow

Agent workflow, scope, approvals, verification and reporting are governed by `AGENTS.md`.
Project-specific requirements in this contract remain binding. If they conflict, pause the
affected work and ask the owner.
